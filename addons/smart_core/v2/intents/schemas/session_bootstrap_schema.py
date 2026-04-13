from __future__ import annotations

from typing import Any, Dict


class SessionBootstrapRequestSchemaV2:
    schema_name = "v2.session.bootstrap.request.v1"

    @staticmethod
    def validate(payload: Dict[str, Any], context: Dict[str, Any] | None = None) -> Dict[str, Any]:
        data = payload if isinstance(payload, dict) else {}
        if "app_key" in data and data.get("app_key") is not None and not isinstance(data.get("app_key"), str):
            raise ValueError("app_key must be string")
        app_key = str(data.get("app_key") or "platform").strip() or "platform"
        trace_id = ""
        if isinstance(context, dict):
            trace_id = str(context.get("trace_id") or "")
        return {
            "app_key": app_key,
            "schema_validated": True,
            "schema_trace_id": trace_id,
            "raise_handler_error": bool(data.get("raise_handler_error")),
        }
