-- DailyRead 删除用户脚本
-- 用途：从数据库彻底删除指定用户及其所有关联数据
-- 使用方法：在 MySQL 客户端中执行，先替换 @username 变量

SET @username = 'somnusweiwei1989';

-- 1. 查看用户是否存在
SELECT id, username, nickname, created_at FROM users WHERE username = @username;

-- 2. 开启事务删除（按外键依赖顺序）
START TRANSACTION;

SET @user_id = (SELECT id FROM users WHERE username = @username);

-- 2a. 删除每日任务项（通过 daily_tasks 关联）
DELETE di FROM daily_task_items di
INNER JOIN daily_tasks dt ON dt.id = di.task_id
WHERE dt.user_id = @user_id;

-- 2b. 删除每日任务
DELETE FROM daily_tasks WHERE user_id = @user_id;

-- 2c. 删除打卡记录
DELETE FROM checkins WHERE article_id IN (SELECT id FROM articles WHERE user_id = @user_id);

-- 2d. 删除文章
DELETE FROM articles WHERE user_id = @user_id;

-- 2e. 删除用户配置
DELETE FROM user_configs WHERE user_id = @user_id;

-- 2f. 删除用户
DELETE FROM users WHERE id = @user_id;

COMMIT;

-- 3. 验证
SELECT '用户已删除' AS result, @username AS deleted_username, @user_id AS deleted_user_id;
