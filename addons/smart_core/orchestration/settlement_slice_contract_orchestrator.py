# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo.addons.smart_core.core.industry_orchestration_service_adapter import (
    build_settlement_slice_service,
)
from odoo.addons.smart_core.orchestration.base_scene_entry_orchestrator import BaseSceneEntryOrchestrator


class SettlementSliceContractOrchestrator(BaseSceneEntryOrchestrator):
    scene_key = "settlement"
    scene_label = "结算结果"
    state_fallback_text = "后端未提供结算结果状态摘要"
    title_empty = "结算结果"
    suggested_action_key = "load_settlement_summary"
    suggested_action_reason_code = "SETTLEMENT_SLICE_PREPARED_READY"
    block_fetch_intent = "settlement.block.fetch"
    entry_summary_keys = (
        "project_code",
        "manager_name",
        "stage_name",
        "total_cost",
        "total_payment",
        "delta",
    )
    entry_blocks = (
        ("settlement_summary", "结算结果", "deferred"),
        ("next_actions", "结算下一步", "deferred"),
    )

    def __init__(self, env):
        super().__init__(env, build_settlement_slice_service(env))

    def resolve_title(self, project_payload):
        return "结算结果：%s" % str(project_payload.get("name") or "项目")
