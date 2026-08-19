// 打卡同步路由：增量拉取、上报打卡
const express = require('express');
const { pool } = require('../db');
const { authRequired } = require('../middleware/auth');
const { success, error } = require('../utils/response');

const router = express.Router();

// GET /api/checkins?since=  增量拉取（返回 articleId = 文章的 client_id，供客户端匹配）
router.get('/', authRequired, async (req, res) => {
  const since = req.query.since || '';
  try {
    let sql, params;
    if (since) {
      sql = `SELECT c.id, a.client_id AS articleId, c.check_in_date AS checkInDate,
                    c.check_in_time AS checkInTime, c.last_modified AS lastModified
             FROM checkins c
             INNER JOIN articles a ON a.id = c.article_id AND a.user_id = c.user_id
             WHERE c.user_id = ? AND c.last_modified > ?
             ORDER BY c.last_modified ASC`;
      params = [req.userId, since];
    } else {
      sql = `SELECT c.id, a.client_id AS articleId, c.check_in_date AS checkInDate,
                    c.check_in_time AS checkInTime, c.last_modified AS lastModified
             FROM checkins c
             INNER JOIN articles a ON a.id = c.article_id AND a.user_id = c.user_id
             WHERE c.user_id = ?
             ORDER BY c.last_modified ASC`;
      params = [req.userId];
    }
    const [rows] = await pool.query(sql, params);
    const [[maxRow]] = await pool.query('SELECT MAX(last_modified) AS maxTs FROM checkins WHERE user_id = ?', [req.userId]);
    const nextSince = (maxRow && maxRow.maxTs) || '';
    return res.json(success({ checkins: rows, nextSince }));
  } catch (e) {
    console.error('[checkins/get]', e);
    return res.status(500).json(error('拉取失败: ' + e.message, 500));
  }
});

// POST /api/checkins  上报打卡（articleId = 文章的 client_id，按 date 唯一）
router.post('/', authRequired, async (req, res) => {
  const { articleId, checkInDate, checkInTime, lastModified } = req.body;
  if (!articleId || !checkInDate) {
    return res.status(400).json(error('缺少 articleId 或 checkInDate', 400));
  }
  try {
    // articleId 是客户端的 client_id，解析为服务端 articles.id
    const [a] = await pool.query('SELECT id FROM articles WHERE user_id = ? AND client_id = ? AND deleted = 0', [req.userId, String(articleId)]);
    if (a.length === 0) {
      return res.status(404).json(error('文章不存在', 404));
    }
    const serverArticleId = a[0].id;
    // upsert（article_id 存储服务端 id，check_in_date + article_id 唯一）
    await pool.query(
      `INSERT INTO checkins (user_id, article_id, check_in_date, check_in_time, last_modified)
       VALUES (?, ?, ?, ?, ?)
       ON DUPLICATE KEY UPDATE check_in_time = VALUES(check_in_time), last_modified = VALUES(last_modified)`,
      [req.userId, serverArticleId, checkInDate, checkInTime || null, lastModified || new Date().toISOString()]
    );
    return res.json(success({ articleId, checkInDate, ok: true }));
  } catch (e) {
    console.error('[checkins/post]', e);
    return res.status(500).json(error('打卡失败: ' + e.message, 500));
  }
});

module.exports = router;
