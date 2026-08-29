// 文章同步路由：增量拉取、新增/修改、软删除
const express = require('express');
const { pool } = require('../db');
const { authRequired } = require('../middleware/auth');
const { success, error } = require('../utils/response');

const router = express.Router();

// 文章字段映射（驼峰 → 下划线）
const ARTICLE_FIELDS = [
  'id', 'title', 'content', 'content_html AS contentHtml', 'chinese_chars AS chineseChars',
  'font_family AS fontFamily', 'font_size AS fontSize', 'font_color AS fontColor',
  'is_bold AS isBold', 'is_reading AS isReading', 'is_required AS isRequired',
  'required_days AS requiredDays', 'use_independent_check_rate AS useIndependentCheckRate',
  'independent_check_rate AS independentCheckRate', 'create_time AS createTime',
  'is_long_article AS isLongArticle', 'check_in_days AS checkInDays',
  'completion_rate AS completionRate', 'imagewebp', 'audiobase64', 'iscontent',
  'last_modified AS lastModified', 'client_id AS clientId', 'server_updated_at AS serverUpdatedAt'
];

// GET /api/articles?since=&batch=1  增量拉取
// batch=1（鸿蒙端）：按累计体积(~3MB)分批返回，nextSince 用复合游标 'last_modified|id'
//   （同秒多篇文章靠 id 推进，避免截断丢数据），客户端循环拉取直到空批次。
// 不带 batch=1 的旧客户端（Win 端 / PWA）：行为不变，一次返回全量。
router.get('/', authRequired, async (req, res) => {
  const since = req.query.since || '';
  const batchMode = req.query.batch === '1';
  try {
    // 解析复合游标 'last_modified|id'，兼容旧格式纯 last_modified（id 视为 0）
    let sinceTs = since;
    let sinceId = 0;
    if (since && since.includes('|')) {
      const parts = since.split('|');
      sinceTs = parts[0];
      sinceId = Number(parts[1]) || 0;
    }
    let sql, params;
    if (sinceTs) {
      sql = `SELECT ${ARTICLE_FIELDS.join(', ')}, LENGTH(audiobase64) AS _aLen, LENGTH(imagewebp) AS _iLen FROM articles WHERE user_id = ? AND deleted = 0 AND (last_modified > ? OR (last_modified = ? AND id > ?)) ORDER BY last_modified ASC, id ASC`;
      params = [req.userId, sinceTs, sinceTs, sinceId];
    } else {
      sql = `SELECT ${ARTICLE_FIELDS.join(', ')}, LENGTH(audiobase64) AS _aLen, LENGTH(imagewebp) AS _iLen FROM articles WHERE user_id = ? AND deleted = 0 ORDER BY last_modified ASC, id ASC`;
      params = [req.userId];
    }
    const [rows] = await pool.query(sql, params);

    let outRows = rows;
    let nextSince;
    if (batchMode) {
      const LIMIT_BYTES = 3 * 1024 * 1024;
      let acc = 0;
      let cut = rows.length;
      for (let i = 0; i < rows.length; i++) {
        const r = rows[i];
        acc += (r._aLen || 0) + (r._iLen || 0) + (r.content ? String(r.content).length : 0);
        // 至少返回 1 篇，保证游标推进（防单篇超限死循环）
        if (acc >= LIMIT_BYTES && i > 0) { cut = i; break; }
      }
      outRows = rows.slice(0, cut);
      const truncated = cut < rows.length;
      if (outRows.length === 0) {
        // 空批次：同步已完成，游标收敛到服务端最新时间
        const [[maxRow]] = await pool.query('SELECT MAX(last_modified) AS maxTs FROM articles WHERE user_id = ? AND deleted = 0', [req.userId]);
        nextSince = (maxRow && maxRow.maxTs) || '';
      } else if (truncated) {
        const lastRow = outRows[outRows.length - 1];
        nextSince = lastRow.lastModified + '|' + lastRow.id;
      } else {
        nextSince = outRows[outRows.length - 1].lastModified;
      }
      outRows = outRows.map(r => { delete r._aLen; delete r._iLen; return r; });
    } else {
      // 获取当前服务端最新时间，作为下次 since
      const [[maxRow]] = await pool.query('SELECT MAX(last_modified) AS maxTs FROM articles WHERE user_id = ? AND deleted = 0', [req.userId]);
      nextSince = (maxRow && maxRow.maxTs) || '';
    }
    return res.json(success({ articles: outRows, nextSince }));
  } catch (e) {
    console.error('[articles/get]', e);
    return res.status(500).json(error('拉取失败: ' + e.message, 500));
  }
});

