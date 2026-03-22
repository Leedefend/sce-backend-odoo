# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo import fields

from odoo.addons.smart_construction_core.services.project_dashboard_builders.base import BaseProjectBlockBuilder


class ProjectExecutionTasksBuilder(BaseProjectBlockBuilder):
    block_key = "block.project.execution_tasks"
    block_type = "execution_task_list"
    title = "执行任务"
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
                "blocked_count": 0,
                "overdue_count": 0,
                "source_model": "project.task",
                "state_field": "sc_state",
                "empty_hint": "当前项目还没有执行任务，请先在 Odoo 项目任务中创建或准备任务。",
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
            rows = model.search(domain, order="priority desc, write_date desc, id desc", limit=6)
        except Exception:
            rows = []

        items = []
        open_count = 0
        blocked_count = 0
        overdue_count = 0
        in_progress_count = 0
        for task in rows:
            task_state = self._task_state(task)
            if task_state != "done":
                open_count += 1
            if task_state == "blocked":
                blocked_count += 1
            if task_state == "in_progress":
                in_progress_count += 1
            deadline_value = getattr(task, "date_deadline", False)
            deadline = str(deadline_value or "")
            if deadline_value and deadline_value < fields.Date.today():
                overdue_count += 1
            items.append(
                {
                    "task_id": int(task.id),
                    "name": str(getattr(task, "name", "") or ""),
                    "assignee_name": str(getattr(getattr(task, "user_ids", False)[:1], "display_name", "") or ""),
                    "stage_name": str(getattr(getattr(task, "stage_id", None), "display_name", "") or ""),
                    "deadline": deadline,
                    "state": task_state,
                }
            )

        return self._envelope(
            state="ready" if items else "empty",
            visibility=visibility,
            data={
                "items": items,
                "summary": {
                    "count": len(items),
                    "open_count": open_count,
                    "blocked_count": blocked_count,
                    "in_progress_count": in_progress_count,
                    "overdue_count": overdue_count,
                    "source_model": "project.task",
                    "state_field": "sc_state",
                    "empty_hint": "当前项目还没有执行任务，请先在 Odoo 项目任务中创建或准备任务。",
                },
            },
        )
