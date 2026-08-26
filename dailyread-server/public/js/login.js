(function() {
  const API_BASE = '';
  const tokenKey = 'admin_token';

  // 如果已有 token，检查是否有效
  const existingToken = localStorage.getItem(tokenKey);
  if (existingToken) {
    fetch(`${API_BASE}/api/admin/check`, {
      headers: { 'Authorization': `Bearer ${existingToken}` }
    })
    .then(res => res.json())
    .then(data => {
      if (data.code === 0) {
        window.location.href = '/admin.html';
      } else {
        localStorage.removeItem(tokenKey);
      }
    })
    .catch(() => {
      localStorage.removeItem(tokenKey);
    });
  }

  const form = document.getElementById('loginForm');
  const errorBox = document.getElementById('loginError');
  const loginBtn = document.getElementById('loginBtn');
  const usernameInput = document.getElementById('username');
  const passwordInput = document.getElementById('password');

  function showError(msg) {
    errorBox.textContent = msg;
    errorBox.classList.add('show');
  }

  function hideError() {
    errorBox.classList.remove('show');
  }

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    hideError();

    const username = usernameInput.value.trim();
    const password = passwordInput.value;

    if (!username || !password) {
      showError('请输入用户名和密码');
      return;
    }

    loginBtn.disabled = true;
    loginBtn.textContent = '登录中...';

    try {
      const res = await fetch(`${API_BASE}/api/admin/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });

      const data = await res.json();

      if (data.code === 0) {
        localStorage.setItem(tokenKey, data.data.token);
        localStorage.setItem('admin_user', JSON.stringify({
          username: data.data.username,
          nickname: data.data.nickname,
          role: data.data.role
        }));
        window.location.href = '/admin.html';
      } else {
        showError(data.message || '登录失败');
        loginBtn.disabled = false;
        loginBtn.textContent = '登 录';
      }
    } catch (err) {
      showError('网络错误，请稍后重试');
      loginBtn.disabled = false;
      loginBtn.textContent = '登 录';
    }
  });
})();
