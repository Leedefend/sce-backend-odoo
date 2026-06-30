# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo.addons.smart_core.core.base_handler import BaseIntentHandler
from odoo.addons.smart_construction_core.handlers.project_context_resolver import (
    ProjectContextResolverMixin,
)
from odoo.addons.smart_construction_core.services.project_dashboard_service import (
    ProjectDashboardService,
)


class ProjectDashboardHandler(ProjectContextResolverMixin, BaseIntentHandler):
    INTENT_TYPE = "project.dashboard"
    DESCRIPTION = "Project management dashboard contract"
    VERSION = "1.0.0"
    ETAG_ENABLED = False
    SOURCE_KIND = "project_dashboard_business_fact_projection"
    PROJECT_ID_INCLUDE_HANDLER_PAYLOAD = True
    PROJECT_ID_PARAM_RECORD_ID = False
    PROJECT_ID_PROJECT_CONTEXT = False
    PROJECT_ID_CTX_RECORD_MODEL_ONLY = "project.project"

    def handle(self, payload=None, ctx=None):
        params = payload or self.params or {}
        ctx = ctx or {}
        project_id = self._resolve_project_id(params, ctx)
        service = ProjectDashboardService(self.env)
        data = service.build(project_id=project_id, context=ctx)
        trace_id = str((ctx or {}).get("trace_id") or (params or {}).get("trace_id") or "")
        return {
            "ok": True,
            "data": data,
            "meta": {
                "intent": self.INTENT_TYPE,
                "trace_id": trace_id,
                "contract_version": "v1",
                "source_authority": service.source_authority_contract(),
            },
        }
