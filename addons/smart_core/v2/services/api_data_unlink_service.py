from __future__ import annotations

from typing import Any, Dict, List

from ..contracts.results import ApiDataUnlinkResultV2


class ApiDataUnlinkServiceV2:
    def execute_stub(self, *, payload: Dict[str, Any], context: Dict[str, Any]) -> ApiDataUnlinkResultV2:
        if bool((payload or {}).get("raise_handler_error")):
            raise RuntimeError("api_data_unlink handler forced error")

        raw_ids = (payload or {}).get("ids")
        ids: List[int] = [int(value) for value in raw_ids] if isinstance(raw_ids, list) else []

        return ApiDataUnlinkResultV2(
            intent="api.data.unlink",
            model=str((payload or {}).get("model") or ""),
            ids=ids,
            schema_validated=bool((payload or {}).get("schema_validated")),
            trace_id=str((context or {}).get("trace_id") or ""),
            status="execution_closure",
            version="v2",
            phase="boundary_closure",
        )
