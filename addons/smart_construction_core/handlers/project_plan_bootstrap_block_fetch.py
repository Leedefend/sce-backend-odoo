# -*- coding: utf-8 -*-
from __future__ import annotations

import time
from typing import Any, Dict

from odoo.addons.smart_core.core.base_handler import BaseIntentHandler
from odoo.addons.smart_core.orchestration.project_plan_bootstrap_scene_orchestrator import (
    ProjectPlanBootstrapSceneOrchestrator,
)


class ProjectPlanBootstrapBlockFetchHandler(BaseIntentHandler):
    INTENT_TYPE = "project.plan_bootstrap.block.fetch"
    DESCRIPTION = "按需返回 project.plan_bootstrap runtime block"
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

    @staticmethod
    def _build_lifecycle_hints(project_id: int) -> Dict[str, Any]:
        if int(project_id or 0) > 0:
            return {
                "stage": "entry_params_missing",
                "first_action": "open_project_plan_bootstrap",
                "primary_action_label": "进入计划编排",
                "suggested_action_intent": "project.plan_bootstrap.enter",
                "suggested_action_title": "进入计划编排",
            }
        return {
            "stage": "no_project_context",
            "first_action": "create_project",
            "primary_action_label": "创建项目",
            "suggested_action_intent": "project.initiation.enter",
            "suggested_action_title": "创建项目",
        }

    def handle(self, payload=None, ctx=None):
        ts0 = time.time()
        params = payload or self.params or {}
        if isinstance(params, dict) and isinstance(params.get("params"), dict):
            params = params.get("params") or {}
        ctx = ctx or {}

        project_id = self._resolve_project_id(params, ctx)
        block_key = str(params.get("block_key") or "").strip().lower()
        if project_id <= 0 or not block_key:
            return {
                "ok": False,
                "error": {
                    "code": "MISSING_PARAMS",
                    "message": "缺少参数：project_id 或 block_key",
                    "suggested_action": "fix_input",
                },
                "data": {
                    "lifecycle_hints": self._build_lifecycle_hints(project_id),
                },
                "meta": {
                    "intent": self.INTENT_TYPE,
                    "elapsed_ms": int((time.time() - ts0) * 1000),
                    "trace_id": str((self.context or {}).get("trace_id") or ""),
                },
            }

        orchestrator = ProjectPlanBootstrapSceneOrchestrator(self.env)
        data = orchestrator.build_runtime_block(block_key=block_key, project_id=project_id, context=ctx)
        return {
            "ok": True,
            "data": data,
            "meta": {
                "intent": self.INTENT_TYPE,
                "elapsed_ms": int((time.time() - ts0) * 1000),
                "trace_id": str((self.context or {}).get("trace_id") or ""),
            },
        }
