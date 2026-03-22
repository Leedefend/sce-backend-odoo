# -*- coding: utf-8 -*-
from __future__ import annotations

import time
from typing import Any, Dict

from odoo.addons.smart_core.core.base_handler import BaseIntentHandler


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

    def handle(self, payload=None, ctx=None):
        ts0 = time.time()
        params = payload or self.params or {}
        if isinstance(params, dict) and isinstance(params.get("params"), dict):
            params = params.get("params") or {}
        ctx = ctx or {}
        project_id = self._resolve_project_id(params, ctx)
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
        task_model = self.env["project.task"]
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
                    "reason_code": "PROJECT_NOT_FOUND",
                    "suggested_action": {
                        "key": "return_execution_entry",
                        "intent": "project.execution.enter",
                        "params": {"project_id": project_id},
                        "reason_code": "PROJECT_NOT_FOUND",
                    },
                },
                "meta": {
                    "intent": self.INTENT_TYPE,
                    "elapsed_ms": int((time.time() - ts0) * 1000),
                    "trace_id": trace_id,
                },
            }

        task_domain = [("project_id", "=", int(project.id))]
        try:
            task_total = int(task_model.search_count(task_domain))
        except Exception:
            task_total = 0
        blocked_count = 0
        if "kanban_state" in getattr(task_model, "_fields", {}):
            try:
                blocked_count = int(task_model.search_count(task_domain + [("kanban_state", "=", "blocked")]))
            except Exception:
                blocked_count = 0

        if task_total <= 0:
            return {
                "ok": True,
                "data": {
                    "result": "blocked",
                    "project_id": int(project.id),
                    "reason_code": "EXECUTION_TASKS_MISSING",
                    "suggested_action": {
                        "key": "return_execution_entry",
                        "intent": "project.execution.enter",
                        "params": {"project_id": int(project.id)},
                        "reason_code": "EXECUTION_TASKS_MISSING",
                    },
                },
                "meta": {
                    "intent": self.INTENT_TYPE,
                    "elapsed_ms": int((time.time() - ts0) * 1000),
                    "trace_id": trace_id,
                },
            }

        if blocked_count > 0:
            return {
                "ok": True,
                "data": {
                    "result": "blocked",
                    "project_id": int(project.id),
                    "reason_code": "EXECUTION_TASKS_BLOCKED",
                    "suggested_action": {
                        "key": "refresh_execution_tasks",
                        "intent": "project.execution.block.fetch",
                        "params": {"project_id": int(project.id), "block_key": "execution_tasks"},
                        "reason_code": "EXECUTION_TASKS_BLOCKED",
                    },
                },
                "meta": {
                    "intent": self.INTENT_TYPE,
                    "elapsed_ms": int((time.time() - ts0) * 1000),
                    "trace_id": trace_id,
                },
            }

        return {
            "ok": True,
            "data": {
                "result": "success",
                "project_id": int(project.id),
                "reason_code": "EXECUTION_ADVANCED",
                "suggested_action": {
                    "key": "refresh_execution_tasks",
                    "intent": "project.execution.block.fetch",
                    "params": {"project_id": int(project.id), "block_key": "execution_tasks"},
                    "reason_code": "EXECUTION_ADVANCED",
                },
            },
            "meta": {
                "intent": self.INTENT_TYPE,
                "elapsed_ms": int((time.time() - ts0) * 1000),
                "trace_id": trace_id,
            },
        }
