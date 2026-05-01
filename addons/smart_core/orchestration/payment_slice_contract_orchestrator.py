# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo.addons.smart_core.core.industry_orchestration_service_adapter import (
    build_payment_slice_service,
)
from odoo.addons.smart_core.orchestration.base_scene_entry_orchestrator import BaseSceneEntryOrchestrator


class PaymentSliceContractOrchestrator(BaseSceneEntryOrchestrator):
    scene_key = "payment"
    scene_label = "付款记录"
    state_fallback_text = "后端未提供付款记录状态摘要"
    title_empty = "付款记录"
    suggested_action_key = "load_payment_entry"
    suggested_action_reason_code = "PAYMENT_SLICE_PREPARED_READY"
    block_fetch_intent = "payment.block.fetch"
    entry_summary_keys = (
        "project_code",
        "manager_name",
        "stage_name",
        "payment_record_count",
        "payment_total_amount",
    )
    entry_blocks = (
        ("payment_entry", "付款录入", "deferred"),
        ("payment_list", "付款记录", "deferred"),
        ("payment_summary", "付款汇总", "deferred"),
        ("next_actions", "付款下一步", "deferred"),
    )

    def __init__(self, env):
        super().__init__(env, build_payment_slice_service(env))

    def resolve_first_action(self, runtime_fetch_hints):
        blocks = runtime_fetch_hints.get("blocks") if isinstance(runtime_fetch_hints.get("blocks"), dict) else {}
        return blocks.get("payment_entry") or blocks.get("payment_list") or {}

    def resolve_title(self, project_payload):
        return "付款记录：%s" % str(project_payload.get("name") or "项目")
