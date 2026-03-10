# -*- coding: utf-8 -*-
from __future__ import annotations

from .base import BaseProjectBlockBuilder


class ProjectProgressBuilder(BaseProjectBlockBuilder):
    block_key = "block.project.progress"
    block_type = "progress_summary"
    title = "项目进度"
    required_groups = ("smart_construction_core.group_sc_cap_project_read",)

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
        completion_percent = round((done * 100.0 / total), 2) if total > 0 else 0.0
        data = {
            "task_total": total,
            "task_done": done,
            "completion_percent": completion_percent,
        }
        return self._envelope(state="ready", visibility=visibility, data=data)
