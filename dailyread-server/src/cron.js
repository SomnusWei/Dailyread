/**
 * 定时任务调度器
 * 每天 00:00 为所有用户重新生成每日任务
 */
const cron = require('node-cron');
const { pool } = require('./db');

/**
 * 获取所有有文章的用户ID
 */
async function getActiveUserIds() {
  const [rows] = await pool.query(
    'SELECT DISTINCT user_id FROM articles WHERE deleted = 0'
  );
  return rows.map(r => r.user_id);
}

/**
 * 为所有用户重新生成今日任务
 */
async function regenerateAllDailyTasks() {
  console.log('[Cron] 开始为所有用户重新生成每日任务...');
  const userIds = await getActiveUserIds();
  console.log(`[Cron] 共 ${userIds.length} 个用户需要生成任务`);

  // 引入 generateDailyTask 函数
  const dailyTasksRouter = require('./routes/dailyTasks');
  const { generateDailyTask } = dailyTasksRouter;

  let success = 0;
  let fail = 0;
  for (const userId of userIds) {
    try {
      await generateDailyTask(userId, true);
      success++;
    } catch (e) {
      console.error(`[Cron] 用户 ${userId} 任务生成失败:`, e.message);
      fail++;
    }
  }
  console.log(`[Cron] 每日任务生成完成: 成功 ${success}, 失败 ${fail}`);
}

/**
 * 启动定时任务
 */
function startScheduler() {
  // 每天 00:00 执行（服务器本地时间）
  cron.schedule('0 0 * * *', async () => {
    console.log('[Cron] 触发每日任务重新生成 @', new Date().toISOString());
    try {
      await regenerateAllDailyTasks();
    } catch (e) {
      console.error('[Cron] 每日任务生成异常:', e);
    }
  }, {
    scheduled: true,
    timezone: 'Asia/Shanghai'
  });

  console.log('[Cron] 定时任务已启动: 每天 00:00 (Asia/Shanghai) 重新生成所有用户的每日任务');
}

module.exports = { startScheduler, regenerateAllDailyTasks };
