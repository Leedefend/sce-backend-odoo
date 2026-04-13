from __future__ import annotations

from typing import Any, Dict

from ..contracts.results import ApiDataCreateResultV2


class ApiDataCreateServiceV2:
    def execute_stub(self, *, payload: Dict[str, Any], context: Dict[str, Any]) -> ApiDataCreateResultV2:
        if bool((payload or {}).get("raise_handler_error")):
            raise RuntimeError("api_data_create handler forced error")

        values = (payload or {}).get("values")
        value_count = len(values) if isinstance(values, dict) else 0

        return ApiDataCreateResultV2(
            intent="api.data.create",
            model=str((payload or {}).get("model") or ""),
            value_count=int(value_count),
            schema_validated=bool((payload or {}).get("schema_validated")),
            trace_id=str((context or {}).get("trace_id") or ""),
            status="execution_closure",
            version="v2",
            phase="boundary_closure",
        )
