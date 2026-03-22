# -*- coding: utf-8 -*-
from __future__ import annotations

import time
from typing import Any, Dict

from odoo.addons.smart_core.core.base_handler import BaseIntentHandler
from odoo.addons.smart_construction_core.handlers.project_dashboard_enter import ProjectDashboardEnterHandler


class ProjectDashboardOpenHandler(BaseIntentHandler):
    INTENT_TYPE = "project.dashboard.open"
    DESCRIPTION = "兼容别名：转发到 project.dashboard.enter"
    VERSION = "1.0.0"
    ETAG_ENABLED = False
    REQUIRED_GROUPS = ["base.group_user"]

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
            (params or {}).get("record_id"),
            ((params or {}).get("project_context") or {}).get("project_id")
            if isinstance((params or {}).get("project_context"), dict)
            else None,
            (ctx or {}).get("project_id"),
            (ctx or {}).get("record_id"),
        ]
        for item in candidates:
            project_id = self._coerce_project_id(item)
            if project_id > 0:
                return project_id
        return 0

    def handle(self, payload=None, ctx=None):
        ts0 = time.time()
        params = payload or self.params or {}
        if isinstance(params, dict) and isinstance(params.get("params"), dict):
            params = params.get("params") or {}
        ctx = ctx or {}
        project_id = self._resolve_project_id(params, ctx)
        delegate = ProjectDashboardEnterHandler(self.env, payload={"project_id": project_id}, context=self.context)
        delegated = delegate.handle(payload={"project_id": project_id}, ctx=ctx)
        meta = delegated.get("meta") if isinstance(delegated.get("meta"), dict) else {}
        meta.update(
            {
                "intent": self.INTENT_TYPE,
                "deprecated": True,
                "deprecated_replacement_intent": "project.dashboard.enter",
                "deprecated_removal_phase": "Phase 12-G",
            }
        )
        if delegated.get("ok") is not True:
            delegated["meta"] = meta
            return delegated
        data = delegated.get("data") if isinstance(delegated.get("data"), dict) else {}
        return {
            "ok": True,
            "data": {
                "alias_intent": self.INTENT_TYPE,
                "target_intent": "project.dashboard.enter",
                "project_id": int(data.get("project_id") or 0),
                "entry": data,
            },
            "meta": meta,
        }
