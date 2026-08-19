// 鉴权路由：注册、登录、校验用户名、获取当前用户
const express = require('express');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const { body, validationResult } = require('express-validator');
const rateLimit = require('express-rate-limit');
const { pool } = require('../db');
const config = require('../config');
const { authRequired } = require('../middleware/auth');
const { success, error } = require('../utils/response');

const router = express.Router();

// 注册限流：3次/小时/IP
const registerLimiter = rateLimit({
  windowMs: 60 * 60 * 1000,
  max: config.rateLimit.registerPerHour,
  standardHeaders: true,
  legacyHeaders: false,
  message: error('注册尝试过多，请稍后再试', 429)
});

// 登录限流：5次/分钟/IP
const loginLimiter = rateLimit({
  windowMs: 60 * 1000,
  max: config.rateLimit.loginPerMin,
  standardHeaders: true,
  legacyHeaders: false,
  message: error('登录尝试过多，请稍后再试', 429)
});

// POST /api/auth/register  注册
router.post('/register', registerLimiter, [
  body('username').isLength({ min: 3, max: 32 }).withMessage('用户名长度 3-32'),
  body('password').isLength({ min: 6, max: 64 }).withMessage('密码长度 6-64'),
  body('nickname').optional().isLength({ max: 64 })
], async (req, res) => {
  const errs = validationResult(req);
  if (!errs.isEmpty()) {
    return res.status(400).json(error(errs.array()[0].msg, 400));
  }
  const { username, password, nickname } = req.body;
  const deviceId = req.body.deviceId || '';
  try {
    // 检查重名
    const [rows] = await pool.query('SELECT id FROM users WHERE username = ?', [username]);
    if (rows.length > 0) {
      return res.status(409).json(error('用户名已存在', 409));
    }
    // 加密 + 入库
    const hash = await bcrypt.hash(password, 10);
    const [result] = await pool.query(
      "INSERT INTO users (username, password, nickname, device_id, role) VALUES (?, ?, ?, ?, 'user')",
      [username, hash, nickname || '', deviceId || '']
    );
    // 初始化用户配置
    await pool.query('INSERT INTO user_configs (user_id) VALUES (?)', [result.insertId]);

    // 签发 token（包含 deviceId）
    const token = jwt.sign(
      { userId: result.insertId, username, deviceId: deviceId || '' },
      config.jwt.secret,
      { expiresIn: config.jwt.expiresIn }
    );
    return res.json(success({ token, user: { id: result.insertId, username, nickname: nickname || '' } }, '注册成功'));
  } catch (e) {
    console.error('[auth/register]', e);
    return res.status(500).json(error('注册失败: ' + e.message, 500));
  }
});

// POST /api/auth/login  登录
router.post('/login', loginLimiter, [
  body('username').isLength({ min: 3, max: 32 }),
  body('password').isLength({ min: 6, max: 64 })
], async (req, res) => {
  const errs = validationResult(req);
  if (!errs.isEmpty()) {
    return res.status(400).json(error(errs.array()[0].msg, 400));
  }
  const { username, password } = req.body;
  const deviceId = req.body.deviceId || '';
  try {
    const [rows] = await pool.query('SELECT id, username, password, nickname, device_id FROM users WHERE username = ?', [username]);
    if (rows.length === 0) {
      return res.status(401).json(error('用户名或密码错误', 401));
    }
    const user = rows[0];
    const ok = await bcrypt.compare(password, user.password);
    if (!ok) {
      return res.status(401).json(error('用户名或密码错误', 401));
    }
    // 唯一设备登录：更新 device_id
    if (deviceId) {
      await pool.query('UPDATE users SET last_login = NOW(), device_id = ? WHERE id = ?', [deviceId, user.id]);
    } else {
      await pool.query('UPDATE users SET last_login = NOW() WHERE id = ?', [user.id]);
    }
    // 签发 token（包含 deviceId）
    const token = jwt.sign(
      { userId: user.id, username: user.username, deviceId: deviceId || user.device_id || '' },
      config.jwt.secret,
      { expiresIn: config.jwt.expiresIn }
    );
    return res.json(success({ token, user: { id: user.id, username: user.username, nickname: user.nickname } }, '登录成功'));
  } catch (e) {
    console.error('[auth/login]', e);
    return res.status(500).json(error('登录失败: ' + e.message, 500));
  }
});

