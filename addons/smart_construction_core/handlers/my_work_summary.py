# -*- coding: utf-8 -*-
from __future__ import annotations

import re

from odoo import fields
from odoo.addons.smart_core.core.base_handler import BaseIntentHandler
from odoo.addons.smart_core.utils.reason_codes import (
    REASON_ACTIVITY_PENDING,
    REASON_FILTER_NO_MATCH,
    REASON_FOLLOWING,
    REASON_MENTIONED,
    REASON_NO_WORK_ITEMS,
    REASON_OK,
    REASON_PROJECT_HEALTH_RISK,
    REASON_PROJECT_HEALTH_WARN,
    REASON_RESPONSIBLE_OWNER,
    REASON_TASK_ASSIGNED,
    REASON_TIER_REVIEW_PENDING,
    REASON_WORKFLOW_PENDING,
)
from odoo.addons.smart_construction_core.services.my_work_aggregate_service import WorkItemAggregateService
from odoo.exceptions import AccessError
from odoo.addons.smart_construction_core.services.project_execution_item_projection_service import (
    ProjectExecutionItemProjectionService,
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
    SORT_FIELDS = WorkItemAggregateService.SORT_FIELDS
    SOURCE_LABELS = {
        "mail.activity": "待办提醒",
        "tier.review": "审批复核",
        "sc.workflow.workitem": "流程待办",
        "project.task": "项目任务",
        "project.risk": "项目风险",
        "project.project": "负责项目",
        "construction.contract": "合同执行事项",
        "payment.request": "付款执行事项",
        "sc.settlement.order": "结算执行事项",
    }

    def _get_model(self, model_name, *, sudo=False):
        try:
            model = self.env[model_name]
            return model.sudo() if sudo else model
        except Exception:
            return None

    def _safe_count(self, model_name, domain, required_fields=None):
        # Aggregate counts with sudo while keeping user-scoped domain conditions.
        Model = self._get_model(model_name, sudo=True)
        if Model is None:
            return 0
        fields_ok = all(field in Model._fields for field in (required_fields or []))
        if not fields_ok:
            return 0
        try:
            return int(Model.search_count(domain))
        except Exception:
            return 0

    def _read_access_state(self, model_name):
        Model = self._get_model(model_name)
        if Model is None:
            return {"model": model_name, "readable": False, "reason": "MODEL_UNAVAILABLE"}
        try:
            if not bool(Model.check_access_rights("read", raise_exception=False)):
                return {"model": model_name, "readable": False, "reason": "READ_ACCESS_DENIED"}
            return {"model": model_name, "readable": True, "reason": ""}
        except AccessError:
            return {"model": model_name, "readable": False, "reason": "READ_ACCESS_DENIED"}
        except Exception:
            return {"model": model_name, "readable": False, "reason": "ACCESS_CHECK_FAILED"}

    def _scene_for_model(self, model_name):
        mapping = {
            "project.project": "projects.list",
            "project.task": "projects.list",
            "payment.request": "finance.payment_requests",
            "construction.contract": "contracts.list",
            "sc.settlement.order": "settlement",
            "sc.workflow.instance": "projects.list",
            "sale.order": "contracts.list",
            "account.move": "finance.vouchers.list",
        }
        return mapping.get(model_name, "projects.list")

    def _resolve_action_context_for_model(self, model_name):
        model = str(model_name or "").strip()
        if not model:
            return {}
        cache = getattr(self, "_mw_action_context_cache", None)
        if cache is None:
            cache = {}
            setattr(self, "_mw_action_context_cache", cache)
        if model in cache:
            return cache[model]
        result = {}
        try:
            Action = self._get_model("ir.actions.act_window", sudo=True)
            Menu = self._get_model("ir.ui.menu", sudo=True)
            if Action is not None:
                action = Action.search([("res_model", "=", model)], order="id asc", limit=1)
                if action:
                    result["action_id"] = int(action.id)
                    if Menu is not None:
                        action_ref = "ir.actions.act_window,%s" % action.id
                        menu = Menu.search([("action", "=", action_ref)], order="id asc", limit=1)
                        if menu:
                            result["menu_id"] = int(menu.id)
        except Exception:
            result = {}
        cache[model] = result
        return result

    def _attach_targets(self, rows):
        attached = list(rows or [])
        for row in attached:
            model = str(row.get("model") or "").strip()
            record_id = self._coerce_record_id(row.get("record_id"))
            scene_key = str(row.get("scene_key") or self._scene_for_model(model)).strip() or "projects.list"
            target = {
                "kind": "record" if model and record_id else "scene",
                "scene_key": scene_key,
            }
            if model:
                target["model"] = model
            if record_id:
                target["record_id"] = record_id
            action_ctx = self._resolve_action_context_for_model(model)
            action_id = int(action_ctx.get("action_id") or 0)
            menu_id = int(action_ctx.get("menu_id") or 0)
            if action_id > 0:
                target["action_id"] = action_id
            if menu_id > 0:
                target["menu_id"] = menu_id
            row["target"] = target
            row.setdefault("source_label", self._source_label(row))
            row.setdefault("project_name", self._row_project_name(model, record_id, row))
            row.setdefault("action_summary", self._action_summary(row))
        return attached

    def _source_label(self, row):
        source = str(row.get("source") or "").strip()
        model = str(row.get("model") or "").strip()
        return self.SOURCE_LABELS.get(source) or self.SOURCE_LABELS.get(model) or source or model or "执行事项"

    def _row_project_name(self, model_name, record_id, row):
        existing = str(row.get("project_name") or "").strip()
        if existing:
            return existing
        model = str(model_name or "").strip()
        rid = int(record_id or 0)
        if not model or not rid:
            return ""
        Model = self._get_model(model, sudo=True)
        if Model is None:
            return ""
        try:
            rec = Model.browse(rid).exists()
            if not rec:
                return ""
            project = getattr(rec, "project_id", False)
            return str(getattr(project, "display_name", "") or getattr(project, "name", "") or "").strip()
        except Exception:
            return ""

    def _action_summary(self, row):
        label = str(row.get("action_label") or "").strip()
        if label:
            return label
        reason = str(row.get("reason_code") or "").strip()
        if reason:
            return reason
        return "进入处理"

    def _coerce_record_id(self, raw):
        value = raw
        if hasattr(value, "id"):
            value = value.id
        try:
            return int(value or 0)
        except Exception:
            return 0

    def _safe_record_title(self, model_name, record_id, fallback):
        model = str(model_name or "").strip()
        rid = int(record_id or 0)
        if not model or not rid:
            return fallback
        Model = self._get_model(model, sudo=True)
        if Model is None:
            return fallback
        try:
            rec = Model.browse(rid).exists()
            if rec:
                return rec.display_name or fallback
        except Exception:
            return fallback
        return fallback

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
        WorkItemAggregateService.append_items(
            target,
            section_key=section_key,
            section_label=self.SECTION_LABELS.get(section_key, section_key),
            rows=rows,
        )

    def _build_facets(self, items):
        return WorkItemAggregateService.build_facets(items)

    def _normalize_section(self, value):
        section = str(value or "").strip().lower()
        return section if section in self.SECTION_KEYS else "all"

    def _normalize_text(self, value):
        return str(value or "").strip().lower()

    def _or_domain(self, clauses):
        valid = [clause for clause in (clauses or []) if clause]
        if not valid:
            return []
        if len(valid) == 1:
            return [valid[0]]
        # Odoo domain OR: prefix with N-1 "|" operators for N clauses.
        return (["|"] * (len(valid) - 1)) + valid

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
        return WorkItemAggregateService.apply_filters(
            items,
            section=section,
            source=source,
            reason_code=reason_code,
            search=search,
        )

    def _apply_sort(self, items, *, sort_by, sort_dir):
        return WorkItemAggregateService.apply_sort(items, sort_by=sort_by, sort_dir=sort_dir)

    def _paginate_items(self, items, *, page, page_size):
        return WorkItemAggregateService.paginate(items, page=page, page_size=page_size)

    def _load_todo_items(self, user, limit):
        Activity = self._get_model("mail.activity", sudo=True)
        if Activity is None:
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
                    "reason_code": followup.get("reason_code") or REASON_ACTIVITY_PENDING,
                    "priority": "medium",
                })
        except Exception:
            return []
        return self._attach_targets(rows)

    def _tier_review_domain(self, user):
        TierReview = self._get_model("tier.review", sudo=True)
        if TierReview is None:
            return None
        fields_map = TierReview._fields
        if "status" not in fields_map:
            return None
        domain = [("status", "=", "pending")]
        if "can_review" in fields_map:
            domain.append(("can_review", "=", True))
        if "reviewer_ids" in fields_map:
            domain.append(("reviewer_ids", "in", user.id))
        elif "reviewer_id" in fields_map:
            domain.append(("reviewer_id", "=", user.id))
        else:
            return None
        return domain

    def _load_tier_review_items(self, user, limit):
        TierReview = self._get_model("tier.review", sudo=True)
        domain = self._tier_review_domain(user)
        if TierReview is None or not domain:
            return []
        required = ("model", "res_id")
        if not all(field in TierReview._fields for field in required):
            return []
        rows = []
        try:
            records = TierReview.search(domain, order="id desc", limit=limit)
            for rec in records:
                model = str(rec.model or "").strip()
                record_id = self._coerce_record_id(rec.res_id)
                fallback = f"{model}#{record_id}" if model and record_id else (rec.name or f"tier.review#{rec.id}")
                rows.append({
                    "id": rec.id,
                    "title": self._safe_record_title(model, record_id, fallback),
                    "model": model,
                    "record_id": record_id,
                    "deadline": "",
                    "scene_key": self._scene_for_model(model),
                    "source": "tier.review",
                    "action_label": "审批处理",
                    "action_key": "tier.review.approve",
                    "reason_code": REASON_TIER_REVIEW_PENDING,
                    "priority": "high",
                })
        except Exception:
            return []
        return self._attach_targets(rows)

    def _workflow_todo_domain(self, user):
        Workitem = self._get_model("sc.workflow.workitem", sudo=True)
        if Workitem is None:
            return None
        required = ("status", "assignee_group_id", "assignee_id")
        if not all(field in Workitem._fields for field in required):
            return None
        return [
            ("status", "=", "todo"),
            "|",
            ("assignee_id", "=", user.id),
            ("assignee_group_id", "in", user.groups_id.ids),
        ]

    def _load_workflow_todo_items(self, user, limit):
        Workitem = self._get_model("sc.workflow.workitem", sudo=True)
        domain = self._workflow_todo_domain(user)
        if Workitem is None or not domain:
            return []
        required = ("instance_id", "node_id")
        if not all(field in Workitem._fields for field in required):
            return []
        rows = []
        try:
            records = Workitem.search(domain, order="created_at desc, id desc", limit=limit)
            for rec in records:
                instance = rec.instance_id
                model = str(getattr(instance, "model_name", "") or "").strip()
                record_id = self._coerce_record_id(getattr(instance, "res_id", 0))
                node_name = str(getattr(rec.node_id, "name", "") or "").strip()
                fallback = f"{instance.name or model} · {node_name or '待审批'}"
                rows.append({
                    "id": rec.id,
                    "title": self._safe_record_title(model, record_id, fallback),
                    "model": model,
                    "record_id": record_id,
                    "deadline": "",
                    "scene_key": self._scene_for_model(model),
                    "source": "sc.workflow.workitem",
                    "action_label": node_name or "流程处理",
                    "action_key": "sc.workflow.approve",
                    "reason_code": REASON_WORKFLOW_PENDING,
                    "priority": "high",
                })
        except Exception:
            return []
        return self._attach_targets(rows)

    def _task_domain_for_user(self, user):
        Task = self._get_model("project.task", sudo=True)
        if Task is None:
            return None
        fields_map = Task._fields
        if "user_ids" in fields_map:
            return [("user_ids", "in", user.id)]
        if "user_id" in fields_map:
            return [("user_id", "=", user.id)]
        return None

    def _load_task_items(self, user, limit):
        Task = self._get_model("project.task", sudo=True)
        domain = self._task_domain_for_user(user)
        if Task is None or not domain:
            return []
        rows = []
        try:
            records = Task.search(domain, order="date_deadline asc, id desc", limit=limit)
            for rec in records:
                rows.append({
                    "id": rec.id,
                    "title": rec.name or f"project.task#{rec.id}",
                    "model": "project.task",
                    "record_id": rec.id,
                    "deadline": fields.Date.to_string(rec.date_deadline) if getattr(rec, "date_deadline", False) else "",
                    "scene_key": self._scene_for_model("project.task"),
                    "source": "project.task",
                    "action_label": "任务处理",
                    "action_key": "project.task.open",
                    "reason_code": REASON_TASK_ASSIGNED,
                    "priority": "medium",
                })
        except Exception:
            return []
        return self._attach_targets(rows)

    def _load_project_execution_items(self, user, limit):
        try:
            service = ProjectExecutionItemProjectionService(self.env)
            rows = service.user_items(user, limit=limit)
        except Exception:
            rows = []
        return self._attach_targets(rows)

    def _project_risk_domain_for_user(self, user):
        Project = self._get_model("project.project", sudo=True)
        if Project is None:
            return None
        if "health_state" not in Project._fields:
            return None
        base = [("health_state", "in", ["risk", "warn"])]
        responsible = self._project_responsible_domain(user)
        return base + responsible if responsible else base

    def _project_responsible_domain(self, user):
        Project = self._get_model("project.project", sudo=True)
        if Project is None:
            return []
        fields_map = Project._fields
        clauses = []
        if "user_id" in fields_map:
            clauses.append(("user_id", "=", user.id))
        if "manager_id" in fields_map:
            clauses.append(("manager_id", "=", user.id))
        if "cost_manager_id" in fields_map:
            clauses.append(("cost_manager_id", "=", user.id))
        if "doc_manager_id" in fields_map:
            clauses.append(("doc_manager_id", "=", user.id))
        return self._or_domain(clauses)

    def _load_project_risk_items(self, user, limit):
        Project = self._get_model("project.project", sudo=True)
        domain = self._project_risk_domain_for_user(user)
        if Project is None or not domain:
            return []
        rows = []
        try:
            records = Project.search(domain, order="write_date desc, id desc", limit=limit)
            for rec in records:
                health_state = str(getattr(rec, "health_state", "") or "").strip().lower()
                reason_code = REASON_PROJECT_HEALTH_RISK if health_state == "risk" else REASON_PROJECT_HEALTH_WARN
                rows.append({
                    "id": rec.id,
                    "title": rec.name or f"project.project#{rec.id}",
                    "model": "project.project",
                    "record_id": rec.id,
                    "deadline": "",
                    "scene_key": self._scene_for_model("project.project"),
                    "source": "project.risk",
                    "action_label": "风险处理",
                    "action_key": "project.risk.resolve",
                    "reason_code": reason_code,
                    "priority": "high" if health_state == "risk" else "medium",
                })
        except Exception:
            return []
        return self._attach_targets(rows)

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
        Project = self._get_model("project.project", sudo=True)
        if Project is None:
            return []
        if "name" not in Project._fields:
            return []
        domain = self._project_responsible_domain(user)
        if not domain:
            return []
        rows = []
        try:
            records = Project.search(domain, order="write_date desc, id desc", limit=limit)
            for rec in records:
                rows.append({
                    "id": rec.id,
                    "title": rec.name or ("project.project#%s" % rec.id),
                    "model": "project.project",
                    "record_id": rec.id,
                    "deadline": "",
                    "scene_key": self._scene_for_model("project.project"),
                    "source": "project.project",
                    "reason_code": REASON_RESPONSIBLE_OWNER,
                    "priority": "medium",
                })
        except Exception:
            return []
        return self._attach_targets(rows)

    def _load_mention_items(self, partner, limit):
        Message = self._get_model("mail.message", sudo=True)
        if Message is None:
            return []
        if not all(field in Message._fields for field in ("partner_ids", "model", "res_id")):
            return []
        rows = []
        try:
            records = Message.search([("partner_ids", "in", partner.id)], order="date desc, id desc", limit=limit)
            for rec in records:
                model = rec.model or ""
                record_id = int(rec.res_id or 0)
                fallback_title = rec.subject or (rec.record_name or model or ("mail.message#%s" % rec.id))
                rows.append({
                    "id": rec.id,
                    "title": self._safe_record_title(model, record_id, fallback_title),
                    "model": model,
                    "record_id": record_id,
                    "deadline": "",
                    "scene_key": self._scene_for_model(model),
                    "source": "mail.message",
                    "reason_code": REASON_MENTIONED,
                    "priority": "low",
                })
        except Exception:
            return []
        return self._attach_targets(rows)

    def _load_following_items(self, partner, limit):
        Follower = self._get_model("mail.followers", sudo=True)
        if Follower is None:
            return []
        if not all(field in Follower._fields for field in ("partner_id", "res_model", "res_id")):
            return []
        rows = []
        try:
            records = Follower.search([("partner_id", "=", partner.id)], order="id desc", limit=limit)
            for rec in records:
                model = rec.res_model or ""
                record_id = int(rec.res_id or 0)
                rows.append({
                    "id": rec.id,
                    "title": self._safe_record_title(model, record_id, model or ("mail.followers#%s" % rec.id)),
                    "model": model,
                    "record_id": record_id,
                    "deadline": "",
                    "scene_key": self._scene_for_model(model),
                    "source": "mail.followers",
                    "reason_code": REASON_FOLLOWING,
                    "priority": "low",
                })
        except Exception:
            return []
        return self._attach_targets(rows)

    def handle(self, payload=None, ctx=None):
        raw_payload = payload or self.params or {}
        params = raw_payload.get("params") if isinstance(raw_payload, dict) and isinstance(raw_payload.get("params"), dict) else raw_payload
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

        mail_todo_count = self._safe_count("mail.activity", [("user_id", "=", user.id)], ["user_id"])
        tier_review_count = self._safe_count("tier.review", self._tier_review_domain(user) or [("id", "=", -1)], ["status"])
        workflow_todo_count = self._safe_count(
            "sc.workflow.workitem",
            self._workflow_todo_domain(user) or [("id", "=", -1)],
            ["status", "assignee_group_id", "assignee_id"],
        )
        task_todo_count = self._safe_count(
            "project.task",
            self._task_domain_for_user(user) or [("id", "=", -1)],
            ["id"],
        )
        projected_execution_count = len(self._load_project_execution_items(user, limit_each))
        risk_todo_count = self._safe_count(
            "project.project",
            self._project_risk_domain_for_user(user) or [("id", "=", -1)],
            ["health_state"],
        )
        todo_count = int(
            mail_todo_count
            + tier_review_count
            + workflow_todo_count
            + task_todo_count
            + projected_execution_count
            + risk_todo_count
        )
        project_responsible_domain = self._project_responsible_domain(user)
        responsible_count = self._safe_count(
            "project.project",
            project_responsible_domain or [("id", "=", -1)],
            ["id"],
        )
        mentioned_count = self._safe_count("mail.message", [("partner_ids", "in", partner.id)], ["partner_ids"])
        following_count = self._safe_count("mail.followers", [("partner_id", "=", partner.id)], ["partner_id"])

        items = []
        self._append_items(items, "todo", self._load_todo_items(user, limit_each))
        self._append_items(items, "todo", self._load_tier_review_items(user, limit_each))
        self._append_items(items, "todo", self._load_workflow_todo_items(user, limit_each))
        self._append_items(items, "todo", self._load_task_items(user, limit_each))
        self._append_items(items, "todo", self._load_project_execution_items(user, limit_each))
        self._append_items(items, "todo", self._load_project_risk_items(user, limit_each))
        self._append_items(items, "owned", self._load_owned_items(user, limit_each))
        self._append_items(items, "mentions", self._load_mention_items(partner, limit_each))
        self._append_items(items, "following", self._load_following_items(partner, limit_each))
        total_before_filter = len(items)
        facets = self._build_facets(items)
        section_scope_items = self._apply_filters(
            items,
            section="all",
            source=filter_source,
            reason_code=filter_reason_code,
            search=filter_search,
        )
        filtered_section_counts = self._build_facets(section_scope_items).get("section_counts", [])
        facets["section_counts_filtered"] = filtered_section_counts
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

        access_models = (
            "mail.activity",
            "tier.review",
            "sc.workflow.workitem",
            "project.task",
            "project.project",
            "construction.contract",
            "payment.request",
            "sc.settlement.order",
            "mail.message",
            "mail.followers",
        )
        access_states = [self._read_access_state(model_name) for model_name in access_models]
        restricted = [
            item
            for item in access_states
            if (not item.get("readable"))
            and str(item.get("reason") or "") != "MODEL_UNAVAILABLE"
            and str(item.get("model") or "") != "sc.workflow.workitem"
        ]
        visibility = {
            "partial_data_hidden": bool(restricted),
            "restricted_sources": restricted,
            "message": "部分数据未显示" if restricted else "",
        }

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
            "visibility": visibility,
        }
        meta = {"intent": self.INTENT_TYPE}
        return {"ok": True, "data": data, "meta": meta}
