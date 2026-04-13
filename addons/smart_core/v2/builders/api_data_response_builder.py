from __future__ import annotations

from ..contracts.results import ApiDataResultV2


class ApiDataResponseBuilderV2:
    def build(self, result: ApiDataResultV2) -> dict:
        return {
            "intent": str(result.intent or "api.data"),
            "model": str(result.model or ""),
            "operation": str(result.operation or "read"),
            "schema_validated": bool(result.schema_validated),
            "trace_id": str(result.trace_id or ""),
            "status": str(result.status or "execution_closure"),
            "version": str(result.version or "v2"),
            "phase": str(result.phase or "boundary_closure"),
        }


def build_api_data_response(result: ApiDataResultV2) -> dict:
    return ApiDataResponseBuilderV2().build(result)
