# -*- coding: utf-8 -*-
# smart_core/core/system_init_dictionary_data_helper.py

from __future__ import annotations

from typing import Any, Dict, List, Tuple


def _fetch_role_entries(env) -> List[dict]:
    rows = env["sc.dictionary"].sudo().search_read(
        [("type", "=", "role_entry"), ("active", "=", True)],
        fields=["code", "name", "scope_type", "scope_ref", "value_json", "sequence"],
        limit=200,
        order="sequence asc, id asc",
    )
    grouped: Dict[str, List[dict]] = {}
    for row in rows:
        scope_type = str(row.get("scope_type") or "").strip() or "global"
        scope_ref = str(row.get("scope_ref") or "").strip()
        role_code = scope_ref if scope_type == "role" else "__global__"
        if not role_code:
            continue
        value_json = row.get("value_json") if isinstance(row.get("value_json"), dict) else {}
        entry_key = (
            str(row.get("code") or "").strip()
            or str(value_json.get("entry_key") or "").strip()
            or str(row.get("name") or "").strip()
        )
        if not entry_key:
            continue
        grouped.setdefault(role_code, []).append(
            {
                "entry_key": entry_key,
                "entry_type": str(value_json.get("entry_type") or "menu").strip() or "menu",
                "is_enabled": bool(value_json.get("is_enabled", True)),
                "sequence": int(row.get("sequence") or 10),
            }
        )

    if not grouped:
        return []

    return [
        {"role_code": role_code, "entries": entries}
        for role_code, entries in sorted(grouped.items(), key=lambda item: str(item[0]))
    ]


def _fetch_home_blocks(env) -> List[dict]:
    rows = env["sc.dictionary"].sudo().search_read(
        [("type", "=", "home_block"), ("active", "=", True)],
        fields=["code", "name", "scope_type", "scope_ref", "value_json", "sequence"],
        limit=200,
        order="sequence asc, id asc",
    )
    grouped: Dict[str, List[Tuple[int, str]]] = {}
    for row in rows:
        scope_type = str(row.get("scope_type") or "").strip() or "global"
        scope_ref = str(row.get("scope_ref") or "").strip()
        role_code = scope_ref if scope_type == "role" else "__global__"
        if not role_code:
            continue

        value_json = row.get("value_json") if isinstance(row.get("value_json"), dict) else {}
        is_enabled = value_json.get("is_enabled")
        if isinstance(is_enabled, bool) and not is_enabled:
            continue

        block_key = (
            str(row.get("code") or "").strip()
            or str(value_json.get("block_key") or "").strip()
            or str(row.get("name") or "").strip()
        )
        if not block_key:
            continue

        sequence = int(row.get("sequence") or 10)
        grouped.setdefault(role_code, []).append((sequence, block_key))

    if not grouped:
        return []

    return [
        {
            "role_code": role_code,
            "blocks": [item[1] for item in sorted(blocks, key=lambda pair: (pair[0], pair[1]))],
        }
        for role_code, blocks in sorted(grouped.items(), key=lambda item: str(item[0]))
    ]


def apply_dictionary_startup_data(env, data: Dict[str, Any]) -> Dict[str, Any]:
    if "sc.dictionary" not in env:
        return data

    try:
        role_entries = _fetch_role_entries(env)
        if role_entries:
            data["role_entries"] = role_entries
    except Exception:
        pass

    try:
        home_blocks = _fetch_home_blocks(env)
        if home_blocks:
            data["home_blocks"] = home_blocks
    except Exception:
        pass

    return data
