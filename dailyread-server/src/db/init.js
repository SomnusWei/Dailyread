// 数据库初始化脚本：建库 + 建表 + 创建用户
// 用法：node src/db/init.js
const mysql = require('mysql2/promise');
const config = require('../config');

const SQL_CREATE_DB = `CREATE DATABASE IF NOT EXISTS \`${config.db.database}\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci`;

const SQL_CREATE_USER = `CREATE USER IF NOT EXISTS '${config.db.user}'@'${config.db.host}' IDENTIFIED BY '${config.db.password}'`;
const SQL_GRANT = `GRANT ALL PRIVILEGES ON \`${config.db.database}\`.* TO '${config.db.user}'@'${config.db.host}'`;
const SQL_FLUSH = `FLUSH PRIVILEGES`;

const SQL_CREATE_USERS = `
CREATE TABLE IF NOT EXISTS users (
    id          BIGINT PRIMARY KEY AUTO_INCREMENT,
    username    VARCHAR(32) UNIQUE NOT NULL,
    password    VARCHAR(255) NOT NULL,
    nickname    VARCHAR(64) DEFAULT '',
    device_id   VARCHAR(128) DEFAULT NULL,
    role        ENUM('admin','user') DEFAULT 'user',
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login  DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
`;

// 迁移：为已存在的 users 表添加 device_id 列
const SQL_ALTER_USERS_ADD_DEVICE_ID = `
ALTER TABLE users ADD COLUMN device_id VARCHAR(128) DEFAULT NULL AFTER nickname
`;

// 迁移：为已存在的 users 表添加 role 列
const SQL_ALTER_USERS_ADD_ROLE = `
ALTER TABLE users ADD COLUMN role ENUM('admin','user') DEFAULT 'user' AFTER device_id
`;

const SQL_CREATE_ARTICLES = `
CREATE TABLE IF NOT EXISTS articles (
    id                         BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id                    BIGINT NOT NULL,
    client_id                  VARCHAR(64) NOT NULL,
    title                      TEXT NOT NULL,
    content                    MEDIUMTEXT NOT NULL,
    content_html               MEDIUMTEXT,
    chinese_chars              INT DEFAULT 0,
    font_family                VARCHAR(32) DEFAULT 'default',
    font_size                  INT DEFAULT 16,
    font_color                 VARCHAR(16) DEFAULT '#000000',
    is_bold                    TINYINT DEFAULT 0,
    is_reading                 TINYINT DEFAULT 1,
    is_required                TINYINT DEFAULT 0,
    required_days              VARCHAR(64) DEFAULT '',
    use_independent_check_rate TINYINT DEFAULT 0,
    independent_check_rate     DECIMAL(5,2) DEFAULT 0,
    create_time                VARCHAR(32),
    is_long_article            TINYINT DEFAULT 0,
    check_in_days              INT DEFAULT 0,
    completion_rate            DECIMAL(5,2) DEFAULT 0,
    imagewebp                  LONGTEXT,
    audiobase64                LONGTEXT,
    iscontent                  TINYINT DEFAULT 1,
    last_modified              VARCHAR(32),
    server_updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted                    TINYINT DEFAULT 0,
    UNIQUE KEY uk_user_client (user_id, client_id),
    INDEX idx_user_modified (user_id, last_modified),
    INDEX idx_user_deleted (user_id, deleted)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
`;

const SQL_CREATE_CHECKINS = `
CREATE TABLE IF NOT EXISTS checkins (
    id             BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id        BIGINT NOT NULL,
    article_id     BIGINT NOT NULL,
    check_in_date  DATE NOT NULL,
    check_in_time  VARCHAR(32),
    last_modified  VARCHAR(32),
    UNIQUE KEY uk_article_date (article_id, check_in_date),
    INDEX idx_user_date (user_id, check_in_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
`;

const SQL_CREATE_DAILY_TASKS = `
CREATE TABLE IF NOT EXISTS daily_tasks (
    id                    BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id               BIGINT NOT NULL,
    task_date             DATE NOT NULL,
    count                 INT DEFAULT 0,
    total_words           INT DEFAULT 0,
    last_long_article_ids TEXT,
    create_time           VARCHAR(32),
    last_modified         VARCHAR(32),
    UNIQUE KEY uk_user_date (user_id, task_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
`;

