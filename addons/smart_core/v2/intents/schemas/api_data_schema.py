from __future__ import annotations

from typing import Any, Dict


class ApiDataRequestSchemaV2:
    schema_name = "v2.api.data.request.v1"

    @staticmethod
    def validate(payload: Dict[str, Any], context: Dict[str, Any] | None = None) -> Dict[str, Any]:
        data = payload if isinstance(payload, dict) else {}
        model = str(data.get("model") or "").strip()
        if not model:
            raise ValueError("model is required")
        operation = str(data.get("operation") or "read").strip() or "read"
        trace_id = ""
        if isinstance(context, dict):
            trace_id = str(context.get("trace_id") or "")
        return {
            "model": model,
            "operation": operation,
            "schema_validated": True,
            "schema_trace_id": trace_id,
            "raise_handler_error": bool(data.get("raise_handler_error")),
        }
