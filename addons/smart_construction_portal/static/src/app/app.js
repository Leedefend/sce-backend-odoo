(function () {
  "use strict";

  const root = (window.scPortal = window.scPortal || {});

  function bootstrap() {
    const el = document.getElementById("sc-portal-root");
    if (!el) return;
    const page = el.dataset.page || "lifecycle";
    if (page === "capability-matrix" && root.capabilityMatrix && root.capabilityMatrix.init) {
      root.capabilityMatrix.init(el);
      return;
    }
    if (page === "dashboard" && root.dashboard && root.dashboard.init) {
      root.dashboard.init(el);
      return;
    }
    if (root.lifecycle && root.lifecycle.init) {
      root.lifecycle.init(el);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", bootstrap);
  } else {
    bootstrap();
  }
})();