const SQL_CREATE_DAILY_TASK_ITEMS = `
CREATE TABLE IF NOT EXISTS daily_task_items (
    id              BIGINT PRIMARY KEY AUTO_INCREMENT,
    task_id         BIGINT NOT NULL,
    article_id      BIGINT NOT NULL,
    article_title   TEXT NOT NULL,
    word_target     INT DEFAULT 0,
    is_checked_in   TINYINT DEFAULT 0,
    is_long_article TINYINT DEFAULT 0,
    is_required     TINYINT DEFAULT 0,
    display_name    VARCHAR(128) DEFAULT '',
    FOREIGN KEY (task_id) REFERENCES daily_tasks(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
`;

const SQL_CREATE_USER_CONFIGS = `
CREATE TABLE IF NOT EXISTS user_configs (
    user_id              BIGINT PRIMARY KEY,
    daily_minutes        INT DEFAULT 20,
    target_check_rate    DECIMAL(5,2) DEFAULT 30,
    keep_screen_on       TINYINT DEFAULT 0,
    last_reset_month     VARCHAR(8) DEFAULT '',
    reader_font_size     INT DEFAULT 26,
    last_sync_time       VARCHAR(32) DEFAULT ''
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
`;

// 迁移：为已存在的 articles 表添加 audiobase64 列（音频 base64，m4a/AAC，纯 base64 无前缀）
const SQL_ALTER_ARTICLES_ADD_AUDIO = `
ALTER TABLE articles ADD COLUMN audiobase64 LONGTEXT AFTER imagewebp
`;

async function init() {
  // 用 root 连接（不指定 database）建库 + 建用户
  const rootConn = await mysql.createConnection({
    host: config.db.host,
    port: config.db.port,
    user: 'root',
    password: process.env.ROOT_DB_PASSWORD || ''
  });

  console.log('[INIT] 创建数据库和用户...');
  await rootConn.query(SQL_CREATE_DB);
  console.log('  - 数据库', config.db.database, 'OK');

  try { await rootConn.query(SQL_CREATE_USER); } catch (e) { console.log('  - 用户已存在，跳过'); }
  try { await rootConn.query(SQL_GRANT); await rootConn.query(SQL_FLUSH); } catch (e) { console.log('  - 授权失败:', e.message); }
  console.log('  - 用户', config.db.user, 'OK');
  await rootConn.end();

  // 用业务用户连接建表
  const conn = await mysql.createConnection({
    host: config.db.host,
    port: config.db.port,
    user: config.db.user,
    password: config.db.password,
    database: config.db.database
  });

  console.log('[INIT] 创建表...');
  await conn.query(SQL_CREATE_USERS);            console.log('  - users OK');
  await conn.query(SQL_CREATE_ARTICLES);        console.log('  - articles OK');
  await conn.query(SQL_CREATE_CHECKINS);         console.log('  - checkins OK');
  await conn.query(SQL_CREATE_DAILY_TASKS);     console.log('  - daily_tasks OK');
  await conn.query(SQL_CREATE_DAILY_TASK_ITEMS);console.log('  - daily_task_items OK');
  await conn.query(SQL_CREATE_USER_CONFIGS);   console.log('  - user_configs OK');

  // 迁移：为已有 users 表添加 device_id 列（如果不存在）
  try {
    await conn.query(SQL_ALTER_USERS_ADD_DEVICE_ID);
    console.log('  - migration: device_id column added to users OK');
  } catch (e) {
    if (e.message && e.message.includes('Duplicate column')) {
      console.log('  - migration: device_id column already exists, skipped');
    } else {
      console.error('  - migration error:', e.message);
    }
  }

  // 迁移：为已有 users 表添加 role 列（如果不存在）
  try {
    await conn.query(SQL_ALTER_USERS_ADD_ROLE);
    console.log('  - migration: role column added to users OK');
  } catch (e) {
    if (e.message && e.message.includes('Duplicate column')) {
      console.log('  - migration: role column already exists, skipped');
    } else {
      console.error('  - migration error:', e.message);
    }
  }

  // 迁移：为已有 articles 表添加 audiobase64 列（音频 base64，如果不存在）
  try {
    await conn.query(SQL_ALTER_ARTICLES_ADD_AUDIO);
    console.log('  - migration: audiobase64 column added to articles OK');
  } catch (e) {
    if (e.message && e.message.includes('Duplicate column')) {
      console.log('  - migration: audiobase64 column already exists, skipped');
    } else {
      console.error('  - migration error:', e.message);
    }
  }

  await conn.end();
  console.log('[INIT] 数据库初始化完成');
  process.exit(0);
}

init().catch(e => {
  console.error('[INIT] 初始化失败:', e);
  process.exit(1);
});
