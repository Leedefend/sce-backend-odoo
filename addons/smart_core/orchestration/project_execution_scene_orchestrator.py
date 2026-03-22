# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo.addons.smart_construction_core.services.project_execution_service import (
    ProjectExecutionService,
)
from odoo.addons.smart_core.orchestration.base_scene_entry_orchestrator import (
    BaseSceneEntryOrchestrator,
)


class ProjectExecutionSceneOrchestrator(BaseSceneEntryOrchestrator):
    scene_key = "project.execution"
    scene_label = "执行推进"
    state_fallback_text = "当前状态：正在查看执行推进状态。"
    title_empty = "项目执行"
    suggested_action_key = "load_execution_next_actions"
    suggested_action_reason_code = "PROJECT_EXECUTION_READY"
    block_fetch_intent = "project.execution.block.fetch"
    entry_summary_keys = (
        "project_code",
        "manager_name",
        "stage_name",
        "date_start",
        "date_end",
    )
    entry_blocks = (
        ("execution_tasks", "执行任务", "deferred"),
        ("pilot_precheck", "试点前检查", "deferred"),
        ("next_actions", "执行下一步", "deferred"),
    )

    def __init__(self, env):
        super().__init__(env, ProjectExecutionService(env))

    def resolve_first_action(self, runtime_fetch_hints):
        blocks = runtime_fetch_hints.get("blocks") if isinstance(runtime_fetch_hints.get("blocks"), dict) else {}
        return blocks.get("next_actions") or blocks.get("execution_tasks") or {}

    def resolve_title(self, project_payload):
        return "执行推进：%s" % str(project_payload.get("name") or "项目")
