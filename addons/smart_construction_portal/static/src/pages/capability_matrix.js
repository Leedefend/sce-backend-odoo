(function () {
  "use strict";

  const root = (window.scPortal = window.scPortal || {});
  const api = root.api;

  function escapeHtml(value) {
    return String(value || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/\"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function renderLoading(container) {
    container.innerHTML = `
      <div class="sc-portal__panel-title">能力矩阵</div>
      <div class="sc-portal__empty">加载中...</div>
    `;
  }

  function renderError(container, message) {
    container.innerHTML = `
      <div class="sc-portal__panel-title">能力矩阵</div>
      <div class="sc-portal__empty">${escapeHtml(message)}</div>
    `;
  }

  function renderMatrix(container, sections) {
    if (!sections || !sections.length) {
      container.innerHTML = `
        <div class="sc-portal__panel-title">能力矩阵</div>
        <div class="sc-portal__empty">暂无可用入口</div>
      `;
      return;
    }
    const blocks = sections
      .map((section) => {
        const items = Array.isArray(section.items) ? section.items : [];
        const cards = items
          .map((item) => {
            const allowed = !!item.allowed;
            const classes = allowed ? "sc-portal__matrix-card" : "sc-portal__matrix-card is-disabled";
            const href = allowed && item.target_url ? `href="${item.target_url}"` : "";
            return `
              <a class="${classes}" ${href}>
                <div class="sc-portal__matrix-label">${escapeHtml(item.label || item.key)}</div>
                <div class="sc-portal__matrix-desc">${escapeHtml(item.desc || "")}</div>
              </a>
            `;
          })
          .join("");
        return `
          <div class="sc-portal__matrix-section">
            <div class="sc-portal__matrix-title">${escapeHtml(section.label || section.key)}</div>
            <div class="sc-portal__matrix-grid">
              ${cards || '<div class="sc-portal__empty">暂无可用入口</div>'}
            </div>
          </div>
        `;
      })
      .join("");

    container.innerHTML = `
      <div class="sc-portal__panel-title">能力矩阵</div>
      ${blocks}
    `;
  }

  function init(el) {
    const panel = el.querySelector("[data-portal='capability-matrix']");
    if (!panel) return;
    renderLoading(panel);
    api
      .getCapabilityMatrix()
      .then((res) => {
        const data = res && res.data ? res.data : null;
        renderMatrix(panel, data ? data.sections : null);
      })
      .catch(() => {
        renderError(panel, "能力矩阵加载失败");
      });
  }

  root.capabilityMatrix = {init};
})();
