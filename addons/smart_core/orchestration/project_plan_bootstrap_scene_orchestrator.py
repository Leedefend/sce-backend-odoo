# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo.addons.smart_core.core.industry_orchestration_service_adapter import (
    build_project_plan_bootstrap_service,
)
from odoo.addons.smart_core.orchestration.base_scene_entry_orchestrator import (
    BaseSceneEntryOrchestrator,
)


class ProjectPlanBootstrapSceneOrchestrator(BaseSceneEntryOrchestrator):
    scene_key = "project.plan_bootstrap"
    scene_label = "计划准备"
    state_fallback_text = "当前状态：正在核对计划准备度。"
    title_empty = "计划编排"
    suggested_action_key = "load_plan_next_actions"
    suggested_action_reason_code = "PROJECT_PLAN_BOOTSTRAP_READY"
    block_fetch_intent = "project.plan_bootstrap.block.fetch"
    entry_summary_keys = (
        "project_code",
        "manager_name",
        "stage_name",
        "date_start",
        "date_end",
    )
    entry_blocks = (
        ("plan_summary_detail", "计划摘要", "deferred"),
        ("plan_tasks", "计划任务", "deferred"),
        ("next_actions", "计划下一步", "deferred"),
    )

    def __init__(self, env):
        super().__init__(env, build_project_plan_bootstrap_service(env))

    def resolve_first_action(self, runtime_fetch_hints):
        blocks = runtime_fetch_hints.get("blocks") if isinstance(runtime_fetch_hints.get("blocks"), dict) else {}
        return blocks.get("next_actions") or blocks.get("plan_summary_detail") or {}

    def resolve_title(self, project_payload):
        return "计划准备：%s" % str(project_payload.get("name") or "项目")
