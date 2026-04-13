from __future__ import annotations

from ..contracts.results import ApiDataCreateResultV2


class ApiDataCreateResponseBuilderV2:
    def build(self, result: ApiDataCreateResultV2) -> dict:
        return {
            "intent": str(result.intent or "api.data.create"),
            "model": str(result.model or ""),
            "value_count": int(result.value_count or 0),
            "schema_validated": bool(result.schema_validated),
            "trace_id": str(result.trace_id or ""),
            "status": str(result.status or "execution_closure"),
            "version": str(result.version or "v2"),
            "phase": str(result.phase or "boundary_closure"),
        }


def build_api_data_create_response(result: ApiDataCreateResultV2) -> dict:
    return ApiDataCreateResponseBuilderV2().build(result)
