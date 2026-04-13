from __future__ import annotations

from typing import Any, Dict

from ..contracts.results import ApiOnchangeResultV2


class ApiOnchangeServiceV2:
    def execute_stub(self, *, payload: Dict[str, Any], context: Dict[str, Any]) -> ApiOnchangeResultV2:
        if bool((payload or {}).get("raise_handler_error")):
            raise RuntimeError("api_onchange handler forced error")

        return ApiOnchangeResultV2(
            intent="api.onchange",
            model=str((payload or {}).get("model") or ""),
            field_name=str((payload or {}).get("field_name") or ""),
            schema_validated=bool((payload or {}).get("schema_validated")),
            trace_id=str((context or {}).get("trace_id") or ""),
            status="execution_closure",
            version="v2",
            phase="boundary_closure",
        )
