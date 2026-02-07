# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo import fields
from odoo.addons.smart_core.core.base_handler import BaseIntentHandler


class MyWorkSummaryHandler(BaseIntentHandler):
    INTENT_TYPE = "my.work.summary"
    DESCRIPTION = "Unified my-work summary for current user"
    VERSION = "1.0.0"
    ETAG_ENABLED = False

    def _safe_count(self, model_name, domain, required_fields=None):
        Model = self.env.get(model_name)
        if not Model:
            return 0
        fields_ok = all(field in Model._fields for field in (required_fields or []))
        if not fields_ok:
            return 0
        try:
            return int(Model.search_count(domain))
        except Exception:
            return 0

    def _scene_for_model(self, model_name):
        mapping = {
            "project.project": "projects.list",
            "project.task": "projects.list",
            "sale.order": "contracts.list",
            "account.move": "finance.vouchers.list",
        }
        return mapping.get(model_name, "projects.list")

    def handle(self, payload=None, ctx=None):
        params = payload or self.params or {}
        user = self.env.user
        partner = user.partner_id
        limit = int(params.get("limit") or 20)
        limit = max(1, min(limit, 100))

        todo_count = self._safe_count("mail.activity", [("user_id", "=", user.id)], ["user_id"])
        responsible_count = self._safe_count("project.project", [("user_id", "=", user.id)], ["user_id"])
        mentioned_count = self._safe_count("mail.message", [("partner_ids", "in", partner.id)], ["partner_ids"])
        following_count = self._safe_count("mail.followers", [("partner_id", "=", partner.id)], ["partner_id"])

        Activity = self.env.get("mail.activity")
        items = []
        if Activity and all(field in Activity._fields for field in ("user_id", "res_model", "res_id", "date_deadline")):
            try:
                records = Activity.search([("user_id", "=", user.id)], order="date_deadline asc, id desc", limit=limit)
                for rec in records:
                    item = {
                        "id": rec.id,
                        "title": rec.summary or rec.activity_type_id.name or rec.res_model,
                        "model": rec.res_model,
                        "record_id": rec.res_id,
                        "deadline": fields.Date.to_string(rec.date_deadline) if rec.date_deadline else "",
                        "scene_key": self._scene_for_model(rec.res_model),
                    }
                    items.append(item)
            except Exception:
                items = []

        data = {
            "generated_at": fields.Datetime.now(),
            "summary": [
                {"key": "todo", "label": "待我处理", "count": todo_count, "scene_key": "projects.list"},
                {"key": "owned", "label": "我负责", "count": responsible_count, "scene_key": "projects.list"},
                {"key": "mentions", "label": "@我的", "count": mentioned_count, "scene_key": "projects.list"},
                {"key": "following", "label": "我关注的", "count": following_count, "scene_key": "projects.list"},
            ],
            "items": items,
        }
        meta = {"intent": self.INTENT_TYPE}
        return {"ok": True, "data": data, "meta": meta}
