# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, List, Set


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


def _user_group_ids(user) -> Set[int]:
    try:
        return {int(item) for item in (user.groups_id.ids or []) if int(item or 0) > 0}
    except Exception:
        return set()


def _access_allowed_for_user(access_row: Dict[str, Any], group_ids: Set[int]) -> bool:
    groups = access_row.get("group_id")
    if not isinstance(groups, list) or len(groups) < 1:
        return True
    group_id = int(groups[0] or 0)
    if group_id <= 0:
        return True
    return group_id in group_ids


def project_model_access_capabilities(env, user=None, *, limit: int = 4000) -> List[Dict[str, Any]]:
    model_rows = env["ir.model"].sudo().search_read(
        [("transient", "=", False)],
        fields=["id", "model", "name"],
        limit=limit,
        order="id asc",
    )
    if not isinstance(model_rows, list) or not model_rows:
        return []

    model_ids = [int(row.get("id") or 0) for row in model_rows if int(row.get("id") or 0) > 0]
    if not model_ids:
        return []

    access_rows = env["ir.model.access"].sudo().search_read(
        [("model_id", "in", model_ids)],
        fields=["model_id", "group_id", "perm_read", "perm_write", "perm_create", "perm_unlink"],
        limit=limit,
    )
    if not isinstance(access_rows, list) or not access_rows:
        return []

    group_ids = _user_group_ids(user or env.user)
    model_xmlids = _safe_xmlid_map(env, "ir.model", model_ids)
    model_index = {int(row.get("id") or 0): row for row in model_rows if int(row.get("id") or 0) > 0}

    perms_by_model: Dict[int, Dict[str, bool]] = {}
    for access in access_rows:
        model_ref = access.get("model_id")
        model_id = int(model_ref[0] if isinstance(model_ref, list) and model_ref else 0)
        if model_id <= 0:
            continue
        if not _access_allowed_for_user(access, group_ids):
            continue
        bucket = perms_by_model.setdefault(
            model_id,
            {"read": False, "write": False, "create": False, "unlink": False},
        )
        bucket["read"] = bool(bucket["read"] or access.get("perm_read"))
        bucket["write"] = bool(bucket["write"] or access.get("perm_write"))
        bucket["create"] = bool(bucket["create"] or access.get("perm_create"))
        bucket["unlink"] = bool(bucket["unlink"] or access.get("perm_unlink"))

    projected: List[Dict[str, Any]] = []
    for model_id, perms in perms_by_model.items():
        if not any(perms.values()):
            continue
        model_row = model_index.get(model_id) or {}
        model_name = _to_text(model_row.get("model"))
        if not model_name:
            continue
        model_label = _to_text(model_row.get("name")) or model_name
        model_xmlid = model_xmlids.get(model_id, "")
        cap_key = f"native.model_access.{model_name}"
        access_mode = "readonly" if perms.get("read") and not (perms.get("write") or perms.get("create") or perms.get("unlink")) else "execute"

        projected.append(
            {
                "identity": {
                    "key": cap_key,
                    "name": model_label,
                    "domain": model_name,
                    "type": "native_model_access",
                    "version": "v1",
                },
                "ownership": {
                    "owner_module": "smart_core",
                    "source_module": "smart_core.native.model",
                    "source_kind": "native_projection",
                },
                "ui": {
                    "label": model_label,
                    "hint": "Projected from ir.model + ir.model.access",
                    "group_key": "native_model_access",
                    "icon": "",
                    "sequence": model_id,
                    "tags": ["native", "model_access", "odoo"],
                },
                "binding": {
                    "contract": {
                        "subject": "native_model_access",
                        "contract_type": "model_access",
                        "contract_version": "v1",
                    },
                    "exposure": {
                        "model": model_name,
                        "model_xmlid": model_xmlid,
                        "perm_read": bool(perms.get("read")),
                        "perm_write": bool(perms.get("write")),
                        "perm_create": bool(perms.get("create")),
                        "perm_unlink": bool(perms.get("unlink")),
                    },
                },
                "permission": {
                    "required_roles": [],
                    "required_groups": [],
                    "access_mode": access_mode,
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
                    "owner_trace": "smart_core.native.model_adapter",
                },
            }
        )
    return projected

