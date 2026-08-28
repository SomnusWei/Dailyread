// 学习中心登录逻辑
(function () {
  'use strict';

  // 已登录则直接进入
  if (localStorage.getItem('lc_token') && localStorage.getItem('lc_user')) {
    location.replace('/center/app.html');
    return;
  }

  var form = document.getElementById('loginForm');
  var errBox = document.getElementById('loginError');
  var btn = document.getElementById('loginBtn');

  function showError(msg) {
    errBox.textContent = msg;
    errBox.classList.add('show');
  }

  form.addEventListener('submit', async function (e) {
    e.preventDefault();
    errBox.classList.remove('show');

    var username = document.getElementById('username').value.trim();
    var password = document.getElementById('password').value;
    if (username.length < 3 || password.length < 6) {
      return showError('请输入正确的账号与密码');
    }

    btn.disabled = true;
    btn.textContent = '登录中…';
    try {
      var res = await fetch('/api/learning/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: username, password: password })
      });
      var json = await res.json();
      if (!res.ok || json.code !== 0) {
        throw new Error(json.message || '登录失败');
      }
      localStorage.setItem('lc_token', json.data.token);
      localStorage.setItem('lc_user', JSON.stringify(json.data.user));
      // 清除过期缓存并进入应用
      if (window.caches && caches.keys) {
        caches.keys().then(function (keys) {
          keys.forEach(function (k) {
            if (k.indexOf('lc-mission-') === 0 && k !== 'lc-mission-v1') caches.delete(k);
          });
        }).catch(function () {});
      }
      location.replace('/center/app.html');
    } catch (err) {
      showError(err.message || '网络异常，请稍后再试');
      btn.disabled = false;
      btn.textContent = '登 录';
    }
  });
})();
