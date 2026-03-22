# -*- coding: utf-8 -*-
from __future__ import annotations

import time
from typing import Any, Dict

from odoo.addons.smart_core.core.base_handler import BaseIntentHandler
from odoo.addons.smart_construction_core.services.project_execution_state_machine import (
    ProjectExecutionStateMachine,
)


class ProjectExecutionAdvanceHandler(BaseIntentHandler):
    INTENT_TYPE = "project.execution.advance"
    DESCRIPTION = "执行最小推进动作"
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

    @staticmethod
    def _resolve_target_state(params: Dict[str, Any]) -> str:
        return ProjectExecutionStateMachine.normalize_state((params or {}).get("target_state"))

    @staticmethod
    def _build_suggested_action(project_id: int, reason_code: str) -> dict:
        return {
            "key": "refresh_execution_next_actions",
            "intent": "project.execution.block.fetch",
            "params": {"project_id": int(project_id), "block_key": "next_actions"},
            "reason_code": reason_code,
        }

    def handle(self, payload=None, ctx=None):
        ts0 = time.time()
        params = payload or self.params or {}
        if isinstance(params, dict) and isinstance(params.get("params"), dict):
            params = params.get("params") or {}
        ctx = ctx or {}
        project_id = self._resolve_project_id(params, ctx)
        requested_target_state = self._resolve_target_state(params)
        trace_id = str((self.context or {}).get("trace_id") or "")
        if project_id <= 0:
            return {
                "ok": False,
                "error": {
                    "code": "PROJECT_CONTEXT_MISSING",
                    "message": "缺少 project_id，无法推进执行",
                    "reason_code": "PROJECT_CONTEXT_MISSING",
                    "suggested_action": "fix_input",
                },
                "meta": {
                    "intent": self.INTENT_TYPE,
                    "elapsed_ms": int((time.time() - ts0) * 1000),
                    "trace_id": trace_id,
                },
            }

        project_model = self.env["project.project"]
        try:
            project = project_model.browse(project_id).exists()
        except Exception:
            project = False
        if not project:
            return {
                "ok": True,
                "data": {
                    "result": "blocked",
                    "project_id": project_id,
                    "from_state": "ready",
                    "to_state": "ready",
                    "reason_code": "PROJECT_NOT_FOUND",
                    "suggested_action": self._build_suggested_action(project_id, "PROJECT_NOT_FOUND"),
                },
                "meta": {
                    "intent": self.INTENT_TYPE,
                    "elapsed_ms": int((time.time() - ts0) * 1000),
                    "trace_id": trace_id,
                },
            }

        from_state = ProjectExecutionStateMachine.normalize_state(getattr(project, "sc_execution_state", "ready"))
        to_state = requested_target_state or ProjectExecutionStateMachine.default_target(from_state)
        if not ProjectExecutionStateMachine.can_transition(from_state, to_state):
            reason_code = ProjectExecutionStateMachine.transition_reason_code(from_state, to_state)
            return {
                "ok": True,
                "data": {
                    "result": "blocked",
                    "project_id": int(project.id),
                    "from_state": from_state,
                    "to_state": from_state,
                    "reason_code": reason_code,
                    "suggested_action": self._build_suggested_action(int(project.id), reason_code),
                },
                "meta": {
                    "intent": self.INTENT_TYPE,
                    "elapsed_ms": int((time.time() - ts0) * 1000),
                    "trace_id": trace_id,
                },
            }

        try:
            project.sudo().write({"sc_execution_state": to_state})
        except Exception:
            reason_code = "EXECUTION_TRANSITION_WRITE_FAILED"
            return {
                "ok": True,
                "data": {
                    "result": "blocked",
                    "project_id": int(project.id),
                    "from_state": from_state,
                    "to_state": from_state,
                    "reason_code": reason_code,
                    "suggested_action": self._build_suggested_action(int(project.id), reason_code),
                },
                "meta": {
                    "intent": self.INTENT_TYPE,
                    "elapsed_ms": int((time.time() - ts0) * 1000),
                    "trace_id": trace_id,
                },
            }

        reason_code = ProjectExecutionStateMachine.transition_reason_code(from_state, to_state)
        return {
            "ok": True,
            "data": {
                "result": "success",
                "project_id": int(project.id),
                "from_state": from_state,
                "to_state": to_state,
                "reason_code": reason_code,
                "suggested_action": self._build_suggested_action(int(project.id), reason_code),
            },
            "meta": {
                "intent": self.INTENT_TYPE,
                "elapsed_ms": int((time.time() - ts0) * 1000),
                "trace_id": trace_id,
            },
        }
