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


def _parse_action_ref(action_ref: Any) -> tuple[str, int]:
    text = _to_text(action_ref)
    if not text or "," not in text:
        return "", 0
    model_name, action_id = text.split(",", 1)
    model_name = _to_text(model_name)
    try:
        action_id_int = int(_to_text(action_id))
    except Exception:
        action_id_int = 0
    return model_name, action_id_int


def _allow_for_user(menu_row: Dict[str, Any], user_group_ids: set[int]) -> bool:
    groups = menu_row.get("groups_id")
    if not isinstance(groups, list) or not groups:
        return True
    return bool(user_group_ids.intersection({int(gid) for gid in groups if int(gid or 0) > 0}))


def project_menu_capabilities(env, user=None, *, limit: int = 600) -> List[Dict[str, Any]]:
    menu_model = env["ir.ui.menu"].sudo()
    menu_rows = menu_model.search_read(
        [("active", "=", True), ("action", "!=", False)],
        fields=["id", "name", "action", "groups_id", "parent_id", "web_icon"],
        limit=limit,
        order="id asc",
    )
    if not isinstance(menu_rows, list) or not menu_rows:
        return []

    user_group_ids = set((user or env.user).groups_id.ids)
    menu_ids = [int(row.get("id") or 0) for row in menu_rows if int(row.get("id") or 0) > 0]
    xmlid_map = _safe_xmlid_map(env, "ir.ui.menu", menu_ids)

    projected: List[Dict[str, Any]] = []
    for row in menu_rows:
        menu_id = int(row.get("id") or 0)
        if menu_id <= 0:
            continue
        if not _allow_for_user(row, user_group_ids):
            continue

        action_model, action_id = _parse_action_ref(row.get("action"))
        xmlid = xmlid_map.get(menu_id, "")
        cap_key = f"native.menu.{xmlid or menu_id}"
        cap_name = _to_text(row.get("name")) or cap_key
        group_key = "native_menu_entry"
        icon = _to_text(row.get("web_icon"))

        projected.append(
            {
                "identity": {
                    "key": cap_key,
                    "name": cap_name,
                    "domain": "native.odoo",
                    "type": "native_menu_entry",
                    "version": "v1",
                },
                "ownership": {
                    "owner_module": "smart_core",
                    "source_module": "smart_core.native.menu",
                    "source_kind": "native_projection",
                },
                "ui": {
                    "label": cap_name,
                    "hint": "Projected from ir.ui.menu",
                    "group_key": group_key,
                    "icon": icon,
                    "sequence": menu_id,
                    "tags": ["native", "menu", "odoo"],
                },
                "binding": {
                    "intent": {
                        "primary_intent": "app.open",
                    },
                    "exposure": {
                        "menu_xmlid": xmlid,
                        "menu_id": menu_id,
                        "action_model": action_model,
                        "action_id": action_id,
                        "action_ref": _to_text(row.get("action")),
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
                    "supports_execute": False,
                    "supports_batch": False,
                    "safe_fallback": "workspace.home",
                },
                "audit": {
                    "audit_enabled": True,
                    "policy_trace_enabled": True,
                    "owner_trace": "smart_core.native.menu_adapter",
                },
            }
        )
    return projected

