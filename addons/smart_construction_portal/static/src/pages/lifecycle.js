(function () {
  "use strict";

  const root = (window.scPortal = window.scPortal || {});
  const api = root.api;

  const STATE_LABELS = {
    draft: "立项中",
    in_progress: "执行中",
    paused: "暂停",
    done: "已完成",
    closing: "收尾中",
    warranty: "质保期",
    closed: "已关闭",
  };

  function escapeHtml(value) {
    return String(value || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/\"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function buildStateOrder(states) {
    if (states && states.length) {
      return states.slice();
    }
    return [
      "draft",
      "in_progress",
      "paused",
      "done",
      "closing",
      "warranty",
      "closed",
    ];
  }

  function groupByState(projects, stateOrder) {
    const groups = {};
    stateOrder.forEach((state) => {
      groups[state] = [];
    });
    projects.forEach((project) => {
      const key = project.lifecycle_state || "draft";
      if (!groups[key]) {
        groups[key] = [];
      }
      groups[key].push(project);
    });
    return groups;
  }

  function renderLifecyclePanel(container, stateOrder, groups, selectedId) {
    const columns = stateOrder
      .map((state) => {
        const items = groups[state] || [];
        const label = STATE_LABELS[state] || state;
        const cards = items
          .map((project) => {
            const active = project.id === selectedId ? "is-active" : "";
            return `
              <button class="sc-portal__card ${active}" data-project-id="${project.id}">
                <div class="sc-portal__card-title">${escapeHtml(project.name || "(未命名项目)")}</div>
                <div class="sc-portal__card-meta">ID ${project.id}</div>
              </button>
            `;
          })
          .join("");
        return `
          <div class="sc-portal__column">
            <div class="sc-portal__column-head">
              <span>${escapeHtml(label)}</span>
              <span class="sc-portal__count">${items.length}</span>
            </div>
            <div class="sc-portal__column-body">
              ${cards || '<div class="sc-portal__empty">暂无项目</div>'}
            </div>
          </div>
        `;
      })
      .join("");

    container.innerHTML = `
      <div class="sc-portal__panel-title">生命周期看板</div>
      <div class="sc-portal__kanban">${columns}</div>
    `;
  }

  function renderDetailPanel(container, project) {
    if (!project) {
      container.innerHTML = `
        <div class="sc-portal__panel-title">项目详情</div>
        <div class="sc-portal__empty">请选择左侧项目</div>
      `;
      return;
    }
    const label = STATE_LABELS[project.lifecycle_state] || project.lifecycle_state || "draft";
    container.innerHTML = `
      <div class="sc-portal__panel-title">项目详情</div>
      <div class="sc-portal__detail">
        <div class="sc-portal__detail-name">${escapeHtml(project.name || "(未命名项目)")}</div>
        <div class="sc-portal__detail-row"><span>项目 ID</span><span>${project.id}</span></div>
        <div class="sc-portal__detail-row"><span>生命周期</span><span class="sc-portal__badge">${escapeHtml(label)}</span></div>
      </div>
    `;
  }

  function renderCapabilities(container, capabilities, capabilityCodes) {
    if (!capabilities) {
      container.innerHTML = `
        <div class="sc-portal__panel-title">能力矩阵</div>
        <div class="sc-portal__empty">选择项目后加载能力矩阵</div>
      `;
      return;
    }

    const codes = capabilityCodes && capabilityCodes.length ? capabilityCodes : Object.keys(capabilities);
    const rows = codes
      .map((code) => {
        const info = capabilities[code] || {mode: "deny"};
        const mode = info.mode || "deny";
        return `
          <div class="sc-portal__cap-row">
            <div class="sc-portal__cap-name">${escapeHtml(code)}</div>
            <div class="sc-portal__cap-mode mode-${mode}">${escapeHtml(mode)}</div>
          </div>
        `;
      })
      .join("");

    container.innerHTML = `
      <div class="sc-portal__panel-title">能力矩阵</div>
      <div class="sc-portal__cap-legend">
        <span class="mode-allow">allow</span>
        <span class="mode-readonly">readonly</span>
        <span class="mode-deny">deny</span>
      </div>
      <div class="sc-portal__cap-list">${rows || ""}</div>
    `;
  }

  function attachCardHandlers(container, onSelect) {
    container.querySelectorAll("[data-project-id]").forEach((node) => {
      node.addEventListener("click", () => {
        const projectId = parseInt(node.getAttribute("data-project-id"), 10);
        if (!Number.isNaN(projectId)) {
          onSelect(projectId);
        }
      });
    });
  }

  function renderLoading(container, title) {
    container.innerHTML = `
      <div class="sc-portal__panel-title">${escapeHtml(title)}</div>
      <div class="sc-portal__empty">加载中...</div>
    `;
  }

  function renderError(container, title, message) {
    container.innerHTML = `
      <div class="sc-portal__panel-title">${escapeHtml(title)}</div>
      <div class="sc-portal__empty">${escapeHtml(message || "加载失败")}</div>
    `;
  }

  function init(rootEl) {
    if (!rootEl || !api) {
      return;
    }

    const lifecyclePanel = rootEl.querySelector("[data-portal='lifecycle']");
    const detailPanel = rootEl.querySelector("[data-portal='detail']");
    const capabilityPanel = rootEl.querySelector("[data-portal='capabilities']");

    const state = {
      projects: [],
      selectedId: null,
      capabilities: null,
      contract: null,
    };

    renderLoading(lifecyclePanel, "生命周期看板");
    renderLoading(detailPanel, "项目详情");
    renderLoading(capabilityPanel, "能力矩阵");

    const initialId = parseInt(rootEl.getAttribute("data-project-id"), 10);
    if (!Number.isNaN(initialId)) {
      state.selectedId = initialId;
    }

    api
      .getPortalContract("/portal/lifecycle")
      .then((res) => {
        if (res && res.data) {
          state.contract = res.data;
        }
      })
      .catch(() => {
        state.contract = null;
      })
      .finally(() => {
        api
          .listProjects()
          .then((res) => {
            const records = (res && res.data && res.data.records) || [];
            state.projects = records;
            if (!state.selectedId && records.length) {
              state.selectedId = records[0].id;
            }
            const order = buildStateOrder(state.contract && state.contract.lifecycle_states);
            const groups = groupByState(state.projects, order);
            renderLifecyclePanel(lifecyclePanel, order, groups, state.selectedId);
            attachCardHandlers(lifecyclePanel, (projectId) => {
              if (state.selectedId === projectId) {
                return;
              }
              state.selectedId = projectId;
              renderLifecyclePanel(lifecyclePanel, order, groups, state.selectedId);
              attachCardHandlers(lifecyclePanel, onSelectProject);
              onSelectProject(projectId);
            });
            const selected = state.projects.find((item) => item.id === state.selectedId);
            renderDetailPanel(detailPanel, selected);
            if (state.selectedId) {
              onSelectProject(state.selectedId);
            } else {
              renderCapabilities(capabilityPanel, null, []);
            }
          })
          .catch(() => {
            renderError(lifecyclePanel, "生命周期看板", "项目数据加载失败");
            renderDetailPanel(detailPanel, null);
            renderCapabilities(capabilityPanel, null, []);
          });
      });

    function onSelectProject(projectId) {
      const selected = state.projects.find((item) => item.id === projectId);
      renderDetailPanel(detailPanel, selected);
      renderLoading(capabilityPanel, "能力矩阵");
      api
        .getProjectCapabilities(projectId)
        .then((res) => {
          if (!res || !res.data) {
            renderError(capabilityPanel, "能力矩阵", "能力矩阵加载失败");
            return;
          }
          state.capabilities = res.data.capabilities || {};
          const codes = (state.contract && state.contract.capability_codes) || [];
          renderCapabilities(capabilityPanel, state.capabilities, codes);
        })
        .catch(() => {
          renderError(capabilityPanel, "能力矩阵", "能力矩阵加载失败");
        });
    }
  }

  root.lifecycle = {init};
})();
