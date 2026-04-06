# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, List


def _to_text(value: Any) -> str:
    return str(value or "").strip()


def _safe_xmlid_map(env, model: str, ids: List[int]) -> Dict[int, str]:
    if not ids:
        return {}
    out: Dict[int, str] = {}
    rows = env["ir.model.data"].sudo().search_read(
        [("model", "=", model), ("res_id", "in", ids)],
        fields=["module", "name", "res_id"],
    )
    for row in rows:
        rid = int(row.get("res_id") or 0)
        if rid <= 0:
            continue
        module = _to_text(row.get("module"))
        name = _to_text(row.get("name"))
        if module and name:
            out[rid] = f"{module}.{name}"
    return out


def project_view_binding_capabilities(env, user=None, *, limit: int = 1200) -> List[Dict[str, Any]]:
    del user
    binding_rows = env["ir.actions.act_window.view"].sudo().search_read(
        [],
        fields=["id", "act_window_id", "view_id", "view_mode", "sequence"],
        limit=limit,
        order="id asc",
    )
    if not isinstance(binding_rows, list) or not binding_rows:
        return []

    act_ids = []
    view_ids = []
    for row in binding_rows:
        act = row.get("act_window_id")
        view = row.get("view_id")
        if isinstance(act, list) and act:
            act_ids.append(int(act[0] or 0))
        if isinstance(view, list) and view:
            view_ids.append(int(view[0] or 0))

    act_xmlids = _safe_xmlid_map(env, "ir.actions.act_window", [aid for aid in act_ids if aid > 0])
    view_xmlids = _safe_xmlid_map(env, "ir.ui.view", [vid for vid in view_ids if vid > 0])

    projected: List[Dict[str, Any]] = []
    for row in binding_rows:
        binding_id = int(row.get("id") or 0)
        if binding_id <= 0:
            continue
        act_ref = row.get("act_window_id")
        view_ref = row.get("view_id")
        action_id = int(act_ref[0] if isinstance(act_ref, list) and act_ref else 0)
        view_id = int(view_ref[0] if isinstance(view_ref, list) and view_ref else 0)
        action_name = _to_text(act_ref[1] if isinstance(act_ref, list) and len(act_ref) > 1 else "")
        view_name = _to_text(view_ref[1] if isinstance(view_ref, list) and len(view_ref) > 1 else "")
        if action_id <= 0 or view_id <= 0:
            continue

        action_xmlid = act_xmlids.get(action_id, "")
        view_xmlid = view_xmlids.get(view_id, "")
        cap_key = f"native.view_binding.{action_xmlid or action_id}.{view_xmlid or view_id}"
        label = f"{action_name or action_id} -> {view_name or view_id}"

        projected.append(
            {
                "identity": {
                    "key": cap_key,
                    "name": label,
                    "domain": "native.odoo",
                    "type": "native_view_binding",
                    "version": "v1",
                },
                "ownership": {
                    "owner_module": "smart_core",
                    "source_module": "smart_core.native.view_binding",
                    "source_kind": "native_projection",
                },
                "ui": {
                    "label": label,
                    "hint": "Projected from ir.actions.act_window.view",
                    "group_key": "native_view_binding",
                    "icon": "",
                    "sequence": int(row.get("sequence") or binding_id),
                    "tags": ["native", "view_binding", "odoo"],
                },
                "binding": {
                    "contract": {
                        "subject": "native_view_binding",
                        "contract_type": "view_binding",
                        "contract_version": "v1",
                    },
                    "exposure": {
                        "binding_id": binding_id,
                        "action_id": action_id,
                        "action_xmlid": action_xmlid,
                        "view_id": view_id,
                        "view_xmlid": view_xmlid,
                        "view_mode": _to_text(row.get("view_mode")),
                    },
                },
                "permission": {
                    "required_roles": [],
                    "required_groups": [],
                    "access_mode": "readonly",
                    "data_scope": "user_env",
                },
                "release": {
                    "tier": "standard",
                    "slice": "native",
                    "exposure_mode": "default",
                    "approval_required": False,
                    "feature_flag": "",
                },
                "lifecycle": {
                    "status": "ga",
                    "deprecated": False,
                    "replacement_key": "",
                    "introduced_in": "",
                    "sunset_after": "",
                },
                "runtime": {
                    "supports_entry": False,
                    "supports_execute": False,
                    "supports_batch": False,
                    "safe_fallback": "",
                },
                "audit": {
                    "audit_enabled": True,
                    "policy_trace_enabled": True,
                    "owner_trace": "smart_core.native.view_binding_adapter",
                },
            }
        )
    return projected

