// 用户配置路由：拉取、推送
const express = require('express');
const { pool } = require('../db');
const { authRequired } = require('../middleware/auth');
const { success, error } = require('../utils/response');

const router = express.Router();

// GET /api/config
router.get('/', authRequired, async (req, res) => {
  try {
    const [rows] = await pool.query(
      `SELECT daily_minutes AS dailyMinutes, target_check_rate AS targetCheckRate,
              keep_screen_on AS keepScreenOn, last_reset_month AS lastResetMonth,
              reader_font_size AS readerFontSize, last_sync_time AS lastSyncTime
       FROM user_configs WHERE user_id = ?`,
      [req.userId]
    );
    if (rows.length === 0) {
      // 不存在则初始化
      await pool.query('INSERT INTO user_configs (user_id) VALUES (?)', [req.userId]);
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

// PUT /api/config
router.put('/', authRequired, async (req, res) => {
  const c = req.body;
  try {
    // 映射 camelCase -> snake_case
    const dailyMinutes = c.dailyMinutes ?? c.daily_minutes ?? 20;
    const targetCheckRate = c.targetCheckRate ?? c.target_check_rate ?? 30;
    const readerFontSize = c.readerFontSize ?? c.reader_font_size ?? 26;
    const lastResetMonth = c.lastResetMonth ?? c.last_reset_month ?? '';
    const lastSyncTime = c.lastSyncTime ?? c.last_sync_time ?? '';
    // keepScreenOn 始终以本地为准，不从客户端覆盖（不同步）
    // 先读取当前 keepScreenOn 值
    const [existing] = await pool.query('SELECT keep_screen_on FROM user_configs WHERE user_id = ?', [req.userId]);
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
      [req.userId, dailyMinutes, targetCheckRate, keepScreenOn, lastResetMonth, readerFontSize, lastSyncTime]
    );
    return res.json(success({ ok: true }));
  } catch (e) {
    return res.status(500).json(error('保存失败: ' + e.message, 500));
  }
});

module.exports = router;
