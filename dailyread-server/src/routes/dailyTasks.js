// 每日任务路由：获取今日任务、生成任务、查询历史、打卡任务项
const express = require('express');
const { pool } = require('../db');
const { authRequired } = require('../middleware/auth');
const { success, error } = require('../utils/response');

const router = express.Router();

function todayStr() {
  const d = new Date();
  const tz = new Date(d.getTime() - d.getTimezoneOffset() * 60000);
  return tz.toISOString().slice(0, 10);
}

// ---------- 任务生成逻辑（与客户端 DailyTaskService 保持一致） ----------

function getEffectiveTargetRate(article, globalRate) {
  if (article.use_independent_check_rate && article.independent_check_rate > 0) {
    return Number(article.independent_check_rate);
  }
  return globalRate;
}

function filterTaskPool(articles, globalTargetRate) {
  const today = new Date();
  const maxDays = new Date(today.getFullYear(), today.getMonth() + 1, 0).getDate();
  return articles.filter(article => {
    if (!article.is_reading) return false;
    if (article.is_required) return true;
    const currentCompletionRate = maxDays > 0
      ? Math.round((Number(article.check_in_days || 0) / maxDays) * 100)
      : 0;
    const effectiveRate = getEffectiveTargetRate(article, globalTargetRate);
    return currentCompletionRate < effectiveRate;
  });
}

function calculateMaxWordLimit(dailyMinutes) {
  const randomFactor = 1.01 + Math.random() * 0.1;
  return Math.floor(dailyMinutes * 100 * randomFactor);
}

function getWordCount(article) {
  return article.chinese_chars > 0 ? article.chinese_chars : (article.content ? article.content.length : 0);
}

function isLongArticle(article, maxWordLimit) {
  return getWordCount(article) > maxWordLimit * 0.3;
}

function categorizeArticles(taskPool, maxWordLimit) {
  const longArticles = [];
  const shortArticles = [];
  for (const a of taskPool) {
    if (isLongArticle(a, maxWordLimit)) {
      longArticles.push(a);
    } else {
      shortArticles.push(a);
    }
  }
  return { longArticles, shortArticles };
}

function selectShortArticles(shortArticles, remainingWord) {
  if (remainingWord <= 0 || shortArticles.length === 0) return [];
  const selected = [];
  let totalWords = 0;
  const available = [...shortArticles];
  while (available.length > 0 && totalWords < remainingWord) {
    const randomIndex = Math.floor(Math.random() * available.length);
    const candidate = available[randomIndex];
    const wc = getWordCount(candidate);
    if (totalWords + wc <= remainingWord) {
      selected.push(candidate);
      totalWords += wc;
    }
    available.splice(randomIndex, 1);
  }
  return selected;
}

function arraysEqualIgnoreOrder(a, b) {
  if (a.length !== b.length) return false;
  const sortedA = [...a].sort((x, y) => x - y);
  const sortedB = [...b].sort((x, y) => x - y);
  for (let i = 0; i < sortedA.length; i++) {
    if (sortedA[i] !== sortedB[i]) return false;
  }
  return true;
}

function checkAntiDuplicate(currentIds, lastIds, totalLongCount) {
  if (!lastIds || lastIds.length === 0) return true;
  if (totalLongCount <= 2) {
    return !arraysEqualIgnoreOrder(currentIds, lastIds);
  } else {
    for (let i = 0; i < currentIds.length; i++) {
      if (!lastIds.includes(currentIds[i])) return true;
    }
    return false;
  }
}

