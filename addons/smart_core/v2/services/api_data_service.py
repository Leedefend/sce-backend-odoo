from __future__ import annotations

from typing import Any, Dict

from ..contracts.results import ApiDataResultV2


class ApiDataServiceV2:
    def execute_stub(self, *, payload: Dict[str, Any], context: Dict[str, Any]) -> ApiDataResultV2:
        if bool((payload or {}).get("raise_handler_error")):
            raise RuntimeError("api_data handler forced error")

        return ApiDataResultV2(
            intent="api.data",
            model=str((payload or {}).get("model") or ""),
            operation=str((payload or {}).get("operation") or "read"),
            schema_validated=bool((payload or {}).get("schema_validated")),
            trace_id=str((context or {}).get("trace_id") or ""),
            status="execution_closure",
            version="v2",
            phase="boundary_closure",
        )
