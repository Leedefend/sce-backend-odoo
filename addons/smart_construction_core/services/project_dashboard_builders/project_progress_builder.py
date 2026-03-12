# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo import fields

from .base import BaseProjectBlockBuilder


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
                    "completion_percent": 0.0,
                },
            )
        if not project:
            return self._envelope(
                state="empty",
                visibility=visibility,
                data={
                    "task_total": 0,
                    "task_done": 0,
                    "completion_percent": 0.0,
                },
            )

        task_domain = self._project_domain("project.task", project)
        total = self._safe_count("project.task", task_domain)
        done = self._safe_count("project.task", task_domain + [("kanban_state", "=", "done")]) if self._model_has_fields("project.task", ["kanban_state"]) else 0
        overdue = self._safe_count("project.task", task_domain + [("date_deadline", "<", fields.Date.today())]) if self._model_has_fields("project.task", ["date_deadline"]) else 0
        completion_percent = round((done * 100.0 / total), 2) if total > 0 else 0.0

        milestone_domain = self._project_domain("project.milestone", project)
        milestone_total = self._safe_count("project.milestone", milestone_domain)
        milestone_done = self._safe_count("project.milestone", milestone_domain + [("status", "in", ["done", "completed"])]) if self._model_has_fields("project.milestone", ["status"]) else 0
        milestone_delay = self._safe_count("project.milestone", milestone_domain + [("status", "in", ["delay", "overdue", "blocked"])]) if self._model_has_fields("project.milestone", ["status"]) else 0
        milestone_progress = self._safe_rate(milestone_done, milestone_total)
        data = {
            "task_total": total,
            "task_done": done,
            "task_overdue": overdue,
            "completion_percent": completion_percent,
            "milestone_total": milestone_total,
            "milestone_done": milestone_done,
            "milestone_delay": milestone_delay,
            "milestone_progress": milestone_progress,
            "summary": {
                "task_completion_rate": completion_percent,
                "milestone_progress": milestone_progress,
                "delayed_tasks": overdue,
                "delayed_milestones": milestone_delay,
            },
        }
        return self._envelope(state="ready", visibility=visibility, data=data)
