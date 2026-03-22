# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo import fields

from .base import BaseProjectBlockBuilder
from odoo.addons.smart_construction_core.services.project_task_state_support import (
    ProjectTaskStateSupport,
)


class ProjectProgressBuilder(BaseProjectBlockBuilder):
    block_key = "block.project.progress"
    block_type = "progress_summary"
    title = "项目进度"
    required_groups = ()

    def build(self, project=None, context=None):
        visibility = self._visibility()
        if not visibility.get("allowed"):
            return self._envelope(
                state="forbidden",
                visibility=visibility,
                data={
                    "task_total": 0,
                    "task_done": 0,
                    "task_open": 0,
                    "task_critical": 0,
                    "task_blocked": 0,
                    "task_overdue": 0,
                    "completion_percent": 0.0,
                    "milestone_total": 0,
                    "milestone_done": 0,
                    "milestone_delay": 0,
                    "milestone_progress": 0.0,
                    "milestone_upcoming_days": 0,
                    "critical_path_health": "unknown",
                },
            )
        if not project:
            return self._envelope(
                state="empty",
                visibility=visibility,
                data={
                    "task_total": 0,
                    "task_done": 0,
                    "task_open": 0,
                    "task_critical": 0,
                    "task_blocked": 0,
                    "task_overdue": 0,
                    "completion_percent": 0.0,
                    "milestone_total": 0,
                    "milestone_done": 0,
                    "milestone_delay": 0,
                    "milestone_progress": 0.0,
                    "milestone_upcoming_days": 0,
                    "critical_path_health": "unknown",
                },
            )

        task_domain = self._project_domain("project.task", project)
        total = self._safe_count("project.task", task_domain)
        done = self._safe_count("project.task", task_domain + ProjectTaskStateSupport.done_domain())
        blocked = 0
        try:
            for task in self.env["project.task"].search(task_domain):
                if ProjectTaskStateSupport.normalize(getattr(task, "sc_state", "draft")) == "draft" and getattr(task, "readiness_status", "") == "blocked":
                    blocked += 1
        except Exception:
            blocked = 0
        critical = self._safe_count("project.task", task_domain + [("priority", "in", ["2", "3"])]) if self._model_has_fields("project.task", ["priority"]) else 0
        overdue = self._safe_count("project.task", task_domain + [("date_deadline", "<", fields.Date.today())]) if self._model_has_fields("project.task", ["date_deadline"]) else 0
        open_count = max(total - done, 0)
        completion_percent = round((done * 100.0 / total), 2) if total > 0 else 0.0

        milestone_domain = self._project_domain("project.milestone", project)
        milestone_total = self._safe_count("project.milestone", milestone_domain)
        milestone_done = self._safe_count("project.milestone", milestone_domain + [("status", "in", ["done", "completed"])]) if self._model_has_fields("project.milestone", ["status"]) else 0
        milestone_delay = self._safe_count("project.milestone", milestone_domain + [("status", "in", ["delay", "overdue", "blocked"])]) if self._model_has_fields("project.milestone", ["status"]) else 0
        milestone_progress = self._safe_rate(milestone_done, milestone_total)
        milestone_upcoming_days = 0
        if self._model_has_fields("project.milestone", ["plan_date", "status"]):
            next_row = self.env["project.milestone"].search(
                milestone_domain + [
                    ("status", "not in", ["done", "completed"]),
                    ("plan_date", "!=", False),
                ],
                order="plan_date asc",
                limit=1,
            )
            if next_row and next_row.plan_date:
                delta = (next_row.plan_date - fields.Date.today()).days
                milestone_upcoming_days = int(delta)

        critical_path_health = "normal"
        if blocked > 0 or overdue > 0:
            critical_path_health = "risk"
        if blocked > 1 or overdue > 2:
            critical_path_health = "critical"

        data = {
            "task_total": total,
            "task_done": done,
            "task_open": open_count,
            "task_critical": critical,
            "task_blocked": blocked,
            "task_overdue": overdue,
            "completion_percent": completion_percent,
            "milestone_total": milestone_total,
            "milestone_done": milestone_done,
            "milestone_delay": milestone_delay,
            "milestone_progress": milestone_progress,
            "milestone_upcoming_days": milestone_upcoming_days,
            "critical_path_health": critical_path_health,
            "summary": {
                "task_completion_rate": completion_percent,
                "milestone_progress": milestone_progress,
                "delayed_tasks": overdue,
                "delayed_milestones": milestone_delay,
                "critical_task_count": critical,
                "blocked_task_count": blocked,
                "open_task_count": open_count,
                "critical_path_health": critical_path_health,
            },
        }
        return self._envelope(state="ready", visibility=visibility, data=data)
