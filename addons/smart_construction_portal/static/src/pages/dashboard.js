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

  function showToast(message, type) {
    const toast = document.createElement("div");
    toast.className = `sc-portal__toast is-${type || "info"}`;
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => {
      toast.classList.add("is-hide");
      setTimeout(() => toast.remove(), 300);
    }, 2400);
  }

  function renderActionPanel(container, payload) {
    if (!payload) {
      container.innerHTML = `
        <div class="sc-portal__panel-title">快捷动作</div>
        <div class="sc-portal__empty">动作配置不可用</div>
      `;
      return;
    }
    const allowed = !!payload.allowed;
    const action = payload.action || {};
    const error = payload.error || {};
    const hint = !allowed ? (error.message || "当前不可执行") : "";
    const buttonClass = allowed ? "sc-portal__action-btn" : "sc-portal__action-btn is-disabled";

    container.innerHTML = `
      <div class="sc-portal__panel-title">快捷动作</div>
      <div class="sc-portal__action-card">
        <div class="sc-portal__action-text">
          <div class="sc-portal__action-label">${escapeHtml(action.label || "执行动作")}</div>
          <div class="sc-portal__action-desc">${escapeHtml(action.desc || "")}</div>
          ${hint ? `<div class="sc-portal__action-hint">${escapeHtml(hint)}</div>` : ""}
        </div>
        <button class="${buttonClass}" type="button" ${allowed ? "" : "disabled"}>
          立即执行
        </button>
      </div>
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
    const actionPanel = el.querySelector("[data-portal='dashboard-action']");
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

    if (actionPanel) {
      const loadActionPanel = () => {
        api
          .getPortalExecuteButton()
          .then((res) => {
            const data = res && res.data ? res.data : null;
            renderActionPanel(actionPanel, data);
            const btn = actionPanel.querySelector(".sc-portal__action-btn");
            if (btn && data && data.allowed && data.target) {
              btn.addEventListener("click", () => {
                btn.classList.add("is-loading");
                api
                  .executePortalButton({
                    model: data.target.model,
                    res_id: data.target.res_id,
                    method: data.target.method,
                  })
                  .then((result) => {
                    if (result && result.ok) {
                      showToast("动作执行成功", "success");
                      loadActionPanel();
                    } else {
                      const msg = (result && result.error && result.error.message) || "动作执行失败";
                      showToast(msg, "error");
                    }
                  })
                  .catch(() => showToast("动作执行失败", "error"))
                  .finally(() => {
                    btn.classList.remove("is-loading");
                  });
              });
            }
          })
          .catch(() => {
            renderActionPanel(actionPanel, null);
          });
      };
      loadActionPanel();
    }
  }

  root.dashboard = {init};
})();
