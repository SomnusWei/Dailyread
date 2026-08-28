// 每日阅读完成率结算（PWA 专用，不影响 DailyRead 原有逻辑）
// 每天 12:00 (Asia/Shanghai) 结算所有已绑定 DailyRead 账号的学习中心用户当日任务完成率
// 完成率 = 已打卡数量 / 任务总数量 * 100，记录到 lc_dr_completion_rates 表
const { pool } = require('../db');

function todayStr() {
  const d = new Date();
  const tz = new Date(d.getTime() - d.getTimezoneOffset() * 60000);
  return tz.toISOString().slice(0, 10);
}

/**
 * 结算单个用户的今日完成率
 * @param {number} lcUserId - 学习中心账号 id
 * @param {number} drUserId - 绑定的 DailyRead 账号 id
 * @param {string} dateStr - 日期 YYYY-MM-DD
 */
async function settleOne(lcUserId, drUserId, dateStr) {
  // 查今日任务（daily_tasks + daily_task_items）
  const [tasks] = await pool.query(
    'SELECT id FROM daily_tasks WHERE user_id = ? AND task_date = ? LIMIT 1',
    [drUserId, dateStr]
  );
  if (tasks.length === 0) {
    // 今日无任务：记录 total=0, checked=0, rate=0
    await pool.query(
      `INSERT INTO lc_dr_completion_rates (lc_user_id, dr_user_id, task_date, total_items, checked_items, completion_rate)
       VALUES (?, ?, ?, 0, 0, 0)
       ON DUPLICATE KEY UPDATE total_items=0, checked_items=0, completion_rate=0, settled_at=NOW()`,
      [lcUserId, drUserId, dateStr]
    );
    return { lcUserId, drUserId, total: 0, checked: 0, rate: 0 };
  }
  const taskId = tasks[0].id;
  // 查任务条目总数 + 已打卡数
  const [[totalRow]] = await pool.query(
    'SELECT COUNT(*) AS cnt FROM daily_task_items WHERE task_id = ?',
    [taskId]
  );
  const [[checkedRow]] = await pool.query(
    'SELECT COUNT(*) AS cnt FROM daily_task_items WHERE task_id = ? AND is_checked_in = 1',
    [taskId]
  );
  const total = totalRow ? totalRow.cnt : 0;
  const checked = checkedRow ? checkedRow.cnt : 0;
  const rate = total > 0 ? Math.round(checked / total * 100) : 0;
  await pool.query(
    `INSERT INTO lc_dr_completion_rates (lc_user_id, dr_user_id, task_date, total_items, checked_items, completion_rate)
     VALUES (?, ?, ?, ?, ?, ?)
     ON DUPLICATE KEY UPDATE total_items=VALUES(total_items), checked_items=VALUES(checked_items), completion_rate=VALUES(completion_rate), settled_at=NOW()`,
    [lcUserId, drUserId, dateStr, total, checked, rate]
  );
  return { lcUserId, drUserId, total, checked, rate };
}

/**
 * 结算所有已绑定 DailyRead 账号的学习中心用户
 */
async function settleAllCompletionRates() {
  const dateStr = todayStr();
  console.log('[DR-Settle] 开始结算每日阅读完成率 @', dateStr);
  // 查所有已绑定 dr_user_id 的学习中心账号
  const [users] = await pool.query(
    'SELECT id, username, nickname, dr_user_id FROM lc_users WHERE dr_user_id IS NOT NULL'
  );
  console.log('[DR-Settle] 共', users.length, '个已绑定账号需要结算');
  let ok = 0, fail = 0;
  for (const u of users) {
    try {
      const r = await settleOne(u.id, u.dr_user_id, dateStr);
      console.log(`  - ${u.nickname || u.username}: ${r.checked}/${r.total} (${r.rate}%)`);
      ok++;
    } catch (e) {
      console.error(`  - ${u.username} 结算失败:`, e.message);
      fail++;
    }
  }
  console.log(`[DR-Settle] 结算完成: 成功 ${ok}, 失败 ${fail}`);
  return { date: dateStr, total: users.length, ok, fail };
}

module.exports = { settleAllCompletionRates, settleOne };
