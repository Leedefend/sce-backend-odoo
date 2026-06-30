# -*- coding: utf-8 -*-
from __future__ import annotations

import time

from odoo.addons.smart_core.core.base_handler import BaseIntentHandler
from odoo.addons.smart_construction_core.handlers.project_context_resolver import (
    ProjectContextResolverMixin,
)
from odoo.addons.smart_construction_core.services.project_entry_context_service import (
    ProjectEntryContextService,
)


class ProjectEntryContextOptionsHandler(ProjectContextResolverMixin, BaseIntentHandler):
    INTENT_TYPE = "project.entry.context.options"
    DESCRIPTION = "返回驾驶舱可切换项目列表"
    VERSION = "1.0.0"
    ETAG_ENABLED = False
    REQUIRED_GROUPS = ["base.group_user"]
    SOURCE_AUTHORITY = {
        "kind": "project_entry_context_projection",
        "authorities": ["project.project", "ir.model.access", "ir.rule", "odoo.orm"],
        "projection_only": True,
        "runtime_carrier": "project_context_selector_contract",
    }
    PROJECT_ID_PARAM_RECORD_ID = False
    PROJECT_ID_CTX_RECORD_ID = False

    def handle(self, payload=None, ctx=None):
        ts0 = time.time()
        params = payload or self.params or {}
        if isinstance(params, dict) and isinstance(params.get("params"), dict):
            params = params.get("params") or {}
        ctx = ctx or {}
        service = ProjectEntryContextService(self.env)
        data = service.list_options(
            active_project_id=self._resolve_project_id(params, ctx),
            company_id=self._resolve_company_id(params, ctx),
            operation_strategy=self._resolve_operation_strategy(params, ctx),
        )
        return {
            "ok": True,
            "data": data,
            "meta": {
                "intent": self.INTENT_TYPE,
                "elapsed_ms": int((time.time() - ts0) * 1000),
                "trace_id": str((self.context or {}).get("trace_id") or ""),
                "source_authority": self.SOURCE_AUTHORITY,
            },
        }
