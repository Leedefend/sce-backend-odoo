# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo.addons.smart_core.core.industry_orchestration_service_adapter import (
    build_project_dashboard_service,
)
from odoo.addons.smart_core.orchestration.base_scene_entry_orchestrator import (
    BaseSceneEntryOrchestrator,
)


class ProjectDashboardSceneOrchestrator(BaseSceneEntryOrchestrator):
    scene_key = "project.management"
    scene_label = "项目驾驶舱"
    state_fallback_text = "后端未提供项目驾驶舱状态摘要"
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
        "lifecycle_state",
        "milestone",
        "health_state",
        "progress_percent",
        "cost_total",
        "payment_total",
        "status",
    )
    entry_blocks = (
        ("progress", "项目进度", "deferred"),
        ("risks", "风险提醒", "deferred"),
        ("next_actions", "下一步动作", "deferred"),
    )

    def __init__(self, env):
        super().__init__(env, build_project_dashboard_service(env))

    def resolve_first_action(self, runtime_fetch_hints):
        blocks = runtime_fetch_hints.get("blocks") if isinstance(runtime_fetch_hints.get("blocks"), dict) else {}
        return blocks.get("progress") or {}

    def resolve_title(self, project_payload):
        return "项目驾驶舱：%s" % str(project_payload.get("name") or "项目")
