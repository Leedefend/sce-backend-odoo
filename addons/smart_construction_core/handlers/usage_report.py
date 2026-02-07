# -*- coding: utf-8 -*-
from __future__ import annotations

from collections import defaultdict

from odoo.addons.smart_core.core.base_handler import BaseIntentHandler


class UsageReportHandler(BaseIntentHandler):
    INTENT_TYPE = "usage.report"
    DESCRIPTION = "Usage analytics report for scene/capability"
    VERSION = "1.0.0"
    ETAG_ENABLED = False

    def handle(self, payload=None, ctx=None):
        params = payload or self.params or {}
        top_n = self._normalize_top(params.get("top"), default=10, max_value=30)

        user = self.env.user
        company = user.company_id if user else None
        Usage = self.env.get("sc.usage.counter")
        if not Usage or not company:
            return {"ok": True, "data": self._empty_report()}

        counters = Usage.sudo().search([("company_id", "=", company.id)])
        scene_total = 0
        capability_total = 0
        scene_counts = defaultdict(int)
        capability_counts = defaultdict(int)
        latest_updated_at = ""

        for rec in counters:
            key = str(rec.key or "")
            value = int(rec.value or 0)
            if key == "usage.scene_open.total":
                scene_total = value
            elif key.startswith("usage.scene_open."):
                scene_key = key[len("usage.scene_open."):]
                if scene_key and scene_key != "total":
                    scene_counts[scene_key] += value
            elif key == "usage.capability_open.total":
                capability_total = value
            elif key.startswith("usage.capability_open."):
                cap_key = key[len("usage.capability_open."):]
                if cap_key and cap_key != "total":
                    capability_counts[cap_key] += value
            if rec.updated_at and str(rec.updated_at) > latest_updated_at:
                latest_updated_at = str(rec.updated_at)

        data = {
            "generated_at": latest_updated_at,
            "totals": {
                "scene_open_total": scene_total,
                "capability_open_total": capability_total,
            },
            "scene_top": _top_items(scene_counts, top_n),
            "capability_top": _top_items(capability_counts, top_n),
        }
        return {"ok": True, "data": data, "meta": {"intent": self.INTENT_TYPE}}

    def _normalize_top(self, value, default=10, max_value=30):
        try:
            parsed = int(value)
        except Exception:
            return default
        return max(1, min(parsed, max_value))

    def _empty_report(self):
        return {
            "generated_at": "",
            "totals": {"scene_open_total": 0, "capability_open_total": 0},
            "scene_top": [],
            "capability_top": [],
        }


def _top_items(counter_map, top_n):
    items = [{"key": key, "count": int(value)} for key, value in counter_map.items()]
    items.sort(key=lambda item: item["count"], reverse=True)
    return items[:top_n]
