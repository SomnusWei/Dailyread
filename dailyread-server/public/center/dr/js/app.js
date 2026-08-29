// DailyRead PWA - 核心应用逻辑
// 通过学习中心 lc token + 绑定关系，经 /api/dr/* 代理路由读写绑定的 DailyRead 数据
// 不签发 DailyRead token，与鸿蒙/Win 端完全隔离
(function () {
  'use strict';

  // ---------- 常量 ----------
  var TOKEN_KEY = 'lc_token';
  var USER_KEY = 'lc_user';
  var FONT_KEY = 'dr_reader_font_size';

  var NAV_ITEMS = [
    { key: 'home', icon: '🏠', label: '首页' },
    { key: 'articles', icon: '📚', label: '文章管理' },
    { key: 'random', icon: '🎲', label: '随心阅读' },
    { key: 'ear', icon: '🎧', label: '磨耳跟背' },
    { key: 'settings', icon: '⚙️', label: '设置' }
  ];

  // ---------- 全局状态 ----------
  var state = {
    lcUser: null,        // 学习中心用户
    drUser: null,        // 绑定的 DailyRead 用户
    config: null,        // DailyRead 用户配置
    todayTask: null,     // 今日任务
    articles: [],        // 文章列表（轻量）
    serverOk: false,     // 服务器状态
    fontSize: parseInt(localStorage.getItem(FONT_KEY) || '20', 10),
    currentView: 'home',
    audioEl: null,        // 当前 audio 元素
    loopAudio: false
  };

  // ---------- API 封装（lc token + /api/dr/* 代理路由） ----------
  function getToken() { return localStorage.getItem(TOKEN_KEY) || ''; }

  function drApi(method, path, body, isForm) {
    var opts = { method: method, headers: {} };
    var token = getToken();
    if (token) opts.headers['Authorization'] = 'Bearer ' + token;
    if (isForm) {
      opts.body = body; // FormData
    } else {
      opts.headers['Content-Type'] = 'application/json';
      if (body) opts.body = JSON.stringify(body);
    }
    return fetch('/api/dr' + path, opts).then(function (r) {
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

  // 学习中心 API（非代理，走 /api/learning/*）
  function lcApi(method, path, body) {
    var opts = { method: method, headers: { 'Content-Type': 'application/json' } };
    var token = getToken();
    if (token) opts.headers['Authorization'] = 'Bearer ' + token;
    if (body) opts.body = JSON.stringify(body);
    return fetch('/api/learning' + path, opts).then(function (r) {
      return r.json().then(function (d) {
        if (!r.ok || d.code !== 0) throw new Error((d && d.message) || '请求失败');
        return d.data;
      });
    });
  }

  // ---------- 工具 ----------
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
  function fmtDate(d) {
    if (!d) return '';
    var dt = new Date(d);
    if (isNaN(dt)) return d;
    return dt.getFullYear() + '-' + String(dt.getMonth() + 1).padStart(2, '0') + '-' + String(dt.getDate()).padStart(2, '0');
  }
  function fmtTime(s) {
    if (!s) return '--:--';
    var sec = Math.floor(Number(s) || 0);
    var m = Math.floor(sec / 60), ss = sec % 60;
    return String(m).padStart(2, '0') + ':' + String(ss).padStart(2, '0');
  }

  // ---------- 导航 ----------
  function buildNav() {
    var side = document.getElementById('sideNav');
    var bottom = document.getElementById('bottomNav');
    side.innerHTML = ''; bottom.innerHTML = '';
    NAV_ITEMS.forEach(function (item) {
      // 侧边
      var sb = document.createElement('button');
      sb.className = 'lc-nav-item' + (state.currentView === item.key ? ' active' : '');
      sb.innerHTML = '<span>' + item.icon + '</span><span>' + item.label + '</span>';
      sb.addEventListener('click', function () { go(item.key); });
      side.appendChild(sb);
      // 底部
      var bb = document.createElement('button');
      bb.className = 'lc-bn-item' + (state.currentView === item.key ? ' active' : '');
      bb.innerHTML = '<span class="bn-icon">' + item.icon + '</span><span>' + item.label + '</span>';
      bb.addEventListener('click', function () { go(item.key); });
      bottom.appendChild(bb);
    });
  }

  function go(view) {
    state.currentView = view;
    document.querySelectorAll('.lc-view').forEach(function (v) { v.classList.remove('active'); });
    var target = document.getElementById('view-' + view);
    if (target) target.classList.add('active');
    buildNav();
    if (view === 'home') renderHome();
    else if (view === 'articles') renderArticles();
    else if (view === 'random') renderRandom();
    else if (view === 'ear') renderEar();
    else if (view === 'settings') renderSettings();
  }

  // ---------- 初始化 ----------
  function init() {
    if (!getToken()) {
      location.href = '/center/index.html';
      return;
    }
    // 加载学习中心用户信息 + 绑定状态
    Promise.all([
      lcApi('GET', '/me'),
      lcApi('GET', '/dr/status')
    ]).then(function (results) {
      state.lcUser = results[0];
      var bindStatus = results[1];
      if (!bindStatus || !bindStatus.bound) {
        // 未绑定，跳转绑定页
        location.href = '/center/dr/bind.html';
        return;
      }
      state.drUser = bindStatus.drUser;
      // 渲染顶栏用户信息
      var name = (state.lcUser.nickname || state.lcUser.username);
      document.getElementById('userName').textContent = name;
      document.getElementById('userAvatar').textContent = name.charAt(0).toUpperCase();
      // 加载 DailyRead 配置 + 服务器状态，进入首页
      Promise.all([
        drApi('GET', '/config').catch(function () { return null; }),
        fetch('/health').then(function (r) { return r.ok; }).catch(function () { return false; })
      ]).then(function (r) {
        state.config = r[0] || { dailyMinutes: 20, targetCheckRate: 30, readerFontSize: 26 };
        state.serverOk = r[1];
        go('home');
      });
    }).catch(function (e) {
      if (e.status === 401) {
        location.href = '/center/index.html';
      } else {
        alert('初始化失败：' + e.message);
      }
    });
  }

  // ---------- 视图渲染（阶段 4-6 填充） ----------
  function renderHome() {
    var el = document.getElementById('view-home');
    el.innerHTML = '<div class="dr-home-head"><span class="dr-server-light ' + (state.serverOk ? 'ok' : 'err') + '"><span class="dr-server-dot"></span>' + (state.serverOk ? '服务器正常' : '服务器异常') + '</span><h2 class="dr-home-title">今日阅读</h2><p class="dr-home-sub">' + fmtDate(new Date()) + '</p></div><div class="dr-loading"><div class="dr-spinner"></div><p>加载中…</p></div>';
    // 加载今日任务
    drApi('GET', '/daily-tasks/today').then(function (task) {
      state.todayTask = task;
      renderHomeTaskList(el, task);
    }).catch(function (e) {
      el.innerHTML = '<div class="dr-empty"><div class="dr-empty-icon">⚠️</div><div class="dr-empty-text">加载失败：' + esc(e.message) + '</div></div>';
    });
  }

  function renderHomeTaskList(el, task) {
    if (!task || !task.items || task.items.length === 0) {
      el.innerHTML = '<div class="dr-home-head"><span class="dr-server-light ' + (state.serverOk ? 'ok' : 'err') + '"><span class="dr-server-dot"></span>' + (state.serverOk ? '服务器正常' : '服务器异常') + '</span><h2 class="dr-home-title">今日阅读</h2><p class="dr-home-sub">' + fmtDate(new Date()) + '</p></div><div class="dr-empty"><div class="dr-empty-icon">📭</div><div class="dr-empty-text">今日暂无阅读任务</div></div>';
      return;
    }
    var items = task.items;
    var doneCount = items.filter(function (i) { return i.isCheckedIn; }).length;
    var progress = items.length > 0 ? Math.round(doneCount / items.length * 100) : 0;
    var html = '<div class="dr-home-head"><span class="dr-server-light ' + (state.serverOk ? 'ok' : 'err') + '"><span class="dr-server-dot"></span>' + (state.serverOk ? '服务器正常' : '服务器异常') + '</span><h2 class="dr-home-title">今日阅读</h2><p class="dr-home-sub">' + fmtDate(new Date()) + ' · 共 ' + items.length + ' 篇</p></div>';
    html += '<div class="dr-progress"><div class="dr-progress-head"><span>今日进度</span><span>' + doneCount + '/' + items.length + '（' + progress + '%）</span></div><div class="dr-progress-bar"><div class="dr-progress-fill" style="width:' + progress + '%"></div></div></div>';
    items.forEach(function (item) {
      html += '<div class="dr-task-card' + (item.isCheckedIn ? ' done' : '') + '" data-client-id="' + esc(item.articleId) + '" data-checked="' + (item.isCheckedIn ? '1' : '0') + '">'
        + '<div class="dr-task-card-head">'
        + '<span class="dr-task-card-title">' + esc(item.articleTitle) + '</span>'
        + (item.isCheckedIn ? '<span class="dr-task-badge dr-badge-done">✓ 已打卡</span>' : '<span class="dr-task-badge dr-badge-pending">待打卡</span>')
        + '</div>'
        + '<div class="dr-task-meta">'
        + '<span>📖 ' + (item.wordTarget || 0) + ' 字</span>'
        + (item.isLongArticle ? '<span>📄 长文</span>' : '')
        + (item.isRequired ? '<span class="dr-required-tag">必读</span>' : '')
        + '</div></div>';
    });
    el.innerHTML = html;
    // 绑定点击：进入阅读页
    el.querySelectorAll('.dr-task-card').forEach(function (card) {
      card.addEventListener('click', function () {
        var clientId = card.getAttribute('data-client-id');
        var checked = card.getAttribute('data-checked') === '1';
        openReader(clientId, 'home', checked);
      });
    });
  }

  // ---------- 阅读页（阶段 4 填充完整逻辑） ----------
  function openReader(clientId, from, alreadyCheckedIn) {
    var mask = document.getElementById('readerMask');
    var content = document.getElementById('readerContent');
    var title = document.getElementById('readerTitle');
    var checkinBtn = document.getElementById('readerCheckinBtn');
    mask.style.display = 'flex';
    // 记录打开时间：10 秒后才允许打卡
    state.readerOpenedAt = Date.now();
    checkinBtn.disabled = true;
    checkinBtn.textContent = '打卡';
    content.innerHTML = '<div class="dr-loading"><div class="dr-spinner"></div><p>加载文章…</p></div>';
    title.textContent = '加载中…';
    // 拉取单篇详情（含音频/图片）
    drApi('GET', '/articles/' + encodeURIComponent(clientId)).then(function (article) {
      renderReader(article, clientId, from, alreadyCheckedIn);
    }).catch(function (e) {
      content.innerHTML = '<div class="dr-empty"><div class="dr-empty-icon">⚠️</div><div class="dr-empty-text">加载失败：' + esc(e.message) + '</div></div>';
    });
  }

  function renderReader(article, clientId, from, alreadyCheckedIn) {
    document.getElementById('readerTitle').textContent = article.title || '—';
    var content = document.getElementById('readerContent');
    // 应用字号
    content.style.fontSize = state.fontSize + 'px';
    // 渲染内容（content_html 优先，否则 content）
    var html = article.contentHtml || article.content || '';
    if (article.imagewebp && !article.iscontent) {
      html = '<img src="data:image/webp;base64,' + article.imagewebp + '" />' + html;
    }
    content.innerHTML = html;
    // 音频
    var audioBar = document.getElementById('audioBar');
    if (article.audiobase64) {
      audioBar.style.display = 'flex';
      setupAudio(article.audiobase64, clientId, from);
    } else {
      audioBar.style.display = 'none';
      stopAudio();
    }
    // 打卡（按钮 + 双击，统一 10 秒门控）
    setupCheckin(clientId, from, alreadyCheckedIn);
  }

  // ---------- 音频播放（base64 → Blob → <audio>） ----------
  function setupAudio(base64Str, clientId, from) {
    stopAudio();
    var audio = new Audio();
    audio.style.display = 'none';
    document.body.appendChild(audio);
    state.audioEl = audio;
    // base64 → Blob → URL
    try {
      var bytes = atob(base64Str);
      var arr = new Uint8Array(bytes.length);
      for (var i = 0; i < bytes.length; i++) arr[i] = bytes.charCodeAt(i);
      var blob = new Blob([arr], { type: 'audio/mp4' });
      audio.src = URL.createObjectURL(blob);
    } catch (e) {
      console.error('音频解码失败', e);
      return;
    }
    audio.loop = state.loopAudio;
    // UI 绑定
    var playBtn = document.getElementById('audioPlayBtn');
    var timeEl = document.getElementById('audioTime');
    var loopChk = document.getElementById('audioLoopChk');
    playBtn.onclick = function () {
      if (audio.paused) { audio.play(); playBtn.textContent = '⏸'; }
      else { audio.pause(); playBtn.textContent = '▶'; }
    };
    audio.addEventListener('timeupdate', function () { timeEl.textContent = fmtTime(audio.currentTime); });
    audio.addEventListener('ended', function () { playBtn.textContent = '▶'; });
    loopChk.checked = state.loopAudio;
    loopChk.onchange = function () { state.loopAudio = loopChk.checked; audio.loop = loopChk.checked; };
    // 自动播放
    if (state.config && state.config.keepScreenOn !== false) {
      // 不自动播放，等用户点击（移动端限制）
    }
  }

  function stopAudio() {
    if (state.audioEl) {
      state.audioEl.pause();
      if (state.audioEl.src && state.audioEl.src.startsWith('blob:')) URL.revokeObjectURL(state.audioEl.src);
      state.audioEl.remove();
      state.audioEl = null;
    }
  }

  // ---------- 打卡（按钮 + 双击，统一 10 秒门控） ----------
  var CHECKIN_WAIT_MS = 10000;
  var checkinTimer = null;

  function setupCheckin(clientId, from, alreadyCheckedIn) {
    var btn = document.getElementById('readerCheckinBtn');
    var hint = document.getElementById('checkinHint');
    var scroll = document.getElementById('readerScroll');
    state.readerCheckedIn = !!alreadyCheckedIn;
    if (checkinTimer) { clearInterval(checkinTimer); checkinTimer = null; }

    // 刷新按钮状态：已打卡禁用；未满 10 秒显示倒计时；满 10 秒可打卡
    function refreshBtn() {
      if (state.readerCheckedIn) {
        btn.textContent = '✓ 已打卡';
        btn.disabled = true;
        return true;
      }
      var left = CHECKIN_WAIT_MS - (Date.now() - state.readerOpenedAt);
      if (left > 0) {
        btn.textContent = Math.ceil(left / 1000) + 's 后可打卡';
        btn.disabled = true;
        return false;
      }
      btn.textContent = '打卡';
      btn.disabled = false;
      return true;
    }
    refreshBtn();
    checkinTimer = setInterval(function () {
      if (refreshBtn() && checkinTimer) { clearInterval(checkinTimer); checkinTimer = null; }
    }, 500);

    function showHint(text) {
      hint.textContent = text;
      hint.classList.add('show');
      setTimeout(function () { hint.classList.remove('show'); }, 1500);
    }

    function tryCheckin() {
      if (state.readerCheckedIn) { showHint('本文今日已打卡'); return; }
      if (Date.now() - state.readerOpenedAt < CHECKIN_WAIT_MS) { showHint('请阅读 ' + CHECKIN_WAIT_MS / 1000 + ' 秒后再打卡'); return; }
      btn.disabled = true;
      btn.textContent = '打卡中…';
      drApi('POST', '/daily-tasks/today/checkin-by-article', { articleId: clientId })
        .then(function (r) {
          state.readerCheckedIn = true;
          btn.textContent = '✓ 已打卡';
          showHint('✓ 打卡成功 · 累计 ' + (r.checkInDays || 0) + ' 天');
          // 更新今日任务缓存
          if (state.todayTask && state.todayTask.items) {
            state.todayTask.items.forEach(function (it) {
              if (it.articleId === clientId) it.isCheckedIn = true;
            });
          }
        })
        .catch(function (e) {
          showHint('✗ ' + (e.message || '打卡失败'));
          refreshBtn();
        });
    }

    btn.onclick = tryCheckin;
    scroll.ondblclick = tryCheckin;
  }

  // ---------- 关闭阅读页 ----------
  document.getElementById('readerBack').addEventListener('click', function () {
    document.getElementById('readerMask').style.display = 'none';
    if (checkinTimer) { clearInterval(checkinTimer); checkinTimer = null; }
    stopAudio();
    // 返回时刷新当前视图
    if (state.currentView === 'home') renderHome();
    else if (state.currentView === 'random') renderRandom();
    else if (state.currentView === 'ear') renderEar();
  });

  // 字号调节
  document.getElementById('readerFontBtn').addEventListener('click', function () {
    var sizes = [16, 18, 20, 22, 24, 26, 28, 30];
    var idx = sizes.indexOf(state.fontSize);
    idx = (idx + 1) % sizes.length;
    state.fontSize = sizes[idx];
    localStorage.setItem(FONT_KEY, state.fontSize);
    document.getElementById('readerContent').style.fontSize = state.fontSize + 'px';
  });

  // ---------- 文章管理（阶段 5 填充） ----------
  function renderArticles() {
    var el = document.getElementById('view-articles');
    el.innerHTML = '<div class="dr-art-toolbar"><input class="dr-art-search" id="artSearch" placeholder="搜索文章标题…"></div><div class="dr-art-list" id="artList"><div class="dr-loading"><div class="dr-spinner"></div><p>加载中…</p></div></div>';
    // 首次加载文章列表
    if (state.articles.length === 0) {
      drApi('GET', '/articles').then(function (data) {
        state.articles = (data && data.articles) || [];
        renderArticleList(el);
      }).catch(function (e) {
        el.querySelector('#artList').innerHTML = '<div class="dr-empty"><div class="dr-empty-icon">⚠️</div><div class="dr-empty-text">加载失败</div></div>';
      });
    } else {
      renderArticleList(el);
    }
    // 搜索
    document.getElementById('artSearch').addEventListener('input', function () { renderArticleList(el); });
  }

  function renderArticleList(container) {
    var q = (document.getElementById('artSearch').value || '').trim().toLowerCase();
    var list = state.articles.filter(function (a) {
      if (!q) return true;
      return (a.title || '').toLowerCase().indexOf(q) >= 0;
    });
    var listEl = container.querySelector('#artList');
    if (list.length === 0) {
      listEl.innerHTML = '<div class="dr-empty"><div class="dr-empty-icon">📭</div><div class="dr-empty-text">暂无文章</div></div>';
      return;
    }
    listEl.innerHTML = list.map(function (a) {
      return '<div class="dr-art-item" data-cid="' + esc(a.clientId) + '">'
        + '<div class="dr-art-info"><div class="dr-art-title">' + esc(a.title) + '</div>'
        + '<div class="dr-art-sub"><span>📖 ' + (a.chineseChars || 0) + ' 字</span>'
        + (a.hasAudio ? '<span>🔊 有音频</span>' : '') + '</div></div>'
        + '<div class="dr-art-actions"><button class="dr-icon-btn" data-act="read">📖</button></div></div>';
    }).join('');
    listEl.querySelectorAll('.dr-art-item').forEach(function (item) {
      item.addEventListener('click', function () {
        openReader(item.getAttribute('data-cid'), 'articles');
      });
    });
  }

  // ---------- 随心阅读（阶段 6 填充） ----------
  function renderRandom() {
    var el = document.getElementById('view-random');
    // 随机选一篇 isReading 的文章
    var pool = state.articles.filter(function (a) { return a.isReading !== false; });
    if (pool.length === 0) {
      el.innerHTML = '<div class="dr-empty"><div class="dr-empty-icon">🎲</div><div class="dr-empty-text">暂无可阅读的文章，请先在文章管理中添加</div></div>';
      return;
    }
    var pick = pool[Math.floor(Math.random() * pool.length)];
    el.innerHTML = '<div class="dr-home-head"><h2 class="dr-home-title">随心阅读</h2><p class="dr-home-sub">随机推荐一篇</p></div><div class="dr-task-card" data-cid="' + esc(pick.clientId) + '"><div class="dr-task-card-head"><span class="dr-task-card-title">' + esc(pick.title) + '</span></div><div class="dr-task-meta"><span>📖 ' + (pick.chineseChars || 0) + ' 字</span></div></div><button class="dr-btn dr-btn-ghost" id="randomNext" style="margin-top:12px;">🎲 换一篇</button>';
    el.querySelector('.dr-task-card').addEventListener('click', function () { openReader(pick.clientId, 'random'); });
    el.querySelector('#randomNext').addEventListener('click', function () { renderRandom(); });
  }

  // ---------- 磨耳跟背（阶段 6 填充） ----------
  function renderEar() {
    var el = document.getElementById('view-ear');
    var pool = state.articles.filter(function (a) { return a.hasAudio; });
    if (pool.length === 0) {
      el.innerHTML = '<div class="dr-empty"><div class="dr-empty-icon">🎧</div><div class="dr-empty-text">暂无带音频的文章</div></div>';
      return;
    }
    el.innerHTML = '<div class="dr-home-head"><h2 class="dr-home-title">磨耳跟背</h2><p class="dr-home-sub">只展示有音频的文章，专注跟听跟背</p></div>' + pool.map(function (a) {
      return '<div class="dr-task-card" data-cid="' + esc(a.clientId) + '"><div class="dr-task-card-head"><span class="dr-task-card-title">' + esc(a.title) + '</span></div><div class="dr-task-meta"><span>📖 ' + (a.chineseChars || 0) + ' 字</span><span>🔊 有音频</span></div></div>';
    }).join('');
    el.querySelectorAll('.dr-task-card').forEach(function (card) {
      card.addEventListener('click', function () { openReader(card.getAttribute('data-cid'), 'ear'); });
    });
  }

  // ---------- 设置（阶段 6 填充） ----------
  function renderSettings() {
    var el = document.getElementById('view-settings');
    var c = state.config || { dailyMinutes: 20, targetCheckRate: 30 };
    el.innerHTML = '<div class="dr-home-head"><h2 class="dr-home-title">设置</h2></div>'
      + '<div class="dr-settings-section">'
      + '<div class="dr-settings-row"><div><div class="dr-settings-label">每日阅读时长</div><div class="dr-settings-desc">影响每日任务字数生成</div></div><input class="dr-settings-input" type="number" id="cfgMinutes" value="' + (c.dailyMinutes || 20) + '" min="1" max="300"> 分钟</div>'
      + '<div class="dr-settings-row"><div><div class="dr-settings-label">目标完成率</div><div class="dr-settings-desc">影响任务筛选</div></div><input class="dr-settings-input" type="number" id="cfgRate" value="' + (c.targetCheckRate || 30) + '" min="0" max="100"> %</div>'
      + '<div class="dr-settings-row"><div><div class="dr-settings-label">阅读字号</div><div class="dr-settings-desc">阅读页当前字号：' + state.fontSize + 'px</div></div><button class="dr-btn dr-btn-ghost" id="cfgFontBtn">调节字号</button></div>'
      + '</div>'
      + '<div class="dr-settings-section">'
      + '<div class="dr-settings-row"><div><div class="dr-settings-label">绑定的 DailyRead 账号</div><div class="dr-settings-desc">' + esc(state.drUser ? (state.drUser.nickname || state.drUser.username) : '—') + '（' + esc(state.drUser ? state.drUser.username : '') + '）</div></div><button class="dr-btn dr-btn-ghost" id="cfgUnbind">管理绑定</button></div>'
      + '</div>'
      + '<button class="dr-btn dr-btn-primary" id="cfgSave" style="width:100%;margin-top:12px;">保存配置</button>'
      + '<a class="dr-btn dr-btn-ghost" href="/center/app.html" style="margin-top:10px;">返回学习中心</a>';

    document.getElementById('cfgSave').addEventListener('click', function () {
      var minutes = parseInt(document.getElementById('cfgMinutes').value, 10) || 20;
      var rate = parseInt(document.getElementById('cfgRate').value, 10) || 30;
      drApi('PUT', '/config', { dailyMinutes: minutes, targetCheckRate: rate, readerFontSize: state.fontSize })
        .then(function () {
          state.config.dailyMinutes = minutes;
          state.config.targetCheckRate = rate;
          alert('配置已保存');
        })
        .catch(function (e) { alert('保存失败：' + e.message); });
    });
    document.getElementById('cfgFontBtn').addEventListener('click', function () {
      var sizes = [16, 18, 20, 22, 24, 26, 28, 30];
      var idx = sizes.indexOf(state.fontSize);
      idx = (idx + 1) % sizes.length;
      state.fontSize = sizes[idx];
      localStorage.setItem(FONT_KEY, state.fontSize);
      renderSettings();
    });
    document.getElementById('cfgUnbind').addEventListener('click', function () {
      location.href = '/center/dr/bind.html';
    });
  }

  // ---------- 启动 ----------
  init();
})();
