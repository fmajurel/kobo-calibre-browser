const CACHE = 'calibre-pwa-v1';
const PRECACHE = ['/app', '/static/app.css', '/static/app.js'];

self.addEventListener('install', e => {
    self.skipWaiting();
    e.waitUntil(caches.open(CACHE).then(c => c.addAll(PRECACHE)));
});

self.addEventListener('activate', e => {
    e.waitUntil(
        caches.keys().then(keys =>
            Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
        ).then(() => clients.claim())
    );
});

self.addEventListener('fetch', e => {
    if (e.request.method !== 'GET') return;
    // Toujours réseau en premier ; cache seulement en fallback offline
    e.respondWith(
        fetch(e.request)
            .then(res => {
                // Mettre en cache les assets statiques
                if (e.request.url.includes('/static/')) {
                    const clone = res.clone();
                    caches.open(CACHE).then(c => c.put(e.request, clone));
                }
                return res;
            })
            .catch(() => caches.match(e.request))
    );
});
