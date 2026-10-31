"use strict";
// Installing the PWA must not change game logic or claim offline gameplay.
// A registration failure never blocks the normal browser experience.
if ("serviceWorker" in navigator && window.isSecureContext) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/service-worker.js", {scope:"/"})
      .catch(error => console.warn("Install support unavailable:", error));
  }, {once:true});
}
