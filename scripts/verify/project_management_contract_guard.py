#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MAPPING_JSON = ROOT / "docs" / "contract" / "project_management_capability_mapping_v2.json"
REGISTRY_PY = ROOT / "addons" / "smart_construction_core" / "services" / "capability_registry.py"


def _load_mapping() -> dict:
    payload = json.loads(MAPPING_JSON.read_text(encoding="utf-8"))
    if str(payload.get("scene_key") or "") != "project.management":
        raise SystemExit("mapping scene_key mismatch")
    if str(payload.get("page_key") or "") != "project.management.dashboard":
        raise SystemExit("mapping page_key mismatch")
    rows = payload.get("mappings")
    if not isinstance(rows, list) or len(rows) != 7:
        raise SystemExit("mapping size mismatch: expected 7")
    return payload


def _extract_registry_keys() -> set[str]:
    text = REGISTRY_PY.read_text(encoding="utf-8")
    keys = set(re.findall(r'_cap\("([a-z0-9_.]+)"', text))
    if not keys:
        raise SystemExit("no capability keys extracted from registry")
    return keys


def main() -> None:
    mapping = _load_mapping()
    rows = mapping.get("mappings") or []
    registry_keys = _extract_registry_keys()

    zone_keys = set()
    block_keys = set()
    missing_caps = []

    for row in rows:
        zone_key = str(row.get("zone_key") or "").strip()
        block_key = str(row.get("block_key") or "").strip()
        cap_key = str(row.get("capability_key") or "").strip()
        intent_key = str(row.get("intent_key") or "").strip()
        if not zone_key or not block_key or not cap_key:
            raise SystemExit("mapping row has empty required key")
        if intent_key != "project.dashboard":
            raise SystemExit(f"mapping intent_key invalid: {intent_key}")
        if cap_key not in registry_keys:
            missing_caps.append(cap_key)
        if zone_key in zone_keys:
            raise SystemExit(f"duplicate zone_key: {zone_key}")
        if block_key in block_keys:
            raise SystemExit(f"duplicate block_key: {block_key}")
        zone_keys.add(zone_key)
        block_keys.add(block_key)

    if missing_caps:
        raise SystemExit(f"capability keys not found in registry: {sorted(set(missing_caps))}")

    print("[verify.project.dashboard.contract] PASS")


if __name__ == "__main__":
    main()