async function selectLongArticles(longArticles, maxWordLimit, lastLongArticleIds) {
  const maxTotalWords = maxWordLimit * 0.7;
  const lastIds = lastLongArticleIds || [];
  const totalLongCount = longArticles.length;
  const maxAttempts = 10;

  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    const selected = [];
    let totalWords = 0;
    const available = [...longArticles];
    while (available.length > 0) {
      const randomIndex = Math.floor(Math.random() * available.length);
      const candidate = available[randomIndex];
      const wc = getWordCount(candidate);
      if (totalWords + wc <= maxTotalWords) {
        selected.push(candidate);
        totalWords += wc;
      }
      available.splice(randomIndex, 1);
    }
    if (selected.length === 0) {
      let minLen = Number.MAX_VALUE;
      let minArticle = null;
      for (const a of longArticles) {
        const wc = getWordCount(a);
        if (wc < minLen && wc <= maxTotalWords) {
          minLen = wc;
          minArticle = a;
        }
      }
      if (minArticle) selected.push(minArticle);
    }
    const currentIds = selected.map(a => a.id);
    if (checkAntiDuplicate(currentIds, lastIds, totalLongCount)) {
      return selected;
    }
  }

  // 降级：允许重复
  console.warn('防重复校验多次失败，降级为允许重复');
  const selected = [];
  let totalWords = 0;
  const available = [...longArticles];
  while (available.length > 0 && totalWords < maxTotalWords) {
    const randomIndex = Math.floor(Math.random() * available.length);
    const candidate = available[randomIndex];
    const wc = getWordCount(candidate);
    if (totalWords + wc <= maxTotalWords) {
      selected.push(candidate);
      totalWords += wc;
    }
    available.splice(randomIndex, 1);
  }
  if (selected.length === 0) {
    let minLen = Number.MAX_VALUE;
    let minArticle = null;
    for (const a of longArticles) {
      const wc = getWordCount(a);
      if (wc < minLen && wc <= maxTotalWords) {
        minLen = wc;
        minArticle = a;
      }
    }
    if (minArticle) selected.push(minArticle);
  }
  return selected;
}

/**
 * 生成今日任务列表（与客户端 DailyTaskService.getOrGenerateTodayTasks 逻辑一致）
 * @param {number} userId 用户ID
 * @param {boolean} force 是否强制重新生成（忽略已有任务）
 */
