from __future__ import annotations

from typing import Any, Dict

from ..contracts.results import LoadContractResultV2


class LoadContractServiceV2:
    def execute_stub(self, *, payload: Dict[str, Any], context: Dict[str, Any]) -> LoadContractResultV2:
        if bool((payload or {}).get("raise_handler_error")):
            raise RuntimeError("load_contract handler forced error")

        return LoadContractResultV2(
            intent="load_contract",
            model=str((payload or {}).get("model") or ""),
            view_type=str((payload or {}).get("view_type") or "tree"),
            schema_validated=bool((payload or {}).get("schema_validated")),
            trace_id=str((context or {}).get("trace_id") or ""),
            status="execution_closure",
            version="v2",
            phase="boundary_closure",
        )
