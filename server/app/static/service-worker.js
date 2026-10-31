"use strict";
// SHITHEAD Games: installability and truthful offline messaging ONLY.
// Never cache rooms, seat credentials, websocket traffic, actions or private state.
self.addEventListener("install", () => {
  self.skipWaiting();
});
self.addEventListener("activate", event => {
  event.waitUntil(self.clients.claim());
});
self.addEventListener("fetch", event => {
  const req = event.request;
  if (req.method !== "GET" || req.mode !== "navigate") return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;
  // No offline gameplay: all navigations and state remain network-owned.
  event.respondWith(
    fetch(req).catch(() => new Response(
      '<!doctype html><html lang="en"><meta charset="utf-8">' +
      '<meta name="viewport" content="width=device-width,initial-scale=1">' +
      '<meta name="theme-color" content="#0b0b0e">' +
      '<title>SHITHEAD Games — Connection lost</title>' +
      '<main style="max-width:32rem;margin:15vh auto;padding:2rem;' +
      'background:#171315;color:#f8e9d3;font:1rem system-ui">' +
      '<h1>Connection lost</h1>' +
      '<p>SHITHEAD Games needs internet for multiplayer and Solo Play. ' +
      'Your turn was not submitted while offline.</p>' +
      '<button onclick="location.reload()" style="padding:.8rem 1.1rem;' +
      'background:#d8a769;border:0;border-radius:8px">Try again</button>' +
      '</main></html>',
      {status:503,headers:{"Content-Type":"text/html; charset=utf-8","Cache-Control":"no-store"}}
    ))
  );
});
