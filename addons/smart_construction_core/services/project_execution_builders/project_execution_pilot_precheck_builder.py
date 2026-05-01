# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo.addons.smart_construction_core.services.project_dashboard_builders.base import BaseProjectBlockBuilder
from odoo.addons.smart_construction_core.services.project_execution_consistency_guard import (
    ProjectExecutionConsistencyGuard,
)


class ProjectExecutionPilotPrecheckBuilder(BaseProjectBlockBuilder):
    block_key = "block.project.execution_pilot_precheck"
    block_type = "checklist"
    title = "试点前检查"
    required_groups = ()

    def build(self, project=None, context=None):
        visibility = self._visibility()
        empty_data = {
            "checks": [],
            "summary": {
                "overall_state": "blocked",
                "passed_count": 0,
                "failed_count": 0,
                "primary_reason_code": "PROJECT_CONTEXT_MISSING",
                "primary_message": "缺少项目上下文，无法执行试点前检查。",
                "empty_hint": "请先进入具体项目，再执行试点前检查。",
                "single_open_task_only": True,
            },
        }
        if not visibility.get("allowed"):
            return self._envelope(state="forbidden", visibility=visibility, data=empty_data)
        if not project:
            return self._envelope(state="empty", visibility=visibility, data=empty_data)

        report = ProjectExecutionConsistencyGuard(self.env).pilot_precheck(project)
        summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
        data = {
            "checks": report.get("checks") if isinstance(report.get("checks"), list) else [],
            "summary": {
                **summary,
                "empty_hint": "当前项目没有试点检查结果，请先刷新区块。",
            },
        }
        return self._envelope(state="ready", visibility=visibility, data=data)
