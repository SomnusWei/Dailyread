// 炎武班学习中心 - SPA 应用逻辑
(function () {
  'use strict';

  // ================= 基础 =================
  var token = localStorage.getItem('lc_token');
  var me = null;
  try { me = JSON.parse(localStorage.getItem('lc_user') || 'null'); } catch (e) { me = null; }
  if (!token || !me) {
    localStorage.removeItem('lc_token');
    localStorage.removeItem('lc_user');
    location.replace('/center/index.html');
    return;
  }

  var ROLE_LABELS = { admin: '管理员', teacher: '教师', phd: '博士生', master: '研究生', bachelor: '本科生', apprentice: '师承生' };
  var ALL_ROLES = ['admin', 'teacher', 'phd', 'master', 'bachelor', 'apprentice'];
  var STUDENT_ROLES = ['phd', 'master', 'bachelor', 'apprentice'];
  var CATEGORIES = ['基础学', '诊断学', '针灸腧穴', '中药', '方剂', '内科', '外科', '妇科', '儿科', '推拿', '养生', '经典'];
  var isStaff = (me.role === 'admin' || me.role === 'teacher');
  var isAdmin = (me.role === 'admin');

  function esc(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }
  function fmtTime(s) {
    if (!s) return '';
    var d = new Date(typeof s === 'number' ? s : String(s).replace(' ', 'T'));
    if (isNaN(d.getTime())) return String(s);
    return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0')
      + ' ' + String(d.getHours()).padStart(2, '0') + ':' + String(d.getMinutes()).padStart(2, '0');
  }
  // 作业窗口状态 → 展示文案
  function windowBadge(a) {
    if (!a.start_at && !a.due_at) return '<span class="lc-win-badge lc-win-open">不限时</span>';
    if (a.window === 'pending') return '<span class="lc-win-badge lc-win-pending">⏳ ' + fmtTime(a.start_at) + ' 开交</span>';
    if (a.window === 'closed') return '<span class="lc-win-badge lc-win-closed">⛔ 已截止' + (a.due_at ? '（' + fmtTime(a.due_at) + '）' : '') + '</span>';
    if (a.due_at) return '<span class="lc-win-badge lc-win-open">🕒 截止 ' + fmtTime(a.due_at) + '</span>';
    return '<span class="lc-win-badge lc-win-open">🟢 提交中</span>';
  }
  function fmtSize(n) {
    if (!n) return '';
    if (n < 1024) return n + 'B';
    if (n < 1048576) return (n / 1024).toFixed(1) + 'KB';
    return (n / 1048576).toFixed(1) + 'MB';
  }

  // ---- API ----
  async function api(path, opts) {
    opts = opts || {};
    opts.headers = Object.assign({}, opts.headers);
    if (!(opts.body instanceof FormData)) {
      opts.headers['Content-Type'] = opts.headers['Content-Type'] || 'application/json';
    }
    opts.headers['Authorization'] = 'Bearer ' + token;
    var res = await fetch('/api/learning' + path, opts);
    var json = null;
    try { json = await res.json(); } catch (e) { json = { code: -1, message: '响应解析失败' }; }
    if (res.status === 401) {
      localStorage.removeItem('lc_token');
      localStorage.removeItem('lc_user');
      location.replace('/center/index.html');
      throw new Error('未登录');
    }
    if (!res.ok || json.code !== 0) {
      throw new Error(json.message || ('请求失败（' + res.status + '）'));
    }
    return json.data;
  }

  // ---- Toast ----
  var toastTimer = null;
  function toast(msg, type) {
    var el = document.getElementById('lcToast');
    el.textContent = msg;
    el.className = type ? type : '';
    void el.offsetWidth;
    el.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { el.classList.remove('show'); }, 2400);
  }

  // ================= 模态框 =================
  var modalMask = document.getElementById('modalMask');
  function openModal(cfg) {
    document.getElementById('modalCat').textContent = cfg.catLabel;
    document.getElementById('modalCat').className = 'lc-cat-badge lc-cat-' + cfg.cat;
    document.getElementById('modalTitle').textContent = cfg.title || '';
    document.getElementById('modalMeta').innerHTML = cfg.metaHtml || '';
    var bodyEl = document.getElementById('modalBody');
    bodyEl.innerHTML = '';
    if (cfg.bodyNode) bodyEl.appendChild(cfg.bodyNode);
    var foot = document.getElementById('modalFoot');
    foot.innerHTML = '';
    (cfg.buttons || []).forEach(function (b) {
      var a = document.createElement('a');
      a.href = b.href || '#';
      a.className = b.primary === false ? 'btn btn-outline btn-sm' : 'btn btn-primary btn-sm';
      if (b.href) { a.target = '_blank'; a.rel = 'noopener'; a.textContent = b.label; foot.appendChild(a); }
      else { a.textContent = b.label; a.addEventListener('click', function (ev) { ev.preventDefault(); b.onClick(); }); foot.appendChild(a); }
    });
    modalMask.classList.add('show');
  }
  function closeModal() {
    modalMask.classList.remove('show');
    document.getElementById('modalBody').innerHTML = '';
    document.getElementById('modalFoot').innerHTML = '';
  }
  document.getElementById('modalClose').addEventListener('click', closeModal);
  modalMask.addEventListener('click', function (e) { if (e.target === modalMask) closeModal(); });

  function iframeOf(srcdoc, src) {
    var f = document.createElement('iframe');
    f.setAttribute('sandbox', '');               // 禁止脚本执行，防内容逃逸
    f.style.background = '#fff';
    if (srcdoc !== undefined && srcdoc !== null) f.srcdoc = srcdoc;
    else f.src = src;
    return f;
  }

  // ================= 头部信息 =================
  function initials(name) { return (name || '?').charAt(0).toUpperCase(); }
  function paintHeader() {
    var nick = me.nickname || me.username;
    document.getElementById('avatar').textContent = initials(nick);
    document.getElementById('chipName').textContent = nick;
    document.getElementById('chipRole').textContent = ROLE_LABELS[me.role] || me.role;
    document.getElementById('pfAvatar').textContent = initials(nick);
    document.getElementById('pfName').textContent = nick;
    document.getElementById('pfUsername').textContent = '@' + me.username;
    document.getElementById('pfRole').textContent = ROLE_LABELS[me.role] || me.role;
    document.querySelectorAll('.lc-staff-only').forEach(function (el) { el.style.display = isStaff ? '' : 'none'; });
    document.querySelectorAll('.lc-admin-only').forEach(function (el) { el.style.display = isAdmin ? '' : 'none'; });
    var logoutBtn = document.getElementById('logoutBtn');
    logoutBtn.addEventListener('click', function () {
      localStorage.removeItem('lc_token');
      localStorage.removeItem('lc_user');
      location.replace('/center/index.html');
    });
  }

  // ================= 导航与路由 =================
  var NAV_ITEMS = [
    { key: 'messages', icon: '🔔', label: '消息', show: true },
    { key: 'handouts', icon: '📨', label: '讲义库', show: true },
    { key: 'assignments', icon: '📝', label: '作业', show: true },
    { key: 'manage', icon: '🛠️', label: '管理', show: isStaff },
    { key: 'profile', icon: '👤', label: '我的', show: true }
  ];

  var unreadCount = 0;

  function buildNav() {
    var side = document.getElementById('sideNav');
    var bottom = document.getElementById('bottomNav');
    side.innerHTML = ''; bottom.innerHTML = '';
    NAV_ITEMS.forEach(function (item) {
      if (!item.show) return;
      var mkBtn = function (extraCls) {
        var b = document.createElement(extraCls ? 'div' : 'button');
        b.className = 'lc-nav-item';
        b.setAttribute('data-nav', item.key);
        b.innerHTML = '<span>' + item.icon + '</span><span>' + item.label + '</span>'
          + (item.key === 'messages'
            ? '<span class="lc-nav-badge" style="' + (unreadCount ? '' : 'display:none') + '">' + unreadCount + '</span>'
            : '');
        b.addEventListener('click', function () { go(item.key); });
        return b;
      };
      var sb = mkBtn('');
      sb.className = 'lc-nav-item' + (currentView === item.key ? ' active' : '');
      side.appendChild(sb);

      var bb = mkBtn('');
      bb.className = 'lc-bn-item' + (currentView === item.key ? ' active' : '');
      bb.setAttribute('data-bn', item.key);
      bb.innerHTML = '<span class="bn-icon">' + item.icon + '</span><span>' + item.label + '</span>'
        + (item.key === 'messages'
          ? '<span class="lc-bn-badge" style="' + (unreadCount ? '' : 'display:none') + '">' + unreadCount + '</span>'
          : '');
      bottom.appendChild(bb);
    });
  }

  var currentView = 'messages';
  var loadedViews = {};

  function go(view) {
    currentView = view;
    document.querySelectorAll('.lc-view').forEach(function (v) { v.classList.remove('active'); });
    var target = document.getElementById('view-' + view);
    if (target) target.classList.add('active');
    buildNav();
    if (!loadedViews[view]) loadView(view, true);
  }

  // 管理页快速跳转按钮（分发讲义/布置作业）
  document.querySelectorAll('[data-goto-manage]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      go('manage');
      switchManageTab(btn.getAttribute('data-goto-manage'));
    });
  });

  // ================= 未读轮询 =================
  async function refreshUnread() {
    try {
      var d = await api('/inbox/unread-count');
      unreadCount = d.count || 0;
      document.querySelectorAll('.lc-nav-badge, .lc-bn-badge').forEach(function (b) {
        b.style.display = unreadCount ? '' : 'none';
        b.textContent = unreadCount;
      });
    } catch (e) { /* 静默 */ }
  }

  // ================= 视图加载 =================
  function loadingCard(text) {
    return '<div class="lc-empty"><p>' + esc(text || '加载中…') + '</p></div>';
  }

  function loadView(view, force) {
    if (view === 'messages') { renderInbox(); return; }
    if (view === 'handouts') { renderHandouts(force); return; }
    if (view === 'assignments') { renderAssignments(force); return; }
    if (view === 'manage') { /* 面板常驻 */ }
    if (view === 'profile') { /* 静态 */ }
  }

  // ---------- 收件箱 ----------
  var inboxCache = [];
  async function renderInbox() {
    var list = document.getElementById('inboxList');
    list.innerHTML = loadingCard('正在获取消息…');
    try {
      var d = await api('/inbox');
      inboxCache = d.list || [];
      unreadCount = d.unread || 0;
      if (inboxCache.length === 0) {
        list.innerHTML = '<div class="lc-empty"><div class="lc-empty-icon">🕊️</div><p>暂无消息<br><small>收到讲义、作业或通知时会出现在这里</small></p></div>';
      } else {
        list.innerHTML = inboxCache.map(renderInboxItem).join('');
        bindInboxEvents();
      }
      refreshUnread();
    } catch (e) {
      list.innerHTML = '<div class="lc-empty"><p>加载失败：' + esc(e.message) + '</p></div>';
    }
  }

  function scopeTags(item) {
    // 讲义条目补充可见等级
    if (item.category === 'handout' && handoutCache.length) {
      var h = handoutCache.find(function (x) { return x.id === item.ref_id; });
      if (h) return h.level_scope.map(scopeName).join(' ');
    }
    if (item.category === 'assignment' && assignCacheMeta.length) {
      var a = assignCacheMeta.find(function (x) { return x.id === item.ref_id; });
      if (a) return a.level_scope.map(scopeName).join(' ');
    }
    return '';
  }

  function scopeName(lv) { return lv === 'all' ? '全等级' : (ROLE_LABELS[lv] || lv); }

  function renderInboxItem(m) {
    var catLabel = m.category === 'handout' ? '讲义分发' : m.category === 'assignment' ? '作业布置' : '通知消息';
    var tags = scopeTags(m);
    var hasContent = m.content && m.content.trim();
    return (
      '<div class="lc-card ' + (m.is_read ? '' : 'unread') + '" data-inbox-id="' + m.id + '">'
      + '<div class="lc-card-head">'
      + '<span class="lc-cat-badge lc-cat-' + m.category + '">' + catLabel + '</span>'
      + '<span class="lc-card-title">' + esc((m.title || '').replace(/^\[管理员消息\]/, '')) + '</span>'
      + (m.is_read ? '' : '<span class="lc-dot-unread" title="未读"></span>')
      + '</div>'
      + '<div class="lc-card-meta">'
      + '<span>来自：' + esc(m.sender_name || '系统') + '</span>'
      + '<span>' + fmtTime(m.created_at) + '</span>'
      + (tags ? '<span class="lc-scope-tag">' + esc(tags) + '</span>' : '')
      + '</div>'
      + (m.category === 'message' && hasContent ? '<div class="lc-card-body-text" style="display:none;" data-content-block>' + esc(m.content) + '</div>' : '')
      + (hasContent && m.category === 'message' ? '' : '')
      + '</div>'
    );
  }

  function bindInboxEvents() {
    document.querySelectorAll('#inboxList .lc-card').forEach(function (card) {
      card.addEventListener('click', function () { handleInboxClick(card); });
    });
  }

  async function handleInboxClick(card) {
    var id = Number(card.getAttribute('data-inbox-id'));
    var m = inboxCache.find(function (x) { return x.id === id; });
    if (!m) return;
    var wasUnread = !m.is_read;
    var contentBlock = card.querySelector('[data-content-block]');
    var expanded = contentBlock && contentBlock.style.display !== 'none';

    if (contentBlock && !expanded) {
      // 展开管理员消息正文
      contentBlock.style.display = 'block';
    } else if (contentBlock && expanded) {
      contentBlock.style.display = 'none';
    } else if (m.category === 'handout') {
      await openHandoutByRef(m.ref_id);
    } else if (m.category === 'assignment') {
      await openAssignmentByRef(m.ref_id);
    }

    if (wasUnread) {
      try {
        await api('/inbox/read', { method: 'POST', body: JSON.stringify({ ids: [id] }) });
        m.is_read = 1;
        unreadCount = Math.max(0, unreadCount - 1);
        card.classList.remove('unread');
        var dot = card.querySelector('.lc-dot-unread');
        if (dot) dot.remove();
        refreshUnread();
      } catch (e) { /* 忽略 */ }
    }
  }

  document.getElementById('markAllReadBtn').addEventListener('click', async function () {
    try {
      await api('/inbox/read', { method: 'POST', body: JSON.stringify({ all: true }) });
      unreadCount = 0;
      document.querySelectorAll('#inboxList .lc-card').forEach(function (c) { c.classList.remove('unread'); c.querySelectorAll('.lc-dot-unread').forEach(function (d) { d.remove(); }); });
      refreshUnread();
      toast('已全部标记为已读', 'success');
    } catch (e) { toast(e.message, 'error'); }
  });

  // ---------- 讲义库 ----------
  var handoutCache = [];
  var handoutCatFilter = '';

  function renderCatFilter() {
    var box = document.getElementById('handoutCatFilter');
    var counts = {};
    handoutCache.forEach(function (h) {
      var c = h.category || '未分类';
      counts[c] = (counts[c] || 0) + 1;
    });
    var hasUncat = counts['未分类'] || 0;
    var html = '<button class="lc-cat-chip' + (handoutCatFilter === '' ? ' on' : '') + '" data-cat="">全部 <i>' + handoutCache.length + '</i></button>';
    CATEGORIES.forEach(function (c) {
      if (!counts[c]) return;
      html += '<button class="lc-cat-chip' + (handoutCatFilter === c ? ' on' : '') + '" data-cat="' + esc(c) + '">' + esc(c) + ' <i>' + counts[c] + '</i></button>';
    });
    if (hasUncat) {
      html += '<button class="lc-cat-chip' + (handoutCatFilter === '未分类' ? ' on' : '') + '" data-cat="未分类">未分类 <i>' + hasUncat + '</i></button>';
    }
    box.innerHTML = html;
    box.style.display = handoutCache.length ? '' : 'none';
    box.querySelectorAll('.lc-cat-chip').forEach(function (chip) {
      chip.addEventListener('click', function () {
        handoutCatFilter = chip.getAttribute('data-cat') || '';
        renderCatFilter();
        renderHandoutCards();
      });
    });
  }

  function renderHandoutCards() {
    var list = document.getElementById('handoutList');
    var visible = handoutCatFilter
      ? handoutCache.filter(function (h) { return (h.category || '未分类') === handoutCatFilter; })
      : handoutCache;
    if (visible.length === 0) {
      list.innerHTML = '<div class="lc-empty"><div class="lc-empty-icon">📭</div><p>' + (handoutCache.length ? '该分类下暂无讲义' : '暂无可见的讲义<br><small>教师分发后会在这里出现</small>') + '</p></div>';
      return;
    }
    list.innerHTML = visible.map(renderHandoutItem).join('');
    bindHandoutEvents();
  }

  async function renderHandouts() {
    var list = document.getElementById('handoutList');
    list.innerHTML = loadingCard('正在加载讲义…');
    try {
      var d = await api('/handouts');
      handoutCache = d.list || [];
      if (d.categories && d.categories.length) CATEGORIES = d.categories;
      renderCatFilter();
      renderHandoutCards();
    } catch (e) {
      list.innerHTML = '<div class="lc-empty"><p>加载失败：' + esc(e.message) + '</p></div>';
    }
  }

  function renderHandoutItem(h) {
    var canDelete = isAdmin || h.uploader_id === me.id;
    var cat = h.category || '未分类';
    return (
      '<div class="lc-card" data-handout-id="' + h.id + '">'
      + '<div class="lc-card-head">'
      + '<span class="lc-cat-badge lc-cat-handout">' + esc(cat) + '</span>'
      + '<span class="lc-card-title">' + esc(h.title) + '</span>'
      + '</div>'
      + '<div class="lc-card-meta">'
      + '<span>发布者：' + esc(h.uploader_name || '-') + '</span>'
      + '<span>' + fmtTime(h.created_at) + '</span>'
      + (h.file_size ? '<span>' + fmtSize(h.file_size) + '</span>' : '')
      + '<span class="lc-scope-tag">面向：' + esc((h.level_scope || []).map(scopeName).join(' ')) + '</span>'
      + '</div>'
      + '<div class="lc-card-actions">'
      + '<button class="btn btn-primary btn-sm" data-act="read">📖 在线阅读</button>'
      + '<a class="btn btn-outline btn-sm" href="/uploads/handouts/' + encodeURIComponent(h.filename) + '" target="_blank" rel="noopener">新窗口打开</a>'
      + (canDelete ? '<button class="lc-link-danger" data-act="del">删除</button>' : '')
      + '</div>'
      + '</div>'
    );
  }

  function bindHandoutEvents() {
    document.querySelectorAll('#handoutList .lc-card').forEach(function (card) {
      var id = Number(card.getAttribute('data-handout-id'));
      card.querySelector('[data-act="read"]').addEventListener('click', function () { openHandoutDirect(id); });
      var del = card.querySelector('[data-act="del"]');
      if (del) del.addEventListener('click', function () {
        if (!confirm('确认删除该讲义？此操作不可恢复。')) return;
        api('/handouts/' + id, { method: 'DELETE' })
          .then(function () { toast('讲义已删除', 'success'); renderHandouts(); })
          .catch(function (e) { toast(e.message, 'error'); });
      });
    });
  }

  async function openHandoutDirect(id) {
    var h = handoutCache.find(function (x) { return x.id === id; }) ||
      (await api('/handouts')).list.find(function (x) { return x.id === id; });
    if (!h) return toast('未找到该讲义', 'error');
    openModal({
      cat: 'handout', catLabel: '讲义阅读', title: h.title,
      metaHtml: '<span>发布者：' + esc(h.uploader_name || '-') + '</span><span>' + fmtTime(h.created_at) + '</span>',
      bodyNode: iframeOf(null, '/uploads/handouts/' + encodeURIComponent(h.filename)),
      buttons: [{ label: '新窗口全屏查看', href: '/uploads/handouts/' + encodeURIComponent(h.filename), primary: true }]
    });
  }

  async function openHandoutByRef(refId) {
    if (!handoutCache.length) { await renderHandouts().catch(function () {}); go('handouts'); }
    var h = handoutCache.find(function (x) { return x.id === refId; });
    if (h) { openHandoutDirect(h.id); }
    else { toast('请前往「讲义库」查看最新列表', 'error'); go('handouts'); }
  }

  // ---------- 作业 ----------
  var assignCacheMeta = [];
  async function renderAssignments() {
    var list = document.getElementById('assignList');
    list.innerHTML = loadingCard('正在加载作业…');
    try {
      var d = await api('/assignments');
      assignCacheMeta = d.list || [];
      if (assignCacheMeta.length === 0) {
        list.innerHTML = '<div class="lc-empty"><div class="lc-empty-icon">📄</div><p>暂无作业<br><small>新的作业下发后，这里会同步展示</small></p></div>';
      } else {
        list.innerHTML = assignCacheMeta.map(renderAssignItem).join('');
        bindAssignEvents();
      }
      if (isStaff) renderMyAssignRecords();
    } catch (e) {
      list.innerHTML = '<div class="lc-empty"><p>加载失败：' + esc(e.message) + '</p></div>';
    }
  }

  function mySubBadge(a) {
    var s = a.my_submission;
    if (!s) return a.window === 'closed' ? '<span class="lc-sub-badge lc-sub-none">未提交</span>' : '';
    if (s.score != null) return '<span class="lc-sub-badge lc-sub-graded">✔ 已批 ' + s.score + ' 分</span>';
    return '<span class="lc-sub-badge lc-sub-sent">📤 已提交</span>';
  }

  function renderAssignItem(a) {
    var canDelete = isAdmin || a.uploader_id === me.id;
    var stat = '';
    if (isStaff && a.submit_stat) {
      stat = '<span class="lc-scope-tag">📥 提交 ' + a.submit_stat.submitted + ' 人 · 已批 ' + a.submit_stat.graded + '</span>';
    }
    return (
      '<div class="lc-card" data-assign-id="' + a.id + '">'
      + '<div class="lc-card-head">'
      + '<span class="lc-card-title">' + esc(a.title) + '</span>'
      + windowBadge(a)
      + '</div>'
      + '<div class="lc-card-meta">'
      + '<span>布置人：' + esc(a.uploader_name || '-') + '</span>'
      + '<span>' + fmtTime(a.created_at) + '</span>'
      + '<span class="lc-scope-tag">面向：' + esc((a.level_scope || []).map(scopeName).join(' ')) + '</span>'
      + stat
      + mySubBadge(a)
      + '</div>'
      + '<div class="lc-card-actions">'
      + '<button class="btn btn-primary btn-sm" data-act="view">查看详情</button>'
      + (canDelete ? '<button class="lc-link-danger" data-act="del">删除</button>' : '')
      + '</div>'
      + '</div>'
    );
  }

  function bindAssignEvents() {
    document.querySelectorAll('#assignList .lc-card').forEach(function (card) {
      var id = Number(card.getAttribute('data-assign-id'));
      card.querySelector('[data-act="view"]').addEventListener('click', function () { openAssignmentByRef(id); });
      var del = card.querySelector('[data-act="del"]');
      if (del) del.addEventListener('click', function () {
        if (!confirm('确认删除该作业？')) return;
        api('/assignments/' + id, { method: 'DELETE' })
          .then(function () { toast('作业已删除', 'success'); renderAssignments(); })
          .catch(function (e) { toast(e.message, 'error'); });
      });
    });
  }

  async function openAssignmentByRef(id, fromManage) {
    try {
      var a = await api('/assignments/' + id);
      var wrap = document.createElement('div');
      var frame = iframeOf('<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1.0"><style>body{font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;line-height:1.8;padding:20px;color:#1a1a2e;}img{max-width:100%;}</style></head><body>' + a.content + '</body></html>', undefined);
      wrap.appendChild(frame);
      var extra = document.createElement('div');
      extra.className = 'lc-assign-extra';
      extra.innerHTML = buildAssignExtraHtml(a);
      wrap.appendChild(extra);
      bindAssignExtraEvents(extra, a);

      var winMeta = '';
      if (a.start_at) winMeta += '<span>⏳ 开始 ' + fmtTime(a.start_at) + '</span>';
      if (a.due_at) winMeta += '<span>⛔ 截止 ' + fmtTime(a.due_at) + '</span>';
      if (!a.start_at && !a.due_at) winMeta = '<span>🕒 不限时提交</span>';
      openModal({
        cat: 'assignment', catLabel: '作业详情', title: a.title,
        metaHtml: '<span>布置人：' + esc(a.uploader_name || '-') + '</span>'
          + '<span>' + fmtTime(a.created_at) + '</span>'
          + '<span class="lc-scope-tag">面向：' + esc((a.level_scope || []).map(scopeName).join(' ')) + '</span>'
          + winMeta,
        bodyNode: wrap,
        buttons: (a.canGrade && !fromManage)
          ? [{ label: '📋 查看提交与批改', onClick: function () { openGradePanel(a.id, a.title); } }]
          : []
      });
    } catch (e) {
      toast(e.message, 'error');
    }
  }

  // 作业详情附加区（学员提交 / 教师提示）
  function buildAssignExtraHtml(a) {
    if (isStaff) {
      var hint = a.canGrade
        ? '你是该作业的布置者，可点击右上角「查看提交与批改」进行评分与评语。'
        : '该作业由 ' + esc(a.uploader_name || '其他教师') + ' 布置，仅布置者与管理员可批改。';
      return '<div class="lc-submit-box"><p class="lc-submit-hint">👩‍🏫 ' + hint + '</p></div>';
    }
    var s = a.my_submission;
    var win = a.window;
    var html = '<div class="lc-submit-box">';
    html += '<h4>📤 我的作业提交</h4>';
    if (s) {
      html += '<div class="lc-sub-status">'
        + '<p><b>已提交：</b>' + esc(s.original_name || s.filename) + '（' + fmtSize(s.file_size) + ' · ' + fmtTime(s.submitted_at) + '）'
        + ' <a class="lc-link-action" href="javascript:void(0)" data-open-sub="' + s.id + '">查看/下载</a></p>';
      if (s.score != null) {
        html += '<div class="lc-grade-result"><span class="lc-grade-score">' + s.score + ' 分</span>'
          + '<span class="lc-grade-meta">批改人：' + esc(s.graded_by || '-') + ' · ' + fmtTime(s.graded_at) + '</span></div>';
        if (s.comment) html += '<p class="lc-grade-comment">💬 ' + esc(s.comment) + '</p>';
      } else {
        html += '<p class="lc-submit-hint">⏳ 老师尚未批改</p>';
      }
      html += '</div>';
    }
    if (win === 'pending') {
      html += '<p class="lc-submit-hint">⏳ 提交将于 ' + fmtTime(a.start_at) + ' 开放，届时可在此上传作业文件。</p>';
    } else if (win === 'closed') {
      html += s
        ? '<p class="lc-submit-hint">⛔ 作业已截止，不能重新提交，可查看上方提交与批改结果。</p>'
        : '<p class="lc-submit-hint">⛔ 作业已截止，未能提交。如有特殊情况请联系老师。</p>';
    } else {
      html += '<div class="lc-submit-form">'
        + '<input type="file" id="subFile" accept=".doc,.docx,.xls,.xlsx,.pdf,.jpg,.jpeg,.png,.gif,.webp">'
        + '<p class="lc-editor-note">支持 Word / Excel / PDF / 图片，≤20MB' + (s ? '；重新提交将覆盖此前版本并清除已有批改' : '') + '。</p>'
        + '<button type="button" class="btn btn-primary btn-sm" id="subBtn">' + (s ? '🔄 重新提交' : '📤 提交作业') + '</button>'
        + '</div>';
    }
    html += '</div>';
    return html;
  }

  // 带 token 查看提交文件（浏览器直接导航无法携带 JWT 头，需 fetch blob 中转）
  async function openSubmissionFile(id) {
    try {
      var res = await fetch('/api/learning/submissions/' + id + '/file', {
        headers: { 'Authorization': 'Bearer ' + token }
      });
      if (!res.ok) {
        var msg = '打开失败（' + res.status + '）';
        try { var j = await res.json(); msg = j.message || msg; } catch (e) {}
        throw new Error(msg);
      }
      var cd = res.headers.get('Content-Disposition') || '';
      var m = cd.match(/filename\*=UTF-8''([^;]+)/);
      var name = '';
      try { name = m ? decodeURIComponent(m[1]) : ''; } catch (e) {}
      var blob = await res.blob();
      var url = URL.createObjectURL(blob);
      if (/^image\//.test(blob.type) || blob.type === 'application/pdf') {
        var w = window.open(url, '_blank');
        if (!w) triggerDownload(url, name);
      } else {
        triggerDownload(url, name);
      }
      setTimeout(function () { URL.revokeObjectURL(url); }, 60000);
    } catch (e) {
      toast(e.message || '打开失败', 'error');
    }
  }
  function triggerDownload(url, name) {
    var a = document.createElement('a');
    a.href = url;
    if (name) a.download = name;
    document.body.appendChild(a);
    a.click();
    a.remove();
  }

  function bindAssignExtraEvents(extra, a) {
    extra.querySelectorAll('[data-open-sub]').forEach(function (el) {
      el.addEventListener('click', function () { openSubmissionFile(el.getAttribute('data-open-sub')); });
    });
    var btn = extra.querySelector('#subBtn');
    if (!btn) return;
    btn.addEventListener('click', async function () {
      var fileInput = extra.querySelector('#subFile');
      var f = fileInput && fileInput.files[0];
      if (!f) return toast('请选择要提交的文件', 'error');
      if (f.size > 20 * 1024 * 1024) return toast('文件不能超过 20MB', 'error');
      var ok = /\.(docx?|xlsx?|pdf|jpe?g|png|gif|webp)$/i.test(f.name);
      if (!ok) return toast('仅支持 Word/Excel/PDF/图片', 'error');
      if (a.my_submission && !confirm('重新提交将覆盖上一版本并清除已有批改，确定继续？')) return;
      btn.disabled = true; btn.textContent = '上传中…';
      try {
        var fd = new FormData();
        fd.append('file', f);
        await api('/assignments/' + a.id + '/submit', { method: 'POST', body: fd });
        toast('作业提交成功', 'success');
        assignCacheMeta = [];
        renderAssignments();
        closeModal();
      } catch (e) {
        toast(e.message, 'error');
        btn.disabled = false; btn.textContent = a.my_submission ? '🔄 重新提交' : '📤 提交作业';
      }
    });
  }

  // ---------- 批改面板（发布者/管理员） ----------
  async function openGradePanel(assignId, title) {
    try {
      var d = await api('/assignments/' + assignId + '/submissions');
      var list = d.list || [];
      var bodyEl = document.getElementById('modalBody');
      var footEl = document.getElementById('modalFoot');
      footEl.innerHTML = '';
      document.getElementById('modalCat').textContent = '作业批改';
      document.getElementById('modalTitle').textContent = title;
      document.getElementById('modalMeta').innerHTML = '<span>📥 共 ' + list.length + ' 份提交</span>';
      var box = document.createElement('div');
      box.className = 'lc-grade-panel';
      if (list.length === 0) {
        box.innerHTML = '<div class="lc-empty"><p>还没有学员提交作业</p></div>';
      } else {
        box.innerHTML = list.map(function (s) {
          var graded = s.score != null;
          return '<div class="lc-grade-row" data-sid="' + s.id + '">'
            + '<div class="lc-grade-info">'
            + '<b>' + esc(s.student_nickname || s.student_username) + '</b>'
            + '<span class="lc-grade-meta">@' + esc(s.student_username) + ' · ' + esc(s.original_name || s.filename) + ' · ' + fmtSize(s.file_size) + ' · ' + fmtTime(s.submitted_at) + '</span>'
            + (graded ? '<span class="lc-sub-badge lc-sub-graded">已批 ' + s.score + ' 分 · ' + esc(s.graded_by || '') + '</span>' : '<span class="lc-sub-badge lc-sub-pending">待批改</span>')
            + (graded && s.comment ? '<p class="lc-grade-comment">💬 ' + esc(s.comment) + '</p>' : '')
            + '</div>'
            + '<div class="lc-grade-ops">'
            + '<button class="btn btn-outline btn-sm" data-open-sub="' + s.id + '">查看</button>'
            + '<button class="btn btn-primary btn-sm" data-act="grade">' + (graded ? '重新批改' : '批改') + '</button>'
            + '</div>'
            + '<div class="lc-grade-form" style="display:none;">'
            + '<input type="number" min="0" max="100" placeholder="分数(0-100)" class="lc-grade-score-input">'
            + '<input type="text" placeholder="评语（选填）" class="lc-grade-comment-input" maxlength="2000">'
            + '<button class="btn btn-primary btn-sm" data-act="save">保存并通知学员</button>'
            + '</div>'
            + '</div>';
        }).join('');
      }
      bodyEl.innerHTML = '';
      bodyEl.appendChild(box);
      bindGradeEvents(box, assignId, title);
    } catch (e) {
      toast(e.message, 'error');
    }
  }

  function bindGradeEvents(box, assignId, title) {
    box.querySelectorAll('.lc-grade-row').forEach(function (row) {
      var sid = row.getAttribute('data-sid');
      var form = row.querySelector('.lc-grade-form');
      row.querySelector('[data-open-sub]').addEventListener('click', function () {
        openSubmissionFile(sid);
      });
      row.querySelector('[data-act="grade"]').addEventListener('click', function () {
        form.style.display = form.style.display === 'none' ? '' : 'none';
        if (form.style.display !== 'none') {
          row.querySelector('.lc-grade-score-input').focus();
        }
      });
      row.querySelector('[data-act="save"]').addEventListener('click', async function () {
        var scoreRaw = row.querySelector('.lc-grade-score-input').value.trim();
        var comment = row.querySelector('.lc-grade-comment-input').value.trim();
        if (scoreRaw !== '' && (!/^\d+$/.test(scoreRaw) || Number(scoreRaw) > 100)) {
          return toast('分数需为 0-100 的整数或留空', 'error');
        }
        var saveBtn = row.querySelector('[data-act="save"]');
        saveBtn.disabled = true; saveBtn.textContent = '保存中…';
        try {
          await api('/submissions/' + sid + '/grade', {
            method: 'POST',
            body: JSON.stringify({ score: scoreRaw === '' ? null : Number(scoreRaw), comment: comment })
          });
          toast('批改已保存并通知学员', 'success');
          // 重新渲染批改面板
          openGradePanel(assignId, title);
        } catch (e) {
          toast(e.message, 'error');
          saveBtn.disabled = false; saveBtn.textContent = '保存并通知学员';
        }
      });
    });
  }

  // ================= 等级选择组件 =================
  function makeChip(label, val, onClick, cls) {
    var chip = document.createElement('div');
    chip.className = 'lc-check-chip' + (cls ? ' ' + cls : '');
    chip.setAttribute('data-level', val);
    chip.textContent = label;
    chip.addEventListener('click', function () {
      if (onClick) onClick(chip);
      else chip.classList.toggle('on');
    });
    return chip;
  }

  function buildLevelGroup(container, opts) {
    container.innerHTML = '';
    if (opts.allowAll) {
      var allChip = makeChip('🌐 全等级', 'all', function (chip) {
        chip.classList.toggle('on');
        if (chip.classList.contains('on')) {
          container.querySelectorAll('.lc-check-chip:not(.lc-check-all)').forEach(function (c) { c.classList.remove('on'); });
        }
      }, 'lc-check-all');
      container.appendChild(allChip);
    }
    var roles = opts.roles || ALL_ROLES;
    roles.forEach(function (r) {
      container.appendChild(makeChip(ROLE_LABELS[r], r, null));
    });
    container.getSelected = function () {
      var vals = [];
      container.querySelectorAll('.lc-check-chip.on').forEach(function (c) { vals.push(c.getAttribute('data-level')); });
      return vals;
    };
    return container;
  }

  // ================= 管理后台 =================
  var manageTab = 'handout';
  function switchManageTab(tab) {
    manageTab = tab;
    document.querySelectorAll('#manageTabs .lc-sub-tab').forEach(function (t) {
      t.classList.toggle('active', t.getAttribute('data-tab') === tab && t.style.display !== 'none');
    });
    ['handout', 'assignment', 'message', 'users'].forEach(function (k) {
      var p = document.getElementById('panel-' + k);
      if (p) p.style.display = (k === tab) ? '' : 'none';
    });
  }
  document.querySelectorAll('#manageTabs .lc-sub-tab').forEach(function (tab) {
    tab.addEventListener('click', function () { switchManageTab(tab.getAttribute('data-tab')); });
  });

  // 等级组
  var hoLevels = buildLevelGroup(document.getElementById('hoLevels'), { allowAll: true, roles: ALL_ROLES });
  hoLevels.querySelector('.lc-check-all').classList.add('on');   // 默认全等级
  var asLevels = buildLevelGroup(document.getElementById('asLevels'), { roles: STUDENT_ROLES });
  var mLevels = buildLevelGroup(document.getElementById('mLevels'), { roles: ALL_ROLES });

  // 角色下拉（新建账号）
  (function fillRoleSelect() {
    var sel = document.getElementById('cuRole');
    sel.innerHTML = '';
    ALL_ROLES.forEach(function (r) {
      var o = document.createElement('option');
      o.value = r;
      o.textContent = ROLE_LABELS[r];
      if (r === 'bachelor') o.selected = true;
      sel.appendChild(o);
    });
  })();

  // ---------- 富文本编辑器 ----------
  (function initEditor() {
    var area = document.getElementById('edArea');
    var bar = document.getElementById('edToolbar');
    var cmds = [
      { label: '𝐁', title: '加粗', cmd: 'bold' },
      { label: '𝘐', title: '斜体', cmd: 'italic' },
      { label: 'U̲', title: '下划线', cmd: 'underline' },
      { label: 'H₂', title: '大标题', cmd: 'formatBlock', arg: 'h2' },
      { label: 'H₃', title: '小标题', cmd: 'formatBlock', arg: 'h3' },
      { label: '¶', title: '正文段落', cmd: 'formatBlock', arg: 'p' },
      { label: '•', title: '无序列表', cmd: 'insertUnorderedList' },
      { label: '1.', title: '有序列表', cmd: 'insertOrderedList' },
      { label: '❝', title: '引用', cmd: 'formatBlock', arg: 'blockquote' },
      { label: '―', title: '分隔线', cmd: 'insertHorizontalRule' },
      { label: '🔗', title: '插入链接', custom: 'link' },
      { label: '🖼️', title: '插入图片(URL)', custom: 'img' },
      { label: '⌫', title: '清除格式', cmd: 'removeFormat' }
    ];
    cmds.forEach(function (c) {
      var b = document.createElement('button');
      b.type = 'button';
      b.className = 'lc-ed-btn';
      b.textContent = c.label;
      b.title = c.title;
      b.addEventListener('mousedown', function (e) { e.preventDefault(); });
      b.addEventListener('click', function () {
        area.focus();
        if (c.custom === 'link') {
          var url = prompt('输入链接地址：', 'https://');
          if (url) document.execCommand('createLink', false, url);
        } else if (c.custom === 'img') {
          var iu = prompt('输入图片 URL：', 'https://');
          if (iu) document.execCommand('insertImage', false, iu);
        } else {
          document.execCommand(c.cmd, false, c.arg || null);
        }
      });
      bar.appendChild(b);
    });
  })();

  // 分类下拉（讲义分发）
  (function fillCategorySelect() {
    var sel = document.getElementById('hoCategory');
    sel.innerHTML = '';
    CATEGORIES.forEach(function (c) {
      var o = document.createElement('option');
      o.value = c;
      o.textContent = c;
      sel.appendChild(o);
    });
  })();

  // ---------- 发布：讲义 ----------
  document.getElementById('handoutForm').addEventListener('submit', async function (e) {
    e.preventDefault();
    var fileInput = document.getElementById('hoFile');
    var title = document.getElementById('hoTitle').value.trim();
    var category = document.getElementById('hoCategory').value;
    if (!fileInput.files[0]) return toast('请选择 HTML 文件', 'error');
    if (!title) return toast('请填写标题', 'error');
    var levels = hoLevels.getSelected();
    if (levels.length === 0) return toast('请选择分发等级（可全选）', 'error');
    if (levels.indexOf('all') >= 0) levels = ['all'];

    var fd = new FormData();
    fd.append('title', title);
    fd.append('category', category);
    fd.append('levels', JSON.stringify(levels));
    fd.append('file', fileInput.files[0]);

    var btn = document.getElementById('hoSubmitBtn');
    btn.disabled = true; btn.textContent = '上传中…';
    try {
      var d = await api('/handouts', { method: 'POST', body: fd });
      toast(d.notified != null ? '已发布，已通知 ' + d.notified + ' 位成员' : '已发布', 'success');
      this.reset();
      document.getElementById('hoCategory').value = category;
      handoutCache = [];
      renderHandouts();
      renderMyHandoutRecords();
    } catch (err) {
      toast(err.message, 'error');
    } finally {
      btn.disabled = false; btn.textContent = '发布并分发';
    }
  });

  // ---------- 发布：作业 ----------
  document.getElementById('assignForm').addEventListener('submit', async function (e) {
    e.preventDefault();
    var title = document.getElementById('asTitle').value.trim();
    var content = document.getElementById('edArea').innerHTML.trim();
    var plainText = document.getElementById('edArea').innerText.trim();
    var startRaw = document.getElementById('asStartAt').value;
    var dueRaw = document.getElementById('asDueAt').value;
    if (!title) return toast('请填写标题', 'error');
    if (!plainText && content.indexOf('<img') < 0) return toast('请填写作业内容', 'error');
    var levels = asLevels.getSelected();
    if (levels.length === 0) return toast('请至少选择一个学员等级', 'error');
    var startAt = startRaw ? new Date(startRaw).getTime() : null;
    var dueAt = dueRaw ? new Date(dueRaw).getTime() : null;
    if (startRaw && !startAt) return toast('开始时间无效', 'error');
    if (dueRaw && !dueAt) return toast('截止时间无效', 'error');
    if (startAt && dueAt && startAt >= dueAt) return toast('开始时间必须早于截止时间', 'error');

    var btn = document.getElementById('asSubmitBtn');
    btn.disabled = true; btn.textContent = '发布中…';
    try {
      var d = await api('/assignments', {
        method: 'POST',
        body: JSON.stringify({ title: title, content: content, levels: levels, startAt: startAt, dueAt: dueAt })
      });
      toast(d.notified != null ? '作业已布置，已通知 ' + d.notified + ' 位学员' : '已发布', 'success');
      this.reset();
      document.getElementById('edArea').innerHTML = '';
      assignCacheMeta = [];
      renderAssignments();
    } catch (err) {
      toast(err.message, 'error');
    } finally {
      btn.disabled = false; btn.textContent = '发布作业';
    }
  });

  // ---------- 我的分发记录（讲义） ----------
  async function renderMyHandoutRecords() {
    var tbody = document.getElementById('myHandoutTbody');
    if (!tbody) return;
    try {
      var d = await api('/handouts');
      var mine = (d.list || []).filter(function (h) { return h.uploader_id === me.id; });
      var countEl = document.getElementById('myHandoutCount');
      if (countEl) countEl.textContent = '共 ' + mine.length + ' 条';
      if (mine.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" style="color:var(--text-muted)">暂无分发记录</td></tr>';
        return;
      }
      tbody.innerHTML = '';
      mine.forEach(function (h) {
        var tr = document.createElement('tr');
        tr.innerHTML =
          '<td><b>' + esc(h.title) + '</b></td>'
          + '<td>' + esc(h.category || '未分类') + '</td>'
          + '<td>' + esc((h.level_scope || []).map(scopeName).join(' ')) + '</td>'
          + '<td>' + fmtTime(h.created_at) + '</td>'
          + '<td><div class="lc-row-actions">'
          + '<a class="lc-link-action" href="/uploads/handouts/' + encodeURIComponent(h.filename) + '" target="_blank" rel="noopener">预览</a>'
          + '<button class="lc-link-danger" data-act="del">删除</button>'
          + '</div></td>';
        tr.querySelector('[data-act="del"]').addEventListener('click', function () {
          if (!confirm('确认删除讲义「' + h.title + '」？')) return;
          api('/handouts/' + h.id, { method: 'DELETE' })
            .then(function () { toast('已删除', 'success'); renderMyHandoutRecords(); renderHandouts(); })
            .catch(function (e) { toast(e.message, 'error'); });
        });
        tbody.appendChild(tr);
      });
    } catch (e) {
      tbody.innerHTML = '<tr><td colspan="5" style="color:var(--error)">加载失败：' + esc(e.message) + '</td></tr>';
    }
  }

  // ---------- 我的作业与批改记录 ----------
  async function renderMyAssignRecords() {
    var tbody = document.getElementById('myAssignTbody');
    if (!tbody) return;
    try {
      var d = await api('/assignments');
      var mine = (d.list || []).filter(function (a) { return a.uploader_id === me.id; });
      var countEl = document.getElementById('myAssignCount');
      if (countEl) countEl.textContent = '共 ' + mine.length + ' 条';
      if (mine.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="color:var(--text-muted)">暂无作业记录</td></tr>';
        return;
      }
      tbody.innerHTML = '';
      mine.forEach(function (a) {
        var tr = document.createElement('tr');
        var stat = a.submit_stat ? (a.submit_stat.submitted + ' / ' + a.submit_stat.graded) : '0 / 0';
        tr.innerHTML =
          '<td><b>' + esc(a.title) + '</b></td>'
          + '<td>' + esc((a.level_scope || []).map(scopeName).join(' ')) + '</td>'
          + '<td>' + (a.due_at ? fmtTime(a.due_at) : '不限时') + '</td>'
          + '<td>📥 ' + stat + '</td>'
          + '<td>' + fmtTime(a.created_at) + '</td>'
          + '<td><div class="lc-row-actions">'
          + '<button class="lc-link-action" data-act="grade">批改 / 提交列表</button>'
          + '<button class="lc-link-danger" data-act="del">删除</button>'
          + '</div></td>';
        tr.querySelector('[data-act="grade"]').addEventListener('click', function () {
          openModal({ cat: 'assignment', catLabel: '作业批改', title: a.title, metaHtml: '', bodyNode: document.createElement('div'), buttons: [] });
          openGradePanel(a.id, a.title);
        });
        tr.querySelector('[data-act="del"]').addEventListener('click', function () {
          if (!confirm('确认删除作业「' + a.title + '」？学员提交将一并删除。')) return;
          api('/assignments/' + a.id, { method: 'DELETE' })
            .then(function () { toast('已删除', 'success'); renderMyAssignRecords(); renderAssignments(); })
            .catch(function (e) { toast(e.message, 'error'); });
        });
        tbody.appendChild(tr);
      });
    } catch (e) {
      tbody.innerHTML = '<tr><td colspan="6" style="color:var(--error)">加载失败：' + esc(e.message) + '</td></tr>';
    }
  }

  // ---------- 发送：消息（管理员） ----------
  document.getElementById('msgForm').addEventListener('submit', async function (e) {
    e.preventDefault();
    var title = document.getElementById('mTitle').value.trim();
    var content = document.getElementById('mContent').value.trim();
    if (!title) return toast('请填写标题', 'error');
    var levels = mLevels.getSelected();
    if (levels.length === 0) return toast('请至少选择一个接收等级', 'error');
    var btn = document.getElementById('mSubmitBtn');
    btn.disabled = true; btn.textContent = '发送中…';
    try {
      var d = await api('/messages', { method: 'POST', body: JSON.stringify({ title: title, content: content, levels: levels }) });
      toast('已发送，触达 ' + (d.notified || 0) + ' 位成员', 'success');
      this.reset();
      renderInbox();
    } catch (err) {
      toast(err.message, 'error');
    } finally {
      btn.disabled = false; btn.textContent = '发送消息';
    }
  });

  // ---------- 用户管理（管理员） ----------
  async function renderUsers() {
    var tbody = document.getElementById('userTbody');
    try {
      var d = await api('/users');
      var users = d.list || [];
      document.getElementById('userCount').textContent = '共 ' + users.length + ' 人';
      if (users.length === 0) { tbody.innerHTML = '<tr><td colspan="6" style="color:var(--text-muted)">暂无账号</td></tr>'; return; }
      tbody.innerHTML = '';
      users.forEach(function (u) {
        var tr = document.createElement('tr');
        tr.innerHTML =
          '<td><b>' + esc(u.username) + '</b></td>'
          + '<td>' + esc(u.nickname || '-') + '</td>'
          + '<td><select class="role-select"' + (u.username === 'somnusweiwei1989' || u.id === me.id ? ' disabled' : '') + '>'
          + ALL_ROLES.map(function (r) {
            return '<option value="' + r + '"' + (r === u.role ? ' selected' : '') + '>' + ROLE_LABELS[r] + '</option>';
          }).join('')
          + '</select></td>'
          + '<td>' + fmtTime(u.created_at) + '</td>'
          + '<td>' + fmtTime(u.last_login) + '</td>'
          + '<td><div class="lc-row-actions">'
          + '<button class="lc-link-action" data-uact="resetpwd">重置密码</button>'
          + ((u.id === me.id || u.role === 'admin') ? '' : '<button class="lc-link-danger" data-uact="del">删除</button>')
          + '</div></td>';
        var select = tr.querySelector('.role-select');
        select.addEventListener('change', async function () {
          try {
            await api('/users/' + u.id + '/role', { method: 'PUT', body: JSON.stringify({ role: select.value }) });
            toast('等级已更新为「' + ROLE_LABELS[select.value] + '」', 'success');
          } catch (e) {
            toast(e.message, 'error');
            select.value = u.role;
          }
        });
        tr.querySelector('[data-uact="resetpwd"]').addEventListener('click', async function () {
          var pwd = prompt('为账号「' + u.username + '」设置新密码（≥6位）：');
          if (pwd === null) return;
          if (pwd.length < 6) return toast('密码长度需 ≥6', 'error');
          try {
            await api('/users/' + u.id + '/password', { method: 'PUT', body: JSON.stringify({ password: pwd }) });
            toast('密码已重置', 'success');
          } catch (e) { toast(e.message, 'error'); }
        });
        var del = tr.querySelector('[data-uact="del"]');
        if (del) del.addEventListener('click', async function () {
          if (!confirm('确认删除账号「' + u.username + '」？其收件箱数据将一并清除。')) return;
          try {
            await api('/users/' + u.id, { method: 'DELETE' });
            toast('账号已删除', 'success');
            renderUsers();
          } catch (e) { toast(e.message, 'error'); }
        });
        tbody.appendChild(tr);
      });
    } catch (e) {
      tbody.innerHTML = '<tr><td colspan="6" style="color:var(--error)">加载失败：' + esc(e.message) + '</td></tr>';
    }
  }

  function copyText(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(function () { toast('已复制', 'success'); }).catch(function () {});
    } else {
      var ta = document.createElement('textarea');
      ta.value = text;
      document.body.appendChild(ta);
      ta.select();
      try { document.execCommand('copy'); toast('已复制', 'success'); } catch (e) {}
      document.body.removeChild(ta);
    }
  }

  document.getElementById('createUserForm').addEventListener('submit', async function (e) {
    e.preventDefault();
    var username = document.getElementById('cuName').value.trim();
    var nickname = document.getElementById('cuNick').value.trim();
    var password = document.getElementById('cuPass').value;
    var role = document.getElementById('cuRole').value;
    if (username.length < 3) return toast('用户名至少 3 个字符', 'error');
    if (password.length < 6) return toast('密码长度需 ≥6', 'error');
    var btn = document.getElementById('cuBtn');
    btn.disabled = true; btn.textContent = '创建中…';
    try {
      var d = await api('/users', { method: 'POST', body: JSON.stringify({ username: username, nickname: nickname, password: password, role: role }) });
      var panel = document.getElementById('cuResult');
      panel.style.display = '';
      panel.innerHTML =
        '<div class="lc-result-title">✅ 账号创建成功，请将以下信息分发给本人</div>'
        + '<div class="lc-cred-row"><span class="lc-cred-key">账号</span><span class="lc-cred-val">' + esc(d.username) + '</span><button class="lc-link-action" data-copy="' + esc(d.username) + '">复制</button></div>'
        + '<div class="lc-cred-row"><span class="lc-cred-key">初始密码</span><span class="lc-cred-val">' + esc(password) + '</span><button class="lc-link-action" data-copy="' + esc(password) + '">复制</button></div>'
        + '<div class="lc-cred-row"><span class="lc-cred-key">等级</span><span class="lc-cred-val">' + esc(d.roleLabel || ROLE_LABELS[d.role]) + '</span></div>'
        + '<div style="font-size:12px;color:var(--text-muted);margin-top:6px;">登录地址：dailyread.sonnusww.top/center/</div>';
      panel.querySelectorAll('[data-copy]').forEach(function (cbtn) {
        cbtn.addEventListener('click', function () { copyText(cbtn.getAttribute('data-copy')); });
      });
      document.getElementById('cuName').value = '';
      document.getElementById('cuNick').value = '';
      document.getElementById('cuPass').value = '';
      renderUsers();
    } catch (err) {
      toast(err.message, 'error');
    } finally {
      btn.disabled = false; btn.textContent = '创建账号';
    }
  });

  // ================= PWA / SW =================
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', function () {
      navigator.serviceWorker.register('/sw.js').catch(function () {});
    });
  }

  // ================= 启动 =================
  paintHeader();
  buildNav();
  go('messages');
  refreshUnread();
  setInterval(refreshUnread, 45000);
  window.addEventListener('focus', refreshUnread);

  if (isAdmin) renderUsers();
  if (isStaff) {
    renderMyHandoutRecords();
    renderMyAssignRecords();
  }
})();
