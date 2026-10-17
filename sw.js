/* 2026-10-17 網頁變 App 用的 service worker:只為了讓手機 / Chrome 認得這是 App(可「安裝」)。
   不快取、不攔截任何請求(每次都拿最新報表,也不影響 Cloudflare 登入)。 */
self.addEventListener('install', function(){ self.skipWaiting(); });
self.addEventListener('activate', function(e){ e.waitUntil(self.clients.claim()); });
