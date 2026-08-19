// 全局错误处理中间件
const { error } = require('../utils/response');

function errorHandler(err, req, res, next) {
  console.error('[ERROR]', err.message);
  if (err.type === 'entity.parse.failed') {
    return res.status(400).json(error('JSON 解析失败', 400));
  }
  return res.status(500).json(error('服务器内部错误', 500));
}

module.exports = errorHandler;
