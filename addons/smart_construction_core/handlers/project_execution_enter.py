# -*- coding: utf-8 -*-
from __future__ import annotations

import time
from typing import Any, Dict

from odoo.addons.smart_core.core.base_handler import BaseIntentHandler
from odoo.addons.smart_construction_core.orchestration.project_execution_scene_orchestrator import (
    ProjectExecutionSceneOrchestrator,
)


class ProjectExecutionEnterHandler(BaseIntentHandler):
    INTENT_TYPE = "project.execution.enter"
    DESCRIPTION = "返回项目执行最小 scene-ready contract"
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
        if project_id <= 0:
            return {
                "ok": False,
                "error": {
                    "code": "PROJECT_CONTEXT_MISSING",
                    "message": "缺少 project_id，无法进入执行场景",
                    "suggested_action": "fix_input",
                },
                "meta": {
                    "intent": self.INTENT_TYPE,
                    "elapsed_ms": int((time.time() - ts0) * 1000),
                    "trace_id": str((self.context or {}).get("trace_id") or ""),
                },
            }

        orchestrator = ProjectExecutionSceneOrchestrator(self.env)
        data = orchestrator.build_entry(project_id=project_id, context=ctx)
        if int(data.get("project_id") or 0) <= 0:
            return {
                "ok": False,
                "error": {
                    "code": "PROJECT_NOT_FOUND",
                    "message": "项目不存在或当前账号不可访问",
                    "suggested_action": "fix_input",
                },
                "meta": {
                    "intent": self.INTENT_TYPE,
                    "elapsed_ms": int((time.time() - ts0) * 1000),
                    "trace_id": str((self.context or {}).get("trace_id") or ""),
                },
            }

        return {
            "ok": True,
            "data": data,
            "meta": {
                "intent": self.INTENT_TYPE,
                "elapsed_ms": int((time.time() - ts0) * 1000),
                "trace_id": str((self.context or {}).get("trace_id") or ""),
            },
        }
