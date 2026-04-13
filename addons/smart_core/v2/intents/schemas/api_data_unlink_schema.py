from __future__ import annotations

from typing import Any, Dict, List


class ApiDataUnlinkRequestSchemaV2:
    schema_name = "v2.api.data.unlink.request.v1"

    @staticmethod
    def validate(payload: Dict[str, Any], context: Dict[str, Any] | None = None) -> Dict[str, Any]:
        data = payload if isinstance(payload, dict) else {}
        model = str(data.get("model") or "").strip()
        if not model:
            raise ValueError("model is required")

        raw_ids = data.get("ids")
        if not isinstance(raw_ids, list) or not raw_ids:
            raise ValueError("ids must be a non-empty list")

        ids: List[int] = []
        for value in raw_ids:
            if value is None:
                continue
            ids.append(int(value))
        if not ids:
            raise ValueError("ids must contain at least one integer")

        trace_id = ""
        if isinstance(context, dict):
            trace_id = str(context.get("trace_id") or "")

        return {
            "model": model,
            "ids": ids,
            "schema_validated": True,
            "schema_trace_id": trace_id,
            "raise_handler_error": bool(data.get("raise_handler_error")),
        }
