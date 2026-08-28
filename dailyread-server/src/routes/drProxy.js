// DailyRead PWA 代理路由
// 学习中心账号通过 lc token + 绑定关系代理访问绑定的 DailyRead 数据
// 中间件 lcDrProxyAuth 验证 lc token 并注入 req.drUserId（绑定的 DailyRead user_id）
// 与原 /api/articles 等路由隔离：不签发 DailyRead token、不触发 device_id 冲突
// 复用 dailyTasks.js 的 generateDailyTask 函数保证任务生成逻辑一致
const express = require('express');
const { pool } = require('../db');
const { lcDrProxyAuth } = require('../middleware/lcDrProxyAuth');
const { success, error } = require('../utils/response');
// 复用服务端任务生成逻辑（与鸿蒙/Win 端一致）
const { generateDailyTask } = require('./dailyTasks');

const router = express.Router();

// 所有代理路由均需 lc token + 绑定关系
router.use(lcDrProxyAuth);

// ---------- 文章字段映射（与 articles.js 一致） ----------
// 轻量列表：不含 content/contentHtml/imagewebp/audiobase64 大字段
// 加 hasAudio/hasImage 标记供前端筛选（磨耳跟背需 hasAudio）
const ARTICLE_FIELDS_LIGHT = [
  'id', 'title', 'chinese_chars AS chineseChars',
  'font_family AS fontFamily', 'font_size AS fontSize', 'font_color AS fontColor',
  'is_bold AS isBold', 'is_reading AS isReading', 'is_required AS isRequired',
  'required_days AS requiredDays', 'use_independent_check_rate AS useIndependentCheckRate',
  'independent_check_rate AS independentCheckRate', 'create_time AS createTime',
  'is_long_article AS isLongArticle', 'check_in_days AS checkInDays',
  'completion_rate AS completionRate', 'iscontent',
  'last_modified AS lastModified', 'client_id AS clientId', 'server_updated_at AS serverUpdatedAt',
  "CASE WHEN audiobase64 IS NOT NULL AND audiobase64 != '' THEN 1 ELSE 0 END AS hasAudio",
  "CASE WHEN imagewebp IS NOT NULL AND imagewebp != '' THEN 1 ELSE 0 END AS hasImage"
];

const ARTICLE_FIELDS_FULL = [
  'id', 'title', 'content', 'content_html AS contentHtml', 'chinese_chars AS chineseChars',
  'font_family AS fontFamily', 'font_size AS fontSize', 'font_color AS fontColor',
  'is_bold AS isBold', 'is_reading AS isReading', 'is_required AS isRequired',
  'required_days AS requiredDays', 'use_independent_check_rate AS useIndependentCheckRate',
  'independent_check_rate AS independentCheckRate', 'create_time AS createTime',
  'is_long_article AS isLongArticle', 'check_in_days AS checkInDays',
  'completion_rate AS completionRate', 'imagewebp', 'audiobase64', 'iscontent',
  'last_modified AS lastModified', 'client_id AS clientId', 'server_updated_at AS serverUpdatedAt'
];

// ============================================================
// 文章
// ============================================================

// GET /api/dr/articles?since=  增量拉取（轻量，不含音频/图片大字段）
router.get('/articles', async (req, res) => {
  const since = req.query.since || '';
  try {
    let sql, params;
    if (since) {
      sql = `SELECT ${ARTICLE_FIELDS_LIGHT.join(', ')} FROM articles WHERE user_id = ? AND deleted = 0 AND last_modified > ? ORDER BY last_modified ASC`;
      params = [req.drUserId, since];
    } else {
      sql = `SELECT ${ARTICLE_FIELDS_LIGHT.join(', ')} FROM articles WHERE user_id = ? AND deleted = 0 ORDER BY last_modified ASC`;
      params = [req.drUserId];
    }
    const [rows] = await pool.query(sql, params);
    const [[maxRow]] = await pool.query('SELECT MAX(last_modified) AS maxTs FROM articles WHERE user_id = ? AND deleted = 0', [req.drUserId]);
    const nextSince = (maxRow && maxRow.maxTs) || '';
    return res.json(success({ articles: rows, nextSince }));
  } catch (e) {
    console.error('[dr/articles:get]', e);
    return res.status(500).json(error('拉取失败: ' + e.message, 500));
  }
});

