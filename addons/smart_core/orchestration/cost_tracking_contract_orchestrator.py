# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo.addons.smart_construction_core.services.cost_tracking_service import CostTrackingService
from odoo.addons.smart_core.orchestration.base_scene_entry_orchestrator import BaseSceneEntryOrchestrator


class CostTrackingContractOrchestrator(BaseSceneEntryOrchestrator):
    scene_key = "cost.tracking"
    scene_label = "成本记录"
    state_fallback_text = "当前状态：正在查看项目成本记录。"
    title_empty = "成本记录"
    suggested_action_key = "load_cost_entry"
    suggested_action_reason_code = "COST_SLICE_PREPARED_READY"
    block_fetch_intent = "cost.tracking.block.fetch"
    entry_summary_keys = (
        "project_code",
        "manager_name",
        "stage_name",
        "cost_record_count",
        "cost_total_amount",
    )
    entry_blocks = (
        ("cost_entry", "成本录入", "deferred"),
        ("cost_list", "成本记录", "deferred"),
        ("cost_summary", "成本汇总", "deferred"),
        ("next_actions", "成本下一步", "deferred"),
    )

    def __init__(self, env):
        super().__init__(env, CostTrackingService(env))

    def resolve_first_action(self, runtime_fetch_hints):
        blocks = runtime_fetch_hints.get("blocks") if isinstance(runtime_fetch_hints.get("blocks"), dict) else {}
        return blocks.get("cost_entry") or blocks.get("cost_list") or {}

    def resolve_title(self, project_payload):
        return "成本记录：%s" % str(project_payload.get("name") or "项目")
