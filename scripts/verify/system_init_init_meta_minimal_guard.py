#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from system_init_minimal_surface_probe import fetch_system_init_payload


ROOT = Path(__file__).resolve().parents[2]
OUT_JSON = ROOT / "artifacts" / "backend" / "system_init_init_meta_minimal_guard.json"

ALLOWED_INIT_META_KEYS = {
    "preload_requested",
    "scene_subset",
    "scene_subset_count",
    "workspace_home_preload_hint",
    "page_contract_meta",
    "contract_mode",
}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _validate(result: dict[str, Any], *, label: str, expect_preload: bool) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    data = result.get("data") if isinstance(result.get("data"), dict) else {}
    init_meta = data.get("init_meta") if isinstance(data.get("init_meta"), dict) else {}
    keys = set(init_meta.keys())
    unknown = sorted(keys - ALLOWED_INIT_META_KEYS)
    missing = sorted(ALLOWED_INIT_META_KEYS - keys)
    if unknown:
        errors.append(f"{label} init_meta unknown keys present: {', '.join(unknown)}")
    if missing:
        errors.append(f"{label} init_meta missing keys: {', '.join(missing)}")
    if bool(init_meta.get("preload_requested")) != expect_preload:
        errors.append(f"{label} init_meta.preload_requested expected {expect_preload}")
    page_contract_meta = init_meta.get("page_contract_meta") if isinstance(init_meta.get("page_contract_meta"), dict) else {}
    preload_hint = init_meta.get("workspace_home_preload_hint") if isinstance(init_meta.get("workspace_home_preload_hint"), dict) else {}
    if set(page_contract_meta.keys()) - {"intent"}:
        errors.append(f"{label} page_contract_meta must only expose intent")
    if str(page_contract_meta.get("intent") or "").strip() not in {"scene.page_contract", "page.contract"}:
        errors.append(f"{label} page_contract_meta.intent invalid")
    if set(preload_hint.keys()) - {"intent", "scene_key"}:
        errors.append(f"{label} workspace_home_preload_hint must only expose intent/scene_key")
    if str(preload_hint.get("intent") or "").strip() != "ui.contract":
        errors.append(f"{label} workspace_home_preload_hint.intent invalid")
    return errors, {
        "keys": sorted(keys),
        "page_contract_meta": page_contract_meta,
        "workspace_home_preload_hint": preload_hint,
    }


def main() -> int:
    errors: list[str] = []
    boot = fetch_system_init_payload(with_preload=False)
    preload = fetch_system_init_payload(with_preload=True)
    boot_errors, boot_report = _validate(boot, label="boot", expect_preload=False)
    preload_errors, preload_report = _validate(preload, label="preload", expect_preload=True)
    errors.extend(boot_errors)
    errors.extend(preload_errors)
    report = {
        "status": "PASS" if not errors else "FAIL",
        "boot": boot_report,
        "preload": preload_report,
        "errors": errors,
    }
    _write_json(OUT_JSON, report)
    if errors:
        print("[system_init_init_meta_minimal_guard] FAIL")
        for item in errors:
            print(f" - {item}")
        return 1
    print("[system_init_init_meta_minimal_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