// GET /api/dr/articles/:clientId  单篇详情（含音频/图片大字段，PWA 点击时拉取）
router.get('/articles/:clientId', async (req, res) => {
  try {
    const [rows] = await pool.query(
      `SELECT ${ARTICLE_FIELDS_FULL.join(', ')} FROM articles WHERE user_id = ? AND client_id = ? AND deleted = 0 LIMIT 1`,
      [req.drUserId, req.params.clientId]
    );
    if (rows.length === 0) return res.status(404).json(error('文章不存在', 404));
    return res.json(success(rows[0]));
  } catch (e) {
    console.error('[dr/articles:detail]', e);
    return res.status(500).json(error('查询失败: ' + e.message, 500));
  }
});

// POST /api/dr/articles  新增/修改（按 client_id 幂等，与 articles.js 逻辑一致）
router.post('/articles', async (req, res) => {
  const a = req.body;
  if (!a || !a.clientId || !a.title) {
    return res.status(400).json(error('缺少 clientId 或 title', 400));
  }
  try {
    // 冲突检查
    const [exist] = await pool.query('SELECT last_modified, deleted FROM articles WHERE user_id = ? AND client_id = ?', [req.drUserId, a.clientId]);
    if (exist.length > 0 && exist[0].last_modified && a.lastModified && exist[0].last_modified > a.lastModified) {
      const [serverRow] = await pool.query(`SELECT ${ARTICLE_FIELDS_FULL.join(', ')} FROM articles WHERE user_id = ? AND client_id = ?`, [req.drUserId, a.clientId]);
      return res.status(409).json({ code: 409, message: '冲突：服务端版本更新', data: serverRow[0] });
    }

    const values = [
      a.title, a.content || '', a.contentHtml || null, a.chineseChars || 0,
      a.fontFamily || 'default', a.fontSize || 16, a.fontColor || '#000000', a.isBold ? 1 : 0,
      a.isReading !== undefined ? (a.isReading ? 1 : 0) : 1, a.isRequired ? 1 : 0,
      a.requiredDays || '', a.useIndependentCheckRate ? 1 : 0, a.independentCheckRate || 0,
      a.createTime || null, a.isLongArticle ? 1 : 0, a.checkInDays || 0,
      a.completionRate || 0, a.imagewebp || null, a.audiobase64 || null, a.iscontent !== undefined ? (a.iscontent ? 1 : 0) : 1,
      a.lastModified || null
    ];

    const sql = `INSERT INTO articles (
      user_id, client_id, title, content, content_html, chinese_chars,
      font_family, font_size, font_color, is_bold, is_reading, is_required,
      required_days, use_independent_check_rate, independent_check_rate,
      create_time, is_long_article, check_in_days, completion_rate,
      imagewebp, audiobase64, iscontent, last_modified, deleted
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
    ON DUPLICATE KEY UPDATE
      title=VALUES(title), content=VALUES(content), content_html=VALUES(content_html),
      chinese_chars=VALUES(chinese_chars), font_family=VALUES(font_family),
      font_size=VALUES(font_size), font_color=VALUES(font_color), is_bold=VALUES(is_bold),
      is_reading=VALUES(is_reading), is_required=VALUES(is_required),
      required_days=VALUES(required_days),
      use_independent_check_rate=VALUES(use_independent_check_rate),
      independent_check_rate=VALUES(independent_check_rate),
      create_time=VALUES(create_time), is_long_article=VALUES(is_long_article),
      check_in_days=VALUES(check_in_days), completion_rate=VALUES(completion_rate),
      imagewebp=VALUES(imagewebp), audiobase64=VALUES(audiobase64), iscontent=VALUES(iscontent),
      last_modified=VALUES(last_modified), deleted=0`;
    await pool.query(sql, [req.drUserId, a.clientId, ...values]);

    const [[row]] = await pool.query('SELECT server_updated_at AS serverUpdatedAt FROM articles WHERE user_id = ? AND client_id = ?', [req.drUserId, a.clientId]);
    return res.json(success({ clientId: a.clientId, serverUpdatedAt: row ? row.serverUpdatedAt : null }));
  } catch (e) {
    console.error('[dr/articles:post]', e);
    return res.status(500).json(error('保存失败: ' + e.message, 500));
  }
});

