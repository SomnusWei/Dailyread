// 统一响应格式
function success(data, message) {
  return { code: 0, message: message || 'success', data: data || null };
}

function error(message, code) {
  return { code: code || -1, message: message, data: null };
}

module.exports = { success, error };
