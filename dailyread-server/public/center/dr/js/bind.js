// DailyRead 账号绑定逻辑
// 复用学习中心 token（localStorage 中 lc_token），调 /api/learning/dr/* 接口
(function () {
  'use strict';

  var TOKEN_KEY = 'lc_token';
  var USER_KEY = 'lc_user';

  function getToken() {
    return localStorage.getItem(TOKEN_KEY) || '';
  }

  // 统一请求封装（带 lc token）
  function api(method, path, body) {
    var opts = { method: method, headers: { 'Content-Type': 'application/json' } };
    var token = getToken();
    if (token) opts.headers['Authorization'] = 'Bearer ' + token;
    if (body) opts.body = JSON.stringify(body);
    return fetch(path, opts).then(function (r) {
      return r.json().then(function (d) {
        if (!r.ok || d.code !== 0) {
          var msg = (d && d.message) || ('请求失败 (' + r.status + ')');
          var err = new Error(msg);
          err.status = r.status;
          err.body = d;
          throw err;
        }
        return d.data;
      });
    });
  }

  function showPanel(id) {
    ['boundPanel', 'bindForm', 'loadingPanel'].forEach(function (p) {
      document.getElementById(p).style.display = (p === id ? 'block' : 'none');
    });
  }

  function showError(msg) {
    var el = document.getElementById('errorMsg');
    el.textContent = msg || '';
    el.style.display = msg ? 'block' : 'none';
  }

  // 检查登录态 + 绑定状态
  function checkStatus() {
    if (!getToken()) {
      // 未登录学习中心，跳转登录
      location.href = '/center/index.html';
      return;
    }
    api('GET', '/api/learning/dr/status').then(function (data) {
      if (data && data.bound) {
        document.getElementById('boundUser').textContent =
          (data.drUser.nickname || data.drUser.username) + '（' + data.drUser.username + '）';
        showPanel('boundPanel');
      } else {
        showPanel('bindForm');
      }
    }).catch(function (e) {
      if (e.status === 401) {
        location.href = '/center/index.html';
      } else {
        showError(e.message);
        showPanel('bindForm');
      }
    });
  }

  // 绑定
  document.getElementById('bindForm').addEventListener('submit', function (e) {
    e.preventDefault();
    showError('');
    var btn = document.getElementById('bindBtn');
    btn.disabled = true; btn.textContent = '绑定中…';
    var username = document.getElementById('drUsername').value.trim();
    var password = document.getElementById('drPassword').value;
    api('POST', '/api/learning/dr/bind', { drUsername: username, drPassword: password })
      .then(function (data) {
        // 绑定成功，进入 PWA
        location.href = '/center/dr/app.html';
      })
      .catch(function (err) {
        btn.disabled = false; btn.textContent = '确认绑定';
        showError(err.message || '绑定失败');
      });
  });

  // 解绑
  document.getElementById('unbindBtn').addEventListener('click', function () {
    if (!confirm('确定要解除 DailyRead 账号绑定吗？解除后将无法使用每日阅读功能。')) return;
    api('POST', '/api/learning/dr/unbind').then(function () {
      showPanel('bindForm');
      showError('');
      document.getElementById('drUsername').value = '';
      document.getElementById('drPassword').value = '';
    }).catch(function (err) {
      showError(err.message || '解绑失败');
    });
  });

  checkStatus();
})();