// PATCH /api/dr/articles/:clientId  部分更新（与 articles.js 逻辑一致）
router.patch('/articles/:clientId', async (req, res) => {
  const { clientId } = req.params;
  const body = req.body;
  if (!clientId) return res.status(400).json(error('缺少 clientId', 400));
  try {
    const [exist] = await pool.query('SELECT id FROM articles WHERE user_id = ? AND client_id = ?', [req.drUserId, clientId]);
    if (exist.length === 0) return res.status(404).json(error('文章不存在', 404));
    const fields = [];
    const values = [];
    const camelToSnake = {
      checkInDays: 'check_in_days', completionRate: 'completion_rate', lastModified: 'last_modified',
      isReading: 'is_reading', isRequired: 'is_required', useIndependentCheckRate: 'use_independent_check_rate',
      independentCheckRate: 'independent_check_rate', isBold: 'is_bold', fontSize: 'font_size',
      fontColor: 'font_color', fontFamily: 'font_family', isLongArticle: 'is_long_article',
      iscontent: 'iscontent', requiredDays: 'required_days'
    };
    const boolFields = ['is_reading', 'is_required', 'is_bold', 'is_long_article', 'iscontent', 'use_independent_check_rate'];
    for (const [camelKey, snakeKey] of Object.entries(camelToSnake)) {
      if (body[camelKey] !== undefined) {
        fields.push(`${snakeKey} = ?`);
        values.push(boolFields.includes(snakeKey) ? (body[camelKey] ? 1 : 0) : body[camelKey]);
      }
    }
    if (fields.length === 0) return res.json(success({ ok: true, message: '无需要更新的字段' }));
    values.push(new Date().toISOString(), req.drUserId, clientId);
    fields.push('last_modified = ?');
    await pool.query(`UPDATE articles SET ${fields.join(', ')} WHERE user_id = ? AND client_id = ?`, values);
    return res.json(success({ clientId, updated: true }));
  } catch (e) {
    console.error('[dr/articles:patch]', e);
    return res.status(500).json(error('更新失败: ' + e.message, 500));
  }
});

// DELETE /api/dr/articles/:clientId  软删除
router.delete('/articles/:clientId', async (req, res) => {
  try {
    await pool.query('UPDATE articles SET deleted = 1, last_modified = ? WHERE user_id = ? AND client_id = ?', [new Date().toISOString(), req.drUserId, req.params.clientId]);
    return res.json(success({ clientId: req.params.clientId, deleted: true }));
  } catch (e) {
    return res.status(500).json(error('删除失败: ' + e.message, 500));
  }
});

// ============================================================
// 打卡（与 checkins.js 逻辑一致，articleId = client_id）
// ============================================================

// POST /api/dr/checkins  上报打卡
router.post('/checkins', async (req, res) => {
  const { articleId, checkInDate, checkInTime, lastModified } = req.body;
  if (!articleId || !checkInDate) return res.status(400).json(error('缺少 articleId 或 checkInDate', 400));
  try {
    const [a] = await pool.query('SELECT id FROM articles WHERE user_id = ? AND client_id = ? AND deleted = 0', [req.drUserId, String(articleId)]);
    if (a.length === 0) return res.status(404).json(error('文章不存在', 404));
    const serverArticleId = a[0].id;
    await pool.query(
      `INSERT INTO checkins (user_id, article_id, check_in_date, check_in_time, last_modified)
       VALUES (?, ?, ?, ?, ?)
       ON DUPLICATE KEY UPDATE check_in_time = VALUES(check_in_time), last_modified = VALUES(last_modified)`,
      [req.drUserId, serverArticleId, checkInDate, checkInTime || null, lastModified || new Date().toISOString()]
    );
    return res.json(success({ articleId, checkInDate, ok: true }));
  } catch (e) {
    console.error('[dr/checkins:post]', e);
    return res.status(500).json(error('打卡失败: ' + e.message, 500));
  }
});

// ============================================================
// 每日任务（复用 generateDailyTask，保证逻辑与鸿蒙/Win 端一致）
// ============================================================

function todayStr() {
  const d = new Date();
  const tz = new Date(d.getTime() - d.getTimezoneOffset() * 60000);
  return tz.toISOString().slice(0, 10);
}

