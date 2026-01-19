/** @odoo-module **/

function focusFieldByName(formView, fieldName) {
  const widget = formView.querySelector(`.o_field_widget[name="${fieldName}"]`);
  if (!widget) return false;
  const input = widget.querySelector("input, textarea, select, .o_input");
  if (!input) return false;
  input.focus();
  if (typeof input.select === "function") input.select();
  return true;
}

function activateTabForElement(el) {
  const pane = el.closest(".o_notebook_page, .tab-pane");
  if (!pane) return false;
  if (pane.classList.contains("active") || pane.classList.contains("show")) return true;

  const notebook = pane.closest(".o_notebook");
  if (!notebook) return false;

  const paneId = pane.getAttribute("id");
  const paneName = pane.dataset.tab || pane.dataset.name || pane.getAttribute("name");
  const header = notebook.querySelector(".o_notebook_headers, .nav-tabs") || notebook;
  const selectors = [];
  if (paneName) {
    selectors.push(
      `[data-name="${paneName}"]`,
      `[data-tab="${paneName}"]`,
      `[data-bs-target="#${paneName}"]`,
      `[href="#${paneName}"]`,
      `[aria-controls="${paneName}"]`
    );
  }
  if (paneId) {
    selectors.push(`[aria-controls="${paneId}"]`, `[href="#${paneId}"]`, `[data-bs-target="#${paneId}"]`);
  }

  for (const selector of selectors) {
    const tabLink = header.querySelector(selector) || notebook.querySelector(selector);
    if (tabLink) {
      tabLink.click();
      return true;
    }
  }
  return false;
}

function activateTabByName(formRoot, tabName) {
  if (!tabName) return false;
  const notebook = formRoot.querySelector(".o_notebook");
  if (!notebook) return false;
  const header = notebook.querySelector(".o_notebook_headers, .nav-tabs") || notebook;
  const selector = [
    `.nav-link[name="${tabName}"]`,
    `.nav-link[data-name="${tabName}"]`,
    `.nav-link[data-tab="${tabName}"]`,
    `.nav-link[aria-controls="${tabName}"]`,
    `.nav-link[href="#${tabName}"]`,
    `.nav-link[data-bs-target="#${tabName}"]`,
    `[role="tab"][name="${tabName}"]`,
    `[role="tab"][data-name="${tabName}"]`,
    `[role="tab"][data-tab="${tabName}"]`,
    `[role="tab"][aria-controls="${tabName}"]`,
    `[role="tab"][href="#${tabName}"]`,
    `[role="tab"][data-bs-target="#${tabName}"]`,
  ].join(",");
  const tabLink = header.querySelector(selector) || notebook.querySelector(selector);
  if (tabLink) {
    tabLink.click();
    return true;
  }
  return false;
}

export function navigateToTarget(formRootEl, target, options = {}) {
  if (!target) return false;
  const onStatus = typeof options.onStatus === "function" ? options.onStatus : null;
  const debug =
    Boolean((window.odoo && window.odoo.__DEBUG__) || /\bdebug\b/.test(window.location.search || ""));
  const anchor = formRootEl.querySelector(`[data-sc-anchor="${target}"]`);
  if (anchor) {
    activateTabForElement(anchor);
    anchor.scrollIntoView({ behavior: "smooth", block: "center" });
    const input = anchor.querySelector("input, textarea, select, .o_input");
    if (input) {
      input.focus();
      if (typeof input.select === "function") input.select();
    }
    if (debug) console.log("[sc_insight] navigate", target, "anchor");
    if (onStatus) onStatus("anchor");
    return true;
  }

  if (target === "schedule") {
    return (
      focusFieldByName(formRootEl, "date_start") ||
      focusFieldByName(formRootEl, "date_end") ||
      focusFieldByName(formRootEl, "date") ||
      focusFieldByName(formRootEl, "start_date") ||
      focusFieldByName(formRootEl, "end_date")
    );
  }
  if (target === "manager") {
    return focusFieldByName(formRootEl, "manager_id");
  }
  if (target === "wbs") {
    if (activateTabByName(formRootEl, "wbs_tab")) {
      if (debug) console.log("[sc_insight] navigate", target, "tab");
      if (onStatus) onStatus("tab");
      return true;
    }
    const btn = formRootEl.querySelector('button[name="action_open_wbs"]');
    if (btn) {
      btn.click();
      if (debug) console.log("[sc_insight] navigate", target, "action");
      if (onStatus) onStatus("action");
      return true;
    }
    if (onStatus) onStatus("no_permission");
    if (debug) console.log("[sc_insight] navigate", target, "no_permission");
  }
  if (target === "boq") {
    if (activateTabByName(formRootEl, "boq_tab")) {
      if (debug) console.log("[sc_insight] navigate", target, "tab");
      if (onStatus) onStatus("tab");
      return true;
    }
    const btn = formRootEl.querySelector('button[name="action_open_boq_import"]');
    if (btn) {
      btn.click();
      if (debug) console.log("[sc_insight] navigate", target, "action");
      if (onStatus) onStatus("action");
      return true;
    }
    if (onStatus) onStatus("no_permission");
    if (debug) console.log("[sc_insight] navigate", target, "no_permission");
  }
  return false;
}
