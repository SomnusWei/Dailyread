// JWT 鉴权中间件
const jwt = require('jsonwebtoken');
const config = require('../config');
const { pool } = require('../db');
const { error } = require('../utils/response');

async function authRequired(req, res, next) {
  const authHeader = req.headers.authorization;
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json(error('未登录', 401));
  }
  const token = authHeader.split(' ')[1];
  try {
    const decoded = jwt.verify(token, config.jwt.secret);
    req.userId = decoded.userId;
    req.username = decoded.username;
    req.deviceId = decoded.deviceId || '';

    // 唯一设备登录校验：检查 token 中的 device_id 是否与用户当前绑定的一致
    if (decoded.deviceId) {
      try {
        const [rows] = await pool.query('SELECT device_id FROM users WHERE id = ?', [decoded.userId]);
        if (rows.length > 0 && rows[0].device_id && rows[0].device_id !== decoded.deviceId) {
          // 设备不一致：在其他设备登录了
          const errBody = { code: 401, message: '账号已在其他设备登录，请重新登录', data: { conflict: true } };
          return res.status(401).json(errBody);
        }
      } catch (dbErr) {
        console.error('authRequired device check error:', dbErr.message);
      }
    }
    next();
  } catch (e) {
    return res.status(401).json(error('token 无效或已过期', 401));
  }
}

// 可选鉴权（不强制登录，但若带 token 则解析）
function authOptional(req, res, next) {
  const authHeader = req.headers.authorization;
  if (authHeader && authHeader.startsWith('Bearer ')) {
    const token = authHeader.split(' ')[1];
    try {
      const decoded = jwt.verify(token, config.jwt.secret);
      req.userId = decoded.userId;
      req.username = decoded.username;
      req.deviceId = decoded.deviceId || '';
    } catch (e) {
      // 忽略错误，继续
    }
  }
  next();
}

module.exports = { authRequired, authOptional };
