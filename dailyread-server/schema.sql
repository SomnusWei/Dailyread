-- DailyRead 数据库建表脚本（用 dailyread_user 执行）
USE dailyread_db;

CREATE TABLE IF NOT EXISTS users (
    id          BIGINT PRIMARY KEY AUTO_INCREMENT,
    username    VARCHAR(32) UNIQUE NOT NULL,
    password    VARCHAR(255) NOT NULL,
    nickname    VARCHAR(64) DEFAULT '',
    role        ENUM('admin', 'user') NOT NULL DEFAULT 'user',
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login  DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS checkins (
    id             BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id        BIGINT NOT NULL,
    article_id     BIGINT NOT NULL,
    check_in_date  DATE NOT NULL,
    check_in_time  VARCHAR(32),
    last_modified  VARCHAR(32),
    UNIQUE KEY uk_article_date (article_id, check_in_date),
    INDEX idx_user_date (user_id, check_in_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS user_configs (
    user_id              BIGINT PRIMARY KEY,
    daily_minutes        INT DEFAULT 20,
    target_check_rate    DECIMAL(5,2) DEFAULT 30,
    keep_screen_on       TINYINT DEFAULT 0,
    last_reset_month     VARCHAR(8) DEFAULT '',
    reader_font_size     INT DEFAULT 26,
    last_sync_time       VARCHAR(32) DEFAULT ''
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SHOW TABLES;
