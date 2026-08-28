// 炎武班学习中心：数据库表初始化（独立于 DailyRead 用户体系）
// 在服务启动时调用，幂等：CREATE TABLE IF NOT EXISTS + 按需种子管理员
const bcrypt = require('bcryptjs');
const { pool } = require('../db');

const SQL_CREATE_LC_USERS = `
CREATE TABLE IF NOT EXISTS lc_users (
    id         BIGINT PRIMARY KEY AUTO_INCREMENT,
    username   VARCHAR(32) UNIQUE NOT NULL,
    password   VARCHAR(255) NOT NULL,
    nickname   VARCHAR(64) DEFAULT '',
    role       ENUM('admin','teacher','phd','master','bachelor','apprentice') NOT NULL DEFAULT 'bachelor',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
`;

const SQL_CREATE_LC_HANDOUTS = `
CREATE TABLE IF NOT EXISTS lc_handouts (
    id           BIGINT PRIMARY KEY AUTO_INCREMENT,
    uploader_id  BIGINT NOT NULL,
    title        VARCHAR(128) NOT NULL,
    filename     VARCHAR(128) NOT NULL,
    original_name VARCHAR(255) DEFAULT '',
    file_size    INT DEFAULT 0,
    level_scope  TEXT NOT NULL,
    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_uploader (uploader_id),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
`;

const SQL_CREATE_LC_ASSIGNMENTS = `
CREATE TABLE IF NOT EXISTS lc_assignments (
    id           BIGINT PRIMARY KEY AUTO_INCREMENT,
    uploader_id  BIGINT NOT NULL,
    title        VARCHAR(128) NOT NULL,
    content      MEDIUMTEXT NOT NULL,
    level_scope  TEXT NOT NULL,
    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_uploader (uploader_id),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
`;

const SQL_CREATE_LC_INBOX = `
CREATE TABLE IF NOT EXISTS lc_inbox (
    id          BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id     BIGINT NOT NULL,
    category    ENUM('handout','assignment','message') NOT NULL,
    ref_id      BIGINT DEFAULT 0,
    title       VARCHAR(191) NOT NULL,
    sender_name VARCHAR(64) DEFAULT '',
    content     MEDIUMTEXT NULL,
    is_read     TINYINT DEFAULT 0,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_created (user_id, created_at DESC),
    INDEX idx_user_read (user_id, is_read)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
`;

// 迁移：为已有 lc_inbox 表补充 content 列（若表是旧版本创建的）
const SQL_ALTER_LC_INBOX_ADD_CONTENT = `
ALTER TABLE lc_inbox ADD COLUMN content MEDIUMTEXT NULL AFTER sender_name
`;

// 迁移：讲义分类（12 选 1，空串表示历史未分类数据）
const SQL_ALTER_LC_HANDOUTS_ADD_CATEGORY = `
ALTER TABLE lc_handouts ADD COLUMN category VARCHAR(32) NOT NULL DEFAULT '' AFTER title
`;

// 迁移：作业时间范围（毫秒时间戳，NULL 表示不限；比较在应用层做以规避时区问题）
const SQL_ALTER_LC_ASSIGNMENTS_ADD_START_AT = `
ALTER TABLE lc_assignments ADD COLUMN start_at BIGINT NULL AFTER level_scope
`;
const SQL_ALTER_LC_ASSIGNMENTS_ADD_DUE_AT = `
ALTER TABLE lc_assignments ADD COLUMN due_at BIGINT NULL AFTER start_at
`;

// 学生作业提交表：每人每作业一份，重复提交覆盖文件并重置成绩
const SQL_CREATE_LC_SUBMISSIONS = `
CREATE TABLE IF NOT EXISTS lc_submissions (
    id               BIGINT PRIMARY KEY AUTO_INCREMENT,
    assignment_id    BIGINT NOT NULL,
    student_id       BIGINT NOT NULL,
    student_username VARCHAR(32) NOT NULL,
    student_nickname VARCHAR(64) DEFAULT '',
    filename         VARCHAR(128) NOT NULL,
    original_name    VARCHAR(255) DEFAULT '',
    file_size        INT DEFAULT 0,
    file_ext         VARCHAR(16) DEFAULT '',
    submitted_at     BIGINT NOT NULL,
    score            INT NULL,
    comment          TEXT NULL,
    graded_at        BIGINT NULL,
    graded_by        VARCHAR(64) DEFAULT '',
    UNIQUE KEY uk_assign_student (assignment_id, student_id),
    INDEX idx_student (student_id),
    INDEX idx_submitted (submitted_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
`;

async function ensureLearningSchema() {
  console.log('[Learning] 初始化学习中心表...');
  await pool.query(SQL_CREATE_LC_USERS);
  await pool.query(SQL_CREATE_LC_HANDOUTS);
  await pool.query(SQL_CREATE_LC_ASSIGNMENTS);
  await pool.query(SQL_CREATE_LC_INBOX);
  await pool.query(SQL_CREATE_LC_SUBMISSIONS);

  const migrations = [
    ['lc_inbox.content', SQL_ALTER_LC_INBOX_ADD_CONTENT],
    ['lc_handouts.category', SQL_ALTER_LC_HANDOUTS_ADD_CATEGORY],
    ['lc_assignments.start_at', SQL_ALTER_LC_ASSIGNMENTS_ADD_START_AT],
    ['lc_assignments.due_at', SQL_ALTER_LC_ASSIGNMENTS_ADD_DUE_AT]
  ];
  for (const [name, sql] of migrations) {
    try {
      await pool.query(sql);
      console.log('  - migration: ' + name + ' added OK');
    } catch (e) {
      if (!(e.message && e.message.includes('Duplicate column'))) {
        console.error('  - migration error (' + name + '):', e.message);
      }
    }
  }

  // 种子管理员（仅当不存在时创建）
  const [rows] = await pool.query(
    "SELECT id FROM lc_users WHERE username = ? LIMIT 1",
    ['somnusweiwei1989']
  );
  if (rows.length === 0) {
    const hash = await bcrypt.hash('Somnus890930', 10);
    await pool.query(
      "INSERT INTO lc_users (username, password, nickname, role) VALUES (?, ?, ?, 'admin')",
      ['somnusweiwei1989', hash, '管理员']
    );
    console.log('[Learning] 已创建默认管理员: somnusweiwei1989');
  } else {
    // 确保该账号始终具备 admin 角色
    await pool.query("UPDATE lc_users SET role = 'admin' WHERE username = ?", ['somnusweiwei1989']);
    console.log('[Learning] 默认管理员已存在');
  }
  console.log('[Learning] 学习中心表就绪');
}

module.exports = { ensureLearningSchema };
