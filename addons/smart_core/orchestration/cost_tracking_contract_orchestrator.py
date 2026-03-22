# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo.addons.smart_construction_core.services.cost_tracking_service import CostTrackingService
from odoo.addons.smart_core.orchestration.base_scene_entry_orchestrator import BaseSceneEntryOrchestrator


class CostTrackingContractOrchestrator(BaseSceneEntryOrchestrator):
    scene_key = "cost.tracking"
    scene_label = "成本跟踪"
    state_fallback_text = "当前状态：正在查看原生成本跟踪。"
    title_empty = "成本跟踪"
    suggested_action_key = "load_cost_summary"
    suggested_action_reason_code = "COST_TRACKING_READY"
    block_fetch_intent = "cost.tracking.block.fetch"
    entry_summary_keys = (
        "project_code",
        "manager_name",
        "stage_name",
        "posted_move_count",
        "posted_cost_amount",
    )
    entry_blocks = (
        ("summary", "成本摘要", "deferred"),
        ("recent_moves", "原生凭证", "deferred"),
        ("next_actions", "成本下一步", "deferred"),
    )

    def __init__(self, env):
        super().__init__(env, CostTrackingService(env))

    def resolve_first_action(self, runtime_fetch_hints):
        blocks = runtime_fetch_hints.get("blocks") if isinstance(runtime_fetch_hints.get("blocks"), dict) else {}
        return blocks.get("summary") or blocks.get("recent_moves") or {}

    def resolve_title(self, project_payload):
        return "成本跟踪：%s" % str(project_payload.get("name") or "项目")
