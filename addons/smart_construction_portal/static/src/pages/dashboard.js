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
      <div class="sc-portal__panel-title">我的工作台</div>
      <div class="sc-portal__empty">加载中...</div>
    `;
  }

  function renderError(container, message) {
    container.innerHTML = `
      <div class="sc-portal__panel-title">我的工作台</div>
      <div class="sc-portal__empty">${escapeHtml(message)}</div>
    `;
  }

  function renderDashboard(container, entries) {
    if (!entries || !entries.length) {
      container.innerHTML = `
        <div class="sc-portal__panel-title">我的工作台</div>
        <div class="sc-portal__empty">暂无可用入口</div>
      `;
      return;
    }
    const cards = entries
      .map((entry) => {
        const allowed = !!entry.allowed;
        const target = entry.target || {};
        const href = allowed && target.value ? `href="${target.value}"` : "";
        const classes = allowed ? "sc-portal__dashboard-card" : "sc-portal__dashboard-card is-disabled";
        return `
          <a class="${classes}" ${href}>
            <div class="sc-portal__dashboard-label">${escapeHtml(entry.label || entry.key)}</div>
            <div class="sc-portal__dashboard-desc">${escapeHtml(entry.desc || "")}</div>
          </a>
        `;
      })
      .join("");

    container.innerHTML = `
      <div class="sc-portal__panel-title">我的工作台</div>
      <div class="sc-portal__dashboard-grid">${cards}</div>
    `;
  }

  function init(el) {
    const panel = el.querySelector("[data-portal='dashboard']");
    if (!panel) return;
    renderLoading(panel);
    api
      .getPortalDashboard()
      .then((res) => {
        const data = res && res.data ? res.data : null;
        renderDashboard(panel, data ? data.entries : null);
      })
      .catch(() => {
        renderError(panel, "工作台加载失败");
      });
  }

  root.dashboard = {init};
})();
