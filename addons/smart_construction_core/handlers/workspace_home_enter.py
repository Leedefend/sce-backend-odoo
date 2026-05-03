# -*- coding: utf-8 -*-
from __future__ import annotations

import time

from odoo.addons.smart_core.core.base_handler import BaseIntentHandler
from odoo.addons.smart_construction_core.services.workspace_contract_builder import WorkspaceContractBuilder


class WorkspaceHomeEnterHandler(BaseIntentHandler):
    INTENT_TYPE = "workspace.home.enter"
    DESCRIPTION = "返回角色首页 scene contract"
    VERSION = "1.0.0"
    ETAG_ENABLED = False
    REQUIRED_GROUPS = ["base.group_user"]

    def handle(self, payload=None, ctx=None):
        ts0 = time.time()
        contract = WorkspaceContractBuilder(self.env).build()
        return {
            "ok": True,
            "data": contract,
            "meta": {
                "intent": self.INTENT_TYPE,
                "elapsed_ms": int((time.time() - ts0) * 1000),
                "source_authority": WorkspaceContractBuilder.source_authority_contract(),
            },
        }
