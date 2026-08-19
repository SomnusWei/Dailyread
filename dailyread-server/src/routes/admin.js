/**
 * DailyRead 管理员面板 - 后端 API
 * 数据库角色认证：role='admin' 的用户可登录管理后台
 * 默认管理员账号：chef_somnus / Somnus890930
 */
const express = require('express');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const rateLimit = require('express-rate-limit');
const { pool } = require('../db');
const config = require('../config');
const { success, error } = require('../utils/response');

const router = express.Router();

// 内存中存储管理员 session
const adminSessions = new Map(); // token -> { userId, username, nickname, createdAt }

// ========== 登录限流 ==========
const adminLoginLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 10,
  message: { code: 429, message: '登录尝试过于频繁，请15分钟后再试', data: null }
});

// ========== 管理员鉴权中间件 ==========
function adminAuth(req, res, next) {
  const authHeader = req.headers.authorization;
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json(error('未登录', 401));
  }
  const token = authHeader.split(' ')[1];
  const session = adminSessions.get(token);
  if (!session) {
    return res.status(401).json(error('登录已过期，请重新登录', 401));
  }
  // 检查 session 是否过期（24小时）
  if (Date.now() - session.createdAt > 24 * 60 * 60 * 1000) {
    adminSessions.delete(token);
    return res.status(401).json(error('登录已过期，请重新登录', 401));
  }
  req.adminId = session.userId;
  req.adminUsername = session.username;
  req.adminNickname = session.nickname;
  next();
}

// ========== 登录 ==========
router.post('/login', adminLoginLimiter, async (req, res) => {
  const { username, password } = req.body;
  if (!username || !password) {
    return res.status(400).json(error('用户名和密码不能为空', 400));
  }
  try {
    // 查询用户（必须是管理员角色）
    const [users] = await pool.query(
      'SELECT id, username, nickname, password, role FROM users WHERE username = ?',
      [username]
    );
    if (users.length === 0) {
      return res.status(401).json(error('用户名或密码错误', 401));
    }
    const user = users[0];
    if (user.role !== 'admin') {
      return res.status(401).json(error('该账号没有管理员权限', 401));
    }
    const ok = bcrypt.compareSync(password, user.password);
    if (!ok) {
      return res.status(401).json(error('用户名或密码错误', 401));
    }
    // 更新最后登录时间
    await pool.query('UPDATE users SET last_login = NOW() WHERE id = ?', [user.id]);
    // 生成 session token
    const token = jwt.sign(
      { userId: user.id, username: user.username, type: 'admin' },
      config.jwt.secret + '_admin',
      { expiresIn: '24h' }
    );
    adminSessions.set(token, {
      userId: user.id,
      username: user.username,
      nickname: user.nickname || user.username,
      createdAt: Date.now()
    });
    res.json(success({
      token,
      username: user.username,
      nickname: user.nickname || user.username,
      role: user.role
    }, '登录成功'));
  } catch (e) {
    console.error('[admin/login]', e);
    res.status(500).json(error('登录失败: ' + e.message, 500));
  }
});

// ========== 登出 ==========
router.post('/logout', adminAuth, (req, res) => {
  const authHeader = req.headers.authorization;
  const token = authHeader.split(' ')[1];
  adminSessions.delete(token);
  res.json(success({}, '已退出登录'));
});

// ========== 验证登录状态 ==========
router.get('/check', adminAuth, (req, res) => {
  res.json(success({
    username: req.adminUsername,
    nickname: req.adminNickname,
    role: 'admin'
  }, '已登录'));
});

// ========== 获取所有用户 ==========
router.get('/users', adminAuth, async (req, res) => {
  try {
    const [users] = await pool.query(`
      SELECT id, username, nickname, role, created_at, last_login
      FROM users ORDER BY id ASC
    `);
    const result = [];
    for (const u of users) {
      const [articleCount] = await pool.query(
        'SELECT COUNT(*) as cnt FROM articles WHERE user_id = ? AND deleted = 0',
        [u.id]
      );
      const [checkinCount] = await pool.query(`
        SELECT COUNT(*) as cnt FROM checkins ci
        INNER JOIN articles a ON a.id = ci.article_id
        WHERE a.user_id = ?
      `, [u.id]);
      result.push({
        id: u.id,
        username: u.username,
        nickname: u.nickname || '',
        role: u.role,
        is_admin: u.role === 'admin',
        created_at: u.created_at,
        last_login: u.last_login,
        article_count: articleCount[0].cnt,
        checkin_count: checkinCount[0].cnt
      });
    }
    res.json(success({ users: result, total: result.length }));
  } catch (e) {
    console.error('[admin/users]', e);
    res.status(500).json(error('查询失败: ' + e.message, 500));
  }
});

