from __future__ import annotations

from ..contracts.results import UIContractResultV2


class UIContractResponseBuilderV2:
    def build(self, result: UIContractResultV2) -> dict:
        payload = dict(result.contract or {}) if isinstance(result.contract, dict) else {}
        payload.update({
            "intent": str(result.intent or "ui.contract"),
            "model": str(result.model or ""),
            "view_type": str(result.view_type or "form"),
            "contract_surface": str(result.contract_surface or "governed"),
            "render_mode": str(result.render_mode or "governed"),
            "source_mode": str(result.source_mode or "v2_dispatch"),
            "governed_from_native": bool(result.governed_from_native),
            "surface_mapping": result.surface_mapping if isinstance(result.surface_mapping, dict) else {},
            "schema_validated": bool(result.schema_validated),
            "trace_id": str(result.trace_id or ""),
            "status": str(result.status or "execution_closure"),
            "version": str(result.version or "v2"),
            "phase": str(result.phase or "boundary_closure"),
        })
        return payload


def build_ui_contract_response(result: UIContractResultV2) -> dict:
    return UIContractResponseBuilderV2().build(result)
