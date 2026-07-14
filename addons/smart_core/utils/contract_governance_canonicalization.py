# -*- coding: utf-8 -*-
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any


def _load_registry_module() -> Any:
    try:
        from . import contract_governance_registry as registry

        return registry
    except ImportError:
        spec = importlib.util.spec_from_file_location(
            "contract_governance_registry",
            Path(__file__).with_name("contract_governance_registry.py"),
        )
        if spec is None or spec.loader is None:
            raise
        registry = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(registry)
        return registry


_registry = _load_registry_module()
_CONTRACT_KEY_CANONICAL_MAP = _registry._CONTRACT_KEY_CANONICAL_MAP


def canonicalize_contract_keys(
    obj: Any,
    *,
    path: str = "$",
    conflicts: list[dict[str, Any]] | None = None,
) -> Any:
    conflicts = conflicts if isinstance(conflicts, list) else []
    if isinstance(obj, list):
        return [
            canonicalize_contract_keys(item, path=f"{path}[{idx}]", conflicts=conflicts)
            for idx, item in enumerate(obj)
        ]
    if not isinstance(obj, dict):
        return obj
    out: dict[str, Any] = {}
    source_keys: dict[str, str] = {}
    for raw_key, raw_val in obj.items():
        key = str(raw_key)
        canonical = _CONTRACT_KEY_CANONICAL_MAP.get(key, key)
        normalized_val = canonicalize_contract_keys(raw_val, path=f"{path}.{canonical}", conflicts=conflicts)
        if canonical not in out:
            out[canonical] = normalized_val
            source_keys[canonical] = key
            continue
        previous = source_keys.get(canonical, canonical)
        snake_preferred = canonical
        should_replace = key == snake_preferred and previous != snake_preferred
        conflicts.append(
            {
                "path": f"{path}.{canonical}",
                "canonical": canonical,
                "kept_from": key if should_replace else previous,
                "dropped_from": previous if should_replace else key,
            }
        )
        if should_replace:
            out[canonical] = normalized_val
            source_keys[canonical] = key
    return out
