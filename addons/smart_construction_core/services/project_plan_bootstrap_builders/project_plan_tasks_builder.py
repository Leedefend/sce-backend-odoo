# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo import fields

from odoo.addons.smart_construction_core.services.project_dashboard_builders.base import BaseProjectBlockBuilder


class ProjectPlanTasksBuilder(BaseProjectBlockBuilder):
    block_key = "block.project.plan_tasks"
    block_type = "plan_task_list"
    title = "计划任务"
    required_groups = ()

    @staticmethod
    def _task_state(task) -> str:
        sc_state = str(getattr(task, "sc_state", "") or "").strip().lower()
        if sc_state in {"draft", "ready", "in_progress", "done", "cancelled"}:
            return sc_state
        kanban_state = str(getattr(task, "kanban_state", "") or "").strip().lower()
        if kanban_state == "done":
            return "done"
        if kanban_state == "blocked":
            return "blocked"
        return "open"

    def build(self, project=None, context=None):
        visibility = self._visibility()
        empty_data = {
            "items": [],
            "summary": {
                "count": 0,
                "open_count": 0,
                "overdue_count": 0,
                "source_model": "project.task",
                "state_field": "sc_state",
                "empty_hint": "当前项目还没有计划任务，请先在 Odoo 项目任务中补齐任务。",
            },
        }
        if not visibility.get("allowed"):
            return self._envelope(state="forbidden", visibility=visibility, data=empty_data)
        if not project:
            return self._envelope(state="empty", visibility=visibility, data=empty_data)

        model = self._model("project.task")
        if model is None:
            return self._envelope(state="empty", visibility=visibility, data=empty_data)

        domain = self._project_domain("project.task", project)
        rows = []
        try:
            rows = model.search(domain, order="priority desc, date_deadline asc, id asc", limit=5)
        except Exception:
            rows = []

        items = []
        overdue_count = 0
        open_count = 0
        ready_count = 0
        for task in rows:
            deadline = str(getattr(task, "date_deadline", "") or "")
            task_state = self._task_state(task)
            if task_state != "done":
                open_count += 1
            if task_state in {"ready", "in_progress"}:
                ready_count += 1
            if deadline and getattr(task, "date_deadline", False) and getattr(task, "date_deadline") < fields.Date.today():
                overdue_count += 1
            stage = getattr(getattr(task, "stage_id", None), "display_name", "") or ""
            items.append(
                {
                    "task_id": int(task.id),
                    "name": str(getattr(task, "name", "") or ""),
                    "stage_name": str(stage),
                    "deadline": deadline,
                    "priority": str(getattr(task, "priority", "") or ""),
                    "state": task_state,
                }
            )

        state = "ready" if items else "empty"
        return self._envelope(
            state=state,
            visibility=visibility,
            data={
                "items": items,
                "summary": {
                    "count": len(items),
                    "open_count": open_count,
                    "ready_count": ready_count,
                    "overdue_count": overdue_count,
                    "source_model": "project.task",
                    "state_field": "sc_state",
                    "empty_hint": "当前项目还没有计划任务，请先在 Odoo 项目任务中补齐任务。",
                },
            },
        )
