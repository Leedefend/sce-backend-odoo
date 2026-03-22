# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo.addons.smart_construction_core.services.project_dashboard_service import (
    ProjectDashboardService,
)
from odoo.addons.smart_core.orchestration.base_scene_entry_orchestrator import (
    BaseSceneEntryOrchestrator,
)


class ProjectDashboardSceneOrchestrator(BaseSceneEntryOrchestrator):
    scene_key = "project.dashboard"
    scene_label = "项目驾驶舱"
    state_fallback_text = "当前状态：已完成立项，正在查看项目驾驶舱。"
    title_empty = "项目驾驶舱"
    suggested_action_key = "load_dashboard_progress"
    suggested_action_reason_code = "PROJECT_DASHBOARD_READY"
    block_fetch_intent = "project.dashboard.block.fetch"
    block_alias_map = {"risk": "risks"}
    entry_summary_keys = (
        "project_code",
        "manager_name",
        "partner_name",
        "stage_name",
        "health_state",
    )
    entry_blocks = (
        ("progress", "项目进度", "deferred"),
        ("risks", "风险提醒", "deferred"),
        ("next_actions", "下一步动作", "deferred"),
    )

    def __init__(self, env):
        super().__init__(env, ProjectDashboardService(env))

    def resolve_first_action(self, runtime_fetch_hints):
        blocks = runtime_fetch_hints.get("blocks") if isinstance(runtime_fetch_hints.get("blocks"), dict) else {}
        return blocks.get("progress") or {}

    def resolve_title(self, project_payload):
        return "项目驾驶舱：%s" % str(project_payload.get("name") or "项目")