// POST /api/articles  新增/修改（按 client_id 幂等）
router.post('/', authRequired, async (req, res) => {
  const a = req.body;
  if (!a || !a.clientId || !a.title) {
    return res.status(400).json(error('缺少 clientId 或 title', 400));
  }
  try {
    // 冲突检查：服务端版本是否更新
    const [exist] = await pool.query('SELECT last_modified, deleted FROM articles WHERE user_id = ? AND client_id = ?', [req.userId, a.clientId]);
    if (exist.length > 0 && exist[0].last_modified && a.lastModified && exist[0].last_modified > a.lastModified) {
      // 服务端更新，返回 409 + 服务端版本
      const [serverRow] = await pool.query(`SELECT ${ARTICLE_FIELDS.join(', ')} FROM articles WHERE user_id = ? AND client_id = ?`, [req.userId, a.clientId]);
      return res.status(409).json(error('冲突：服务端版本更新', 409)).json({ code: 409, message: '冲突', data: serverRow[0] });
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

    // upsert：按 (user_id, client_id) 唯一索引
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
    await pool.query(sql, [req.userId, a.clientId, ...values]);

    // 返回最新 serverUpdatedAt
    const [[row]] = await pool.query('SELECT server_updated_at AS serverUpdatedAt FROM articles WHERE user_id = ? AND client_id = ?', [req.userId, a.clientId]);
    return res.json(success({ clientId: a.clientId, serverUpdatedAt: row ? row.serverUpdatedAt : null }));
  } catch (e) {
    console.error('[articles/post]', e);
    return res.status(500).json(error('保存失败: ' + e.message, 500));
  }
});

// 批量推送（离线队列补传时用）
router.post('/batch', authRequired, async (req, res) => {
  const list = req.body;
  if (!Array.isArray(list)) {
    return res.status(400).json(error('需要数组', 400));
  }
  const results = [];
  for (const a of list) {
    try {
      // 复用单条逻辑（简化处理，逐条调用）
      const [exist] = await pool.query('SELECT last_modified FROM articles WHERE user_id = ? AND client_id = ?', [req.userId, a.clientId]);
      if (exist.length > 0 && exist[0].last_modified && a.lastModified && exist[0].last_modified > a.lastModified) {
        results.push({ clientId: a.clientId, status: 'conflict' });
        continue;
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
      await pool.query(sql, [req.userId, a.clientId, ...values]);
      results.push({ clientId: a.clientId, status: 'ok' });
    } catch (e) {
      results.push({ clientId: a.clientId, status: 'error', message: e.message });
    }
  }
  return res.json(success(results));
});

// PATCH /api/articles/:clientId  部分更新（仅更新指定字段，不校验 title）
router.patch('/:clientId', authRequired, async (req, res) => {
  const { clientId } = req.params;
  const body = req.body;
  if (!clientId) {
    return res.status(400).json(error('缺少 clientId', 400));
  }
  try {
    // 检查是否存在
    const [exist] = await pool.query('SELECT id FROM articles WHERE user_id = ? AND client_id = ?', [req.userId, clientId]);
    if (exist.length === 0) {
      return res.status(404).json(error('文章不存在', 404));
    }
    const fields = [];
    const values = [];
    const allowedFields = ['check_in_days', 'completion_rate', 'last_modified', 'is_reading', 'is_required',
      'use_independent_check_rate', 'independent_check_rate', 'is_bold', 'font_size', 'font_color',
      'font_family', 'is_long_article', 'iscontent', 'required_days'];
    const camelToSnake = {
      checkInDays: 'check_in_days',
      completionRate: 'completion_rate',
      lastModified: 'last_modified',
      isReading: 'is_reading',
      isRequired: 'is_required',
      useIndependentCheckRate: 'use_independent_check_rate',
      independentCheckRate: 'independent_check_rate',
      isBold: 'is_bold',
      fontSize: 'font_size',
      fontColor: 'font_color',
      fontFamily: 'font_family',
      isLongArticle: 'is_long_article',
      iscontent: 'iscontent',
      requiredDays: 'required_days'
    };
    for (const [camelKey, snakeKey] of Object.entries(camelToSnake)) {
      if (body[camelKey] !== undefined) {
        if (['is_reading', 'is_required', 'is_bold', 'is_long_article', 'iscontent', 'use_independent_check_rate'].includes(snakeKey)) {
          fields.push(`${snakeKey} = ?`);
          values.push(body[camelKey] ? 1 : 0);
        } else {
          fields.push(`${snakeKey} = ?`);
          values.push(body[camelKey]);
        }
      }
    }
    if (fields.length === 0) {
      return res.json(success({ ok: true, message: '无需要更新的字段' }));
    }
    values.push(new Date().toISOString(), req.userId, clientId);
    fields.push('last_modified = ?');
    const sql = `UPDATE articles SET ${fields.join(', ')} WHERE user_id = ? AND client_id = ?`;
    await pool.query(sql, values);
    return res.json(success({ clientId, updated: true }));
  } catch (e) {
    console.error('[articles/patch]', e);
    return res.status(500).json(error('更新失败: ' + e.message, 500));
  }
});

// DELETE /api/articles/:clientId  软删除
router.delete('/:clientId', authRequired, async (req, res) => {
  const { clientId } = req.params;
  try {
    await pool.query('UPDATE articles SET deleted = 1, last_modified = ? WHERE user_id = ? AND client_id = ?', [new Date().toISOString(), req.userId, clientId]);
    return res.json(success({ clientId, deleted: true }));
  } catch (e) {
    return res.status(500).json(error('删除失败: ' + e.message, 500));
  }
});

module.exports = router;
