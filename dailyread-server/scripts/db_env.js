#!/usr/bin/env node
/**
 * 读取 /opt/dailyread-server/.env 中的数据库连接配置，
 * 输出为 shell 可安全 eval 的赋值行（KEY='value'）。
 *
 * 使用应用自身的 dotenv 解析 .env，与服务端 Node 服务解析行为完全一致。
 * 密码只进入调用进程的内存环境变量，不会出现在脚本源码、命令行参数或日志中。
 */
const envPath = '/opt/dailyread-server/.env';
const loaded = require('/opt/dailyread-server/node_modules/dotenv').config({ path: envPath });

if (loaded.error) {
  console.error('读取 .env 失败: ' + loaded.error.message);
  process.exit(1);
}

const env = loaded.parsed || {};
const keys = ['DB_HOST', 'DB_PORT', 'DB_USER', 'DB_PASSWORD', 'DB_NAME'];

// 单引号包裹，内部单引号转义为 '\''，保证 eval 安全
const quote = (s) => "'" + String(s == null ? '' : s).replace(/'/g, "'\\''") + "'";

for (const k of keys) {
  console.log(k + '=' + quote(env[k] || ''));
}
