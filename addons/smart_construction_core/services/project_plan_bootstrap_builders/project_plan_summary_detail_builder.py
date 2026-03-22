# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo import fields

from odoo.addons.smart_construction_core.services.project_dashboard_builders.base import BaseProjectBlockBuilder
from odoo.addons.smart_construction_core.services.project_task_state_support import (
    ProjectTaskStateSupport,
)


class ProjectPlanSummaryDetailBuilder(BaseProjectBlockBuilder):
    block_key = "block.project.plan_summary_detail"
    block_type = "plan_summary_detail"
    title = "计划摘要"
    required_groups = ()

    def build(self, project=None, context=None):
        visibility = self._visibility()
        empty_data = {
            "task_total": 0,
            "task_open": 0,
            "task_done": 0,
            "task_overdue": 0,
            "milestone_total": 0,
            "milestone_done": 0,
            "next_deadline": "",
            "planning_health": "unknown",
            "summary": {
                "task_completion_rate": 0.0,
                "milestone_completion_rate": 0.0,
                "timeline_state": "unknown",
            },
        }
        if not visibility.get("allowed"):
            return self._envelope(state="forbidden", visibility=visibility, data=empty_data)
        if not project:
            return self._envelope(state="empty", visibility=visibility, data=empty_data)

        task_domain = self._project_domain("project.task", project)
        total = self._safe_count("project.task", task_domain)
        done = self._safe_count("project.task", task_domain + ProjectTaskStateSupport.done_domain())
        overdue = self._safe_count("project.task", task_domain + [("date_deadline", "<", fields.Date.today())]) if self._model_has_fields("project.task", ["date_deadline"]) else 0
        open_count = max(total - done, 0)

        milestone_domain = self._project_domain("project.milestone", project)
        milestone_total = self._safe_count("project.milestone", milestone_domain)
        milestone_done = self._safe_count("project.milestone", milestone_domain + [("status", "in", ["done", "completed"])]) if self._model_has_fields("project.milestone", ["status"]) else 0

        next_deadline = ""
        if self._model_has_fields("project.task", ["date_deadline"]):
            next_task_domain = task_domain + [("date_deadline", "!=", False)] + ProjectTaskStateSupport.open_domain()
            try:
                next_task = self.env["project.task"].search(
                    next_task_domain,
                    order="date_deadline asc, id asc",
                    limit=1,
                )
            except Exception:
                next_task = False
            if next_task and next_task.date_deadline:
                next_deadline = str(next_task.date_deadline)

        planning_health = "normal"
        if overdue > 0:
            planning_health = "warning"
        if overdue > 2:
            planning_health = "critical"
        if total <= 0 and milestone_total <= 0:
            planning_health = "bootstrap_needed"

        data = {
            "task_total": total,
            "task_open": open_count,
            "task_done": done,
            "task_overdue": overdue,
            "milestone_total": milestone_total,
            "milestone_done": milestone_done,
            "next_deadline": next_deadline,
            "planning_health": planning_health,
            "summary": {
                "task_completion_rate": self._safe_rate(done, total),
                "milestone_completion_rate": self._safe_rate(milestone_done, milestone_total),
                "timeline_state": planning_health,
            },
        }
        return self._envelope(state="ready", visibility=visibility, data=data)
