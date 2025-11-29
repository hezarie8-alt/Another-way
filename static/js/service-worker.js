// Service Worker for Push Notifications

self.addEventListener('push', function(event) {
    if (!event.data) return;
    
    const data = event.data.json();
    const options = {
        body: data.body,
        icon: data.icon || '/static/images/logo.png',
        badge: '/static/images/logo.png',
        vibrate: [200, 100, 200],
        data: data.data,
        actions: [
            {
                action: 'open',
                title: 'باز کردن'
            },
            {
                action: 'close',
                title: 'بستن'
            }
        ]
    };
    
    event.waitUntil(
        self.registration.showNotification(data.title, options)
    );
});

self.addEventListener('notificationclick', function(event) {
    event.notification.close();
    
    if (event.action === 'close') {
        return;
    }
    
    // باز کردن صفحه چت
    const urlToOpen = event.notification.data.url || '/inbox';
    
    event.waitUntil(
        clients.matchAll({
            type: 'window',
            includeUncontrolled: true
        }).then(function(clientList) {
            // اگر تب باز است، فوکوس کن
            for (let i = 0; i < clientList.length; i++) {
                const client = clientList[i];
                if (client.url.includes(urlToOpen) && 'focus' in client) {
                    return client.focus();
                }
            }
            // اگر تب باز نیست، تب جدید باز کن
            if (clients.openWindow) {
                return clients.openWindow(urlToOpen);
            }
        })
    );
});

// Cache static assets
self.addEventListener('install', function(event) {
    event.waitUntil(
        caches.open('chat-app-v1').then(function(cache) {
            return cache.addAll([
                '/',
                '/static/css/style.css',
                '/static/js/chat.js',
                '/static/js/chat-enhanced.js',
                '/static/images/logo.png'
            ]);
        })
    );
});

self.addEventListener('fetch', function(event) {
    event.respondWith(
        caches.match(event.request).then(function(response) {
            return response || fetch(event.request);
        })
    );
});