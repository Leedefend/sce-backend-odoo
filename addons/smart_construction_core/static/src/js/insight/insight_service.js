/** @odoo-module **/

import { registry } from "@web/core/registry";

window.__scInsightServiceLoaded = true;

function buildKey({ model, id, scene }) {
  return `${model}:${id}:${scene || ""}`;
}

export const insightService = {
  dependencies: ["user"],
  start(env, { user }) {
    const cache = new Map();
    const TTL_MS = 30000;

    async function fetchInsight({ model, id, scene }) {
      const url = `/api/insight?model=${encodeURIComponent(model)}&id=${encodeURIComponent(
        String(id)
      )}&scene=${encodeURIComponent(scene || "")}`;

      const res = await fetch(url, {
        method: "GET",
        credentials: "include",
        headers: { Accept: "application/json" },
      });

      let payload;
      try {
        payload = await res.json();
      } catch (err) {
        payload = { ok: false, error: { message: `HTTP ${res.status}` } };
      }
      return payload;
    }

    return {
      async get({ model, id, scene }) {
        if (!model || !id) {
          return { ok: false, error: { message: "missing identity" } };
        }
        const key = buildKey({ model, id, scene });
        const now = Date.now();
        const hit = cache.get(key);
        if (hit && now - hit.ts < TTL_MS) {
          return hit.payload;
        }
        const payload = await fetchInsight({ model, id, scene });
        cache.set(key, { ts: now, payload });
        return payload;
      },
      invalidate({ model, id, scene }) {
        if (!model) return;
        if (id && scene) {
          cache.delete(buildKey({ model, id, scene }));
          return;
        }
        for (const key of cache.keys()) {
          if (id) {
            if (key.startsWith(`${model}:${id}:`)) cache.delete(key);
          } else if (key.startsWith(`${model}:`)) {
            cache.delete(key);
          }
        }
      },
    };
  },
};

registry.category("services").add("sc_insight", insightService);
