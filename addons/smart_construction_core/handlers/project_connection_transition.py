# -*- coding: utf-8 -*-
from __future__ import annotations

import time
from typing import Any, Dict

from odoo.addons.smart_core.core.base_handler import BaseIntentHandler


class ProjectConnectionTransitionHandler(BaseIntentHandler):
    INTENT_TYPE = "project.connection.transition"
    DESCRIPTION = "项目连接层显式阶段推进"
    VERSION = "1.0.0"
    ETAG_ENABLED = False
    REQUIRED_GROUPS = ["base.group_user"]

    TRANSITIONS = {
        "start_execution": {"target_state": "in_progress", "reason_code": "PROJECT_START_EXECUTION"},
        "confirm_settlement": {"target_state": "closing", "reason_code": "PROJECT_CONFIRM_SETTLEMENT"},
        "complete_project": {"target_state": "closed", "reason_code": "PROJECT_COMPLETE"},
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
            (ctx or {}).get("record_id"),
        ]
        for item in candidates:
            project_id = self._coerce_project_id(item)
            if project_id > 0:
                return project_id
        return 0

    @staticmethod
    def _build_lifecycle_hints(project_id: int, *, stage: str) -> Dict[str, Any]:
        if int(project_id or 0) > 0:
            return {
                "stage": stage,
                "first_action": "open_project_dashboard",
                "primary_action_label": "进入项目管理",
                "suggested_action_intent": "project.dashboard.enter",
                "suggested_action_title": "进入项目管理",
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
        trace_id = str((self.context or {}).get("trace_id") or "")
        project_id = self._resolve_project_id(params, ctx)
        transition_key = str((params or {}).get("transition_key") or "").strip().lower()
        transition = self.TRANSITIONS.get(transition_key)
        if project_id <= 0 or not transition:
            return {
                "ok": False,
                "error": {
                    "code": "INVALID_TRANSITION_INPUT",
                    "message": "缺少 project_id 或 transition_key 不受支持",
                    "suggested_action": "fix_input",
                },
                "data": {
                    "lifecycle_hints": self._build_lifecycle_hints(project_id, stage="transition_input_missing"),
                },
                "meta": {
                    "intent": self.INTENT_TYPE,
                    "elapsed_ms": int((time.time() - ts0) * 1000),
                    "trace_id": trace_id,
                },
            }
        project = self.env["project.project"].browse(project_id).exists()
        if not project:
            return {
                "ok": False,
                "error": {
                    "code": "PROJECT_NOT_FOUND",
                    "message": "项目不存在或当前账号不可访问",
                    "suggested_action": "fix_input",
                },
                "data": {
                    "lifecycle_hints": self._build_lifecycle_hints(project_id, stage="project_not_found"),
                },
                "meta": {
                    "intent": self.INTENT_TYPE,
                    "elapsed_ms": int((time.time() - ts0) * 1000),
                    "trace_id": trace_id,
                },
            }
        from_state = str(getattr(project, "lifecycle_state", "") or "")
        target_state = str(transition.get("target_state") or "")
        try:
            project.action_set_lifecycle_state(target_state)
            result = "success"
            message = "项目阶段已推进。"
            reason_code = str(transition.get("reason_code") or "")
        except Exception as exc:
            result = "blocked"
            message = str(exc)
            target_state = from_state
            reason_code = "PROJECT_TRANSITION_BLOCKED"
        return {
            "ok": True,
            "data": {
                "result": result,
                "project_id": int(project.id),
                "transition_key": transition_key,
                "from_state": from_state,
                "to_state": target_state,
                "reason_code": reason_code,
                "message": message,
            },
            "meta": {
                "intent": self.INTENT_TYPE,
                "elapsed_ms": int((time.time() - ts0) * 1000),
                "trace_id": trace_id,
            },
        }
