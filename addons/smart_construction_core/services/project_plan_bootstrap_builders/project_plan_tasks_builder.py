# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo.addons.smart_construction_core.services.project_dashboard_builders.base import BaseProjectBlockBuilder


class ProjectPlanTasksBuilder(BaseProjectBlockBuilder):
    block_key = "block.project.plan_tasks"
    block_type = "task_list"
    title = "计划任务"
    required_groups = ()

    def build(self, project=None, context=None):
        visibility = self._visibility()
        empty_data = {"items": [], "summary": {"count": 0, "source_model": "project.task"}}
        if not visibility.get("allowed"):
            return self._envelope(state="forbidden", visibility=visibility, data=empty_data)
        if not project:
            return self._envelope(state="empty", visibility=visibility, data=empty_data)

        model = self._model("project.task")
        if model is None:
            return self._envelope(state="empty", visibility=visibility, data=empty_data)

        rows = []
        try:
            rows = model.search(self._project_domain("project.task", project), order="sequence asc, id asc", limit=10)
        except Exception:
            rows = []
        items = []
        for task in rows:
            items.append(
                {
                    "task_id": int(task.id),
                    "source_model": "project.task",
                    "source_id": int(task.id),
                    "name": str(getattr(task, "name", "") or ""),
                    "stage_name": str(getattr(getattr(task, "stage_id", None), "display_name", "") or ""),
                    "deadline": str(getattr(task, "date_deadline", "") or ""),
                }
            )
        return self._envelope(
            state="ready" if items else "empty",
            visibility=visibility,
            data={"items": items, "summary": {"count": len(items), "source_model": "project.task"}},
        )
