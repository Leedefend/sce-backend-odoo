# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo import fields

from .base import BaseProjectBlockBuilder
from odoo.addons.smart_construction_core.services.project_task_state_support import (
    ProjectTaskStateSupport,
)
from odoo.addons.smart_construction_core.services.project_state_explain_service import lifecycle_state_label


class ProjectHeaderBuilder(BaseProjectBlockBuilder):
    block_key = "block.project.header"
    block_type = "record_summary"
    title = "项目头部信息"
    required_groups = ()

    def build(self, project=None, context=None):
        visibility = self._visibility()
        if not visibility.get("allowed"):
            return self._envelope(
                state="forbidden",
                visibility=visibility,
                data={"summary": {}, "quick_actions": []},
            )
        if not project:
            return self._envelope(
                state="empty",
                visibility=visibility,
                data={"summary": {}, "quick_actions": []},
            )

        task_domain = self._project_domain("project.task", project)
        overdue_tasks = self._safe_count(
            "project.task",
            task_domain + [("date_deadline", "<", fields.Date.today())],
        ) if self._model_has_fields("project.task", ["date_deadline"]) else 0
        blocked_tasks = 0
        try:
            for task in self.env["project.task"].search(task_domain):
                if ProjectTaskStateSupport.normalize(getattr(task, "sc_state", "draft")) == "draft" and getattr(task, "readiness_status", "") == "blocked":
                    blocked_tasks += 1
        except Exception:
            blocked_tasks = 0
        risk_open = self._safe_count("project.risk", [("project_id", "=", int(project.id)), ("status", "not in", ["closed", "done"])])
        payment_domain = self._project_domain("payment.request", project)
        payment_pending = self._safe_count(
            "payment.request",
            payment_domain + [("state", "in", ["draft", "submitted", "pending", "confirm"])],
        )

        quick_actions = [
            {
                "key": "open_task_overdue",
                "label": "处理延期任务（%s）" % int(overdue_tasks),
                "intent": "ui.contract",
                "priority": 110,
                "pending_count": int(overdue_tasks),
                "source": "business",
            },
            {
                "key": "open_task_blocked",
                "label": "处理阻塞任务（%s）" % int(blocked_tasks),
                "intent": "ui.contract",
                "priority": 100,
                "pending_count": int(blocked_tasks),
                "source": "business",
            },
            {
                "key": "open_risk_list",
                "label": "处理风险事项（%s）" % int(risk_open),
                "intent": "ui.contract",
                "priority": 95,
                "pending_count": int(risk_open),
                "source": "business",
            },
            {
                "key": "open_payment_requests",
                "label": "处理资金申请（%s）" % int(payment_pending),
                "intent": "ui.contract",
                "priority": 80,
                "pending_count": int(payment_pending),
                "source": "business",
            },
            {
                "key": "open_project_form",
                "label": "查看项目详情",
                "intent": "ui.contract",
                "priority": 40,
                "pending_count": 0,
                "source": "navigation",
            },
        ]
        quick_actions = [row for row in quick_actions if int(row.get("pending_count", 0)) > 0 or row.get("key") == "open_project_form"]
        quick_actions.sort(key=lambda row: (-int(row.get("pending_count", 0)), -int(row.get("priority", 0))))

        data = {
            "summary": {
                "id": int(project.id),
                "name": str(getattr(project, "name", "") or ""),
                "project_code": str(getattr(project, "project_code", "") or ""),
                "partner_name": str(getattr(getattr(project, "partner_id", None), "display_name", "") or ""),
                "manager_name": str(getattr(getattr(project, "user_id", None), "display_name", "") or ""),
                "stage_name": lifecycle_state_label(project),
                "company_name": str(getattr(getattr(project, "company_id", None), "display_name", "") or ""),
                "date_start": str(getattr(project, "date_start", "") or ""),
                "date_end": str(getattr(project, "date", "") or getattr(project, "date_end", "") or ""),
                "state": str(getattr(project, "state", "") or ""),
                "health_state": str(getattr(project, "health_state", "") or ""),
            },
            "semantic_summary": {
                "project_name": str(getattr(project, "name", "") or ""),
                "owner_org": str(getattr(getattr(project, "partner_id", None), "display_name", "") or ""),
                "contractor_org": str(getattr(getattr(project, "company_id", None), "display_name", "") or ""),
                "project_manager": str(getattr(getattr(project, "user_id", None), "display_name", "") or ""),
                "current_stage": lifecycle_state_label(project),
                "planned_finish_date": str(getattr(project, "date", "") or getattr(project, "date_end", "") or ""),
            },
            "quick_actions": quick_actions,
        }
        return self._envelope(state="ready", visibility=visibility, data=data)
