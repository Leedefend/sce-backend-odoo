from __future__ import annotations

from typing import Any, Dict

from ..contracts.results import ApiDataBatchResultV2


class ApiDataBatchServiceV2:
    def execute_stub(self, *, payload: Dict[str, Any], context: Dict[str, Any]) -> ApiDataBatchResultV2:
        if bool((payload or {}).get("raise_handler_error")):
            raise RuntimeError("api_data_batch handler forced error")

        operations = (payload or {}).get("operations")
        operation_count = len(operations) if isinstance(operations, list) else 0

        return ApiDataBatchResultV2(
            intent="api.data.batch",
            model=str((payload or {}).get("model") or ""),
            operation_count=int(operation_count),
            schema_validated=bool((payload or {}).get("schema_validated")),
            trace_id=str((context or {}).get("trace_id") or ""),
            status="execution_closure",
            version="v2",
            phase="boundary_closure",
        )
