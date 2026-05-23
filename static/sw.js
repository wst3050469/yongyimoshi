/* 永颐无机磨石 - Service Worker */
const CACHE_NAME = 'yongyi-v1';
const ASSETS_TO_CACHE = [
  '/',
  '/static/style.css',
  '/static/manifest.json',
  '/static/icon-192.png',
  '/static/icon-512.png',
];

// 安装时缓存核心资源
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      return cache.addAll(ASSETS_TO_CACHE);
    })
  );
});

// 激活时清理旧缓存
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys => {
      return Promise.all(
        keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k))
      );
    })
  );
});

// 网络优先，缓存备用
self.addEventListener('fetch', event => {
  event.respondWith(
    fetch(event.request)
      .then(response => {
        const clone = response.clone();
        if (event.request.url.startsWith(self.location.origin) &&
            event.request.method === 'GET') {
          caches.open(CACHE_NAME).then(cache => {
            cache.put(event.request, clone);
          });
        }
        return response;
      })
      .catch(() => {
        return caches.match(event.request);
      })
  );
});
