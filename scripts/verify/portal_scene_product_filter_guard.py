#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCENE_PRODUCT_FILE = ROOT / "docs" / "product" / "scene_catalog_product_v1.json"


def main() -> int:
    if not SCENE_PRODUCT_FILE.is_file():
        raise SystemExit(f"[FAIL] missing file: {SCENE_PRODUCT_FILE}")
    payload = json.loads(SCENE_PRODUCT_FILE.read_text(encoding="utf-8"))
    scenes = payload.get("scenes") if isinstance(payload.get("scenes"), list) else []
    if not scenes:
        raise SystemExit("[FAIL] scene_catalog_product_v1 has zero scenes")

    invalid = []
    for row in scenes:
        key = str((row or {}).get("scene_key") or "").strip().lower()
        if "__pkg" in key or key.startswith("default"):
            invalid.append(key)
    if invalid:
        sample = ", ".join(invalid[:10])
        raise SystemExit(f"[FAIL] product scene catalog contains technical scenes: {sample}")

    print(f"[PASS] product scene filter guard scene_count={len(scenes)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
