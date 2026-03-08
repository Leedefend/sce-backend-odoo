#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ROLE_FILE = ROOT / "docs" / "product" / "role_scene_matrix_v1.json"
SCENE_FILE = ROOT / "docs" / "product" / "scene_catalog_product_v1.json"
MAPPING_FILE = ROOT / "docs" / "product" / "capability_scene_mapping_v1.json"


def main() -> int:
    for path in (ROLE_FILE, SCENE_FILE, MAPPING_FILE):
        if not path.is_file():
            raise SystemExit(f"[FAIL] missing file: {path}")

    role_payload = json.loads(ROLE_FILE.read_text(encoding="utf-8"))
    scene_payload = json.loads(SCENE_FILE.read_text(encoding="utf-8"))
    mapping_payload = json.loads(MAPPING_FILE.read_text(encoding="utf-8"))

    roles = role_payload.get("roles") if isinstance(role_payload.get("roles"), list) else []
    scene_keys = {
        str((row or {}).get("scene_key") or "").strip()
        for row in (scene_payload.get("scenes") if isinstance(scene_payload.get("scenes"), list) else [])
        if str((row or {}).get("scene_key") or "").strip()
    }
    mapped_scene_keys = {
        str((row or {}).get("scene_key") or "").strip()
        for row in (mapping_payload.get("product_scene_to_capabilities") if isinstance(mapping_payload.get("product_scene_to_capabilities"), list) else [])
        if str((row or {}).get("scene_key") or "").strip()
    }

    missing_home = []
    unmapped_home = []
    for row in roles:
        role_key = str((row or {}).get("role_key") or "").strip()
        home_scene = str((row or {}).get("home_scene") or "").strip()
        if not role_key or not home_scene:
            continue
        if home_scene not in scene_keys:
            missing_home.append(f"{role_key}:{home_scene}")
        elif home_scene not in mapped_scene_keys:
            unmapped_home.append(f"{role_key}:{home_scene}")

    if missing_home:
        raise SystemExit(f"[FAIL] role home scenes missing in product catalog: {', '.join(missing_home[:10])}")
    if unmapped_home:
        raise SystemExit(f"[FAIL] role home scenes missing capability mapping: {', '.join(unmapped_home[:10])}")

    print(f"[PASS] role home scene guard roles={len(roles)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
