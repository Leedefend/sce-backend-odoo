from __future__ import annotations

from ..contracts.results import ApiOnchangeResultV2


class ApiOnchangeResponseBuilderV2:
    def build(self, result: ApiOnchangeResultV2) -> dict:
        return {
            "intent": str(result.intent or "api.onchange"),
            "model": str(result.model or ""),
            "field_name": str(result.field_name or ""),
            "schema_validated": bool(result.schema_validated),
            "trace_id": str(result.trace_id or ""),
            "status": str(result.status or "execution_closure"),
            "version": str(result.version or "v2"),
            "phase": str(result.phase or "boundary_closure"),
        }


def build_api_onchange_response(result: ApiOnchangeResultV2) -> dict:
    return ApiOnchangeResponseBuilderV2().build(result)
