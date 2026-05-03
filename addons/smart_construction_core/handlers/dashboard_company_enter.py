# -*- coding: utf-8 -*-
from __future__ import annotations

import time

from odoo.addons.smart_core.core.base_handler import BaseIntentHandler
from odoo.addons.smart_construction_core.services.dashboard_contract_builder import DashboardContractBuilder


class DashboardCompanyEnterHandler(BaseIntentHandler):
    INTENT_TYPE = "dashboard.company.enter"
    DESCRIPTION = "返回公司驾驶舱 scene contract"
    VERSION = "1.0.0"
    ETAG_ENABLED = False
    REQUIRED_GROUPS = ["base.group_user"]

    def handle(self, payload=None, ctx=None):
        ts0 = time.time()
        builder = DashboardContractBuilder(self.env)
        contract = builder.build()
        return {
            "ok": True,
            "data": contract,
            "meta": {
                "intent": self.INTENT_TYPE,
                "elapsed_ms": int((time.time() - ts0) * 1000),
                "source_authority": builder.source_authority_contract(),
            },
        }
