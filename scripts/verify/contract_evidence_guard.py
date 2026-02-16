#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_JSON = ROOT / "artifacts" / "contract" / "phase11_1_contract_evidence.json"
BASELINE_JSON = ROOT / "scripts" / "verify" / "baselines" / "contract_evidence_guard_baseline.json"


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def main() -> int:
    policy = {
        "max_errors": 0,
        "min_business_capability_check_count": 1,
        "min_scene_catalog_runtime_ratio": 0.0,
        "require_alignment_ok": True,
        "require_business_capability_ok": True,
    }
    policy_payload = _load_json(BASELINE_JSON)
    if policy_payload:
        policy.update(policy_payload)

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
    if bool(policy.get("require_alignment_ok", True)) and not bool(align.get("ok")):
        errors.append("scene_runtime_alignment.ok must be true under baseline policy")
    min_ratio = float(policy.get("min_scene_catalog_runtime_ratio", 0.0) or 0.0)
    if float(align.get("catalog_runtime_ratio") or 0.0) < min_ratio:
        errors.append(f"scene_runtime_alignment.catalog_runtime_ratio must be >= {min_ratio}")

    capability_baseline = payload.get("business_capability_baseline") if isinstance(payload.get("business_capability_baseline"), dict) else {}
    if not isinstance(capability_baseline.get("ok"), bool):
        errors.append("business_capability_baseline.ok must be bool")
    if bool(policy.get("require_business_capability_ok", True)) and not bool(capability_baseline.get("ok")):
        errors.append("business_capability_baseline.ok must be true under baseline policy")
    min_checks = int(policy.get("min_business_capability_check_count", 1) or 1)
    if int(capability_baseline.get("check_count") or 0) < min_checks:
        errors.append(f"business_capability_baseline.check_count must be >= {min_checks}")

    if len(errors) > int(policy.get("max_errors", 0)):
        print("[contract_evidence_guard] FAIL")
        for item in errors:
            print(item)
        return 1

    print("[contract_evidence_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
