from __future__ import annotations

from typing import Any, Dict


class UIContractRequestSchemaV2:
    schema_name = "v2.ui.contract.request.v1"

    @staticmethod
    def validate(payload: Dict[str, Any], context: Dict[str, Any] | None = None) -> Dict[str, Any]:
        data = payload if isinstance(payload, dict) else {}
        op = str(data.get("op") or "model").strip().lower() or "model"
        model = str(data.get("model") or "").strip()
        action_id = int(data.get("action_id") or 0)
        if op == "model" and not model:
            raise ValueError("model is required")
        if op == "action_open" and action_id <= 0:
            raise ValueError("action_id is required")
        view_type = str(data.get("view_type") or "").strip().lower() or "form"
        record_id = int(data.get("record_id") or data.get("recordId") or data.get("res_id") or data.get("resId") or 0)
        render_profile = str(
            data.get("render_profile")
            or data.get("renderProfile")
            or data.get("profile")
            or data.get("mode")
            or ""
        ).strip().lower()
        if render_profile in {"read", "view"}:
            render_profile = "readonly"
        if render_profile not in {"create", "edit", "readonly"}:
            render_profile = ""
        trace_id = ""
        if isinstance(context, dict):
            trace_id = str(context.get("trace_id") or "")
        return {
            "op": op,
            "model": model,
            "action_id": action_id if action_id > 0 else None,
            "view_type": view_type,
            "record_id": record_id if record_id > 0 else None,
            "render_profile": render_profile,
            "contract_surface": str(data.get("contract_surface") or data.get("surface") or "").strip().lower(),
            "source_mode": str(data.get("source_mode") or "").strip().lower(),
            "schema_validated": True,
            "schema_trace_id": trace_id,
            "raise_handler_error": bool(data.get("raise_handler_error")),
        }
