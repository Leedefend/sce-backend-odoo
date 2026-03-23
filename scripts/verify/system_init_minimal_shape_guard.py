#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from system_init_minimal_surface_probe import fetch_system_init_payload


ROOT = Path(__file__).resolve().parents[2]
OUT_JSON = ROOT / "artifacts" / "backend" / "system_init_minimal_shape_guard.json"
OUT_MD = ROOT / "artifacts" / "backend" / "system_init_minimal_shape_guard.md"

REQUIRED_KEYS = {
    "user",
    "nav",
    "nav_meta",
    "default_route",
    "scene_ready_contract_v1",
    "intents",
    "feature_flags",
    "role_surface",
    "version",
    "init_meta",
}

FORBIDDEN_KEYS = {
    "scenes",
    "capabilities",
    "capability_groups",
    "page_contracts",
    "workspace_home",
    "runtime_collections",
    "ext_facts",
    "role_surface_map",
    "role_surface_override_providers",
    "surface_mapping",
}


def _write(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")


def main() -> int:
    errors: list[str] = []
    report: dict[str, Any] = {}
    try:
        result = fetch_system_init_payload()
        data = result.get("data") if isinstance(result.get("data"), dict) else {}
        keys = set(data.keys())

        missing_required = sorted(REQUIRED_KEYS - keys)
        unknown_keys = sorted(keys - REQUIRED_KEYS)
        forbidden_present = sorted(keys & FORBIDDEN_KEYS)

        if missing_required:
            errors.append(f"missing required keys: {', '.join(missing_required)}")
        if unknown_keys:
            errors.append(f"unknown keys present: {', '.join(unknown_keys)}")
        if forbidden_present:
            errors.append(f"forbidden keys present: {', '.join(forbidden_present)}")

        if not isinstance(data.get("nav"), list):
            errors.append("data.nav must be list")
        if not isinstance(data.get("default_route"), dict):
            errors.append("data.default_route must be object")
        if not isinstance(data.get("nav_meta"), dict):
            errors.append("data.nav_meta must be object")
        if not isinstance(data.get("intents"), list):
            errors.append("data.intents must be list")
        if not isinstance(data.get("feature_flags"), dict):
            errors.append("data.feature_flags must be object")
        if not isinstance(data.get("role_surface"), dict):
            errors.append("data.role_surface must be object")
        if not isinstance(data.get("version"), dict):
            errors.append("data.version must be object")
        if not isinstance(data.get("init_meta"), dict):
            errors.append("data.init_meta must be object")
        scene_ready = data.get("scene_ready_contract_v1")
        if not isinstance(scene_ready, dict):
            errors.append("data.scene_ready_contract_v1 must be object")
        elif not isinstance(scene_ready.get("scenes"), list) or not scene_ready.get("scenes"):
            errors.append("data.scene_ready_contract_v1.scenes must be non-empty list")

        report = {
            "status": "PASS" if not errors else "FAIL",
            "payload_bytes": result.get("payload_bytes"),
            "keys": sorted(keys),
            "required_keys": sorted(REQUIRED_KEYS),
            "missing_required": missing_required,
            "unknown_keys": unknown_keys,
            "forbidden_present": forbidden_present,
            "errors": errors,
        }
    except Exception as exc:
        report = {"status": "FAIL", "errors": [f"ENV_UNSTABLE: {exc}"]}
        errors = report["errors"]

    _write(OUT_JSON, json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    lines = [
        "# System Init Minimal Shape Guard",
        "",
        f"- status: {report.get('status', 'FAIL')}",
        f"- payload_bytes: {report.get('payload_bytes', '-')}",
        f"- missing_required: {', '.join(report.get('missing_required') or []) or '(none)'}",
        f"- unknown_keys: {', '.join(report.get('unknown_keys') or []) or '(none)'}",
        f"- forbidden_present: {', '.join(report.get('forbidden_present') or []) or '(none)'}",
    ]
    if errors:
        lines.extend(["", "## Errors", *[f"- {item}" for item in errors]])
    _write(OUT_MD, "\n".join(lines) + "\n")

    if errors:
        print("[system_init_minimal_shape_guard] FAIL")
        for item in errors:
            print(f" - {item}")
        return 1
    print("[system_init_minimal_shape_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
