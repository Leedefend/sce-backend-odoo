#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from system_init_minimal_surface_probe import fetch_system_init_payload


ROOT = Path(__file__).resolve().parents[2]
OUT_JSON = ROOT / "artifacts" / "backend" / "system_init_startup_layer_contract_guard.json"
OUT_MD = ROOT / "artifacts" / "backend" / "system_init_startup_layer_contract_guard.md"

BOOT_KEYS = {
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
PRELOAD_EXTRA_KEYS = {
    "workspace_home",
}
FORBIDDEN_BOOT_KEYS = {
    "workspace_home",
    "page_contracts",
    "runtime_collections",
    "scene_catalog",
    "scene_details",
    "workspace_collections",
    "scenes",
    "capabilities",
    "capability_groups",
    "ext_facts",
}
FORBIDDEN_PRELOAD_KEYS = {
    "page_contracts",
    "runtime_collections",
    "scene_catalog",
    "scene_details",
    "workspace_collections",
    "scenes",
    "capabilities",
    "capability_groups",
    "ext_facts",
}


def _write(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")


def _validate_boot(data: dict[str, Any], errors: list[str]) -> dict[str, Any]:
    keys = set(data.keys())
    unknown = sorted(keys - BOOT_KEYS)
    forbidden = sorted(keys & FORBIDDEN_BOOT_KEYS)
    init_meta = data.get("init_meta") if isinstance(data.get("init_meta"), dict) else {}
    page_contract_meta = init_meta.get("page_contract_meta") if isinstance(init_meta.get("page_contract_meta"), dict) else {}
    preload_hint = init_meta.get("workspace_home_preload_hint") if isinstance(init_meta.get("workspace_home_preload_hint"), dict) else {}
    scene_ready = data.get("scene_ready_contract_v1") if isinstance(data.get("scene_ready_contract_v1"), dict) else {}

    if unknown:
        errors.append(f"boot surface unknown keys present: {', '.join(unknown)}")
    if forbidden:
        errors.append(f"boot surface forbidden keys present: {', '.join(forbidden)}")
    if bool(init_meta.get("preload_requested")):
        errors.append("boot surface init_meta.preload_requested must be false")
    if str(page_contract_meta.get("intent") or "").strip() not in {"scene.page_contract", "page.contract"}:
        errors.append("boot surface page_contract_meta.intent must be scene.page_contract or page.contract")
    if str(preload_hint.get("intent") or "").strip() != "ui.contract":
        errors.append("boot surface workspace_home_preload_hint.intent must be ui.contract")
    if not str(preload_hint.get("scene_key") or "").strip():
        errors.append("boot surface workspace_home_preload_hint.scene_key missing")
    if not scene_ready:
        errors.append("boot surface scene_ready_contract_v1 missing or empty")
    elif not isinstance(scene_ready.get("scenes"), list) or not scene_ready.get("scenes"):
        errors.append("boot surface scene_ready_contract_v1.scenes missing or empty")

    return {
        "keys": sorted(keys),
        "unknown_keys": unknown,
        "forbidden_keys": forbidden,
        "page_contract_meta": page_contract_meta,
        "workspace_home_preload_hint": preload_hint,
        "scene_ready_loaded": bool(scene_ready),
    }


def _validate_preload(data: dict[str, Any], errors: list[str]) -> dict[str, Any]:
    keys = set(data.keys())
    allowed = BOOT_KEYS | PRELOAD_EXTRA_KEYS
    unknown = sorted(keys - allowed)
    forbidden = sorted(keys & FORBIDDEN_PRELOAD_KEYS)
    init_meta = data.get("init_meta") if isinstance(data.get("init_meta"), dict) else {}
    workspace_home = data.get("workspace_home") if isinstance(data.get("workspace_home"), dict) else {}
    scene_ready = data.get("scene_ready_contract_v1") if isinstance(data.get("scene_ready_contract_v1"), dict) else {}

    if unknown:
        errors.append(f"preload surface unknown keys present: {', '.join(unknown)}")
    if forbidden:
        errors.append(f"preload surface forbidden keys present: {', '.join(forbidden)}")
    if not bool(init_meta.get("preload_requested")):
        errors.append("preload surface init_meta.preload_requested must be true")
    if not workspace_home:
        errors.append("preload surface workspace_home missing or empty")
    if not scene_ready:
        errors.append("preload surface scene_ready_contract_v1 missing or empty")

    return {
        "keys": sorted(keys),
        "unknown_keys": unknown,
        "forbidden_keys": forbidden,
        "workspace_home_loaded": bool(workspace_home),
        "scene_ready_loaded": bool(scene_ready),
    }


def main() -> int:
    errors: list[str] = []
    report: dict[str, Any] = {}
    try:
        boot_result = fetch_system_init_payload(with_preload=False)
        preload_result = fetch_system_init_payload(with_preload=True)
        boot_data = boot_result.get("data") if isinstance(boot_result.get("data"), dict) else {}
        preload_data = preload_result.get("data") if isinstance(preload_result.get("data"), dict) else {}

        report = {
            "status": "PASS",
            "boot": {
                "payload_bytes": boot_result.get("payload_bytes"),
                **_validate_boot(boot_data, errors),
            },
            "preload": {
                "payload_bytes": preload_result.get("payload_bytes"),
                **_validate_preload(preload_data, errors),
            },
        }
        if errors:
            report["status"] = "FAIL"
            report["errors"] = errors
    except Exception as exc:
        errors = [f"ENV_UNSTABLE: {exc}"]
        report = {"status": "FAIL", "errors": errors}

    _write(OUT_JSON, json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    lines = [
        "# System Init Startup Layer Contract Guard",
        "",
        f"- status: {report.get('status', 'FAIL')}",
        f"- boot_payload_bytes: {((report.get('boot') or {}).get('payload_bytes', '-'))}",
        f"- preload_payload_bytes: {((report.get('preload') or {}).get('payload_bytes', '-'))}",
        "",
        "## Boot Layer",
        f"- keys: {', '.join(((report.get('boot') or {}).get('keys') or [])) or '(none)'}",
        f"- unknown_keys: {', '.join(((report.get('boot') or {}).get('unknown_keys') or [])) or '(none)'}",
        f"- forbidden_keys: {', '.join(((report.get('boot') or {}).get('forbidden_keys') or [])) or '(none)'}",
        "",
        "## Preload Layer",
        f"- keys: {', '.join(((report.get('preload') or {}).get('keys') or [])) or '(none)'}",
        f"- unknown_keys: {', '.join(((report.get('preload') or {}).get('unknown_keys') or [])) or '(none)'}",
        f"- forbidden_keys: {', '.join(((report.get('preload') or {}).get('forbidden_keys') or [])) or '(none)'}",
        f"- workspace_home_loaded: {((report.get('preload') or {}).get('workspace_home_loaded', False))}",
        f"- scene_ready_loaded: {((report.get('preload') or {}).get('scene_ready_loaded', False))}",
    ]
    if errors:
        lines.extend(["", "## Errors", *[f"- {item}" for item in errors]])
    _write(OUT_MD, "\n".join(lines) + "\n")

    if errors:
        print("[system_init_startup_layer_contract_guard] FAIL")
        for item in errors:
            print(f" - {item}")
        return 1
    print("[system_init_startup_layer_contract_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
