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


def project_server_action_capabilities(env, user=None, *, limit: int = 600) -> List[Dict[str, Any]]:
    del user
    action_rows = env["ir.actions.server"].sudo().search_read(
        [("usage", "!=", "ir_cron")],
        fields=["id", "name", "model_id", "state", "binding_model_id", "binding_type"],
        limit=limit,
        order="id asc",
    )
    if not isinstance(action_rows, list) or not action_rows:
        return []

    action_ids = [int(row.get("id") or 0) for row in action_rows if int(row.get("id") or 0) > 0]
    xmlid_map = _safe_xmlid_map(env, "ir.actions.server", action_ids)

    projected: List[Dict[str, Any]] = []
    for row in action_rows:
        action_id = int(row.get("id") or 0)
        if action_id <= 0:
            continue
        name = _to_text(row.get("name")) or f"server_action_{action_id}"
        model_ref = row.get("model_id")
        model_name = _to_text(model_ref[1] if isinstance(model_ref, list) and len(model_ref) > 1 else "")
        xmlid = xmlid_map.get(action_id, "")
        cap_key = f"native.server_action.{xmlid or action_id}"

        projected.append(
            {
                "identity": {
                    "key": cap_key,
                    "name": name,
                    "domain": model_name or "native.odoo",
                    "type": "native_server_action",
                    "version": "v1",
                },
                "ownership": {
                    "owner_module": "smart_core",
                    "source_module": "smart_core.native.server_action",
                    "source_kind": "native_projection",
                },
                "ui": {
                    "label": name,
                    "hint": "Projected from ir.actions.server",
                    "group_key": "native_server_action",
                    "icon": "",
                    "sequence": action_id,
                    "tags": ["native", "server_action", "odoo"],
                },
                "binding": {
                    "contract": {
                        "subject": "native_server_action",
                        "contract_type": "server_action",
                        "contract_version": "v1",
                    },
                    "exposure": {
                        "action_id": action_id,
                        "action_xmlid": xmlid,
                        "state": _to_text(row.get("state")),
                        "binding_type": _to_text(row.get("binding_type")),
                        "model": model_name,
                    },
                    "intent": {
                        "primary_intent": "execute_button",
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
                    "supports_entry": False,
                    "supports_execute": True,
                    "supports_batch": False,
                    "safe_fallback": "",
                },
                "audit": {
                    "audit_enabled": True,
                    "policy_trace_enabled": True,
                    "owner_trace": "smart_core.native.server_action_adapter",
                },
            }
        )
    return projected

