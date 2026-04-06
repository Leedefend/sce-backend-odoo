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


def project_window_action_capabilities(env, user=None, *, limit: int = 600) -> List[Dict[str, Any]]:
    action_model = env["ir.actions.act_window"].sudo()
    action_rows = action_model.search_read(
        [("type", "=", "ir.actions.act_window")],
        fields=["id", "name", "res_model", "view_mode", "target", "binding_model_id", "binding_type"],
        limit=limit,
        order="id asc",
    )
    if not isinstance(action_rows, list) or not action_rows:
        return []

    action_ids = [int(row.get("id") or 0) for row in action_rows if int(row.get("id") or 0) > 0]
    xmlid_map = _safe_xmlid_map(env, "ir.actions.act_window", action_ids)

    projected: List[Dict[str, Any]] = []
    for row in action_rows:
        action_id = int(row.get("id") or 0)
        if action_id <= 0:
            continue
        action_name = _to_text(row.get("name")) or f"act_window_{action_id}"
        res_model = _to_text(row.get("res_model"))
        xmlid = xmlid_map.get(action_id, "")
        cap_key = f"native.act_window.{xmlid or action_id}"
        domain = res_model or "native.odoo"

        projected.append(
            {
                "identity": {
                    "key": cap_key,
                    "name": action_name,
                    "domain": domain,
                    "type": "native_window_action",
                    "version": "v1",
                },
                "ownership": {
                    "owner_module": "smart_core",
                    "source_module": "smart_core.native.action",
                    "source_kind": "native_projection",
                },
                "ui": {
                    "label": action_name,
                    "hint": "Projected from ir.actions.act_window",
                    "group_key": "native_window_action",
                    "icon": "",
                    "sequence": action_id,
                    "tags": ["native", "act_window", "odoo"],
                },
                "binding": {
                    "contract": {
                        "subject": "native_window_action",
                        "contract_type": "act_window",
                        "contract_version": "v1",
                    },
                    "exposure": {
                        "action_xmlid": xmlid,
                        "action_id": action_id,
                        "res_model": res_model,
                        "view_mode": _to_text(row.get("view_mode")),
                        "target": _to_text(row.get("target")),
                        "binding_type": _to_text(row.get("binding_type")),
                    },
                },
                "permission": {
                    "required_roles": [],
                    "required_groups": [],
                    "access_mode": "execute",
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
                    "supports_entry": True,
                    "supports_execute": True,
                    "supports_batch": False,
                    "safe_fallback": "workspace.home",
                },
                "audit": {
                    "audit_enabled": True,
                    "policy_trace_enabled": True,
                    "owner_trace": "smart_core.native.action_adapter",
                },
            }
        )
    return projected

