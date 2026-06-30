# -*- coding: utf-8 -*-
from __future__ import annotations

import time

from odoo.exceptions import UserError

from odoo.addons.smart_core.core.base_handler import BaseIntentHandler
from odoo.addons.smart_core.core.project_context import (
    project_scope_denied_response,
    selected_project_id_from_context,
)
from odoo.addons.smart_construction_core.services.cost_tracking_service import CostTrackingService
from odoo.addons.smart_construction_core.handlers.project_context_resolver import (
    ProjectContextResolverMixin,
)


class CostTrackingRecordCreateHandler(ProjectContextResolverMixin, BaseIntentHandler):
    INTENT_TYPE = "cost.tracking.record.create"
    DESCRIPTION = "创建最小项目成本记录"
    VERSION = "1.0.0"
    ETAG_ENABLED = False
    REQUIRED_GROUPS = ["base.group_user"]
    ACL_MODE = "explicit_check"
    PROJECT_ID_PARAM_RECORD_ID = False

    def handle(self, payload=None, ctx=None):
        ts0 = time.time()
        source_authority = CostTrackingService.write_source_authority_contract()
        params = payload or self.params or {}
        if isinstance(params, dict) and isinstance(params.get("params"), dict):
            params = params.get("params") or {}
        ctx = ctx or {}
        trace_id = str((self.context or {}).get("trace_id") or "")
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
        if project_id <= 0:
            return {
                "ok": False,
                "error": {
                    "code": "PROJECT_CONTEXT_MISSING",
                    "message": "缺少 project_id，无法创建成本记录",
                    "suggested_action": "fix_input",
                },
                "meta": {"intent": self.INTENT_TYPE, "elapsed_ms": int((time.time() - ts0) * 1000), "trace_id": trace_id, "source_authority": source_authority},
            }

        service = CostTrackingService(self.env)
        project, _diag = service.resolve_project_with_diagnostics(project_id)
        if not project:
            return {
                "ok": False,
                "error": {
                    "code": "PROJECT_NOT_FOUND",
                    "message": "项目不存在或当前账号不可访问",
                    "suggested_action": "fix_input",
                },
                "meta": {"intent": self.INTENT_TYPE, "elapsed_ms": int((time.time() - ts0) * 1000), "trace_id": trace_id, "source_authority": source_authority},
            }

        try:
            result = service.create_cost_entry(project=project, values=params, context=ctx)
        except UserError as exc:
            return {
                "ok": False,
                "error": {
                    "code": "COST_ENTRY_CREATE_FAILED",
                    "message": str(exc),
                    "suggested_action": "fix_input",
                },
                "meta": {"intent": self.INTENT_TYPE, "elapsed_ms": int((time.time() - ts0) * 1000), "trace_id": trace_id, "source_authority": source_authority},
            }

        return {
            "ok": True,
            "data": result,
            "meta": {"intent": self.INTENT_TYPE, "elapsed_ms": int((time.time() - ts0) * 1000), "trace_id": trace_id, "source_authority": source_authority},
        }
