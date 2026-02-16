#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
EXPORT_SCRIPT = ROOT / "scripts/contract/export_catalogs.py"
INTENT_CATALOG = ROOT / "docs/contract/exports/intent_catalog.json"
SCENE_CATALOG = ROOT / "docs/contract/exports/scene_catalog.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _export_once() -> tuple[str, str]:
    subprocess.run(["python3", str(EXPORT_SCRIPT)], check=True, cwd=str(ROOT))
    if not INTENT_CATALOG.is_file() or not SCENE_CATALOG.is_file():
        raise RuntimeError("catalog export missing output files")
    return _sha256(INTENT_CATALOG), _sha256(SCENE_CATALOG)


def main() -> int:
    first_intent, first_scene = _export_once()
    second_intent, second_scene = _export_once()

    errors: list[str] = []
    if first_intent != second_intent:
        errors.append("intent_catalog.json is not deterministic across two exports")
    if first_scene != second_scene:
        errors.append("scene_catalog.json is not deterministic across two exports")

    if errors:
        print("[contract_catalog_determinism_guard] FAIL")
        for item in errors:
            print(item)
        return 1

    print("[contract_catalog_determinism_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
