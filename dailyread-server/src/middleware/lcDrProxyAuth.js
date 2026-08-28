// 学习中心账号代理访问 DailyRead 数据的鉴权中间件
// 流程：验证 lc token（scope='lc'）→ 查 lc_users.dr_user_id → 注入 req.drUserId
// 与 authRequired 的区别：
//   - authRequired 走 DailyRead token（含 device_id 唯一设备校验），用于鸿蒙/Win 端
//   - lcDrProxyAuth 走学习中心 token + 绑定关系，用于 PWA 代理路由 /api/dr/*
//   - 不签发 DailyRead token，不触发 device_id 冲突，对现有端零影响
const jwt = require('jsonwebtoken');
const config = require('../config');
const { pool } = require('../db');
const { error } = require('../utils/response');

async function lcDrProxyAuth(req, res, next) {
  const authHeader = req.headers.authorization;
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json(error('未登录', 401));
  }
  try {
    const decoded = jwt.verify(authHeader.split(' ')[1], config.jwt.secret);
    // 仅接受学习中心 token
    if (decoded.scope !== 'lc' || !decoded.lcId) {
      return res.status(401).json(error('token 无效', 401));
    }
    // 查绑定的 DailyRead user_id
    const [rows] = await pool.query(
      'SELECT dr_user_id FROM lc_users WHERE id = ? LIMIT 1',
      [decoded.lcId]
    );
    if (rows.length === 0) {
      return res.status(401).json(error('账号不存在', 401));
    }
    if (!rows[0].dr_user_id) {
      return res.status(403).json(error('未绑定 DailyRead 账号，请先在设置中绑定', 403));
    }
    // 注入代理身份（不签发 DailyRead token）
    req.drUserId = rows[0].dr_user_id;
    req.lcUser = { id: decoded.lcId, username: decoded.username, role: decoded.role };
    next();
  } catch (e) {
    return res.status(401).json(error('token 无效或已过期', 401));
  }
}

module.exports = { lcDrProxyAuth };