async function generateDailyTask(userId, force = false) {
  const today = todayStr();

  // 0. 跨月重置：如果用户配置的 last_reset_month 不是当前月份，重置 check_in_days
  const currentMonth = today.slice(0, 7); // YYYY-MM
  const [configRows] = await pool.query(
    `SELECT last_reset_month FROM user_configs WHERE user_id = ?`, [userId]
  );
  const lastResetMonth = configRows.length > 0 ? (configRows[0].last_reset_month || '') : '';
  if (lastResetMonth !== currentMonth) {
    // 重置所有文章的 check_in_days 和 completion_rate
    await pool.query(
      `UPDATE articles SET check_in_days = 0, completion_rate = 0
       WHERE user_id = ? AND deleted = 0`, [userId]
    );
    // 更新 last_reset_month
    await pool.query(
      `INSERT INTO user_configs (user_id, last_reset_month) VALUES (?, ?)
       ON DUPLICATE KEY UPDATE last_reset_month = ?`,
      [userId, currentMonth, currentMonth]
    );
    console.log(`[DailyTask] 用户 ${userId} 跨月重置 check_in_days: ${lastResetMonth} -> ${currentMonth}`);
  }

  // 1. 获取用户文章
  const [articles] = await pool.query(
    `SELECT id, client_id, title, content, chinese_chars, is_reading, is_required,
            use_independent_check_rate, independent_check_rate,
            check_in_days, completion_rate, is_long_article
     FROM articles WHERE user_id = ? AND deleted = 0`,
    [userId]
  );

  // 2. 获取用户配置
  const [configs] = await pool.query(
    `SELECT daily_minutes, target_check_rate FROM user_configs WHERE user_id = ?`,
    [userId]
  );
  const config = configs[0] || { daily_minutes: 20, target_check_rate: 30 };
  const dailyMinutes = Number(config.daily_minutes || 20);
  const globalTargetRate = Number(config.target_check_rate || 30);

  // 3. 获取昨日长文章ID列表
  let lastLongArticleIds = [];
  const yesterday = new Date();
  yesterday.setDate(yesterday.getDate() - 1);
  const yesterdayStr = `${yesterday.getFullYear()}-${String(yesterday.getMonth() + 1).padStart(2, '0')}-${String(yesterday.getDate()).padStart(2, '0')}`;
  const [yesterdayTasks] = await pool.query(
    `SELECT last_long_article_ids FROM daily_tasks WHERE user_id = ? AND task_date = ?`,
    [userId, yesterdayStr]
  );
  if (yesterdayTasks.length > 0 && yesterdayTasks[0].last_long_article_ids) {
    try {
      lastLongArticleIds = JSON.parse(yesterdayTasks[0].last_long_article_ids);
    } catch (e) {
      lastLongArticleIds = [];
    }
  }

  // 4. 如果今日已有任务且不强制，直接返回现有
  if (!force) {
    const [existing] = await pool.query(
      `SELECT id FROM daily_tasks WHERE user_id = ? AND task_date = ?`,
      [userId, today]
    );
    if (existing.length > 0) {
      return { existing: true };
    }
  } else {
    // 强制模式：删除今日已有任务
    await pool.query(`DELETE FROM daily_task_items WHERE task_id IN (
      SELECT id FROM daily_tasks WHERE user_id = ? AND task_date = ?
    )`, [userId, today]);
    await pool.query(`DELETE FROM daily_tasks WHERE user_id = ? AND task_date = ?`, [userId, today]);
  }

  // 5. 生成任务列表
  let resultItems = [];
  let selectedLongArticleIds = [];

  if (dailyMinutes > 0 && articles.length > 0) {
    const taskPool = filterTaskPool(articles, globalTargetRate);
    if (taskPool.length > 0) {
      // 必读文章前置
      const requiredArticles = [];
      const remainingPool = [];
      for (const a of taskPool) {
        if (a.is_required) requiredArticles.push(a);
        else remainingPool.push(a);
      }
      for (const a of requiredArticles) {
        resultItems.push({
          article_id: a.id,
          client_id: a.client_id,
          article_title: a.title,
          word_target: getWordCount(a),
          is_long_article: a.is_long_article ? 1 : 0,
          is_required: 1,
          display_name: a.title
        });
      }

      const maxWordLimit = calculateMaxWordLimit(dailyMinutes);
      const { longArticles, shortArticles } = categorizeArticles(remainingPool, maxWordLimit);

      let selectedLongArticles = [];
      let selectedShortArticles = [];

      if (longArticles.length === 0) {
        selectedShortArticles = selectShortArticles(shortArticles, maxWordLimit);
      } else if (longArticles.length === 1) {
        const longArticle = longArticles[0];
        const longWordCount = getWordCount(longArticle);
        if (longWordCount <= maxWordLimit) {
          selectedLongArticles = [longArticle];
          selectedLongArticleIds = [longArticle.id];
          selectedShortArticles = selectShortArticles(shortArticles, maxWordLimit - longWordCount);
        } else {
          selectedShortArticles = selectShortArticles(shortArticles, maxWordLimit);
        }
      } else {
        selectedLongArticles = await selectLongArticles(longArticles, maxWordLimit, lastLongArticleIds);
        selectedLongArticleIds = selectedLongArticles.map(a => a.id);
        let longTotalWords = 0;
        for (const a of selectedLongArticles) longTotalWords += getWordCount(a);
        selectedShortArticles = selectShortArticles(shortArticles, maxWordLimit - longTotalWords);
      }

      for (const a of selectedLongArticles) {
        resultItems.push({
          article_id: a.id,
          client_id: a.client_id,
          article_title: a.title,
          word_target: getWordCount(a),
          is_long_article: 1,
          is_required: 0,
          display_name: a.title
        });
      }
      for (const a of selectedShortArticles) {
        resultItems.push({
          article_id: a.id,
          client_id: a.client_id,
          article_title: a.title,
          word_target: getWordCount(a),
          is_long_article: 0,
          is_required: 0,
          display_name: a.title
        });
      }
    }
  }

  // 5.5 兜底：如果没有选出任何文章但用户有文章，至少选一篇
  if (resultItems.length === 0 && articles.length > 0) {
    // 优先选必读文章，否则选最短的一篇
    const required = articles.find(a => a.is_required && a.is_reading);
    let fallback = required || articles.find(a => a.is_reading);
    if (!fallback) fallback = articles[0];
    resultItems.push({
      article_id: fallback.id,
      client_id: fallback.client_id,
      article_title: fallback.title,
      word_target: getWordCount(fallback),
      is_long_article: fallback.is_long_article ? 1 : 0,
      is_required: fallback.is_required ? 1 : 0,
      display_name: fallback.title
    });
  }

  // 6. 计算总字数（必读文章不计入）
  let totalWords = 0;
  for (const item of resultItems) {
    if (!item.is_required) totalWords += item.word_target;
  }

  // 7. 保存到数据库
  const conn = await pool.getConnection();
  try {
    await conn.beginTransaction();
    const [insertResult] = await conn.query(
      `INSERT INTO daily_tasks (user_id, task_date, count, total_words, last_long_article_ids, create_time, last_modified)
       VALUES (?, ?, ?, ?, ?, ?, ?)`,
      [userId, today, resultItems.length, totalWords, JSON.stringify(selectedLongArticleIds), new Date().toISOString(), new Date().toISOString()]
    );
    const taskId = insertResult.insertId;
    for (const item of resultItems) {
      await conn.query(
        `INSERT INTO daily_task_items (task_id, article_id, article_title, word_target, is_checked_in, is_long_article, is_required, display_name)
         VALUES (?, ?, ?, ?, 0, ?, ?, ?)`,
        [taskId, item.article_id, item.article_title, item.word_target, item.is_long_article, item.is_required, item.display_name]
      );
    }
    await conn.commit();

    // 构造返回数据（articleId 使用 client_id）
    const responseItems = resultItems.map(item => ({
      articleId: item.client_id,
      articleTitle: item.article_title,
      wordTarget: item.word_target,
      isCheckedIn: false,
      isLongArticle: item.is_long_article === 1,
      isRequired: item.is_required === 1,
      displayName: item.display_name
    }));

    return {
      taskId,
      taskDate: today,
      count: resultItems.length,
      totalWords,
      lastLongArticleIds: JSON.stringify(selectedLongArticleIds),
      items: responseItems
    };
  } catch (e) {
    await conn.rollback();
    throw e;
  } finally {
    conn.release();
  }
}

