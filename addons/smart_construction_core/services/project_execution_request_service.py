# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, Tuple

from odoo.addons.smart_construction_core.services.project_execution_state_machine import (
    ProjectExecutionStateMachine,
)


class ProjectExecutionRequestService:
    @staticmethod
    def _coerce_positive_id(raw: Any) -> int:
        try:
            value = int(raw or 0)
        except Exception:
            return 0
        return value if value > 0 else 0

    @classmethod
    def resolve_request(cls, payload: Dict[str, Any] | None, ctx: Dict[str, Any] | None) -> Tuple[int, int, str]:
        params = payload or {}
        if isinstance(params, dict) and isinstance(params.get("params"), dict):
            params = params.get("params") or {}
        context = ctx or {}
        project_id = cls._resolve_project_id(params, context)
        task_id = cls._resolve_task_id(params, context)
        target_state = cls._resolve_target_state(params)
        return project_id, task_id, target_state

    @classmethod
    def _resolve_project_id(cls, params: Dict[str, Any], ctx: Dict[str, Any]) -> int:
        candidates = [
            (params or {}).get("project_id"),
            (params or {}).get("record_id"),
            (ctx or {}).get("project_id"),
            (ctx or {}).get("record_id"),
        ]
        for item in candidates:
            project_id = cls._coerce_positive_id(item)
            if project_id > 0:
                return project_id
        return 0

    @classmethod
    def _resolve_task_id(cls, params: Dict[str, Any], ctx: Dict[str, Any]) -> int:
        candidates = [
            (params or {}).get("task_id"),
            (params or {}).get("taskId"),
            (ctx or {}).get("task_id"),
            (ctx or {}).get("taskId"),
        ]
        for item in candidates:
            task_id = cls._coerce_positive_id(item)
            if task_id > 0:
                return task_id
        return 0

    @staticmethod
    def _resolve_target_state(params: Dict[str, Any]) -> str:
        raw = (params or {}).get("target_state")
        if not str(raw or "").strip():
            return ""
        return ProjectExecutionStateMachine.normalize_state(raw)
