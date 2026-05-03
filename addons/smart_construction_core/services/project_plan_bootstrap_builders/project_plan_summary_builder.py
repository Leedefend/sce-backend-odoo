# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo.addons.smart_construction_core.services.project_dashboard_builders.base import BaseProjectBlockBuilder


class ProjectPlanSummaryBuilder(BaseProjectBlockBuilder):
    block_key = "block.project.plan_summary_detail"
    block_type = "summary"
    title = "计划摘要"
    required_groups = ()

    def build(self, project=None, context=None):
        visibility = self._visibility()
        empty_data = {
            "summary": {
                "task_count": 0,
                "milestone_count": 0,
                "open_task_count": 0,
                "done_task_count": 0,
            },
            "rows": [],
        }
        if not visibility.get("allowed"):
            return self._envelope(state="forbidden", visibility=visibility, data=empty_data)
        if not project:
            return self._envelope(state="empty", visibility=visibility, data=empty_data)

        project_domain = self._project_domain("project.task", project)
        task_count = self._safe_count("project.task", project_domain)
        milestone_count = self._safe_count("project.milestone", self._project_domain("project.milestone", project))
        open_task_count = self._safe_count("project.task", project_domain + [("stage_id.fold", "=", False)])
        done_task_count = max(0, task_count - open_task_count)
        rows = [
            {"key": "task_count", "label": "计划任务", "value": "%s 条" % task_count},
            {"key": "milestone_count", "label": "里程碑", "value": "%s 个" % milestone_count},
            {"key": "open_task_count", "label": "未完成任务", "value": "%s 条" % open_task_count},
            {"key": "done_task_count", "label": "已完成任务", "value": "%s 条" % done_task_count},
        ]
        return self._envelope(
            state="ready" if task_count or milestone_count else "empty",
            visibility=visibility,
            data={
                "summary": {
                    "task_count": task_count,
                    "milestone_count": milestone_count,
                    "open_task_count": open_task_count,
                    "done_task_count": done_task_count,
                },
                "rows": rows,
            },
        )
