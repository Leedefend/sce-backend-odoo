/** @odoo-module **/

// Minimal, SPA-safe banner renderer for /api/insight
// - Reads current record id/model from URL hash (#id=...&model=...)
// - Finds mount points in form views and renders system "voice".
// - Avoids throwing on ACL/endpoint failures; fails quietly with a friendly message.

function parseHashParams() {
  const hash = window.location.hash || "";
  const q = hash.startsWith("#") ? hash.slice(1) : hash;
  const out = {};
  for (const part of q.split("&")) {
    if (!part) continue;
    const idx = part.indexOf("=");
    if (idx < 0) continue;
    const k = decodeURIComponent(part.slice(0, idx));
    const v = decodeURIComponent(part.slice(idx + 1));
    out[k] = v;
  }
  return out;
}

function levelClass(level) {
  // Bootstrap-ish classes in backend
  if (level === "risk") return "alert-danger";
  if (level === "warning") return "alert-warning";
  return "alert-info";
}

function escapeHtml(s) {
  if (s === null || s === undefined) return "";
  return String(s)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function renderBanner(el, payload) {
  // payload: { ok, data } or { ok:false, error }
  const ok = payload && payload.ok === true;
  if (!ok) {
    const msg = payload?.error?.message || "无法获取系统洞察。";
    el.classList.remove("d-none");
    el.classList.add("alert", "alert-warning");
    el.innerHTML = `
      <div class="fw-bold">系统提示</div>
      <div>${escapeHtml(msg)}</div>
    `;
    return;
  }

  const data = payload.data || {};
  const summary = data.summary || {};
  const cls = levelClass(summary.level);

  el.className = ""; // reset
  el.classList.add("alert", cls, "sc-insight-banner");
  el.classList.remove("d-none");

  const title = escapeHtml(summary.title || "系统洞察");
  const message = escapeHtml(summary.message || "");
  const suggestion = escapeHtml(summary.suggestion || "");

  el.innerHTML = `
    <div class="d-flex flex-column gap-1">
      <div class="fw-bold">${title}</div>
      ${message ? `<div>${message}</div>` : ""}
      ${suggestion ? `<div class="text-muted">${suggestion}</div>` : ""}
    </div>
  `;
}

async function fetchInsight({ model, id, scene }) {
  const url = `/api/insight?model=${encodeURIComponent(model)}&id=${encodeURIComponent(
    String(id)
  )}&scene=${encodeURIComponent(scene)}`;

  const res = await fetch(url, {
    method: "GET",
    credentials: "include",
    headers: { Accept: "application/json" },
  });

  // Even on 403/400, try to parse JSON for a friendly message
  let payload = null;
  try {
    payload = await res.json();
  } catch (e) {
    payload = { ok: false, error: { message: `HTTP ${res.status}` } };
  }
  return payload;
}

function getCurrentRecordIdentity(defaultModel) {
  const p = parseHashParams();
  // Odoo form hash commonly includes: model=project.project&id=1&view_type=form
  const model = p.model || defaultModel || "project.project";
  const id = p.id ? parseInt(p.id, 10) : 0;
  return { model, id };
}

function ensureMounted() {
  const nodes = document.querySelectorAll(".sc_insight_mount");
  if (!nodes.length) return;

  for (const mount of nodes) {
    const scene = mount.dataset.scene || "project.entry";
    const defaultModel = mount.dataset.model || "project.project";
    const { model, id } = getCurrentRecordIdentity(defaultModel);

    // New record / unsaved: no id => cannot call API
    if (!id || Number.isNaN(id)) {
      mount.className = "alert alert-info sc-insight-banner";
      mount.innerHTML = `
        <div class="fw-bold">项目尚未保存</div>
        <div>保存后系统将生成“入口洞察”，并给出下一步建议。</div>
      `;
      continue;
    }

    // Avoid repeated fetches for same identity in quick DOM updates
    const key = `${model}:${id}:${scene}`;
    if (mount.dataset._lastKey === key) continue;
    mount.dataset._lastKey = key;

    // skeleton state
    mount.className = "alert alert-info sc-insight-banner";
    mount.innerHTML = `<div class="text-muted">正在生成系统洞察…</div>`;

    fetchInsight({ model, id, scene })
      .then((payload) => renderBanner(mount, payload))
      .catch(() => {
        renderBanner(mount, { ok: false, error: { message: "网络异常，无法获取系统洞察。" } });
      });
  }
}

// SPA: re-run on hash changes and DOM updates
function boot() {
  const start = () => {
    ensureMounted();

    window.addEventListener("hashchange", () => {
      // allow view switch to settle
      setTimeout(ensureMounted, 0);
    });

    // Mutation observer for Odoo client re-rendering form view
    if (document.body) {
      const obs = new MutationObserver(() => {
        // throttle-like behavior
        clearTimeout(window.__scInsightT);
        window.__scInsightT = setTimeout(ensureMounted, 50);
      });
      obs.observe(document.body, { childList: true, subtree: true });
    }
  };

  if (document.body) {
    start();
  } else {
    window.addEventListener("DOMContentLoaded", start, { once: true });
  }
}

boot();