// POST /api/auth/logout  登出（清除 device_id）
router.post('/logout', authRequired, async (req, res) => {
  try {
    await pool.query('UPDATE users SET device_id = NULL WHERE id = ?', [req.userId]);
    return res.json(success({ ok: true }, '已退出登录'));
  } catch (e) {
    return res.status(500).json(error('退出失败: ' + e.message, 500));
  }
});

// POST /api/auth/check-username  检查用户名可用性
router.post('/check-username', [
  body('username').isLength({ min: 3, max: 32 })
], async (req, res) => {
  const errs = validationResult(req);
  if (!errs.isEmpty()) {
    return res.json(success({ available: false, reason: '用户名长度需 3-32' }));
  }
  const { username } = req.body;
  try {
    const [rows] = await pool.query('SELECT id FROM users WHERE username = ?', [username]);
    return res.json(success({ available: rows.length === 0 }));
  } catch (e) {
    return res.status(500).json(error('校验失败', 500));
  }
});

// GET /api/auth/me  获取当前用户
router.get('/me', authRequired, async (req, res) => {
  try {
    const [rows] = await pool.query('SELECT id, username, nickname, created_at, last_login FROM users WHERE id = ?', [req.userId]);
    if (rows.length === 0) {
      return res.status(404).json(error('用户不存在', 404));
    }
    return res.json(success(rows[0]));
  } catch (e) {
    return res.status(500).json(error('查询失败', 500));
  }
});

// DELETE /api/auth/user/:username  删除指定用户及其所有数据（管理员操作）
// 需要在服务端配置 ADMIN_SECRET 环境变量
router.delete('/user/:username', async (req, res) => {
  const adminSecret = process.env.ADMIN_SECRET;
  const providedSecret = req.headers['x-admin-secret'];
  if (!adminSecret || providedSecret !== adminSecret) {
    return res.status(403).json(error('未授权', 403));
  }

  const { username } = req.params;
  if (!username || username.length < 3) {
    return res.status(400).json(error('用户名无效', 400));
  }

  try {
    const [users] = await pool.query('SELECT id FROM users WHERE username = ?', [username]);
    if (users.length === 0) {
      return res.status(404).json(error('用户不存在', 404));
    }
    const userId = users[0].id;

    // 按外键依赖顺序删除，使用事务
    const conn = await pool.getConnection();
    await conn.beginTransaction();
    try {
      // 1. daily_task_items (通过 daily_tasks 关联)
      await conn.query(
        `DELETE di FROM daily_task_items di
         INNER JOIN daily_tasks dt ON dt.id = di.task_id
         WHERE dt.user_id = ?`,
        [userId]
      );
      // 2. daily_tasks
      await conn.query('DELETE FROM daily_tasks WHERE user_id = ?', [userId]);
      // 3. checkins
      await conn.query(
        `DELETE FROM checkins WHERE article_id IN (SELECT id FROM articles WHERE user_id = ?)`,
        [userId]
      );
      // 4. articles
      await conn.query('DELETE FROM articles WHERE user_id = ?', [userId]);
      // 5. user_configs
      await conn.query('DELETE FROM user_configs WHERE user_id = ?', [userId]);
      // 6. users
      await conn.query('DELETE FROM users WHERE id = ?', [userId]);

      await conn.commit();
      return res.json(success({ username, userId }, '用户及关联数据已删除'));
    } catch (e) {
      await conn.rollback();
      throw e;
    } finally {
      conn.release();
    }
  } catch (e) {
    console.error('[auth/delete-user]', e);
    return res.status(500).json(error('删除失败: ' + e.message, 500));
  }
});

module.exports = router;
