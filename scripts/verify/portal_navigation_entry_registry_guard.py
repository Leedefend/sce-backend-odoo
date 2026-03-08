#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
NAV_FILE = ROOT / "docs" / "product" / "navigation_entry_registry_v1.json"
SCENE_FILE = ROOT / "docs" / "product" / "scene_catalog_product_v1.json"
CAP_FILE = ROOT / "docs" / "product" / "capability_catalog_v1.json"


def _load(path: Path) -> dict:
    if not path.is_file():
        raise SystemExit(f"[FAIL] missing file: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit(f"[FAIL] invalid json root: {path}")
    return payload


def main() -> int:
    nav = _load(NAV_FILE)
    scene = _load(SCENE_FILE)
    cap = _load(CAP_FILE)

    entries = nav.get("entries") if isinstance(nav.get("entries"), list) else []
    if not entries:
        raise SystemExit("[FAIL] navigation entry registry is empty")

    scene_keys = {
        str((row or {}).get("scene_key") or "").strip()
        for row in (scene.get("scenes") if isinstance(scene.get("scenes"), list) else [])
        if str((row or {}).get("scene_key") or "").strip()
    }
    cap_keys = {
        str((row or {}).get("capability_key") or "").strip()
        for row in (cap.get("capabilities") if isinstance(cap.get("capabilities"), list) else [])
        if str((row or {}).get("capability_key") or "").strip()
    }

    key_set = set()
    duplicate_keys = []
    invalid_refs = []
    source_counts = {"scene": 0, "capability": 0}
    for row in entries:
        registry_key = str((row or {}).get("registry_key") or "").strip()
        source = str((row or {}).get("entry_source") or "").strip()
        if not registry_key:
            invalid_refs.append("missing_registry_key")
            continue
        if registry_key in key_set:
            duplicate_keys.append(registry_key)
        key_set.add(registry_key)
        if source in source_counts:
            source_counts[source] += 1
        if source == "scene":
            sk = str((row or {}).get("scene_key") or "").strip()
            if not sk or sk not in scene_keys:
                invalid_refs.append(f"scene:{sk or '<empty>'}")
        if source == "capability":
            ck = str((row or {}).get("capability_key") or "").strip()
            if not ck or ck not in cap_keys:
                invalid_refs.append(f"capability:{ck or '<empty>'}")
            for sk in (row or {}).get("scene_keys") or []:
                val = str(sk or "").strip()
                if val and val not in scene_keys:
                    invalid_refs.append(f"scene:{val}")

    if duplicate_keys:
        raise SystemExit(f"[FAIL] duplicate registry keys: {', '.join(sorted(set(duplicate_keys))[:10])}")
    if invalid_refs:
        raise SystemExit(f"[FAIL] navigation registry invalid refs: {', '.join(sorted(set(invalid_refs))[:12])}")
    if source_counts["scene"] <= 0 or source_counts["capability"] <= 0:
        raise SystemExit(f"[FAIL] source counts invalid: {source_counts}")

    print(f"[PASS] navigation entry registry guard entries={len(entries)} sources={source_counts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
