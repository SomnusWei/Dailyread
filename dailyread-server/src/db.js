// MySQL 连接池
const mysql = require('mysql2/promise');
const config = require('./config');

const pool = mysql.createPool({
  host: config.db.host,
  port: config.db.port,
  user: config.db.user,
  password: config.db.password,
  database: config.db.database,
  waitForConnections: true,
  connectionLimit: 10,
  queueLimit: 0,
  charset: 'utf8mb4',
  timezone: '+08:00',
  decimalNumbers: true
});

// 测试连接
async function testConnection() {
  try {
    const conn = await pool.getConnection();
    console.log('[DB] MySQL 连接成功:', config.db.host + ':' + config.db.port + '/' + config.db.database);
    conn.release();
    return true;
  } catch (e) {
    console.error('[DB] MySQL 连接失败:', e.message);
    throw e;
  }
}

module.exports = { pool, testConnection };
