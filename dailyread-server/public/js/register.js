// 注册页面脚本
document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('registerForm');
  const submitBtn = document.getElementById('submitBtn');
  const btnText = submitBtn.querySelector('.btn-text');
  const btnLoader = submitBtn.querySelector('.btn-loader');
  const formSuccess = document.getElementById('formSuccess');

  const usernameInput = document.getElementById('username');
  const nicknameInput = document.getElementById('nickname');
  const passwordInput = document.getElementById('password');
  const confirmInput = document.getElementById('confirmPassword');

  function showError(inputId, message) {
    const input = document.getElementById(inputId);
    const errorEl = document.getElementById(inputId + 'Error');
    input.classList.add('error');
    if (errorEl) {
      errorEl.textContent = message;
    }
  }

  function clearError(inputId) {
    const input = document.getElementById(inputId);
    const errorEl = document.getElementById(inputId + 'Error');
    input.classList.remove('error');
    if (errorEl) {
      errorEl.textContent = '';
    }
  }

  function validateForm() {
    let valid = true;
    const username = usernameInput.value.trim();
    const password = passwordInput.value;
    const confirm = confirmInput.value;

    clearError('username');
    clearError('password');
    clearError('confirmPassword');

    if (username.length < 3) {
      showError('username', '用户名至少 3 个字符');
      valid = false;
    } else if (username.length > 32) {
      showError('username', '用户名不能超过 32 个字符');
      valid = false;
    }

    if (password.length < 6) {
      showError('password', '密码至少 6 位');
      valid = false;
    } else if (password.length > 64) {
      showError('password', '密码不能超过 64 位');
      valid = false;
    }

    if (password !== confirm) {
      showError('confirmPassword', '两次输入的密码不一致');
      valid = false;
    }

    return valid;
  }

  // 实时验证
  passwordInput.addEventListener('input', () => {
    if (confirmInput.value) {
      clearError('confirmPassword');
      if (passwordInput.value !== confirmInput.value) {
        showError('confirmPassword', '两次输入的密码不一致');
      }
    }
  });

  confirmInput.addEventListener('input', () => {
    clearError('confirmPassword');
    if (passwordInput.value !== confirmInput.value) {
      showError('confirmPassword', '两次输入的密码不一致');
    }
  });

  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    const username = usernameInput.value.trim();
    const nickname = nicknameInput.value.trim();
    const password = passwordInput.value;

    // 显示加载状态
    submitBtn.disabled = true;
    btnText.style.display = 'none';
    btnLoader.style.display = 'block';

    try {
      const response = await fetch('/api/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, nickname, password })
      });

      const data = await response.json();

      if (response.ok && data.code === 0) {
        // 注册成功
        formSuccess.style.display = 'block';
        form.style.display = 'none';

        setTimeout(() => {
          window.location.href = '/';
        }, 2000);
      } else {
        // 注册失败
        const errorMessage = data.message || '注册失败，请重试';
        showError('username', errorMessage);
        submitBtn.disabled = false;
        btnText.style.display = 'block';
        btnLoader.style.display = 'none';
      }
    } catch (error) {
      showError('username', '网络错误，请检查网络后重试');
      submitBtn.disabled = false;
      btnText.style.display = 'block';
      btnLoader.style.display = 'none';
    }
  });
});
