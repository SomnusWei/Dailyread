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

// 迁移：讲义指定账号分发（JSON 数组，存 lc_users.id；可见性 = 等级匹配 OR 指定账号）
const SQL_ALTER_LC_HANDOUTS_ADD_EXTRA_USERS = `
ALTER TABLE lc_handouts ADD COLUMN extra_users TEXT NULL AFTER level_scope
`;

// 迁移：作业时间范围（毫秒时间戳，NULL 表示不限；比较在应用层做以规避时区问题）
const SQL_ALTER_LC_ASSIGNMENTS_ADD_START_AT = `
ALTER TABLE lc_assignments ADD COLUMN start_at BIGINT NULL AFTER level_scope
`;
const SQL_ALTER_LC_ASSIGNMENTS_ADD_DUE_AT = `
ALTER TABLE lc_assignments ADD COLUMN due_at BIGINT NULL AFTER start_at
`;

// 迁移：学生作业提交表（每人每作业一份，重复提交覆盖文件并重置成绩）
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

// 迁移：学习中心账号绑定 DailyRead 账号（单向，一个 lc 账号最多绑一个 dr 账号）
// dr_user_id 关联 dailyread_db.users.id，不冗余存用户名（查询时 JOIN users 表）
const SQL_ALTER_LC_USERS_ADD_DR_USER_ID = `
ALTER TABLE lc_users ADD COLUMN dr_user_id BIGINT NULL AFTER role
`;
const SQL_ALTER_LC_USERS_ADD_DR_BOUND_AT = `
ALTER TABLE lc_users ADD COLUMN dr_bound_at DATETIME NULL AFTER dr_user_id
`;

// 考试：试卷/答题卡 HTML 发布（exam_code = 试卷 HTML 内嵌的 exam_id，唯一）
// start_at/end_at 为 DATETIME（存 'YYYY-MM-DD HH:mm:ss' 北京时间墙上时间，应用层读取字符串比较以规避时区歧义）
const SQL_CREATE_LC_EXAMS = `
CREATE TABLE IF NOT EXISTS lc_exams (
    id              BIGINT PRIMARY KEY AUTO_INCREMENT,
    uploader_id     BIGINT NOT NULL,
    exam_code       VARCHAR(64) NOT NULL,
    title           VARCHAR(128) NOT NULL,
    paper_filename  VARCHAR(255) NOT NULL,
    answer_filename VARCHAR(255) NOT NULL,
    start_at        DATETIME NULL,
    end_at          DATETIME NULL,
    level_scope     TEXT NOT NULL,
    extra_users     TEXT NULL,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_exam_code (exam_code),
    INDEX idx_uploader (uploader_id),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
`;

// 考试成绩上报记录（exam_id + student_username 唯一，首次成绩锁定，不覆盖）
const SQL_CREATE_LC_EXAM_SCORES = `
CREATE TABLE IF NOT EXISTS lc_exam_scores (
    id               BIGINT PRIMARY KEY AUTO_INCREMENT,
    exam_id          BIGINT NOT NULL,
    student_username VARCHAR(64) NOT NULL,
    final_score      DECIMAL(6,2) NULL,
    total_score      DECIMAL(6,2) NULL,
    objective_score  DECIMAL(6,2) NULL,
    objective_max    DECIMAL(6,2) NULL,
    subjective_self  DECIMAL(6,2) NULL,
    subjective_max   DECIMAL(6,2) NULL,
    accuracy         DECIMAL(5,2) NULL,
    submitted_at     VARCHAR(32) DEFAULT '',
    detail_json      MEDIUMTEXT NULL,
    created_at       DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_exam_student (exam_id, student_username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
`;

// 每日阅读完成率记录表（PWA 12:00 结算，教师/管理员可查）
// lc_user_id + task_date 唯一约束：每天每账号一条，重复结算覆盖
const SQL_CREATE_LC_DR_COMPLETION_RATES = `
CREATE TABLE IF NOT EXISTS lc_dr_completion_rates (
    id               BIGINT PRIMARY KEY AUTO_INCREMENT,
    lc_user_id       BIGINT NOT NULL,
    dr_user_id       BIGINT NOT NULL,
    task_date        DATE NOT NULL,
    total_items      INT DEFAULT 0,
    checked_items    INT DEFAULT 0,
    completion_rate  INT DEFAULT 0,
    settled_at       DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_lc_date (lc_user_id, task_date),
    INDEX idx_dr_date (dr_user_id, task_date),
    INDEX idx_task_date (task_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
`;

async function ensureLearningSchema() {
  console.log('[Learning] 初始化学习中心表...');
  await pool.query(SQL_CREATE_LC_USERS);
  await pool.query(SQL_CREATE_LC_HANDOUTS);
  await pool.query(SQL_CREATE_LC_ASSIGNMENTS);
  await pool.query(SQL_CREATE_LC_INBOX);
  await pool.query(SQL_CREATE_LC_SUBMISSIONS);
  await pool.query(SQL_CREATE_LC_DR_COMPLETION_RATES);
  await pool.query(SQL_CREATE_LC_EXAMS);
  await pool.query(SQL_CREATE_LC_EXAM_SCORES);

  const migrations = [
    ['lc_inbox.content', SQL_ALTER_LC_INBOX_ADD_CONTENT],
    ['lc_handouts.category', SQL_ALTER_LC_HANDOUTS_ADD_CATEGORY],
    ['lc_assignments.start_at', SQL_ALTER_LC_ASSIGNMENTS_ADD_START_AT],
    ['lc_assignments.due_at', SQL_ALTER_LC_ASSIGNMENTS_ADD_DUE_AT],
    ['lc_handouts.extra_users', SQL_ALTER_LC_HANDOUTS_ADD_EXTRA_USERS],
    ['lc_users.dr_user_id', SQL_ALTER_LC_USERS_ADD_DR_USER_ID],
    ['lc_users.dr_bound_at', SQL_ALTER_LC_USERS_ADD_DR_BOUND_AT],
    ['lc_exam_scores.student_display', "ALTER TABLE lc_exam_scores ADD COLUMN student_display VARCHAR(64) DEFAULT ''"]
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
