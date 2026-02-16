#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_JSON = ROOT / "artifacts" / "contract" / "phase11_1_contract_evidence.json"


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def main() -> int:
    payload = _load_json(EVIDENCE_JSON)
    if not payload:
        print("[contract_evidence_guard] FAIL")
        print(f"missing or invalid evidence: {EVIDENCE_JSON.relative_to(ROOT).as_posix()}")
        return 1

    errors: list[str] = []
    for key in (
        "intent_catalog",
        "scene_catalog",
        "shape_guard",
        "intent_surface",
        "scene_runtime_alignment",
        "business_capability_baseline",
    ):
        if not isinstance(payload.get(key), dict):
            errors.append(f"missing section: {key}")

    scene_catalog = payload.get("scene_catalog") if isinstance(payload.get("scene_catalog"), dict) else {}
    if not str(scene_catalog.get("catalog_scope") or "").strip():
        errors.append("scene_catalog.catalog_scope is required")

    align = payload.get("scene_runtime_alignment") if isinstance(payload.get("scene_runtime_alignment"), dict) else {}
    if not isinstance(align.get("ok"), bool):
        errors.append("scene_runtime_alignment.ok must be bool")
    if float(align.get("catalog_runtime_ratio") or 0.0) <= 0.0:
        errors.append("scene_runtime_alignment.catalog_runtime_ratio must be > 0")

    baseline = payload.get("business_capability_baseline") if isinstance(payload.get("business_capability_baseline"), dict) else {}
    if not isinstance(baseline.get("ok"), bool):
        errors.append("business_capability_baseline.ok must be bool")
    if int(baseline.get("check_count") or 0) < 1:
        errors.append("business_capability_baseline.check_count must be >= 1")

    if errors:
        print("[contract_evidence_guard] FAIL")
        for item in errors:
            print(item)
        return 1

    print("[contract_evidence_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
