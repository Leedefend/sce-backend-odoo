from __future__ import annotations

from ..contracts.results import ApiDataBatchResultV2


class ApiDataBatchResponseBuilderV2:
    def build(self, result: ApiDataBatchResultV2) -> dict:
        return {
            "intent": str(result.intent or "api.data.batch"),
            "model": str(result.model or ""),
            "operation_count": int(result.operation_count or 0),
            "schema_validated": bool(result.schema_validated),
            "trace_id": str(result.trace_id or ""),
            "status": str(result.status or "execution_closure"),
            "version": str(result.version or "v2"),
            "phase": str(result.phase or "boundary_closure"),
        }


def build_api_data_batch_response(result: ApiDataBatchResultV2) -> dict:
    return ApiDataBatchResponseBuilderV2().build(result)
