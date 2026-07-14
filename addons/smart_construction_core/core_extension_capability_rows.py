# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, List


def normalize_capability_row(row: dict[str, Any]) -> dict[str, Any] | None:
    if not isinstance(row, dict):
        return None
    key = str(row.get("key") or "").strip()
    if not key:
        return None
    identity_name = str(row.get("name") or row.get("ui_label") or key).strip() or key
    group_key = str(row.get("group_key") or "others").strip() or "others"
    intent_name = str(row.get("intent") or "ui.contract").strip() or "ui.contract"
    entry_target = row.get("entry_target") if isinstance(row.get("entry_target"), dict) else {}
    entry_scene_key = str(entry_target.get("scene_key") or "").strip()
    required_roles = [str(x).strip() for x in (row.get("required_roles") or []) if str(x).strip()]
    required_groups = [str(x).strip() for x in (row.get("required_groups") or []) if str(x).strip()]
    status = str(row.get("status") or "ga").strip().lower() or "ga"
    domain = str(key.split(".")[0] if "." in key else "construction").strip() or "construction"
    sequence = int(row.get("sequence") or 0)
    tags = list(row.get("tags") or [])
    group_icon = str(row.get("group_icon") or "").strip()
    ui_label = str(row.get("ui_label") or identity_name).strip()
    ui_hint = str(row.get("ui_hint") or "").strip()
    return {
        "key": key,
        "name": identity_name,
        "domain": domain,
        "type": "entry",
        "source_module": "smart_construction_core",
        "owner_module": "smart_core",
        "status": status,
        "group_key": group_key,
        "group_label": str(row.get("group_label") or "").strip(),
        "group_icon": group_icon,
        "group_sequence": int(row.get("group_sequence") or 0),
        "ui_label": ui_label,
        "ui_hint": ui_hint,
        "intent": intent_name,
        "required_roles": required_roles,
        "required_groups": required_groups,
        "entry_target": dict(entry_target),
        "sequence": sequence,
        "tags": tags,
        "identity": {
            "key": key,
            "name": identity_name,
            "domain": domain,
            "type": "entry",
            "version": "v1",
        },
        "ownership": {
            "owner_module": "smart_core",
            "source_module": "smart_construction_core",
            "source_kind": "industry_contribution",
        },
        "ui": {
            "label": ui_label,
            "hint": ui_hint,
            "group_key": group_key,
            "icon": group_icon,
            "sequence": sequence,
            "tags": tags,
        },
        "binding": {
            "scene": {
                "entry_scene_key": entry_scene_key,
                "target_mode": str(entry_target.get("target_mode") or "scene").strip() or "scene",
            },
            "intent": {
                "primary_intent": intent_name,
            },
            "contract": {
                "subject": "scene",
                "contract_type": "entry_contract",
                "contract_version": "v1",
            },
            "exposure": {
                "group_key": group_key,
            },
        },
        "permission": {
            "required_roles": required_roles,
            "required_groups": required_groups,
            "access_mode": "execute",
            "data_scope": "user_env",
        },
        "release": {
            "tier": "standard",
            "slice": "",
            "exposure_mode": "default",
            "approval_required": False,
            "feature_flag": "",
        },
        "lifecycle": {
            "status": status,
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
            "owner_trace": "smart_construction_core.get_capability_contributions",
        },
    }


def normalize_capability_rows(rows: Any) -> List[Dict[str, Any]]:
    if not isinstance(rows, list) or not rows:
        return []
    out: List[Dict[str, Any]] = []
    for row in rows:
        normalized = normalize_capability_row(row)
        if normalized:
            out.append(normalized)
    return out
