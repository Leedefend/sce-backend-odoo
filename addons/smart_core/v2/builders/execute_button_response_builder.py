from __future__ import annotations

from ..contracts.results import ExecuteButtonResultV2


class ExecuteButtonResponseBuilderV2:
    def build(self, result: ExecuteButtonResultV2) -> dict:
        return {
            "intent": str(result.intent or "execute_button"),
            "model": str(result.model or ""),
            "record_id": int(result.record_id or 0),
            "button_name": str(result.button_name or ""),
            "schema_validated": bool(result.schema_validated),
            "trace_id": str(result.trace_id or ""),
            "status": str(result.status or "execution_closure"),
            "version": str(result.version or "v2"),
            "phase": str(result.phase or "boundary_closure"),
        }


def build_execute_button_response(result: ExecuteButtonResultV2) -> dict:
    return ExecuteButtonResponseBuilderV2().build(result)
