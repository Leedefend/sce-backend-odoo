# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo.addons.smart_core.core.industry_orchestration_service_adapter import (
    build_payment_slice_service,
)
from odoo.addons.smart_core.orchestration.base_scene_entry_orchestrator import BaseSceneEntryOrchestrator


class PaymentSliceContractOrchestrator(BaseSceneEntryOrchestrator):
    SOURCE_KIND = BaseSceneEntryOrchestrator.SOURCE_KIND
    NO_BUSINESS_FACT_AUTHORITY = BaseSceneEntryOrchestrator.NO_BUSINESS_FACT_AUTHORITY
    ADAPTER_LAYER = BaseSceneEntryOrchestrator.ADAPTER_LAYER

    def __init__(self, env):
        super().__init__(env, build_payment_slice_service(env))
