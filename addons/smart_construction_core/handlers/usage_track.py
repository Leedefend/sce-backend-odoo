# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo import fields
from odoo.addons.smart_core.core.base_handler import BaseIntentHandler


class UsageTrackHandler(BaseIntentHandler):
    INTENT_TYPE = "usage.track"
    DESCRIPTION = "Track scene/capability usage counters"
    VERSION = "1.0.0"
    ETAG_ENABLED = False

    def _bump(self, usage_model, company, key):
        if not usage_model or not company or not key:
            return
        usage_model.sudo().bump(company, key, 1)

    def _day_key(self):
        return fields.Date.context_today(self.env.user).strftime("%Y-%m-%d")

    def handle(self, payload=None, ctx=None):
        params = payload or self.params or {}
        event_type = str(params.get("event_type") or "").strip().lower()
        scene_key = str(params.get("scene_key") or "").strip()
        capability_key = str(params.get("capability_key") or "").strip()

        user = self.env.user
        company = user.company_id if user else None
        Usage = self.env.get("sc.usage.counter")

        tracked = []
        day_key = self._day_key()
        if event_type == "scene_open" and scene_key:
            self._bump(Usage, company, "usage.scene_open.total")
            self._bump(Usage, company, f"usage.scene_open.{scene_key}")
            self._bump(Usage, company, f"usage.scene_open.daily.{day_key}")
            tracked.extend([
                "usage.scene_open.total",
                f"usage.scene_open.{scene_key}",
                f"usage.scene_open.daily.{day_key}",
            ])
        elif event_type == "capability_open" and capability_key:
            self._bump(Usage, company, "usage.capability_open.total")
            self._bump(Usage, company, f"usage.capability_open.{capability_key}")
            self._bump(Usage, company, f"usage.capability_open.daily.{day_key}")
            tracked.extend([
                "usage.capability_open.total",
                f"usage.capability_open.{capability_key}",
                f"usage.capability_open.daily.{day_key}",
            ])
        else:
            return {"ok": False, "error": {"code": 400, "message": "invalid usage params"}}

        return {"ok": True, "data": {"tracked": tracked, "event_type": event_type}, "meta": {"intent": self.INTENT_TYPE}}
