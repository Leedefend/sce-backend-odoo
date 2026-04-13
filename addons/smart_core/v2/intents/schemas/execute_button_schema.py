from __future__ import annotations

from typing import Any, Dict


class ExecuteButtonRequestSchemaV2:
    schema_name = "v2.execute_button.request.v1"

    @staticmethod
    def validate(payload: Dict[str, Any], context: Dict[str, Any] | None = None) -> Dict[str, Any]:
        data = payload if isinstance(payload, dict) else {}
        model = str(data.get("model") or "").strip()
        if not model:
            raise ValueError("model is required")
        button_name = str(data.get("button_name") or "").strip()
        if not button_name:
            raise ValueError("button_name is required")
        record_id = int(data.get("record_id") or 0)
        if record_id <= 0:
            raise ValueError("record_id must be positive")
        trace_id = ""
        if isinstance(context, dict):
            trace_id = str(context.get("trace_id") or "")
        return {
            "model": model,
            "record_id": record_id,
            "button_name": button_name,
            "schema_validated": True,
            "schema_trace_id": trace_id,
            "raise_handler_error": bool(data.get("raise_handler_error")),
        }
