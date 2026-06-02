# -*- coding: utf-8 -*-
from __future__ import annotations

import time
from typing import Any, Dict

from odoo.addons.smart_core.core.base_handler import BaseIntentHandler
from odoo.addons.smart_construction_core.services.project_entry_context_service import (
    ProjectEntryContextService,
)


class ProjectEntryContextResolveHandler(BaseIntentHandler):
    INTENT_TYPE = "project.entry.context.resolve"
    DESCRIPTION = "解析项目主入口上下文"
    VERSION = "1.0.0"
    ETAG_ENABLED = False
    REQUIRED_GROUPS = ["base.group_user"]
    SOURCE_AUTHORITY = {
        "kind": "project_entry_context_projection",
        "authorities": ["project.project", "ir.model.access", "ir.rule", "odoo.orm"],
        "projection_only": True,
        "runtime_carrier": "project_context_selector_contract",
    }

    @staticmethod
    def _coerce_project_id(raw: Any) -> int:
        try:
            value = int(raw or 0)
        except Exception:
            return 0
        return value if value > 0 else 0

    def _resolve_project_id(self, params: Dict[str, Any], ctx: Dict[str, Any]) -> int:
        candidates = [
            (params or {}).get("project_id"),
            ((params or {}).get("project_context") or {}).get("project_id")
            if isinstance((params or {}).get("project_context"), dict)
            else None,
            (ctx or {}).get("project_id"),
        ]
        for item in candidates:
            project_id = self._coerce_project_id(item)
            if project_id > 0:
                return project_id
        return 0

    def _resolve_company_id(self, params: Dict[str, Any], ctx: Dict[str, Any]) -> int:
        for raw in ((params or {}).get("company_id"), (params or {}).get("current_company_id"), (ctx or {}).get("company_id")):
            company_id = self._coerce_project_id(raw)
            if company_id > 0:
                return company_id
        return 0

    @staticmethod
    def _resolve_operation_strategy(params: Dict[str, Any], ctx: Dict[str, Any]) -> str:
        for source in (params or {}, ctx or {}):
            value = str(source.get("operation_strategy") or source.get("operationStrategy") or "").strip()
            if value in {"direct", "joint"}:
                return value
        return ""

    def handle(self, payload=None, ctx=None):
        ts0 = time.time()
        params = payload or self.params or {}
        if isinstance(params, dict) and isinstance(params.get("params"), dict):
            params = params.get("params") or {}
        ctx = ctx or {}
        project_id = self._resolve_project_id(params, ctx)
        service = ProjectEntryContextService(self.env)
        data = service.resolve(
            project_id=project_id,
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
