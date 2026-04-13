from __future__ import annotations

from typing import Any, Dict

from ..contracts.results import ExecuteButtonResultV2


class ExecuteButtonServiceV2:
    def execute_stub(self, *, payload: Dict[str, Any], context: Dict[str, Any]) -> ExecuteButtonResultV2:
        if bool((payload or {}).get("raise_handler_error")):
            raise RuntimeError("execute_button handler forced error")

        return ExecuteButtonResultV2(
            intent="execute_button",
            model=str((payload or {}).get("model") or ""),
            record_id=int((payload or {}).get("record_id") or 0),
            button_name=str((payload or {}).get("button_name") or ""),
            schema_validated=bool((payload or {}).get("schema_validated")),
            trace_id=str((context or {}).get("trace_id") or ""),
            status="execution_closure",
            version="v2",
            phase="boundary_closure",
        )
