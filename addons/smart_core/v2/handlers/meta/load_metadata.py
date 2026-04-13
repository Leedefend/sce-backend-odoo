from __future__ import annotations

from typing import Any, Dict

from ..base import BaseIntentHandlerV2, HandlerContextV2


class LoadMetadataHandlerV2(BaseIntentHandlerV2):
    intent_name = "load_metadata"

    def execute(self, payload: Dict[str, Any], context: HandlerContextV2) -> Dict[str, Any]:
        data = payload if isinstance(payload, dict) else {}
        return {
            "intent": self.intent_name,
            "model": str(data.get("model") or ""),
            "schema_validated": bool(data.get("schema_validated")),
            "schema_trace_id": str(data.get("schema_trace_id") or ""),
            "handler_trace_id": str(context.trace_id or ""),
            "registry_closure": True,
        }
