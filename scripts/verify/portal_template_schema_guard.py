#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONSTRUCTION_FILE = ROOT / "docs" / "product" / "templates" / "construction_enterprise_template_v1.json"
OWNER_FILE = ROOT / "docs" / "product" / "templates" / "owner_management_template_draft_v1.json"


def _load(path: Path) -> dict:
    if not path.is_file():
        raise SystemExit(f"[FAIL] missing file: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit(f"[FAIL] invalid json root: {path}")
    return payload


def _require_keys(payload: dict, keys: list[str], name: str) -> None:
    missing = [k for k in keys if k not in payload]
    if missing:
        raise SystemExit(f"[FAIL] {name} missing keys: {', '.join(missing)}")


def main() -> int:
    construction = _load(CONSTRUCTION_FILE)
    owner = _load(OWNER_FILE)

    _require_keys(
        construction,
        ["template_key", "version", "default_roles", "default_scenes", "default_capability_groups", "home_layout_sections", "role_entry_policy"],
        "construction_template",
    )
    _require_keys(
        owner,
        ["template_key", "version", "capability_groups", "home_scenes", "role_matrix", "migration_principles"],
        "owner_template",
    )

    if not isinstance(construction.get("default_roles"), list) or not construction.get("default_roles"):
        raise SystemExit("[FAIL] construction default_roles must be a non-empty list")
    if not isinstance(owner.get("role_matrix"), list) or not owner.get("role_matrix"):
        raise SystemExit("[FAIL] owner role_matrix must be a non-empty list")

    print("[PASS] template schema guard")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
