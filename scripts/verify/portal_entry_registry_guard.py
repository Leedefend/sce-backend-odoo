#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCENE_CATALOG_FILE = ROOT / "docs" / "product" / "scene_catalog_product_v1.json"
CAP_CATALOG_FILE = ROOT / "docs" / "product" / "capability_catalog_v1.json"
SCENE_ENTRY_FILE = ROOT / "docs" / "product" / "scene_entry_registry_v1.json"
CAP_ENTRY_FILE = ROOT / "docs" / "product" / "capability_entry_registry_v1.json"


def _load(path: Path) -> dict:
    if not path.is_file():
        raise SystemExit(f"[FAIL] missing file: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit(f"[FAIL] invalid json root: {path}")
    return payload


def main() -> int:
    scene_catalog = _load(SCENE_CATALOG_FILE)
    cap_catalog = _load(CAP_CATALOG_FILE)
    scene_entry = _load(SCENE_ENTRY_FILE)
    cap_entry = _load(CAP_ENTRY_FILE)

    scene_keys = {
        str((row or {}).get("scene_key") or "").strip()
        for row in (scene_catalog.get("scenes") if isinstance(scene_catalog.get("scenes"), list) else [])
        if str((row or {}).get("scene_key") or "").strip()
    }
    cap_keys = {
        str((row or {}).get("capability_key") or "").strip()
        for row in (cap_catalog.get("capabilities") if isinstance(cap_catalog.get("capabilities"), list) else [])
        if str((row or {}).get("capability_key") or "").strip()
    }

    scene_entries = scene_entry.get("entries") if isinstance(scene_entry.get("entries"), list) else []
    cap_entries = cap_entry.get("entries") if isinstance(cap_entry.get("entries"), list) else []
    if not scene_entries:
        raise SystemExit("[FAIL] scene_entry_registry entries empty")
    if not cap_entries:
        raise SystemExit("[FAIL] capability_entry_registry entries empty")

    missing_scene_refs = []
    missing_cap_refs = []
    for row in scene_entries:
        sk = str((row or {}).get("scene_key") or "").strip()
        if not sk or sk not in scene_keys:
            missing_scene_refs.append(sk or "<empty>")
        for ck in (row or {}).get("required_capabilities") or []:
            key = str(ck or "").strip()
            if key and key not in cap_keys:
                missing_cap_refs.append(key)

    missing_cap_entries = []
    for row in cap_entries:
        ck = str((row or {}).get("capability_key") or "").strip()
        if not ck or ck not in cap_keys:
            missing_cap_entries.append(ck or "<empty>")
        for sk in (row or {}).get("scene_keys") or []:
            key = str(sk or "").strip()
            if key and key not in scene_keys:
                missing_scene_refs.append(key)

    if missing_scene_refs:
        sample = ", ".join(sorted(set(missing_scene_refs))[:12])
        raise SystemExit(f"[FAIL] registry references unknown scenes: {sample}")
    if missing_cap_refs:
        sample = ", ".join(sorted(set(missing_cap_refs))[:12])
        raise SystemExit(f"[FAIL] scene entry references unknown capabilities: {sample}")
    if missing_cap_entries:
        sample = ", ".join(sorted(set(missing_cap_entries))[:12])
        raise SystemExit(f"[FAIL] capability entry has unknown capability keys: {sample}")

    print(
        "[PASS] entry registry guard "
        f"scene_entries={len(scene_entries)} capability_entries={len(cap_entries)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
