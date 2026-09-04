// Learning Center | 炎武班 - Service Worker
// 策略：
//   /api/*            -> 仅网络（不缓存）
//   /uploads/*        -> 仅网络（讲义内容需实时）
//   页面导航          -> 网络优先，失败回退缓存
//   静态资源(css/js/图标) -> 缓存优先 + 后台更新 (stale-while-revalidate)
var CACHE_NAME = 'lc-mission-v8';

var CORE_ASSETS = [
  '/',
  '/css/style.css',
  '/center/index.html',
  '/center/app.html',
  '/center/css/center.css',
  '/center/js/login.js',
  '/center/js/app.js',
  '/center/dr/app.html',
  '/center/dr/bind.html',
  '/center/dr/css/dr.css',
  '/center/dr/js/app.js',
  '/center/dr/js/bind.js',
  '/manifest.json',
  '/center/icons/icon-192.png',
  '/center/icons/icon-512.png'
];

self.addEventListener('install', function (event) {
  event.waitUntil(
    caches.open(CACHE_NAME).then(function (cache) {
      return Promise.allSettled(CORE_ASSETS.map(function (url) {
        return cache.add(new Request(url, { cache: 'reload' }));
      }));
    }).then(function () {
      return self.skipWaiting();
    })
  );
});

self.addEventListener('activate', function (event) {
  event.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(keys.map(function (k) {
        if (k !== CACHE_NAME) return caches.delete(k);
      }));
    }).then(function () {
      return self.clients.claim();
    })
  );
});

// 与 app.html 强耦合的核心脚本/样式必须与 HTML 同步更新，
// 否则会出现「新 HTML 引用旧 JS 里已改名的元素」→ 事件绑定失效。
// 这些 shell 资源改走网络优先（同导航），失败再回退缓存，保证版本一致。
var SHELL_ASSETS = [
  '/center/app.html',
  '/center/js/app.js',
  '/center/css/center.css',
  '/center/js/login.js'
];

self.addEventListener('fetch', function (event) {
  var req = event.request;
  if (req.method !== 'GET') return;

  var url = new URL(req.url);
  if (url.origin !== self.location.origin) return;

  // API 与讲义文件：仅网络
  if (url.pathname.indexOf('/api/') === 0 || url.pathname.indexOf('/uploads/') === 0) {
    event.respondWith(fetch(req).catch(function () {
      return new Response(JSON.stringify({ code: -1, message: '当前离线，请稍后重试' }), {
        status: 503, headers: { 'Content-Type': 'application/json' }
      });
    }));
    return;
  }

  // 导航请求 + 核心 SPA shell：网络优先，回退缓存（HTML/JS/CSS 版本始终一致）
  var isShell = (req.mode === 'navigate') || SHELL_ASSETS.indexOf(url.pathname) !== -1;
  if (isShell) {
    event.respondWith(
      fetch(req).then(function (res) {
        var copy = res.clone();
        caches.open(CACHE_NAME).then(function (c) { c.put(req, copy); }).catch(function () {});
        return res;
      }).catch(function () {
        return caches.match(req).then(function (hit) {
          if (hit) return hit;
          // 回退到入口页
          return caches.match(url.pathname.indexOf('/center/') === 0 ? '/center/index.html' : '/');
        });
      })
    );
    return;
  }

  // 其它静态资源（图标 / manifest 等）：缓存优先 + 后台刷新
  event.respondWith(
    caches.match(req).then(function (hit) {
      var fetchPromise = fetch(req).then(function (res) {
        if (res && res.status === 200) {
          var copy = res.clone();
          caches.open(CACHE_NAME).then(function (c) { c.put(req, copy); }).catch(function () {});
        }
        return res;
      }).catch(function () {
        return hit;
      });
      return hit || fetchPromise;
    })
  );
});