// POST /api/daily-tasks/generate  由服务端生成今日任务
router.post('/generate', authRequired, async (req, res) => {
  try {
    const force = req.body && req.body.force ? true : false;
    const result = await generateDailyTask(req.userId, force);
    if (result.existing) {
      // 今日任务已存在，直接返回现有任务
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
        [req.userId, today]
      );
      const existingRow = rows[0];
      if (existingRow.taskDate instanceof Date) {
        const d = existingRow.taskDate;
        existingRow.taskDate = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
      }
      return res.json(success({ ...existingRow, generated: false }));
    }
    return res.json(success({ ...result, generated: true }));
  } catch (e) {
    console.error('[daily-tasks/generate]', e);
    return res.status(500).json(error('生成失败: ' + e.message, 500));
  }
});

// GET /api/daily-tasks/today  获取今日任务（无任务时自动生成，items 的 articleId 返回 client_id）
router.get('/today', authRequired, async (req, res) => {
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
      [req.userId, today]
    );
    if (rows.length > 0) {
      const row = rows[0];
      // 格式化 taskDate 为 YYYY-MM-DD（MySQL DATE 返回 JS Date 对象，序列化为 ISO 字符串）
      if (row.taskDate instanceof Date) {
        const d = row.taskDate;
        row.taskDate = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
      }
      return res.json(success(row));
    }
    // 无今日任务，自动生成
    try {
      const generated = await generateDailyTask(req.userId);
      if (!generated.existing) {
        return res.json(success({ ...generated, autoGenerated: true }));
      }
      // 生成后再次读取
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
        [req.userId, today]
      );
      if (rows2.length > 0 && rows2[0].taskDate instanceof Date) {
        const d = rows2[0].taskDate;
        rows2[0].taskDate = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
      }
      return res.json(success(rows2[0] || null));
    } catch (genErr) {
      console.error('[daily-tasks/today auto-generate]', genErr);
      return res.json(success(null));
    }
  } catch (e) {
    console.error('[daily-tasks/today]', e);
    return res.status(500).json(error('查询失败: ' + e.message, 500));
  }
});

