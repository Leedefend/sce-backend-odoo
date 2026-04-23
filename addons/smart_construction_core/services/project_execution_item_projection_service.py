# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo import fields
from odoo.addons.smart_construction_core.models.support.state_machine import ScStateMachine
from odoo.addons.smart_construction_scene.services.capability_scene_targets import (
    resolve_execution_projection_scene_key,
)


class ProjectExecutionItemProjectionService:
    """Project-scoped execution item projection from non-task business objects."""

    SOURCE_CONFIG = {
        "construction.contract": {
            "title_prefix": "合同事项",
            "pending_states": ("draft", "confirmed", "running"),
            "in_progress_states": ("confirmed", "running"),
            "draft_states": ("draft",),
            "deadline_field": "date_end",
            "fallback_deadline_field": "date_contract",
            "title_field": "subject",
            "action_label": "查看合同",
            "reason_code": "SYSTEM_EXECUTION_PENDING",
            "priority": "high",
        },
        "payment.request": {
            "title_prefix": "付款事项",
            "pending_states": ("draft", "submit", "approve", "approved"),
            "in_progress_states": ("submit", "approve", "approved"),
            "draft_states": ("draft",),
            "deadline_field": "date_request",
            "title_field": "name",
            "action_label": "查看付款申请",
            "reason_code": "SYSTEM_EXECUTION_PENDING",
            "priority": "high",
        },
        "sc.settlement.order": {
            "title_prefix": "结算事项",
            "pending_states": ("draft", "submit", "approve"),
            "in_progress_states": ("submit", "approve"),
            "draft_states": ("draft",),
            "deadline_field": "date_settlement",
            "title_field": "name",
            "action_label": "查看结算单",
            "reason_code": "SYSTEM_EXECUTION_PENDING",
            "priority": "medium",
        },
    }

    def __init__(self, env):
        self.env = env

    def _model(self, model_name):
        try:
            return self.env[model_name]
        except Exception:
            return None

    def _project_responsible_domain(self, user):
        Project = self._model("project.project")
        if Project is None:
            return []
        fields_map = Project._fields
        clauses = []
        for field_name in ("user_id", "manager_id", "cost_manager_id", "doc_manager_id"):
            if field_name in fields_map:
                clauses.append((field_name, "=", int(user.id)))
        if "user_ids" in fields_map:
            clauses.append(("user_ids", "in", [int(user.id)]))
        if not clauses:
            return []
        if len(clauses) == 1:
            return [clauses[0]]
        return (["|"] * (len(clauses) - 1)) + clauses

    def _project_ids_for_user(self, user):
        Project = self._model("project.project")
        if Project is None:
            return []
        try:
            projects = Project.sudo().search(self._project_responsible_domain(user), order="id desc")
        except Exception:
            return []
        return [int(project.id) for project in projects]

    @staticmethod
    def _deadline_text(record, primary_field, fallback_field=""):
        value = getattr(record, primary_field, False) if primary_field else False
        if not value and fallback_field:
            value = getattr(record, fallback_field, False)
        return fields.Date.to_string(value) if value else ""

    @staticmethod
    def _safe_text(value):
        return str(value or "").strip()

    def _state_label(self, model_name, state):
        try:
            return str(ScStateMachine.label(model_name, state) or state)
        except Exception:
            return str(state or "")

    def _project_name(self, record):
        project = getattr(record, "project_id", False)
        return self._safe_text(getattr(project, "display_name", "") or getattr(project, "name", ""))

    def _item_title(self, record, config):
        raw_title = self._safe_text(getattr(record, str(config.get("title_field") or "name"), ""))
        if not raw_title:
            raw_title = "%s#%s" % (record._name, int(record.id))
        prefix = self._safe_text(config.get("title_prefix"))
        return "%s：%s" % (prefix, raw_title) if prefix else raw_title

    def _normalize_state(self, model_name, state, config):
        state_value = str(state or "").strip()
        if state_value in set(config.get("draft_states") or ()):
            return "draft"
        if state_value in set(config.get("in_progress_states") or ()):
            return "in_progress"
        if state_value in set(config.get("pending_states") or ()):
            return "open"
        return "done"

    def _project_items_for_model(self, model_name, project, *, limit=6):
        config = self.SOURCE_CONFIG.get(model_name) or {}
        Model = self._model(model_name)
        if Model is None or not project:
            return []
        domain = [
            ("project_id", "=", int(project.id)),
            ("state", "in", list(config.get("pending_states") or ())),
        ]
        order = "write_date desc, id desc"
        try:
            records = Model.sudo().search(domain, order=order, limit=max(0, int(limit or 0)))
        except Exception:
            return []
        rows = []
        for record in records:
            try:
                raw_state = str(getattr(record, "state", "") or "")
                rows.append(
                    {
                        "task_id": int(record.id),
                        "task_kind": "system",
                        "source_model": model_name,
                        "source_id": int(record.id),
                        "name": self._item_title(record, config),
                        "assignee_name": "",
                        "project_name": self._project_name(record),
                        "stage_name": self._state_label(model_name, raw_state),
                        "deadline": self._deadline_text(
                            record,
                            str(config.get("deadline_field") or ""),
                            str(config.get("fallback_deadline_field") or ""),
                        ),
                        "state": self._normalize_state(model_name, raw_state, config),
                        "state_code": raw_state,
                        "action_label": self._safe_text(config.get("action_label")),
                        "scene_key": resolve_execution_projection_scene_key(model_name),
                        "reason_code": self._safe_text(config.get("reason_code")),
                        "priority": self._safe_text(config.get("priority") or "medium"),
                    }
                )
            except Exception:
                rows.append(
                    {
                        "task_id": int(record.id),
                        "task_kind": "system",
                        "source_model": model_name,
                        "source_id": int(record.id),
                        "name": "%s#%s" % (model_name, int(record.id)),
                        "assignee_name": "",
                        "project_name": "",
                        "stage_name": "",
                        "deadline": "",
                        "state": "open",
                        "state_code": "",
                        "action_label": self._safe_text(config.get("action_label")),
                        "scene_key": resolve_execution_projection_scene_key(model_name),
                        "reason_code": self._safe_text(config.get("reason_code")),
                        "priority": self._safe_text(config.get("priority") or "medium"),
                    }
                )
        return rows

    def project_items(self, project, *, limit=6):
        rows = []
        safe_limit = max(0, int(limit or 0))
        if safe_limit <= 0:
            return rows
        per_source_limit = max(1, (safe_limit + len(self.SOURCE_CONFIG) - 1) // len(self.SOURCE_CONFIG))
        for model_name in self.SOURCE_CONFIG:
            rows.extend(self._project_items_for_model(model_name, project, limit=per_source_limit))
        rows.sort(key=lambda row: (str(row.get("deadline") or ""), int(row.get("source_id") or 0)), reverse=True)
        return rows[:safe_limit]

    def project_summary(self, project):
        items = []
        for model_name in self.SOURCE_CONFIG:
            items.extend(self._project_items_for_model(model_name, project, limit=200))
        overdue_count = 0
        draft_count = 0
        in_progress_count = 0
        today = fields.Date.today()
        for row in items:
            if str(row.get("state") or "") == "draft":
                draft_count += 1
            if str(row.get("state") or "") == "in_progress":
                in_progress_count += 1
            deadline = str(row.get("deadline") or "")
            if deadline and deadline < fields.Date.to_string(today):
                overdue_count += 1
        return {
            "count": len(items),
            "open_count": len([row for row in items if str(row.get("state") or "") != "done"]),
            "blocked_count": draft_count,
            "in_progress_count": in_progress_count,
            "overdue_count": overdue_count,
        }

    def user_items(self, user, *, limit=8):
        safe_limit = max(0, int(limit or 0))
        if safe_limit <= 0:
            return []
        project_ids = self._project_ids_for_user(user)
        if not project_ids:
            return []
        rows = []
        per_source_limit = max(1, (safe_limit + len(self.SOURCE_CONFIG) - 1) // len(self.SOURCE_CONFIG))
        for model_name, config in self.SOURCE_CONFIG.items():
            Model = self._model(model_name)
            if Model is None:
                continue
            domain = [
                ("project_id", "in", project_ids),
                ("state", "in", list(config.get("pending_states") or ())),
            ]
            try:
                records = Model.sudo().search(domain, order="write_date desc, id desc", limit=per_source_limit)
            except Exception:
                continue
            for record in records:
                try:
                    rows.append(
                        {
                            "id": int(record.id),
                            "title": self._item_title(record, config),
                            "model": model_name,
                            "record_id": int(record.id),
                            "deadline": self._deadline_text(
                                record,
                                str(config.get("deadline_field") or ""),
                                str(config.get("fallback_deadline_field") or ""),
                            ),
                            "scene_key": resolve_execution_projection_scene_key(model_name),
                            "source": model_name,
                            "action_label": self._safe_text(config.get("action_label")),
                            "action_key": "%s.open" % model_name,
                            "reason_code": self._safe_text(config.get("reason_code")),
                            "priority": self._safe_text(config.get("priority") or "medium"),
                        }
                    )
                except Exception:
                    rows.append(
                        {
                            "id": int(record.id),
                            "title": "%s#%s" % (model_name, int(record.id)),
                            "model": model_name,
                            "record_id": int(record.id),
                            "deadline": "",
                            "scene_key": resolve_execution_projection_scene_key(model_name),
                            "source": model_name,
                            "action_label": self._safe_text(config.get("action_label")),
                            "action_key": "%s.open" % model_name,
                            "reason_code": self._safe_text(config.get("reason_code")),
                            "priority": self._safe_text(config.get("priority") or "medium"),
                        }
                    )
        rows.sort(key=lambda row: (str(row.get("deadline") or ""), int(row.get("id") or 0)), reverse=True)
        return rows[:safe_limit]
