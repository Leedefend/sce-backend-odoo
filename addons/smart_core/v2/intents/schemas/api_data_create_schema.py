from __future__ import annotations

from typing import Any, Dict


class ApiDataCreateRequestSchemaV2:
    schema_name = "v2.api.data.create.request.v1"

    @staticmethod
    def validate(payload: Dict[str, Any], context: Dict[str, Any] | None = None) -> Dict[str, Any]:
        data = payload if isinstance(payload, dict) else {}
        model = str(data.get("model") or "").strip()
        if not model:
            raise ValueError("model is required")
        values = data.get("values")
        if not isinstance(values, dict) or not values:
            raise ValueError("values must be a non-empty dict")
        trace_id = ""
        if isinstance(context, dict):
            trace_id = str(context.get("trace_id") or "")
        return {
            "model": model,
            "values": values,
            "schema_validated": True,
            "schema_trace_id": trace_id,
            "raise_handler_error": bool(data.get("raise_handler_error")),
        }