// POST /api/daily-tasks/today  保存/更新今日任务（客户端生成后上报）
router.post('/today', authRequired, async (req, res) => {
  const today = todayStr();
  const { count, totalWords, lastLongArticleIds, items } = req.body;
  const conn = await pool.getConnection();
  try {
    await conn.beginTransaction();
    // upsert 任务
    const [result] = await conn.query(
      `INSERT INTO daily_tasks (user_id, task_date, count, total_words, last_long_article_ids, create_time, last_modified)
       VALUES (?, ?, ?, ?, ?, ?, ?)
       ON DUPLICATE KEY UPDATE
         count = VALUES(count), total_words = VALUES(total_words),
         last_long_article_ids = VALUES(last_long_article_ids), last_modified = VALUES(last_modified)`,
      [req.userId, today, count || 0, totalWords || 0, lastLongArticleIds || '', new Date().toISOString(), new Date().toISOString()]
    );
    const taskId = result.insertId;
    // 若任务已存在，insertId 为 0，需要查询
    let realTaskId = taskId;
    if (taskId === 0) {
      const [[r]] = await conn.query('SELECT id FROM daily_tasks WHERE user_id = ? AND task_date = ?', [req.userId, today]);
      realTaskId = r.id;
    }
    // 更新明细：先删后插（item.articleId 是 client_id，解析为服务端 id）
    if (Array.isArray(items)) {
      await conn.query('DELETE FROM daily_task_items WHERE task_id = ?', [realTaskId]);
      for (const it of items) {
        // 解析 client_id → 服务端 articles.id
        let serverArticleId = 0;
        if (it.articleId) {
          const [a] = await conn.query('SELECT id FROM articles WHERE user_id = ? AND client_id = ? AND deleted = 0', [req.userId, String(it.articleId)]);
          if (a.length > 0) {
            serverArticleId = a[0].id;
          }
        }
        await conn.query(
          `INSERT INTO daily_task_items (task_id, article_id, article_title, word_target, is_checked_in, is_long_article, is_required, display_name)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
          [realTaskId, serverArticleId, it.articleTitle, it.wordTarget || 0, it.isCheckedIn ? 1 : 0, it.isLongArticle ? 1 : 0, it.isRequired ? 1 : 0, it.displayName || '']
        );
      }
    }
    await conn.commit();
    return res.json(success({ taskId: realTaskId, taskDate: today }));
  } catch (e) {
    await conn.rollback();
    console.error('[daily-tasks/post]', e);
    return res.status(500).json(error('保存失败: ' + e.message, 500));
  } finally {
    conn.release();
  }
});

// POST /api/daily-tasks/today/checkin  打卡某条任务项（通过 itemId）
router.post('/today/checkin', authRequired, async (req, res) => {
  const { itemId } = req.body;
  if (!itemId) {
    return res.status(400).json(error('缺少 itemId', 400));
  }
  try {
    const today = todayStr();

    // 1. 先获取任务项关联的 article_id
    const [items] = await pool.query(
      `SELECT i.article_id FROM daily_task_items i
       INNER JOIN daily_tasks t ON t.id = i.task_id
       WHERE i.id = ? AND t.user_id = ? AND t.task_date = ?`,
      [itemId, req.userId, today]
    );
    if (items.length === 0) {
      return res.status(404).json(error('任务项不存在或不属于今日', 404));
    }
    const articleId = items[0].article_id;

    // 2. 更新打卡状态
    const [result] = await pool.query(
      `UPDATE daily_task_items i
       INNER JOIN daily_tasks t ON t.id = i.task_id
       SET i.is_checked_in = 1
       WHERE i.id = ? AND t.user_id = ? AND t.task_date = ?`,
      [itemId, req.userId, today]
    );
    if (result.affectedRows === 0) {
      return res.status(404).json(error('任务项不存在或不属于今日', 404));
    }

    // 3. 更新文章的 check_in_days 和 completion_rate
    if (articleId) {
      const [articles] = await pool.query(
        'SELECT check_in_days FROM articles WHERE id = ? AND user_id = ?',
        [articleId, req.userId]
      );
      if (articles.length > 0) {
        const currentDays = Number(articles[0].check_in_days || 0);
        const newDays = currentDays + 1;
        const now = new Date();
        const maxDays = new Date(now.getFullYear(), now.getMonth() + 1, 0).getDate();
        const completionRate = maxDays > 0 ? Math.round((newDays / maxDays) * 100) : 0;
        await pool.query(
          `UPDATE articles SET check_in_days = ?, completion_rate = ?, last_modified = ?
           WHERE id = ? AND user_id = ?`,
          [newDays, completionRate, now.toISOString(), articleId, req.userId]
        );
        return res.json(success({ itemId, checkedIn: true, checkInDays: newDays, completionRate }));
      }
    }

    return res.json(success({ itemId, checkedIn: true }));
  } catch (e) {
    console.error('[daily-tasks/today/checkin]', e);
    return res.status(500).json(error('打卡失败: ' + e.message, 500));
  }
});

// POST /api/daily-tasks/today/checkin-by-article  通过文章 client_id 打卡（推荐，多端安全）
router.post('/today/checkin-by-article', authRequired, async (req, res) => {
  const { articleId } = req.body; // articleId 是客户端的 client_id
  if (!articleId) {
    return res.status(400).json(error('缺少 articleId', 400));
  }
  try {
    // 先解析 client_id → 服务端 articles.id
    const [articles] = await pool.query(
      'SELECT id, check_in_days FROM articles WHERE user_id = ? AND client_id = ? AND deleted = 0',
      [req.userId, String(articleId)]
    );
    if (articles.length === 0) {
      return res.status(404).json(error('文章不存在', 404));
    }
    const serverArticleId = articles[0].id;
    const currentDays = Number(articles[0].check_in_days || 0);
    const today = todayStr();

    // 只更新今日任务中对应文章的 is_checked_in（单向：只设为1，不回退）
    const [result] = await pool.query(
      `UPDATE daily_task_items i
       INNER JOIN daily_tasks t ON t.id = i.task_id
       SET i.is_checked_in = 1
       WHERE i.article_id = ? AND t.user_id = ? AND t.task_date = ?`,
      [serverArticleId, req.userId, today]
    );
    if (result.affectedRows === 0) {
      return res.status(404).json(error('今日任务中未找到该文章', 404));
    }

    // 服务端计算完成率并更新文章的 check_in_days 和 completion_rate
    const newDays = currentDays + 1;
    const now = new Date();
    const maxDays = new Date(now.getFullYear(), now.getMonth() + 1, 0).getDate();
    const completionRate = maxDays > 0 ? Math.round((newDays / maxDays) * 100) : 0;
    await pool.query(
      `UPDATE articles SET check_in_days = ?, completion_rate = ?, last_modified = ?
       WHERE id = ? AND user_id = ?`,
      [newDays, completionRate, now.toISOString(), serverArticleId, req.userId]
    );

    return res.json(success({
      articleId, serverArticleId, checkedIn: true,
      checkInDays: newDays, completionRate
    }));
  } catch (e) {
    console.error('[daily-tasks/checkin-by-article]', e);
    return res.status(500).json(error('打卡失败: ' + e.message, 500));
  }
});

// GET /api/daily-tasks?from=&to=  查询历史任务
router.get('/', authRequired, async (req, res) => {
  const from = req.query.from;
  const to = req.query.to;
  if (!from || !to) {
    return res.status(400).json(error('需要 from 和 to 参数', 400));
  }
  try {
    const [rows] = await pool.query(
      `SELECT t.id, t.task_date AS taskDate, t.count, t.total_words AS totalWords,
              t.last_long_article_ids AS lastLongArticleIds
       FROM daily_tasks t
       WHERE t.user_id = ? AND t.task_date BETWEEN ? AND ?
       ORDER BY t.task_date ASC`,
      [req.userId, from, to]
    );
    return res.json(success(rows));
  } catch (e) {
    return res.status(500).json(error('查询失败: ' + e.message, 500));
  }
});

module.exports = router;
// 导出 generateDailyTask 供 cron 定时任务调用
module.exports.generateDailyTask = generateDailyTask;
