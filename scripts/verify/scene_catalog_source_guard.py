#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
SCENE_CATALOG = ROOT / "docs" / "contract" / "exports" / "scene_catalog.json"
ARTIFACT_JSON = ROOT / "artifacts" / "scene_catalog_source_guard.json"


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def main() -> int:
    payload = _load_json(SCENE_CATALOG)
    if not payload:
        print("[scene_catalog_source_guard] FAIL")
        print(f"missing or invalid scene catalog: {SCENE_CATALOG.relative_to(ROOT).as_posix()}")
        return 1

    source = payload.get("source") if isinstance(payload.get("source"), dict) else {}
    scene_count = int(payload.get("scene_count") or 0)
    contract_scene_count = int(source.get("scene_contract_scene_count") or 0)
    scope = str(source.get("scene_catalog_scope") or "").strip()
    semantics = str(source.get("scene_catalog_semantics") or "").strip()

    errors: list[str] = []
    if not scope:
        errors.append("source.scene_catalog_scope is required")
    if not semantics:
        errors.append("source.scene_catalog_semantics is required")
    if contract_scene_count < 1:
        errors.append("source.scene_contract_scene_count must be >= 1")
    if contract_scene_count < scene_count:
        errors.append(
            f"source.scene_contract_scene_count {contract_scene_count} < scene_count {scene_count}"
        )

    report = {
        "ok": not errors,
        "summary": {
            "scene_count": scene_count,
            "scene_contract_scene_count": contract_scene_count,
            "scene_catalog_scope": scope,
            "error_count": len(errors),
        },
        "errors": errors,
    }
    ARTIFACT_JSON.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(str(ARTIFACT_JSON))
    if errors:
        print("[scene_catalog_source_guard] FAIL")
        for item in errors:
            print(item)
        return 1
    print("[scene_catalog_source_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
