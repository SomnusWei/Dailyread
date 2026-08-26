(function() {
  const API_BASE = '';
  const tokenKey = 'admin_token';
  const userKey = 'admin_user';

  const token = localStorage.getItem(tokenKey);
  const userData = JSON.parse(localStorage.getItem(userKey) || '{}');

  // 检查登录状态
  if (!token) {
    window.location.href = '/login.html';
    return;
  }

  // 设置用户信息
  document.getElementById('adminName').textContent = userData.nickname || userData.username || '管理员';
  document.getElementById('adminAvatar').textContent = (userData.username || 'A').charAt(0).toUpperCase();

  // 退出登录
  document.getElementById('logoutBtn').addEventListener('click', async () => {
    try {
      await fetch(`${API_BASE}/api/admin/logout`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
    } catch (e) {}
    localStorage.removeItem(tokenKey);
    localStorage.removeItem(userKey);
    window.location.href = '/login.html';
  });

  // 页面切换
  const navItems = document.querySelectorAll('.nav-item');
  const pages = {
    dashboard: document.getElementById('dashboardPage'),
    users: document.getElementById('usersPage')
  };
  const pageTitle = document.getElementById('pageTitle');

  navItems.forEach(item => {
    item.addEventListener('click', (e) => {
      e.preventDefault();
      const page = item.dataset.page;
      navItems.forEach(n => n.classList.remove('active'));
      item.classList.add('active');

      if (page === 'dashboard') {
        pages.dashboard.classList.remove('hidden');
        pages.users.classList.add('hidden');
        pageTitle.textContent = '数据统计';
        loadStats();
      } else if (page === 'users') {
        pages.dashboard.classList.add('hidden');
        pages.users.classList.remove('hidden');
        pageTitle.textContent = '用户管理';
        loadUsers();
      }
    });
  });

  // 加载统计数据
  async function loadStats() {
    const grid = document.getElementById('statsGrid');
    grid.innerHTML = '<div class="loading">加载中...</div>';

    try {
      const res = await fetch(`${API_BASE}/api/admin/stats`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();

      if (data.code === 0) {
        const s = data.data;
        grid.innerHTML = `
          <div class="stat-card">
            <div class="stat-label">总用户数</div>
            <div class="stat-value">${s.total_users}</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">管理员数</div>
            <div class="stat-value">${s.admin_users}</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">文章总数</div>
            <div class="stat-value">${s.total_articles}</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">打卡次数</div>
            <div class="stat-value">${s.total_checkins}</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">每日任务</div>
            <div class="stat-value">${s.total_tasks}</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">活跃用户</div>
            <div class="stat-value">${s.active_users}</div>
          </div>
        `;
      } else {
        grid.innerHTML = '<div class="loading">加载失败</div>';
      }
    } catch (e) {
      grid.innerHTML = '<div class="loading">网络错误</div>';
    }
  }

  // 加载用户列表
  async function loadUsers() {
    const list = document.getElementById('usersList');
    list.innerHTML = '<div class="loading">加载中...</div>';

    try {
      const res = await fetch(`${API_BASE}/api/admin/users`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();

      if (data.code === 0 && data.data.users.length > 0) {
        let rows = data.data.users.map(u => `
          <tr>
            <td>${u.id}</td>
            <td><strong>${u.username}</strong></td>
            <td>${u.nickname || '-'}</td>
            <td><span class="badge ${u.is_admin ? 'badge-admin' : 'badge-user'}">${u.role}</span></td>
            <td>${u.article_count}</td>
            <td>${u.checkin_count}</td>
            <td>${u.created_at ? new Date(u.created_at).toLocaleDateString('zh-CN') : '-'}</td>
            <td>
              ${u.username !== userData.username ? `
                <button class="btn btn-sm btn-outline" onclick="editUser('${u.username}')">编辑</button>
                <button class="btn btn-sm btn-danger" onclick="deleteUser('${u.username}')">删除</button>
              ` : '<span style="color:var(--text-muted)">当前用户</span>'}
            </td>
          </tr>
        `).join('');

        list.innerHTML = `
          <table class="admin-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>用户名</th>
                <th>昵称</th>
                <th>角色</th>
                <th>文章</th>
                <th>打卡</th>
                <th>注册时间</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>${rows}</tbody>
          </table>
        `;
      } else {
        list.innerHTML = '<div class="empty">暂无用户</div>';
      }
    } catch (e) {
      list.innerHTML = '<div class="loading">加载失败</div>';
    }
  }

  // 删除用户
  window.deleteUser = async function(username) {
    if (!confirm(`确定删除用户 "${username}" 及其所有关联数据？此操作不可恢复！`)) return;

    try {
      const res = await fetch(`${API_BASE}/api/admin/users/${encodeURIComponent(username)}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();
      if (data.code === 0) {
        alert('删除成功');
        loadUsers();
      } else {
        alert(data.message || '删除失败');
      }
    } catch (e) {
      alert('网络错误');
    }
  };

  // 编辑用户（简易：修改密码）
  window.editUser = async function(username) {
    const newPassword = prompt(`为用户 "${username}" 重置密码（留空取消）：`, '');
    if (newPassword === null || !newPassword.trim()) return;
    if (newPassword.length < 6) {
      alert('密码长度至少6位');
      return;
    }

    try {
      const res = await fetch(`${API_BASE}/api/admin/users/${encodeURIComponent(username)}/password`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ password: newPassword })
      });
      const data = await res.json();
      if (data.code === 0) {
        alert('密码已更新');
      } else {
        alert(data.message || '更新失败');
      }
    } catch (e) {
      alert('网络错误');
    }
  };

  // 添加用户
  const addUserBtn = document.getElementById('addUserBtn');
  const addUserModal = document.getElementById('addUserModal');
  const cancelAddUser = document.getElementById('cancelAddUser');
  const addUserForm = document.getElementById('addUserForm');

  addUserBtn.addEventListener('click', () => {
    addUserModal.classList.remove('hidden');
  });

  cancelAddUser.addEventListener('click', () => {
    addUserModal.classList.add('hidden');
    addUserForm.reset();
  });

  addUserModal.addEventListener('click', (e) => {
    if (e.target === addUserModal) {
      addUserModal.classList.add('hidden');
      addUserForm.reset();
    }
  });

  addUserForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('newUsername').value.trim();
    const nickname = document.getElementById('newNickname').value.trim();
    const password = document.getElementById('newPassword').value;
    const role = document.getElementById('newRole').value;

    try {
      const res = await fetch(`${API_BASE}/api/admin/users`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ username, nickname, password, role })
      });
      const data = await res.json();
      if (data.code === 0) {
        alert('用户创建成功');
        addUserModal.classList.add('hidden');
        addUserForm.reset();
        loadUsers();
      } else {
        alert(data.message || '创建失败');
      }
    } catch (e) {
      alert('网络错误');
    }
  });

  // 初始加载
  loadStats();
})();
