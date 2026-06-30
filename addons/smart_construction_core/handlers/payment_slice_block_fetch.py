# -*- coding: utf-8 -*-
from __future__ import annotations

import time

from odoo.addons.smart_core.core.base_handler import BaseIntentHandler
from odoo.addons.smart_core.core.project_context import (
    project_scope_denied_response,
    selected_project_id_from_context,
)
from odoo.addons.smart_construction_core.services.project_context_contract import (
    attach_project_context_to_runtime_payload,
)
from odoo.addons.smart_core.orchestration.payment_slice_contract_orchestrator import (
    PaymentSliceContractOrchestrator,
)
from odoo.addons.smart_construction_core.handlers.project_context_resolver import (
    ProjectContextResolverMixin,
)


class PaymentSliceBlockFetchHandler(ProjectContextResolverMixin, BaseIntentHandler):
    INTENT_TYPE = "payment.block.fetch"
    DESCRIPTION = "按需返回 payment runtime block"
    VERSION = "1.0.0"
    ETAG_ENABLED = False
    REQUIRED_GROUPS = ["base.group_user"]
    PROJECT_ID_PARAM_RECORD_ID = False

    def handle(self, payload=None, ctx=None):
        ts0 = time.time()
        params = payload or self.params or {}
        if isinstance(params, dict) and isinstance(params.get("params"), dict):
            params = params.get("params") or {}
        ctx = ctx or {}

        project_id = self._resolve_project_id(params, ctx)
        current_project_id = selected_project_id_from_context(params, ctx or self.context or {})
        if current_project_id and project_id > 0 and int(project_id) != int(current_project_id):
            return project_scope_denied_response(
                {
                    "enabled": True,
                    "project_id": int(current_project_id),
                    "applied": True,
                    "domain": [("id", "=", int(current_project_id))],
                    "model": "project.project",
                }
            )
        block_key = str(params.get("block_key") or "").strip().lower()
        orchestrator = PaymentSliceContractOrchestrator(self.env)
        source_authority = orchestrator.source_authority_contract()
        if project_id <= 0 or not block_key:
            return {
                "ok": False,
                "error": {
                    "code": "MISSING_PARAMS",
                    "message": "缺少参数：project_id 或 block_key",
                    "suggested_action": "fix_input",
                },
                "meta": {
                    "intent": self.INTENT_TYPE,
                    "elapsed_ms": int((time.time() - ts0) * 1000),
                    "trace_id": str((self.context or {}).get("trace_id") or ""),
                    "source_authority": source_authority,
                },
            }

        data = orchestrator.build_runtime_block(block_key=block_key, project_id=project_id, context=ctx)
        project, _diag = orchestrator._service.resolve_project_with_diagnostics(project_id)
        data = attach_project_context_to_runtime_payload(data, project)
        return {
            "ok": True,
            "data": data,
            "meta": {
                "intent": self.INTENT_TYPE,
                "elapsed_ms": int((time.time() - ts0) * 1000),
                "trace_id": str((self.context or {}).get("trace_id") or ""),
                "source_authority": source_authority,
            },
        }
