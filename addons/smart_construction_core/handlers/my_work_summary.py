# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo import fields
from odoo.addons.smart_core.core.base_handler import BaseIntentHandler


class MyWorkSummaryHandler(BaseIntentHandler):
    INTENT_TYPE = "my.work.summary"
    DESCRIPTION = "Unified my-work summary for current user"
    VERSION = "1.0.0"
    ETAG_ENABLED = False
    SECTION_LABELS = {
        "todo": "待我处理",
        "owned": "我负责",
        "mentions": "@我的",
        "following": "我关注的",
    }

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

    def _normalize_limit(self, value, default=20, max_value=100):
        try:
            parsed = int(value)
        except Exception:
            parsed = default
        return max(1, min(parsed, max_value))

    def _append_items(self, target, section_key, rows):
        for row in rows:
            row["section"] = section_key
            row["section_label"] = self.SECTION_LABELS.get(section_key, section_key)
            target.append(row)

    def _load_todo_items(self, user, limit):
        Activity = self.env.get("mail.activity")
        if not Activity:
            return []
        required = ("user_id", "res_model", "res_id")
        if not all(field in Activity._fields for field in required):
            return []
        rows = []
        try:
            records = Activity.search([("user_id", "=", user.id)], order="date_deadline asc, id desc", limit=limit)
            for rec in records:
                rows.append({
                    "id": rec.id,
                    "title": rec.summary or rec.activity_type_id.name or rec.res_model,
                    "model": rec.res_model,
                    "record_id": rec.res_id,
                    "deadline": fields.Date.to_string(rec.date_deadline) if rec.date_deadline else "",
                    "scene_key": self._scene_for_model(rec.res_model),
                    "source": "mail.activity",
                })
        except Exception:
            return []
        return rows

    def _load_owned_items(self, user, limit):
        Project = self.env.get("project.project")
        if not Project:
            return []
        if not all(field in Project._fields for field in ("user_id", "name")):
            return []
        rows = []
        try:
            records = Project.search([("user_id", "=", user.id)], order="write_date desc, id desc", limit=limit)
            for rec in records:
                rows.append({
                    "id": rec.id,
                    "title": rec.name or ("project.project#%s" % rec.id),
                    "model": "project.project",
                    "record_id": rec.id,
                    "deadline": "",
                    "scene_key": self._scene_for_model("project.project"),
                    "source": "project.project",
                })
        except Exception:
            return []
        return rows

    def _load_mention_items(self, partner, limit):
        Message = self.env.get("mail.message")
        if not Message:
            return []
        if not all(field in Message._fields for field in ("partner_ids", "model", "res_id")):
            return []
        rows = []
        try:
            records = Message.search([("partner_ids", "in", partner.id)], order="date desc, id desc", limit=limit)
            for rec in records:
                model = rec.model or ""
                record_id = int(rec.res_id or 0)
                rows.append({
                    "id": rec.id,
                    "title": rec.subject or (rec.record_name or model or ("mail.message#%s" % rec.id)),
                    "model": model,
                    "record_id": record_id,
                    "deadline": "",
                    "scene_key": self._scene_for_model(model),
                    "source": "mail.message",
                })
        except Exception:
            return []
        return rows

    def _load_following_items(self, partner, limit):
        Follower = self.env.get("mail.followers")
        if not Follower:
            return []
        if not all(field in Follower._fields for field in ("partner_id", "res_model", "res_id")):
            return []
        rows = []
        try:
            records = Follower.search([("partner_id", "=", partner.id)], order="id desc", limit=limit)
            for rec in records:
                model = rec.res_model or ""
                rows.append({
                    "id": rec.id,
                    "title": model or ("mail.followers#%s" % rec.id),
                    "model": model,
                    "record_id": int(rec.res_id or 0),
                    "deadline": "",
                    "scene_key": self._scene_for_model(model),
                    "source": "mail.followers",
                })
        except Exception:
            return []
        return rows

    def handle(self, payload=None, ctx=None):
        params = payload or self.params or {}
        user = self.env.user
        partner = user.partner_id
        limit = self._normalize_limit(params.get("limit"), default=20, max_value=100)
        limit_each = self._normalize_limit(params.get("limit_each"), default=8, max_value=40)

        todo_count = self._safe_count("mail.activity", [("user_id", "=", user.id)], ["user_id"])
        responsible_count = self._safe_count("project.project", [("user_id", "=", user.id)], ["user_id"])
        mentioned_count = self._safe_count("mail.message", [("partner_ids", "in", partner.id)], ["partner_ids"])
        following_count = self._safe_count("mail.followers", [("partner_id", "=", partner.id)], ["partner_id"])

        items = []
        self._append_items(items, "todo", self._load_todo_items(user, limit_each))
        self._append_items(items, "owned", self._load_owned_items(user, limit_each))
        self._append_items(items, "mentions", self._load_mention_items(partner, limit_each))
        self._append_items(items, "following", self._load_following_items(partner, limit_each))
        items = items[:limit]

        data = {
            "generated_at": fields.Datetime.now(),
            "sections": [
                {"key": "todo", "label": self.SECTION_LABELS["todo"], "scene_key": "projects.list"},
                {"key": "owned", "label": self.SECTION_LABELS["owned"], "scene_key": "projects.list"},
                {"key": "mentions", "label": self.SECTION_LABELS["mentions"], "scene_key": "projects.list"},
                {"key": "following", "label": self.SECTION_LABELS["following"], "scene_key": "projects.list"},
            ],
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
