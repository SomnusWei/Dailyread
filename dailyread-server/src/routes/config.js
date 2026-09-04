// 用户配置路由：拉取、推送
// 规则（产品约定）：
// 1. 每日阅读时长(dailyMinutes)的修改只有 Win 端提交可被接受更新；
//    鸿蒙端只拉取不上传（其 PUT 请求体不含 dailyMinutes 字段时，服务端保留现值）。
// 2. 今日阅读任务的重新生成只有两个途径：每天 00:00 定时全量重建（cron.js），
//    或 Win 端「重新生成」按钮（POST /api/daily-tasks/generate {force:true}）。
//    配置保存本身不再触发任何当日任务重算。
const express = require('express');
const { pool } = require('../db');
const { authRequired } = require('../middleware/auth');
const { success, error } = require('../utils/response');

const router = express.Router();

/**
 * 保存用户配置（供 /api/config 与 /api/dr/config 复用）
 * 仅当请求体显式携带某字段时才更新该字段；未携带的字段保留数据库现值（首次则用默认值）。
 * 不回写 keepScreenOn（各端本地为准）。
 */
async function updateConfig(userId, c) {
  const [rows] = await pool.query(
    `SELECT daily_minutes, target_check_rate, keep_screen_on,
            last_reset_month, reader_font_size, last_sync_time
     FROM user_configs WHERE user_id = ?`, [userId]
  );
  const cur = rows[0] || {};

  const pickVal = (explicit, newVal, col, def) => {
    if (explicit) return newVal;
    const v = cur[col];
    return (v === undefined || v === null) ? def : v;
  };

  const minutesExplicit = ('dailyMinutes' in c) || ('daily_minutes' in c);
  const dailyMinutes = pickVal(minutesExplicit, c.dailyMinutes ?? c.daily_minutes, 'daily_minutes', 20);
  const targetExplicit = ('targetCheckRate' in c) || ('target_check_rate' in c);
  const targetCheckRate = pickVal(targetExplicit, c.targetCheckRate ?? c.target_check_rate, 'target_check_rate', 30);
  const fontExplicit = ('readerFontSize' in c) || ('reader_font_size' in c);
  const readerFontSize = pickVal(fontExplicit, c.readerFontSize ?? c.reader_font_size, 'reader_font_size', 26);
  const resetExplicit = ('lastResetMonth' in c) || ('last_reset_month' in c);
  const lastResetMonth = pickVal(resetExplicit, c.lastResetMonth ?? c.last_reset_month, 'last_reset_month', '');
  const syncExplicit = ('lastSyncTime' in c) || ('last_sync_time' in c);
  const lastSyncTime = pickVal(syncExplicit, c.lastSyncTime ?? c.last_sync_time, 'last_sync_time', '');
  const keepScreenOn = (cur.keep_screen_on !== undefined && cur.keep_screen_on !== null) ? cur.keep_screen_on : 0;

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
    [userId, dailyMinutes, targetCheckRate, keepScreenOn, lastResetMonth, readerFontSize, lastSyncTime]
  );

  return { ok: true };
}

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
  try {
    const data = await updateConfig(req.userId, req.body);
    return res.json(success(data));
  } catch (e) {
    return res.status(500).json(error('保存失败: ' + e.message, 500));
  }
});

module.exports = router;
module.exports.updateConfig = updateConfig;