// GET /api/dr/daily-tasks/today  获取/自动生成今日任务
router.get('/daily-tasks/today', async (req, res) => {
  const today = todayStr();
  try {
    const [rows] = await pool.query(
      `SELECT t.id, t.task_date AS taskDate, t.count, t.total_words AS totalWords,
              t.last_long_article_ids AS lastLongArticleIds, t.create_time AS createTime,
              t.last_modified AS lastModified,
              (SELECT JSON_ARRAYAGG(JSON_OBJECT(
                'id', i.id, 'articleId', IFNULL(a.client_id, ''), 'articleTitle', i.article_title,
                'wordTarget', i.word_target, 'isCheckedIn', i.is_checked_in,
                'isLongArticle', i.is_long_article, 'isRequired', i.is_required,
                'displayName', i.display_name
              )) FROM daily_task_items i
                LEFT JOIN articles a ON a.id = i.article_id AND a.user_id = t.user_id
               WHERE i.task_id = t.id) AS items
       FROM daily_tasks t
       WHERE t.user_id = ? AND t.task_date = ?`,
      [req.drUserId, today]
    );
    if (rows.length > 0) {
      const row = rows[0];
      if (row.taskDate instanceof Date) {
        const d = row.taskDate;
        row.taskDate = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
      }
      return res.json(success(row));
    }
    // 无今日任务，自动生成（复用 generateDailyTask）
    try {
      const generated = await generateDailyTask(req.drUserId);
      if (!generated.existing) {
        return res.json(success({ ...generated, autoGenerated: true }));
      }
      const [rows2] = await pool.query(
        `SELECT t.id, t.task_date AS taskDate, t.count, t.total_words AS totalWords,
                t.last_long_article_ids AS lastLongArticleIds, t.create_time AS createTime,
                t.last_modified AS lastModified,
                (SELECT JSON_ARRAYAGG(JSON_OBJECT(
                  'id', i.id, 'articleId', IFNULL(a.client_id, ''), 'articleTitle', i.article_title,
                  'wordTarget', i.word_target, 'isCheckedIn', i.is_checked_in,
                  'isLongArticle', i.is_long_article, 'isRequired', i.is_required,
                  'displayName', i.display_name
                )) FROM daily_task_items i
                  LEFT JOIN articles a ON a.id = i.article_id AND a.user_id = t.user_id
                 WHERE i.task_id = t.id) AS items
         FROM daily_tasks t
         WHERE t.user_id = ? AND t.task_date = ?`,
        [req.drUserId, today]
      );
      if (rows2.length > 0 && rows2[0].taskDate instanceof Date) {
        const d = rows2[0].taskDate;
        rows2[0].taskDate = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
      }
      return res.json(success(rows2[0] || null));
    } catch (genErr) {
      console.error('[dr/daily-tasks:today auto-generate]', genErr);
      return res.json(success(null));
    }
  } catch (e) {
    console.error('[dr/daily-tasks:today]', e);
    return res.status(500).json(error('查询失败: ' + e.message, 500));
  }
});

// POST /api/dr/daily-tasks/generate  强制重新生成今日任务
router.post('/daily-tasks/generate', async (req, res) => {
  try {
    const force = req.body && req.body.force ? true : false;
    const result = await generateDailyTask(req.drUserId, force);
    if (result.existing) {
      const today = todayStr();
      const [rows] = await pool.query(
        `SELECT t.id, t.task_date AS taskDate, t.count, t.total_words AS totalWords,
                t.last_long_article_ids AS lastLongArticleIds, t.create_time AS createTime,
                t.last_modified AS lastModified,
                (SELECT JSON_ARRAYAGG(JSON_OBJECT(
                  'id', i.id, 'articleId', IFNULL(a.client_id, ''), 'articleTitle', i.article_title,
                  'wordTarget', i.word_target, 'isCheckedIn', i.is_checked_in,
                  'isLongArticle', i.is_long_article, 'isRequired', i.is_required,
                  'displayName', i.display_name
                )) FROM daily_task_items i
                  LEFT JOIN articles a ON a.id = i.article_id AND a.user_id = t.user_id
                 WHERE i.task_id = t.id) AS items
         FROM daily_tasks t
         WHERE t.user_id = ? AND t.task_date = ?`,
        [req.drUserId, today]
      );
      const existingRow = rows[0];
      if (existingRow && existingRow.taskDate instanceof Date) {
        const d = existingRow.taskDate;
        existingRow.taskDate = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
      }
      return res.json(success({ ...existingRow, generated: false }));
    }
    return res.json(success({ ...result, generated: true }));
  } catch (e) {
    console.error('[dr/daily-tasks:generate]', e);
    return res.status(500).json(error('生成失败: ' + e.message, 500));
  }
});

