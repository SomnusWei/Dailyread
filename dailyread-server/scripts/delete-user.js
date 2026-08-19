/**
 * 删除指定用户账号及其所有关联数据
 * 运行方式：node scripts/delete-user.js somnusweiwei1989
 */
require('dotenv').config();
const mysql = require('mysql2/promise');

async function main() {
  const username = process.argv[2];
  if (!username) {
    console.error('用法: node scripts/delete-user.js <username>');
    process.exit(1);
  }

  const host = process.env.DB_HOST || 'localhost';
  const port = parseInt(process.env.DB_PORT || '3306', 10);
  const user = process.env.DB_USER || 'root';
  const password = process.env.DB_PASSWORD || '';
  const database = process.env.DB_NAME || 'dailyread_db';

  console.log(`连接数据库: ${user}@${host}:${port}/${database}`);
  const conn = await mysql.createConnection({ host, port, user, password, database });

  // 1. 查找用户
  const [users] = await conn.query('SELECT id, username FROM users WHERE username = ?', [username]);
  if (users.length === 0) {
    console.log(`用户 "${username}" 不存在`);
    await conn.end();
    process.exit(0);
  }
  const userId = users[0].id;
  console.log(`找到用户: id=${userId}, username=${users[0].username}`);

  // 2. 开启事务，按外键依赖顺序删除
  await conn.beginTransaction();
  try {
    // daily_task_items (通过 daily_tasks 关联)
    await conn.query(
      `DELETE di FROM daily_task_items di
       INNER JOIN daily_tasks dt ON dt.id = di.task_id
       WHERE dt.user_id = ?`,
      [userId]
    );
    console.log('  删除 daily_task_items 完成');

    // daily_tasks
    const [dtResult] = await conn.query('DELETE FROM daily_tasks WHERE user_id = ?', [userId]);
    console.log(`  删除 daily_tasks: ${dtResult.affectedRows} 行`);

    // checkins
    const [ciResult] = await conn.query(
      `DELETE FROM checkins WHERE article_id IN (SELECT id FROM articles WHERE user_id = ?)`,
      [userId]
    );
    console.log(`  删除 checkins: ${ciResult.affectedRows} 行`);

    // articles
    const [arResult] = await conn.query('DELETE FROM articles WHERE user_id = ?', [userId]);
    console.log(`  删除 articles: ${arResult.affectedRows} 行`);

    // user_configs
    await conn.query('DELETE FROM user_configs WHERE user_id = ?', [userId]);
    console.log('  删除 user_configs 完成');

    // users
    const [uResult] = await conn.query('DELETE FROM users WHERE id = ?', [userId]);
    console.log(`  删除 users: ${uResult.affectedRows} 行`);

    await conn.commit();
    console.log(`\n✅ 用户 "${username}" (id=${userId}) 及其所有关联数据已成功删除`);
  } catch (e) {
    await conn.rollback();
    console.error('删除失败，已回滚:', e.message);
    process.exit(1);
  } finally {
    await conn.end();
  }
}

main().catch(e => { console.error(e); process.exit(1); });
