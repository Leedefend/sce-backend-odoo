from __future__ import annotations

from typing import Any, Dict


class LoadMetadataRequestSchemaV2:
    schema_name = "v2.load_metadata.request.v1"

    @staticmethod
    def validate(payload: Dict[str, Any], context: Dict[str, Any] | None = None) -> Dict[str, Any]:
        data = payload if isinstance(payload, dict) else {}
        model = str(data.get("model") or "").strip()
        if not model:
            raise ValueError("model is required")

        trace_id = ""
        if isinstance(context, dict):
            trace_id = str(context.get("trace_id") or "")

        return {
            "model": model,
            "schema_validated": True,
            "schema_trace_id": trace_id,
        }
