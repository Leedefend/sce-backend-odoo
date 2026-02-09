# -*- coding: utf-8 -*-
from __future__ import annotations

import re

from odoo import fields
from odoo.addons.smart_core.core.base_handler import BaseIntentHandler
from odoo.addons.smart_core.utils.reason_codes import (
    REASON_FILTER_NO_MATCH,
    REASON_NO_WORK_ITEMS,
    REASON_OK,
)


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
    SECTION_KEYS = ("todo", "owned", "mentions", "following")
    STATUS_READY = "READY"
    STATUS_EMPTY = "EMPTY"
    STATUS_FILTER_EMPTY = "FILTER_EMPTY"
    SORT_FIELDS = {"id", "title", "model", "deadline", "source", "reason_code", "section"}

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

    def _normalize_page(self, value, default=1, max_value=10000):
        try:
            parsed = int(value)
        except Exception:
            parsed = default
        return max(1, min(parsed, max_value))

    def _normalize_sort_by(self, value):
        key = str(value or "").strip().lower()
        return key if key in self.SORT_FIELDS else "id"

    def _normalize_sort_dir(self, value):
        direction = str(value or "").strip().lower()
        return direction if direction in {"asc", "desc"} else "desc"

    def _append_items(self, target, section_key, rows):
        for row in rows:
            row["section"] = section_key
            row["section_label"] = self.SECTION_LABELS.get(section_key, section_key)
            target.append(row)

    def _build_facets(self, items):
        source_counts = {}
        reason_counts = {}
        section_counts = {}
        for item in items or []:
            source = str(item.get("source") or "").strip()
            reason = str(item.get("reason_code") or "").strip()
            section = str(item.get("section") or "").strip()
            if source:
                source_counts[source] = int(source_counts.get(source, 0)) + 1
            if reason:
                reason_counts[reason] = int(reason_counts.get(reason, 0)) + 1
            if section:
                section_counts[section] = int(section_counts.get(section, 0)) + 1
        return {
            "source_counts": _ranked_counts(source_counts),
            "reason_code_counts": _ranked_counts(reason_counts),
            "section_counts": _ranked_counts(section_counts),
        }

    def _normalize_section(self, value):
        section = str(value or "").strip().lower()
        return section if section in self.SECTION_KEYS else "all"

    def _normalize_text(self, value):
        return str(value or "").strip().lower()

    def _build_status(self, *, total_before_filter, filtered_count):
        if total_before_filter <= 0:
            return {
                "state": self.STATUS_EMPTY,
                "reason_code": REASON_NO_WORK_ITEMS,
                "message": "当前没有待处理事项",
                "hint": "可稍后刷新，或切换到其他场景创建/关注事项。",
            }
        if filtered_count <= 0:
            return {
                "state": self.STATUS_FILTER_EMPTY,
                "reason_code": REASON_FILTER_NO_MATCH,
                "message": "当前筛选条件没有匹配结果",
                "hint": "请重置筛选条件后重试。",
            }
        return {
            "state": self.STATUS_READY,
            "reason_code": REASON_OK,
            "message": "",
            "hint": "",
        }

    def _apply_filters(self, items, *, section, source, reason_code, search):
        result = list(items or [])
        if section and section != "all":
            result = [item for item in result if str(item.get("section") or "") == section]
        if source and source != "all":
            result = [item for item in result if str(item.get("source") or "") == source]
        if reason_code and reason_code != "all":
            result = [item for item in result if str(item.get("reason_code") or "") == reason_code]
        if search:
            result = [
                item
                for item in result
                if search in " ".join(
                    [
                        str(item.get("title") or ""),
                        str(item.get("model") or ""),
                        str(item.get("action_label") or ""),
                        str(item.get("reason_code") or ""),
                    ]
                ).lower()
            ]
        return result

    def _sort_value(self, item, sort_by):
        if sort_by in {"id"}:
            return int(item.get("id") or 0)
        text = str(item.get(sort_by) or "").lower()
        # Keep empty deadlines at the end for ASC and DESC.
        if sort_by == "deadline":
            return (text == "", text)
        return text

    def _apply_sort(self, items, *, sort_by, sort_dir):
        reverse = sort_dir == "desc"
        return sorted(list(items or []), key=lambda item: self._sort_value(item, sort_by), reverse=reverse)

    def _paginate_items(self, items, *, page, page_size):
        rows = list(items or [])
        total = len(rows)
        total_pages = max(1, (total + page_size - 1) // page_size)
        safe_page = min(page, total_pages)
        offset = (safe_page - 1) * page_size
        return rows[offset : offset + page_size], total_pages, safe_page

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
                followup = self._parse_followup_note(rec.note or "")
                rows.append({
                    "id": rec.id,
                    "title": rec.summary or rec.activity_type_id.name or rec.res_model,
                    "model": rec.res_model,
                    "record_id": rec.res_id,
                    "deadline": fields.Date.to_string(rec.date_deadline) if rec.date_deadline else "",
                    "scene_key": self._scene_for_model(rec.res_model),
                    "source": "mail.activity",
                    "action_label": followup.get("action_label") or "",
                    "action_key": followup.get("action_key") or "",
                    "reason_code": followup.get("reason_code") or "",
                })
        except Exception:
            return []
        return rows

    def _parse_followup_note(self, note_text):
        first_line = str(note_text or "").splitlines()[0] if note_text else ""
        if not first_line.startswith("SC_FOLLOWUP"):
            # 兼容早期 note: "...reason=OK"
            reason_match = re.search(r"reason=([A-Z0-9_]+)", str(note_text or ""))
            return {"reason_code": reason_match.group(1) if reason_match else ""}
        result = {}
        for key in ("action_key", "action_label", "reason_code"):
            match = re.search(rf"{key}=([^ ]+)", first_line)
            if match:
                result[key] = match.group(1)
        return result

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
        page = self._normalize_page(params.get("page"), default=1)
        page_size = self._normalize_limit(params.get("page_size"), default=limit, max_value=100)
        sort_by = self._normalize_sort_by(params.get("sort_by"))
        sort_dir = self._normalize_sort_dir(params.get("sort_dir"))
        filter_section = self._normalize_section(params.get("section"))
        filter_source = self._normalize_text(params.get("source")) or "all"
        filter_reason_code = str(params.get("reason_code") or "").strip()
        filter_reason_code = filter_reason_code if filter_reason_code else "all"
        filter_search = self._normalize_text(params.get("search"))

        todo_count = self._safe_count("mail.activity", [("user_id", "=", user.id)], ["user_id"])
        responsible_count = self._safe_count("project.project", [("user_id", "=", user.id)], ["user_id"])
        mentioned_count = self._safe_count("mail.message", [("partner_ids", "in", partner.id)], ["partner_ids"])
        following_count = self._safe_count("mail.followers", [("partner_id", "=", partner.id)], ["partner_id"])

        items = []
        self._append_items(items, "todo", self._load_todo_items(user, limit_each))
        self._append_items(items, "owned", self._load_owned_items(user, limit_each))
        self._append_items(items, "mentions", self._load_mention_items(partner, limit_each))
        self._append_items(items, "following", self._load_following_items(partner, limit_each))
        total_before_filter = len(items)
        facets = self._build_facets(items)
        items = self._apply_filters(
            items,
            section=filter_section,
            source=filter_source,
            reason_code=filter_reason_code,
            search=filter_search,
        )
        filtered_count = len(items)
        items = self._apply_sort(items, sort_by=sort_by, sort_dir=sort_dir)
        items, total_pages, page = self._paginate_items(items, page=page, page_size=page_size)

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
            "facets": facets,
            "filters": {
                "section": filter_section,
                "source": filter_source,
                "reason_code": filter_reason_code,
                "search": filter_search,
                "filtered_count": filtered_count,
                "total_before_filter": total_before_filter,
                "sort_by": sort_by,
                "sort_dir": sort_dir,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
            },
            "status": self._build_status(
                total_before_filter=total_before_filter,
                filtered_count=filtered_count,
            ),
        }
        meta = {"intent": self.INTENT_TYPE}
        return {"ok": True, "data": data, "meta": meta}


def _ranked_counts(counter_map):
    rows = [{"key": key, "count": int(value)} for key, value in (counter_map or {}).items()]
    rows.sort(key=lambda row: row["count"], reverse=True)
    return rows
