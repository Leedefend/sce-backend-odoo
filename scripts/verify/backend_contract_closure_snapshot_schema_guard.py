#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
ARTIFACT = ROOT / "artifacts" / "backend" / "backend_contract_closure_snapshot.json"
REQUIRED_SECTIONS = ("meta_intent_catalog", "scene_governance_v1")


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def main() -> int:
    payload = _load_json(ARTIFACT)
    errors: list[str] = []

    if not payload:
        errors.append(f"missing or invalid artifact: {ARTIFACT.relative_to(ROOT).as_posix()}")
    else:
        for section in REQUIRED_SECTIONS:
            value = payload.get(section)
            if not isinstance(value, dict):
                errors.append(f"{section} must be object")
                continue
            keys = value.get("payload_keys")
            if not isinstance(keys, list) or not all(isinstance(item, str) for item in keys):
                errors.append(f"{section}.payload_keys must be string list")
                continue
            if not keys:
                errors.append(f"{section}.payload_keys must be non-empty")
            if keys != sorted(keys):
                errors.append(f"{section}.payload_keys must be sorted")
            if len(keys) != len(set(keys)):
                errors.append(f"{section}.payload_keys must not contain duplicates")

    if errors:
        print("[backend_contract_closure_snapshot_schema_guard] FAIL")
        for error in errors:
            print(error)
        return 2

    print("[backend_contract_closure_snapshot_schema_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
