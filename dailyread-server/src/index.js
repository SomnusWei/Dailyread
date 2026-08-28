// DailyRead 后端服务 - 主入口
require('dotenv').config();

const path = require('path');
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
const rateLimit = require('express-rate-limit');

const config = require('./config');
const { testConnection } = require('./db');
const errorHandler = require('./middleware/errorHandler');

const authRoutes = require('./routes/auth');
const articleRoutes = require('./routes/articles');
const checkinRoutes = require('./routes/checkins');
const dailyTaskRoutes = require('./routes/dailyTasks');
const configRoutes = require('./routes/config');
const migrateRoutes = require('./routes/migrate');
const adminRoutes = require('./routes/admin');
const learningRoutes = require('./routes/learning');
const { ensureLearningSchema } = require('./db/learning_init');
const { startScheduler } = require('./cron');

const app = express();

// 信任 nginx 反向代理
app.set('trust proxy', 1);

// 安全中间件
app.use(helmet({ contentSecurityPolicy: false, crossOriginEmbedderPolicy: false }));

// CORS
app.use(cors({ origin: config.cors.origin, credentials: true }));

// 日志
app.use(morgan('combined'));

// JSON 解析（支持大体积，文章含 base64 图片与音频）
app.use(express.json({ limit: '50mb' }));
app.use(express.urlencoded({ extended: true, limit: '50mb' }));

// 全局限流：100 次/分钟/IP（业务接口）
const apiLimiter = rateLimit({
  windowMs: 60 * 1000,
  max: config.rateLimit.apiPerMin,
  standardHeaders: true,
  legacyHeaders: false,
  message: { code: 429, message: '请求过于频繁', data: null }
});
app.use('/api', apiLimiter);

// 静态文件 - 官网前端
app.use(express.static(path.join(__dirname, '..', 'public')));

// 讲义文件静态托管（文件名为随机串，路径不可枚举）
app.use('/uploads/handouts', express.static(path.join(__dirname, '..', 'uploads', 'handouts'), { maxAge: '7d' }));

// 管理后台 - 访问 /admin/ 重定向到登录页
app.get('/admin/', (req, res) => {
  res.redirect('/login.html');
});

// 路由
app.use('/api/auth', authRoutes);
app.use('/api/articles', articleRoutes);
app.use('/api/checkins', checkinRoutes);
app.use('/api/daily-tasks', dailyTaskRoutes);
app.use('/api/config', configRoutes);
app.use('/api/migrate', migrateRoutes);
app.use('/api/admin', adminRoutes);
app.use('/api/learning', learningRoutes);

// 健康检查
app.get('/health', (req, res) => res.json({ ok: true, ts: Date.now() }));

// 404
app.use((req, res) => res.status(404).json({ code: 404, message: '接口不存在', data: null }));

// 错误处理
app.use(errorHandler);

// 启动
async function start() {
  try {
    await testConnection();
    // 学习中心表初始化（幂等，含默认管理员种子）
    await ensureLearningSchema();
    app.listen(config.port, '127.0.0.1', () => {
      console.log(`[Server] DailyRead 服务已启动: http://127.0.0.1:${config.port} (env=${config.env})`);
      // 启动定时任务：每天 00:00 重新生成所有用户的每日任务
      startScheduler();
    });
  } catch (e) {
    console.error('[Server] 启动失败:', e.message);
    process.exit(1);
  }
}

start();

// 优雅退出
process.on('SIGTERM', () => {
  console.log('[Server] 收到 SIGTERM，准备退出');
  process.exit(0);
});
process.on('SIGINT', () => {
  console.log('[Server] 收到 SIGINT，准备退出');
  process.exit(0);
});
