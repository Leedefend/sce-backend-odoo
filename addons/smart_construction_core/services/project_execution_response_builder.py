# -*- coding: utf-8 -*-
from __future__ import annotations

import time
from typing import Any, Dict


class ProjectExecutionResponseBuilder:
    @staticmethod
    def _meta(*, intent: str, ts0: float, trace_id: str) -> Dict[str, Any]:
        return {
            "intent": str(intent or ""),
            "elapsed_ms": int((time.time() - float(ts0 or 0.0)) * 1000),
            "trace_id": str(trace_id or ""),
        }

    @classmethod
    def input_error(
        cls,
        *,
        intent: str,
        ts0: float,
        trace_id: str,
        code: str,
        message: str,
        reason_code: str,
        suggested_action: str,
        data: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        return {
            "ok": False,
            "error": {
                "code": str(code or ""),
                "message": str(message or ""),
                "reason_code": str(reason_code or ""),
                "suggested_action": str(suggested_action or ""),
            },
            "data": dict(data or {}),
            "meta": cls._meta(intent=intent, ts0=ts0, trace_id=trace_id),
        }

    @classmethod
    def blocked(
        cls,
        *,
        intent: str,
        ts0: float,
        trace_id: str,
        project_id: int,
        from_state: str,
        to_state: str,
        reason_code: str,
        suggested_action: Dict[str, Any] | None = None,
        lifecycle_hints: Dict[str, Any] | None = None,
        suggested_action_payload: Dict[str, Any] | None = None,
        extra_data: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        data = {
            "result": "blocked",
            "project_id": int(project_id or 0),
            "from_state": str(from_state or ""),
            "to_state": str(to_state or ""),
            "reason_code": str(reason_code or ""),
            "suggested_action": dict(suggested_action or {}),
            "lifecycle_hints": dict(lifecycle_hints or {}),
        }
        if isinstance(suggested_action_payload, dict) and suggested_action_payload:
            data["suggested_action_payload"] = dict(suggested_action_payload)
        if isinstance(extra_data, dict) and extra_data:
            data.update(extra_data)
        return {
            "ok": True,
            "data": data,
            "meta": cls._meta(intent=intent, ts0=ts0, trace_id=trace_id),
        }

    @classmethod
    def success(
        cls,
        *,
        intent: str,
        ts0: float,
        trace_id: str,
        data: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        return {
            "ok": True,
            "data": dict(data or {}),
            "meta": cls._meta(intent=intent, ts0=ts0, trace_id=trace_id),
        }
