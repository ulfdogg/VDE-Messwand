const CACHE_NAME = "my-web-app-cache-v1";
const urlsToCache = [
    "/",
    "/static/images/favicon-32x32.png",
    "/static/css/styles.css", // Dein Haupt-CSS
    "/static/js/main.js" // Falls vorhanden
];

self.addEventListener("install", (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                console.log("Opened cache");
                return cache.addAll(urlsToCache);
            })
    );
});

self.addEventListener("fetch", (event) => {
    event.respondWith(
        caches.match(event.request)
            .then((response) => {
                return response || fetch(event.request);
            })
    );
});
