from __future__ import annotations

from typing import Any, Dict


class LoadContractRequestSchemaV2:
    schema_name = "v2.load_contract.request.v1"

    @staticmethod
    def validate(payload: Dict[str, Any], context: Dict[str, Any] | None = None) -> Dict[str, Any]:
        data = payload if isinstance(payload, dict) else {}
        model = str(data.get("model") or "").strip()
        if not model:
            raise ValueError("model is required")

        view_type = data.get("view_type")
        if view_type is None:
            view_type = "tree"

        trace_id = ""
        if isinstance(context, dict):
            trace_id = str(context.get("trace_id") or "")

        return {
            "model": model,
            "view_type": str(view_type or "tree"),
            "schema_validated": True,
            "schema_trace_id": trace_id,
            "raise_handler_error": bool(data.get("raise_handler_error")),
        }