// ========== 添加用户 ==========
router.post('/users', adminAuth, async (req, res) => {
  const { username, password, nickname, role } = req.body;
  if (!username || !password) {
    return res.status(400).json(error('用户名和密码不能为空', 400));
  }
  if (username.length < 3 || username.length > 32) {
    return res.status(400).json(error('用户名长度需 3-32 字符', 400));
  }
  if (password.length < 6 || password.length > 64) {
    return res.status(400).json(error('密码长度需 6-64 字符', 400));
  }
  const userRole = role === 'admin' ? 'admin' : 'user';
  try {
    const [existing] = await pool.query('SELECT id FROM users WHERE username = ?', [username]);
    if (existing.length > 0) {
      return res.status(409).json(error('用户名已存在', 409));
    }
    const hash = bcrypt.hashSync(password, 10);
    const [result] = await pool.query(
      'INSERT INTO users (username, password, nickname, role) VALUES (?, ?, ?, ?)',
      [username, hash, nickname || '', userRole]
    );
    await pool.query('INSERT INTO user_configs (user_id) VALUES (?)', [result.insertId]);
    res.json(success({ id: result.insertId, username, role: userRole }, '用户创建成功'));
  } catch (e) {
    console.error('[admin/users/create]', e);
    res.status(500).json(error('创建失败: ' + e.message, 500));
  }
});

// ========== 修改用户密码 ==========
router.put('/users/:username/password', adminAuth, async (req, res) => {
  const { username } = req.params;
  const { password } = req.body;
  if (!password || password.length < 6 || password.length > 64) {
    return res.status(400).json(error('密码长度需 6-64 字符', 400));
  }
  try {
    const [users] = await pool.query('SELECT id FROM users WHERE username = ?', [username]);
    if (users.length === 0) {
      return res.status(404).json(error('用户不存在', 404));
    }
    const hash = bcrypt.hashSync(password, 10);
    await pool.query('UPDATE users SET password = ? WHERE id = ?', [hash, users[0].id]);
    res.json(success({}, '密码已更新'));
  } catch (e) {
    console.error('[admin/users/password]', e);
    res.status(500).json(error('修改失败: ' + e.message, 500));
  }
});

// ========== 修改用户信息（含角色） ==========
router.put('/users/:username', adminAuth, async (req, res) => {
  const { username } = req.params;
  const { nickname, newUsername, role } = req.body;
  try {
    const [users] = await pool.query('SELECT id, role FROM users WHERE username = ?', [username]);
    if (users.length === 0) {
      return res.status(404).json(error('用户不存在', 404));
    }
    const u = users[0];
    // 不允许删除最后一个管理员
    if (role === 'user' && u.role === 'admin') {
      const [adminCount] = await pool.query(
        "SELECT COUNT(*) as cnt FROM users WHERE role = 'admin'"
      );
      if (adminCount[0].cnt <= 1) {
        return res.status(400).json(error('不能将最后一个管理员降为普通用户', 400));
      }
    }
    // 检查新用户名是否重复
    if (newUsername && newUsername !== username) {
      const [exists] = await pool.query('SELECT id FROM users WHERE username = ?', [newUsername]);
      if (exists.length > 0) {
        return res.status(409).json(error('新用户名已存在', 409));
      }
    }
    const updates = [];
    const params = [];
    if (nickname !== undefined) {
      updates.push('nickname = ?');
      params.push(nickname);
    }
    if (newUsername) {
      updates.push('username = ?');
      params.push(newUsername);
    }
    if (role !== undefined && role !== u.role) {
      updates.push('role = ?');
      params.push(role === 'admin' ? 'admin' : 'user');
    }
    if (updates.length === 0) {
      return res.status(400).json(error('没有需要更新的字段', 400));
    }
    params.push(u.id);
    await pool.query(`UPDATE users SET ${updates.join(', ')} WHERE id = ?`, params);
    res.json(success({}, '用户信息已更新'));
  } catch (e) {
    console.error('[admin/users/update]', e);
    res.status(500).json(error('修改失败: ' + e.message, 500));
  }
});

