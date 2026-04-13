from __future__ import annotations

from ..contracts.results import LoadContractResultV2


class LoadContractResponseBuilderV2:
    def build(self, result: LoadContractResultV2) -> dict:
        return {
            "intent": str(result.intent or "load_contract"),
            "model": str(result.model or ""),
            "view_type": str(result.view_type or "tree"),
            "schema_validated": bool(result.schema_validated),
            "trace_id": str(result.trace_id or ""),
            "status": str(result.status or "execution_closure"),
            "version": str(result.version or "v2"),
            "phase": str(result.phase or "boundary_closure"),
        }


def build_load_contract_response(result: LoadContractResultV2) -> dict:
    return LoadContractResponseBuilderV2().build(result)
