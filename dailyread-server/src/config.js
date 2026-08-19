// 配置加载模块
require('dotenv').config();

function required(key, defaultValue) {
  const v = process.env[key];
  if (v === undefined || v === '') {
    if (defaultValue !== undefined) return defaultValue;
    throw new Error(`环境变量 ${key} 未设置`);
  }
  return v;
}

module.exports = {
  env: required('NODE_ENV', 'development'),
  port: parseInt(required('PORT', '3001'), 10),

  db: {
    host: required('DB_HOST', 'localhost'),
    port: parseInt(required('DB_PORT', '3306'), 10),
    user: required('DB_USER', 'root'),
    password: required('DB_PASSWORD', ''),
    database: required('DB_NAME', 'dailyread_db')
  },

  jwt: {
    secret: required('JWT_SECRET', 'dev-secret-change-me'),
    expiresIn: required('JWT_EXPIRES_IN', '30d')
  },

  cors: {
    origin: (required('CORS_ORIGIN', '*') === '*') ? true : required('CORS_ORIGIN', '*').split(',')
  },

  rateLimit: {
    registerPerHour: parseInt(required('RATE_LIMIT_REGISTER_PER_HOUR', '3'), 10),
    loginPerMin: parseInt(required('RATE_LIMIT_LOGIN_PER_MIN', '5'), 10),
    apiPerMin: parseInt(required('RATE_LIMIT_API_PER_MIN', '100'), 10)
  }
};
