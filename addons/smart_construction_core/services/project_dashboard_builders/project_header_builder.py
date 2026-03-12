# -*- coding: utf-8 -*-
from __future__ import annotations

from .base import BaseProjectBlockBuilder


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

        data = {
            "summary": {
                "id": int(project.id),
                "name": str(getattr(project, "name", "") or ""),
                "project_code": str(getattr(project, "project_code", "") or ""),
                "partner_name": str(getattr(getattr(project, "partner_id", None), "display_name", "") or ""),
                "manager_name": str(getattr(getattr(project, "user_id", None), "display_name", "") or ""),
                "stage_name": str(getattr(getattr(project, "stage_id", None), "display_name", "") or ""),
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
                "current_stage": str(getattr(getattr(project, "stage_id", None), "display_name", "") or ""),
                "planned_finish_date": str(getattr(project, "date", "") or getattr(project, "date_end", "") or ""),
            },
            "quick_actions": [
                {"key": "open_project_form", "label": "查看项目详情", "intent": "ui.contract"},
                {"key": "open_task_list", "label": "查看任务列表", "intent": "ui.contract"},
            ],
        }
        return self._envelope(state="ready", visibility=visibility, data=data)
