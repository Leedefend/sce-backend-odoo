# -*- coding: utf-8 -*-
from __future__ import annotations

import importlib
from typing import Any, Dict, List, Tuple

from odoo.addons.smart_core.utils.extension_hooks import iter_extension_modules


CapabilityContribution = Dict[str, Any]


def _safe_rows(raw: Any) -> List[Dict[str, Any]]:
    if isinstance(raw, list):
        return [item for item in raw if isinstance(item, dict)]
    if isinstance(raw, tuple):
        return [item for item in list(raw) if isinstance(item, dict)]
    return []


def _normalize_capability_row(module_name: str, row: Dict[str, Any]) -> CapabilityContribution | None:
    identity = row.get("identity") if isinstance(row.get("identity"), dict) else {}
    ownership = row.get("ownership") if isinstance(row.get("ownership"), dict) else {}
    binding = row.get("binding") if isinstance(row.get("binding"), dict) else {}
    permission = row.get("permission") if isinstance(row.get("permission"), dict) else {}
    lifecycle = row.get("lifecycle") if isinstance(row.get("lifecycle"), dict) else {}
    ui = row.get("ui") if isinstance(row.get("ui"), dict) else {}

    key = str(row.get("key") or identity.get("key") or "").strip()
    if not key:
        return None
    normalized = dict(row)
    normalized["key"] = key
    normalized["name"] = str(
        row.get("name") or identity.get("name") or ui.get("label") or row.get("ui_label") or key
    ).strip()
    normalized["group_key"] = str(row.get("group_key") or ui.get("group_key") or "others").strip() or "others"
    normalized["intent"] = str(
        row.get("intent")
        or ((binding.get("intent") or {}).get("primary_intent") if isinstance(binding.get("intent"), dict) else "")
        or "ui.contract"
    ).strip()
    scene_binding = binding.get("scene") if isinstance(binding.get("scene"), dict) else {}
    entry_target = row.get("entry_target") if isinstance(row.get("entry_target"), dict) else {}
    if not entry_target and scene_binding:
        scene_key = str(scene_binding.get("entry_scene_key") or "").strip()
        if scene_key:
            entry_target = {"scene_key": scene_key, "target_mode": str(scene_binding.get("target_mode") or "scene")}
    normalized["entry_target"] = entry_target
    normalized["required_roles"] = (
        list(row.get("required_roles") or [])
        if isinstance(row.get("required_roles"), list)
        else list(permission.get("required_roles") or [])
    )
    normalized["required_groups"] = (
        list(row.get("required_groups") or [])
        if isinstance(row.get("required_groups"), list)
        else list(permission.get("required_groups") or [])
    )
    normalized["source_module"] = str(
        row.get("source_module") or ownership.get("source_module") or module_name
    )
    normalized["owner_module"] = str(
        row.get("owner_module") or ownership.get("owner_module") or module_name
    )
    normalized["status"] = str(row.get("status") or lifecycle.get("status") or "active")
    return normalized


def collect_capability_contributions(env, user) -> Tuple[List[CapabilityContribution], List[dict]]:
    """
    Platform-owned collection path.
    Required hook: get_capability_contributions(env, user)
    """
    rows: List[CapabilityContribution] = []
    errors: List[dict] = []

    for module_name in iter_extension_modules(env):
        try:
            module = importlib.import_module(f"odoo.addons.{module_name}")
        except Exception as exc:
            errors.append({"module": module_name, "stage": "import", "error": str(exc)})
            continue

        provider = getattr(module, "get_capability_contributions", None)
        if not callable(provider):
            continue
        try:
            raw = provider(env, user)
        except Exception as exc:
            errors.append({"module": module_name, "stage": "provider", "error": str(exc)})
            continue

        for row in _safe_rows(raw):
            normalized = _normalize_capability_row(module_name, row)
            if normalized:
                rows.append(normalized)

    merged: Dict[str, CapabilityContribution] = {}
    for row in rows:
        key = str(row.get("key") or "")
        if key and key not in merged:
            merged[key] = row
    return list(merged.values()), errors


def collect_capability_group_contributions(env) -> List[dict]:
    """
    Required hook: get_capability_group_contributions(env)
    """
    groups: List[dict] = []
    seen: set[str] = set()

    for module_name in iter_extension_modules(env):
        try:
            module = importlib.import_module(f"odoo.addons.{module_name}")
        except Exception:
            continue

        provider = getattr(module, "get_capability_group_contributions", None)
        if not callable(provider):
            continue
        try:
            raw = provider(env)
        except Exception:
            continue

        for row in _safe_rows(raw):
            key = str(row.get("key") or "").strip()
            if not key or key in seen:
                continue
            seen.add(key)
            normalized = dict(row)
            normalized["key"] = key
            groups.append(normalized)

    return groups
