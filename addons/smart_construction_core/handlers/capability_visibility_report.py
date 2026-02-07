# -*- coding: utf-8 -*-
from __future__ import annotations

from collections import defaultdict

from odoo.addons.smart_core.core.base_handler import BaseIntentHandler


class CapabilityVisibilityReportHandler(BaseIntentHandler):
    INTENT_TYPE = "capability.visibility.report"
    DESCRIPTION = "Capability visibility/lock report for current user"
    VERSION = "1.0.0"
    ETAG_ENABLED = False

    def handle(self, payload=None, ctx=None):
        user = self.env.user
        Cap = self.env.get("sc.capability")
        if not Cap:
            return {"ok": True, "data": self._empty_payload()}

        caps = Cap.sudo().search([("active", "=", True)], order="sequence, id")
        summary = {
            "total": len(caps),
            "visible": 0,
            "hidden": 0,
            "ready": 0,
            "preview": 0,
            "locked": 0,
        }
        reason_counts = defaultdict(int)
        hidden_samples = []

        for cap in caps:
            access = cap._access_context(user)
            visible = bool(access.get("visible"))
            state = str(access.get("state") or "")
            reason_code = str(access.get("reason_code") or "")

            if visible:
                summary["visible"] += 1
                if state == "READY":
                    summary["ready"] += 1
                elif state == "PREVIEW":
                    summary["preview"] += 1
                elif state == "LOCKED":
                    summary["locked"] += 1
            else:
                summary["hidden"] += 1
                if len(hidden_samples) < 20:
                    hidden_samples.append(
                        {
                            "key": cap.key,
                            "name": cap.name,
                            "reason_code": reason_code or "HIDDEN",
                            "reason": access.get("reason") or "",
                        }
                    )

            if reason_code:
                reason_counts[reason_code] += 1

        role_codes = sorted(list(Cap._role_codes_for_user(user)))
        data = {
            "user": {"id": user.id, "name": user.name, "login": user.login},
            "role_codes": role_codes,
            "summary": summary,
            "reason_counts": _to_ranked_list(reason_counts),
            "hidden_samples": hidden_samples,
        }
        return {"ok": True, "data": data, "meta": {"intent": self.INTENT_TYPE}}

    def _empty_payload(self):
        return {
            "user": {},
            "role_codes": [],
            "summary": {"total": 0, "visible": 0, "hidden": 0, "ready": 0, "preview": 0, "locked": 0},
            "reason_counts": [],
            "hidden_samples": [],
        }


def _to_ranked_list(counter_map):
    rows = [{"reason_code": key, "count": int(value)} for key, value in counter_map.items()]
    rows.sort(key=lambda row: row["count"], reverse=True)
    return rows