// ========== 删除用户 ==========
router.delete('/users/:username', adminAuth, async (req, res) => {
  const { username } = req.params;
  try {
    const [users] = await pool.query('SELECT id, role FROM users WHERE username = ?', [username]);
    if (users.length === 0) {
      return res.status(404).json(error('用户不存在', 404));
    }
    const u = users[0];
    // 不允许删除管理员
    if (u.role === 'admin') {
      return res.status(400).json(error('不能删除管理员账号，请先取消管理员身份', 400));
    }
    const userId = u.id;

    const conn = await pool.getConnection();
    await conn.beginTransaction();
    try {
      const [diResult] = await conn.query(`
        DELETE di FROM daily_task_items di
        INNER JOIN daily_tasks dt ON dt.id = di.task_id
        WHERE dt.user_id = ?`, [userId]);
      const [dtResult] = await conn.query('DELETE FROM daily_tasks WHERE user_id = ?', [userId]);
      const [ciResult] = await conn.query(`
        DELETE FROM checkins WHERE article_id IN (SELECT id FROM articles WHERE user_id = ?)`, [userId]);
      const [arResult] = await conn.query('DELETE FROM articles WHERE user_id = ?', [userId]);
      await conn.query('DELETE FROM user_configs WHERE user_id = ?', [userId]);
      await conn.query('DELETE FROM users WHERE id = ?', [userId]);

      await conn.commit();
      res.json(success({
        deleted: {
          articles: arResult.affectedRows,
          checkins: ciResult.affectedRows,
          tasks: dtResult.affectedRows,
          taskItems: diResult.affectedRows
        }
      }, '用户及关联数据已彻底删除'));
    } catch (e) {
      await conn.rollback();
      throw e;
    } finally {
      conn.release();
    }
  } catch (e) {
    console.error('[admin/users/delete]', e);
    res.status(500).json(error('删除失败: ' + e.message, 500));
  }
});

// ========== 获取单个用户详情 ==========
router.get('/users/:username', adminAuth, async (req, res) => {
  const { username } = req.params;
  try {
    const [users] = await pool.query(`
      SELECT id, username, nickname, role, created_at, last_login
      FROM users WHERE username = ?
    `, [username]);
    if (users.length === 0) {
      return res.status(404).json(error('用户不存在', 404));
    }
    const u = users[0];
    const [articleCount] = await pool.query(
      'SELECT COUNT(*) as cnt FROM articles WHERE user_id = ? AND deleted = 0', [u.id]);
    const [checkinCount] = await pool.query(`
      SELECT COUNT(*) as cnt FROM checkins ci
      INNER JOIN articles a ON a.id = ci.article_id WHERE a.user_id = ?`, [u.id]);
    const [recentArticles] = await pool.query(`
      SELECT id, title, completion_rate, check_in_days, last_modified
      FROM articles WHERE user_id = ? AND deleted = 0
      ORDER BY id DESC LIMIT 10`, [u.id]);

    res.json(success({
      user: {
        id: u.id,
        username: u.username,
        nickname: u.nickname || '',
        role: u.role,
        is_admin: u.role === 'admin',
        created_at: u.created_at,
        last_login: u.last_login,
        article_count: articleCount[0].cnt,
        checkin_count: checkinCount[0].cnt,
        recent_articles: recentArticles
      }
    }));
  } catch (e) {
    console.error('[admin/users/detail]', e);
    res.status(500).json(error('查询失败: ' + e.message, 500));
  }
});

// ========== 数据库统计 ==========
router.get('/stats', adminAuth, async (req, res) => {
  try {
    const [userCount] = await pool.query('SELECT COUNT(*) as cnt FROM users');
    const [adminCount] = await pool.query("SELECT COUNT(*) as cnt FROM users WHERE role = 'admin'");
    const [articleCount] = await pool.query('SELECT COUNT(*) as cnt FROM articles WHERE deleted = 0');
    const [checkinCount] = await pool.query('SELECT COUNT(*) as cnt FROM checkins');
    const [taskCount] = await pool.query('SELECT COUNT(*) as cnt FROM daily_tasks');
    const [activeUsers] = await pool.query(`
      SELECT COUNT(DISTINCT user_id) as cnt FROM articles WHERE deleted = 0`);

    res.json(success({
      total_users: userCount[0].cnt,
      admin_users: adminCount[0].cnt,
      total_articles: articleCount[0].cnt,
      total_checkins: checkinCount[0].cnt,
      total_tasks: taskCount[0].cnt,
      active_users: activeUsers[0].cnt
    }));
  } catch (e) {
    console.error('[admin/stats]', e);
    res.status(500).json(error('查询失败: ' + e.message, 500));
  }
});

module.exports = router;
