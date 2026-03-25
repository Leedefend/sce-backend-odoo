# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo.addons.smart_construction_core.services.settlement_slice_service import SettlementSliceService
from odoo.addons.smart_core.orchestration.base_scene_entry_orchestrator import BaseSceneEntryOrchestrator


class SettlementSliceContractOrchestrator(BaseSceneEntryOrchestrator):
    scene_key = "settlement"
    scene_label = "结算结果"
    state_fallback_text = "当前状态：正在查看项目结算汇总。"
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
        super().__init__(env, SettlementSliceService(env))

    def resolve_title(self, project_payload):
        return "结算结果：%s" % str(project_payload.get("name") or "项目")
