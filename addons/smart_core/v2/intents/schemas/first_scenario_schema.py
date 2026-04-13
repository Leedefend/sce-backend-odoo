from __future__ import annotations

from typing import Any, Dict


class FirstScenarioRequestSchemaV2:
    schema_name = "v2.app.init.request.v1"

    @staticmethod
    def validate(payload: Dict[str, Any], context: Dict[str, Any] | None = None) -> Dict[str, Any]:
        data = payload if isinstance(payload, dict) else {}
        app_key = str(data.get("app_key") or "platform").strip() or "platform"
        model = str(data.get("model") or "").strip()
        if not model:
            raise ValueError("model is required")
        view_type = str(data.get("view_type") or "form").strip().lower() or "form"
        trace_id = ""
        if isinstance(context, dict):
            trace_id = str(context.get("trace_id") or "")
        return {
            "app_key": app_key,
            "model": model,
            "view_type": view_type,
            "schema_validated": True,
            "schema_trace_id": trace_id,
        }
