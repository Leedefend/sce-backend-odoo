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
        "min_business_required_intent_count": 0,
        "min_business_required_role_count": 0,
        "min_business_catalog_runtime_ratio": 0.0,
        "min_scene_catalog_runtime_ratio": 0.0,
        "min_prod_like_fixture_count": 0,
        "max_contract_assembler_semantic_error_count": 0,
        "require_alignment_ok": True,
        "require_business_capability_ok": True,
        "require_prod_like_ok": True,
        "require_contract_assembler_semantic_ok": True,
        "require_backend_architecture_full_ok": True,
        "max_backend_architecture_failed_check_count": 0,
        "require_backend_evidence_manifest_ok": True,
        "max_backend_evidence_manifest_missing_count": 0,
        "require_load_view_access_ok": True,
        "require_load_view_forbidden_status_403": True,
        "require_load_view_forbidden_error_code": "PERMISSION_DENIED",
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
        "role_capability_prod_like",
        "contract_assembler_semantic",
        "runtime_surface_dashboard",
        "load_view_access_contract",
        "backend_architecture_full",
        "backend_evidence_manifest",
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
    min_required_intent_count = int(policy.get("min_business_required_intent_count", 0) or 0)
    if int(capability_baseline.get("required_intent_count") or 0) < min_required_intent_count:
        errors.append(f"business_capability_baseline.required_intent_count must be >= {min_required_intent_count}")
    min_required_role_count = int(policy.get("min_business_required_role_count", 0) or 0)
    if int(capability_baseline.get("required_role_count") or 0) < min_required_role_count:
        errors.append(f"business_capability_baseline.required_role_count must be >= {min_required_role_count}")
    min_business_ratio = float(policy.get("min_business_catalog_runtime_ratio", 0.0) or 0.0)
    if float(capability_baseline.get("catalog_runtime_ratio") or 0.0) < min_business_ratio:
        errors.append(f"business_capability_baseline.catalog_runtime_ratio must be >= {min_business_ratio}")

    prod_like = payload.get("role_capability_prod_like") if isinstance(payload.get("role_capability_prod_like"), dict) else {}
    if not isinstance(prod_like.get("ok"), bool):
        errors.append("role_capability_prod_like.ok must be bool")
    if bool(policy.get("require_prod_like_ok", True)) and not bool(prod_like.get("ok")):
        errors.append("role_capability_prod_like.ok must be true under baseline policy")
    min_prod_fixtures = int(policy.get("min_prod_like_fixture_count", 0) or 0)
    if int(prod_like.get("fixture_count") or 0) < min_prod_fixtures:
        errors.append(f"role_capability_prod_like.fixture_count must be >= {min_prod_fixtures}")

    semantic = payload.get("contract_assembler_semantic") if isinstance(payload.get("contract_assembler_semantic"), dict) else {}
    if not isinstance(semantic.get("ok"), bool):
        errors.append("contract_assembler_semantic.ok must be bool")
    if bool(policy.get("require_contract_assembler_semantic_ok", True)) and not bool(semantic.get("ok")):
        errors.append("contract_assembler_semantic.ok must be true under baseline policy")
    max_semantic_errors = int(policy.get("max_contract_assembler_semantic_error_count", 0) or 0)
    if int(semantic.get("error_count") or 0) > max_semantic_errors:
        errors.append(
            "contract_assembler_semantic.error_count must be <= "
            f"{max_semantic_errors}"
        )

    backend_full = payload.get("backend_architecture_full") if isinstance(payload.get("backend_architecture_full"), dict) else {}
    if not isinstance(backend_full.get("ok"), bool):
        errors.append("backend_architecture_full.ok must be bool")
    if bool(policy.get("require_backend_architecture_full_ok", True)) and not bool(backend_full.get("ok")):
        errors.append("backend_architecture_full.ok must be true under baseline policy")
    max_failed_checks = int(policy.get("max_backend_architecture_failed_check_count", 0) or 0)
    if int(backend_full.get("failed_check_count") or 0) > max_failed_checks:
        errors.append(
            "backend_architecture_full.failed_check_count must be <= "
            f"{max_failed_checks}"
        )

    backend_manifest = payload.get("backend_evidence_manifest") if isinstance(payload.get("backend_evidence_manifest"), dict) else {}
    if not isinstance(backend_manifest.get("ok"), bool):
        errors.append("backend_evidence_manifest.ok must be bool")
    if bool(policy.get("require_backend_evidence_manifest_ok", True)) and not bool(backend_manifest.get("ok")):
        errors.append("backend_evidence_manifest.ok must be true under baseline policy")
    max_manifest_missing = int(policy.get("max_backend_evidence_manifest_missing_count", 0) or 0)
    if int(backend_manifest.get("missing_count") or 0) > max_manifest_missing:
        errors.append(
            "backend_evidence_manifest.missing_count must be <= "
            f"{max_manifest_missing}"
        )

    load_view_access = payload.get("load_view_access_contract") if isinstance(payload.get("load_view_access_contract"), dict) else {}
    if not isinstance(load_view_access.get("ok"), bool):
        errors.append("load_view_access_contract.ok must be bool")
    if bool(policy.get("require_load_view_access_ok", True)) and not bool(load_view_access.get("ok")):
        errors.append("load_view_access_contract.ok must be true under baseline policy")
    if bool(policy.get("require_load_view_forbidden_status_403", True)):
        if int(load_view_access.get("forbidden_status") or 0) != 403:
            errors.append("load_view_access_contract.forbidden_status must be 403")
    required_forbidden_code = str(policy.get("require_load_view_forbidden_error_code") or "").strip()
    if required_forbidden_code:
        actual_forbidden_code = str(load_view_access.get("forbidden_error_code") or "").strip()
        if actual_forbidden_code != required_forbidden_code:
            errors.append(
                "load_view_access_contract.forbidden_error_code must be "
                f"{required_forbidden_code}, got {actual_forbidden_code or '-'}"
            )

    if len(errors) > int(policy.get("max_errors", 0)):
        print("[contract_evidence_guard] FAIL")
        for item in errors:
            print(item)
        return 1

    print("[contract_evidence_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
