from __future__ import annotations

from ..contracts.results import ApiDataUnlinkResultV2


class ApiDataUnlinkResponseBuilderV2:
    def build(self, result: ApiDataUnlinkResultV2) -> dict:
        return {
            "intent": str(result.intent or "api.data.unlink"),
            "model": str(result.model or ""),
            "ids": [int(value) for value in (result.ids or [])],
            "schema_validated": bool(result.schema_validated),
            "trace_id": str(result.trace_id or ""),
            "status": str(result.status or "execution_closure"),
            "version": str(result.version or "v2"),
            "phase": str(result.phase or "boundary_closure"),
        }


def build_api_data_unlink_response(result: ApiDataUnlinkResultV2) -> dict:
    return ApiDataUnlinkResponseBuilderV2().build(result)
