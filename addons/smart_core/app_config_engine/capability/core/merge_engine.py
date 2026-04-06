# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Tuple


PATCHABLE_DICT_KEYS = ("ui", "release", "lifecycle", "permission", "runtime", "audit")


def _merge_dict(base: Dict[str, Any], patch: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(base)
    out.update(patch)
    return out


def _merge_binding(base: Dict[str, Any], patch: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(base)
    for key in ("scene", "intent", "contract", "exposure"):
        current = out.get(key) if isinstance(out.get(key), dict) else {}
        incoming = patch.get(key) if isinstance(patch.get(key), dict) else {}
        if incoming:
            out[key] = _merge_dict(current, incoming)
    return out


def merge_capability_contributions(rows: Iterable[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[str]]:
    merged: Dict[str, Dict[str, Any]] = {}
    errors: List[str] = []

    for row in rows:
        if not isinstance(row, dict):
            continue
        identity = row.get("identity") if isinstance(row.get("identity"), dict) else {}
        key = str(identity.get("key") or "").strip()
        if not key:
            continue
        ownership = row.get("ownership") if isinstance(row.get("ownership"), dict) else {}
        owner_module = str(ownership.get("owner_module") or "smart_core").strip() or "smart_core"
        if key in merged:
            current_owner = str((merged[key].get("ownership") or {}).get("owner_module") or "smart_core")
            if owner_module != current_owner:
                errors.append(f"owner conflict key={key}: {current_owner} vs {owner_module}")
                continue
            patched = dict(merged[key])
            for patch_key in PATCHABLE_DICT_KEYS:
                patch_value = row.get(patch_key)
                if isinstance(patch_value, dict):
                    base = patched.get(patch_key) if isinstance(patched.get(patch_key), dict) else {}
                    patched[patch_key] = _merge_dict(base, patch_value)
            if isinstance(row.get("binding"), dict):
                patched["binding"] = _merge_binding(
                    patched.get("binding") if isinstance(patched.get("binding"), dict) else {},
                    row.get("binding") if isinstance(row.get("binding"), dict) else {},
                )
            if isinstance(row.get("tags"), list):
                base_tags = patched.get("tags") if isinstance(patched.get("tags"), list) else []
                patched["tags"] = list(dict.fromkeys([*base_tags, *row.get("tags")]))
            merged[key] = patched
            continue
        merged[key] = dict(row)

    return list(merged.values()), errors
