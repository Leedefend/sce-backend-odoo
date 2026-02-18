#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
POLICY_FILES = [
    "scripts/verify/baselines/scene_catalog_runtime_alignment.json",
    "scripts/verify/baselines/intent_router_purity_guard.json",
    "scripts/verify/baselines/scene_provider_guard.json",
    "scripts/verify/baselines/capability_provider_guard.json",
    "scripts/verify/baselines/boundary_import_guard.json",
    "scripts/verify/baselines/boundary_import_guard_schema_guard.json",
    "scripts/verify/baselines/boundary_import_guard_strict_guard.json",
    "scripts/verify/baselines/backend_boundary_guard.json",
    "scripts/verify/baselines/role_capability_floor_prod_like.json",
    "scripts/verify/baselines/contract_assembler_semantic_smoke.json",
    "scripts/verify/baselines/runtime_surface_dashboard_report.json",
    "scripts/verify/baselines/business_core_journey_guard.json",
    "scripts/verify/baselines/role_capability_floor_guard.json",
    "scripts/verify/baselines/contract_evidence_guard_baseline.json",
    "scripts/verify/baselines/controller_boundary_guard_baseline.json",
    "scripts/verify/baselines/baseline_frozen_paths.json",
]


def main() -> int:
    errors: list[str] = []
    for rel in POLICY_FILES:
        path = ROOT / rel
        if not path.is_file():
            errors.append(f"missing policy file: {rel}")
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"invalid json policy file: {rel} ({exc})")
            continue
        if not isinstance(payload, dict):
            errors.append(f"policy root must be object: {rel}")

    if errors:
        print("[baseline_policy_integrity_guard] FAIL")
        for item in errors:
            print(item)
        return 1

    print("[baseline_policy_integrity_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
