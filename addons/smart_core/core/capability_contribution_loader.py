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
    key = str(row.get("key") or "").strip()
    if not key:
        return None
    normalized = dict(row)
    normalized["key"] = key
    normalized["source_module"] = str(row.get("source_module") or module_name)
    normalized["owner_module"] = str(row.get("owner_module") or module_name)
    normalized["status"] = str(row.get("status") or "active")
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
