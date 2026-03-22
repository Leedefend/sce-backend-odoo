# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo.addons.smart_core.core.base_handler import BaseIntentHandler
from odoo.addons.smart_core.orchestration.project_dashboard_contract_orchestrator import (
    ProjectDashboardContractOrchestrator,
)


class ProjectDashboardHandler(BaseIntentHandler):
    INTENT_TYPE = "project.dashboard"
    DESCRIPTION = "Project management dashboard contract"
    VERSION = "1.0.0"
    ETAG_ENABLED = False

    @staticmethod
    def _coerce_project_id(raw):
        try:
            value = int(raw or 0)
        except Exception:
            return 0
        return value if value > 0 else 0

    def _resolve_project_id(self, params, ctx):
        payload = self.payload if isinstance(self.payload, dict) else {}
        candidates = [
            (params or {}).get("project_id"),
            payload.get("project_id"),
            (ctx or {}).get("project_id"),
        ]
        model = str((ctx or {}).get("model") or "").strip()
        if model == "project.project":
            candidates.append((ctx or {}).get("record_id"))
        for item in candidates:
            project_id = self._coerce_project_id(item)
            if project_id > 0:
                return project_id
        return 0

    def handle(self, payload=None, ctx=None):
        params = payload or self.params or {}
        ctx = ctx or {}
        project_id = self._resolve_project_id(params, ctx)
        orchestrator = ProjectDashboardContractOrchestrator(self.env)
        data = orchestrator.build_contract(project_id=project_id, context=ctx)
        dashboard_contract = orchestrator.build_dashboard_contract_v1(data, project_id=project_id)
        data["dashboard_contract"] = dashboard_contract
        data["project_context"] = {"project_id": int(project_id or 0)}
        trace_id = str((ctx or {}).get("trace_id") or (params or {}).get("trace_id") or "")
        return {
            "ok": True,
            "data": data,
            "meta": {
                "intent": self.INTENT_TYPE,
                "trace_id": trace_id,
                "contract_version": "v1",
            },
        }