// POST /api/dr/daily-tasks/today/checkin-by-article  通过 client_id 打卡（与 dailyTasks.js 逻辑一致）
router.post('/daily-tasks/today/checkin-by-article', async (req, res) => {
  const { articleId } = req.body;
  if (!articleId) return res.status(400).json(error('缺少 articleId', 400));
  try {
    const [articles] = await pool.query(
      'SELECT id, check_in_days FROM articles WHERE user_id = ? AND client_id = ? AND deleted = 0',
      [req.drUserId, String(articleId)]
    );
    if (articles.length === 0) return res.status(404).json(error('文章不存在', 404));
    const serverArticleId = articles[0].id;
    const currentDays = Number(articles[0].check_in_days || 0);
    const today = todayStr();

    const [result] = await pool.query(
      `UPDATE daily_task_items i
       INNER JOIN daily_tasks t ON t.id = i.task_id
       SET i.is_checked_in = 1
       WHERE i.article_id = ? AND t.user_id = ? AND t.task_date = ?`,
      [serverArticleId, req.drUserId, today]
    );
    if (result.affectedRows === 0) return res.status(404).json(error('今日任务中未找到该文章', 404));

    const newDays = currentDays + 1;
    const now = new Date();
    const maxDays = new Date(now.getFullYear(), now.getMonth() + 1, 0).getDate();
    const completionRate = maxDays > 0 ? Math.round((newDays / maxDays) * 100) : 0;
    await pool.query(
      `UPDATE articles SET check_in_days = ?, completion_rate = ?, last_modified = ?
       WHERE id = ? AND user_id = ?`,
      [newDays, completionRate, now.toISOString(), serverArticleId, req.drUserId]
    );

    return res.json(success({ articleId, serverArticleId, checkedIn: true, checkInDays: newDays, completionRate }));
  } catch (e) {
    console.error('[dr/daily-tasks:checkin-by-article]', e);
    return res.status(500).json(error('打卡失败: ' + e.message, 500));
  }
});

// ============================================================
// 用户配置（与 config.js 逻辑一致）
// ============================================================

// GET /api/dr/config
router.get('/config', async (req, res) => {
  try {
    const [rows] = await pool.query(
      `SELECT daily_minutes AS dailyMinutes, target_check_rate AS targetCheckRate,
              keep_screen_on AS keepScreenOn, last_reset_month AS lastResetMonth,
              reader_font_size AS readerFontSize, last_sync_time AS lastSyncTime
       FROM user_configs WHERE user_id = ?`,
      [req.drUserId]
    );
    if (rows.length === 0) {
      await pool.query('INSERT INTO user_configs (user_id) VALUES (?)', [req.drUserId]);
      return res.json(success({
        dailyMinutes: 20, targetCheckRate: 30, keepScreenOn: false,
        lastResetMonth: '', readerFontSize: 26, lastSyncTime: ''
      }));
    }
    return res.json(success(rows[0]));
  } catch (e) {
    return res.status(500).json(error('查询失败: ' + e.message, 500));
  }
});

// PUT /api/dr/config
router.put('/config', async (req, res) => {
  const c = req.body;
  try {
    const dailyMinutes = c.dailyMinutes ?? c.daily_minutes ?? 20;
    const targetCheckRate = c.targetCheckRate ?? c.target_check_rate ?? 30;
    const readerFontSize = c.readerFontSize ?? c.reader_font_size ?? 26;
    const lastResetMonth = c.lastResetMonth ?? c.last_reset_month ?? '';
    const lastSyncTime = c.lastSyncTime ?? c.last_sync_time ?? '';
    // keepScreenOn 不从 PWA 覆盖（各端本地设置）
    const [existing] = await pool.query('SELECT keep_screen_on FROM user_configs WHERE user_id = ?', [req.drUserId]);
    const keepScreenOn = existing.length > 0 ? existing[0].keep_screen_on : 0;

    await pool.query(
      `INSERT INTO user_configs (user_id, daily_minutes, target_check_rate, keep_screen_on,
                                  last_reset_month, reader_font_size, last_sync_time)
       VALUES (?, ?, ?, ?, ?, ?, ?)
       ON DUPLICATE KEY UPDATE
         daily_minutes = VALUES(daily_minutes),
         target_check_rate = VALUES(target_check_rate),
         last_reset_month = VALUES(last_reset_month),
         reader_font_size = VALUES(reader_font_size),
         last_sync_time = VALUES(last_sync_time)`,
      [req.drUserId, dailyMinutes, targetCheckRate, keepScreenOn, lastResetMonth, readerFontSize, lastSyncTime]
    );
    return res.json(success({ ok: true }));
  } catch (e) {
    return res.status(500).json(error('保存失败: ' + e.message, 500));
  }
});

module.exports = router;
