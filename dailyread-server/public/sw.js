// Learning Center | 炎武班 - Service Worker
// 策略：
//   /api/*            -> 仅网络（不缓存）
//   /uploads/*        -> 仅网络（讲义内容需实时）
//   页面导航          -> 网络优先，失败回退缓存
//   静态资源(css/js/图标) -> 缓存优先 + 后台更新 (stale-while-revalidate)
var CACHE_NAME = 'lc-mission-v4';

var CORE_ASSETS = [
  '/',
  '/css/style.css',
  '/center/index.html',
  '/center/app.html',
  '/center/css/center.css',
  '/center/js/login.js',
  '/center/js/app.js',
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

  // 导航请求：网络优先，回退缓存
  if (req.mode === 'navigate') {
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

  // 静态资源：缓存优先 + 后台刷新
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
