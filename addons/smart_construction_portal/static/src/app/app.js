(function () {
  "use strict";

  const root = (window.scPortal = window.scPortal || {});

  function bootstrap() {
    const el = document.getElementById("sc-portal-root");
    if (!el || !root.lifecycle || !root.lifecycle.init) {
      return;
    }
    root.lifecycle.init(el);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", bootstrap);
  } else {
    bootstrap();
  }
})();
