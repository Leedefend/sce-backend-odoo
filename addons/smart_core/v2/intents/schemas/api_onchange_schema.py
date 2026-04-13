from __future__ import annotations

from typing import Any, Dict


class ApiOnchangeRequestSchemaV2:
    schema_name = "v2.api.onchange.request.v1"

    @staticmethod
    def validate(payload: Dict[str, Any], context: Dict[str, Any] | None = None) -> Dict[str, Any]:
        data = payload if isinstance(payload, dict) else {}
        model = str(data.get("model") or "").strip()
        if not model:
            raise ValueError("model is required")
        field_name = str(data.get("field_name") or "").strip()
        if not field_name:
            raise ValueError("field_name is required")
        trace_id = ""
        if isinstance(context, dict):
            trace_id = str(context.get("trace_id") or "")
        return {
            "model": model,
            "field_name": field_name,
            "schema_validated": True,
            "schema_trace_id": trace_id,
            "raise_handler_error": bool(data.get("raise_handler_error")),
        }
