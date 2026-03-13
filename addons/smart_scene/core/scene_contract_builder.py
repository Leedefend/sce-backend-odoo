# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict


REQUIRED_TOP_LEVEL_KEYS = (
    "scene",
    "page",
    "zones",
    "record",
    "permissions",
    "actions",
    "extensions",
    "diagnostics",
)


def validate_scene_contract_shape(contract: Dict[str, Any]) -> Dict[str, Any]:
    issues = []
    if not isinstance(contract, dict):
        return {"ok": False, "issues": [{"code": "contract_not_dict"}]}
    for key in REQUIRED_TOP_LEVEL_KEYS:
        if key not in contract:
            issues.append({"code": "missing_key", "key": key})
    return {"ok": len(issues) == 0, "issues": issues}


def build_scene_contract(
    *,
    scene: Dict[str, Any],
    page: Dict[str, Any],
    zones: Dict[str, Any],
    record: Dict[str, Any] | None = None,
    permissions: Dict[str, Any] | None = None,
    actions: Dict[str, Any] | None = None,
    extensions: Dict[str, Any] | None = None,
    diagnostics: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    contract = {
        "scene": dict(scene or {}),
        "page": dict(page or {}),
        "zones": dict(zones or {}),
        "record": dict(record or {}),
        "permissions": dict(permissions or {}),
        "actions": dict(actions or {}),
        "extensions": dict(extensions or {}),
        "diagnostics": dict(diagnostics or {}),
    }
    verdict = validate_scene_contract_shape(contract)
    contract["diagnostics"]["scene_contract_shape"] = verdict
    return contract
