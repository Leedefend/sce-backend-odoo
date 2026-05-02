#!/usr/bin/env python3
"""Guard Phase 1 readiness for future Lite runtime integration planning."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
REQUIRED_FILES = (
    "docs/architecture/unified_page_contract_lite/unified_page_contract_lite.schema.json",
    "docs/architecture/unified_page_contract_lite/lite_adapter_source.schema.json",
    "docs/architecture/unified_page_contract_lite/lite_adapter_patch_source.schema.json",
    "docs/architecture/unified_page_contract_lite/semantic_adapter_mapping_inventory_v1.json",
    "docs/architecture/unified_page_contract_lite/lite_runtime_opt_in_envelope.schema.json",
    "docs/architecture/unified_page_contract_lite/lite_runtime_opt_in_envelope.example.json",
    "docs/architecture/unified_page_contract_lite/lite_runtime_opt_in_response.schema.json",
    "docs/architecture/unified_page_contract_lite/lite_runtime_opt_in_response.example.json",
    "docs/architecture/unified_page_contract_lite/fixtures/default_load_contract_request_v1.json",
    "docs/architecture/unified_page_contract_lite/fixtures/default_ui_contract_request_v1.json",
    "docs/architecture/unified_page_contract_lite/fixtures/default_onchange_request_v1.json",
    "docs/architecture/unified_page_contract_lite/fixtures/invalid_lite_preview_missing_version_request_v1.json",
    "docs/architecture/unified_page_contract_lite/api_onchange_lite_preview_acceptance_batch_18.md",
    "docs/architecture/unified_page_contract_lite/api_onchange_lite_preview_runtime_batch_19.md",
    "docs/architecture/unified_page_contract_lite/api_onchange_preview_behavior_batch_20.md",
    "docs/architecture/unified_page_contract_lite/integration_validation_matrix_batch_26.md",
    "docs/architecture/unified_page_contract_lite/api_onchange_preview_interface_batch_27.md",
    "docs/architecture/unified_page_contract_lite/api_onchange_preview_intent_smoke_batch_28.md",
    "docs/architecture/unified_page_contract_lite/startup_chain_negative_smoke_batch_29.md",
    "docs/architecture/unified_page_contract_lite/load_contract_negative_smoke_batch_30.md",
    "docs/architecture/unified_page_contract_lite/frontend_runtime_negative_batch_31.md",
    "docs/architecture/unified_page_contract_lite/runtime_scope_closure_batch_32.md",
    "docs/architecture/unified_page_contract_lite/phase1_closure_batch_36.md",
    "docs/architecture/unified_page_contract_lite/phase2_load_contract_preview_batch_39.md",
    "docs/architecture/unified_page_contract_lite/fixtures/api_onchange_legacy_response_v1.json",
    "addons/smart_core/core/unified_page_contract_lite_source_normalizer.py",
    "addons/smart_core/core/unified_page_contract_lite_patch_normalizer.py",
    "addons/smart_core/core/unified_page_contract_lite_adapter.py",
    "addons/smart_core/core/unified_page_contract_lite_preview.py",
    "scripts/verify/unified_page_contract_lite_source_guard.py",
    "scripts/verify/unified_page_contract_lite_source_normalizer_guard.py",
    "scripts/verify/unified_page_contract_lite_patch_normalizer_guard.py",
    "scripts/verify/unified_page_contract_lite_pipeline_guard.py",
    "scripts/verify/unified_page_contract_lite_adapter_guard.py",
    "scripts/verify/unified_page_contract_lite_runtime_boundary_guard.py",
    "scripts/verify/unified_page_contract_lite_opt_in_envelope_guard.py",
    "scripts/verify/unified_page_contract_lite_opt_in_response_guard.py",
    "scripts/verify/unified_page_contract_lite_opt_in_negative_guard.py",
    "scripts/verify/unified_page_contract_lite_acceptance_checklist_guard.py",
    "scripts/verify/unified_page_contract_lite_api_onchange_preview_guard.py",
    "scripts/verify/unified_page_contract_lite_api_onchange_preview_behavior_guard.py",
    "scripts/verify/unified_page_contract_lite_integration_validation_matrix_guard.py",
    "scripts/verify/unified_page_contract_lite_api_onchange_preview_interface_probe.py",
    "scripts/verify/unified_page_contract_lite_api_onchange_preview_intent_smoke.py",
    "scripts/verify/unified_page_contract_lite_startup_chain_negative_smoke.py",
    "scripts/verify/unified_page_contract_lite_load_contract_negative_smoke.py",
    "scripts/verify/unified_page_contract_lite_load_contract_preview_interface_probe.py",
    "scripts/verify/unified_page_contract_lite_load_contract_preview_intent_smoke.py",
    "scripts/verify/unified_page_contract_lite_frontend_runtime_negative_guard.py",
    "scripts/verify/unified_page_contract_lite_runtime_scope_closure_guard.py",
    "scripts/verify/unified_page_contract_lite_phase1_closure_guard.py",
    "docs/architecture/unified_page_contract_lite/snapshots/legacy_project_form_lite_pipeline_snapshot_v1.json",
    "docs/architecture/unified_page_contract_lite/snapshots/legacy_onchange_lite_patch_pipeline_snapshot_v1.json",
)
REQUIRED_MAKE_TOKENS = (
    "scripts/verify/unified_page_contract_lite_source_guard.py",
    "scripts/verify/unified_page_contract_lite_source_normalizer_guard.py",
    "scripts/verify/unified_page_contract_lite_patch_normalizer_guard.py",
    "scripts/verify/unified_page_contract_lite_pipeline_guard.py",
    "scripts/verify/unified_page_contract_lite_mapping_guard.py",
    "scripts/verify/unified_page_contract_lite_adapter_guard.py",
    "scripts/verify/unified_page_contract_lite_runtime_boundary_guard.py",
    "scripts/verify/unified_page_contract_lite_opt_in_envelope_guard.py",
    "scripts/verify/unified_page_contract_lite_opt_in_response_guard.py",
    "scripts/verify/unified_page_contract_lite_opt_in_negative_guard.py",
    "scripts/verify/unified_page_contract_lite_acceptance_checklist_guard.py",
    "scripts/verify/unified_page_contract_lite_api_onchange_preview_guard.py",
    "scripts/verify/unified_page_contract_lite_api_onchange_preview_behavior_guard.py",
    "scripts/verify/unified_page_contract_lite_integration_validation_matrix_guard.py",
    "scripts/verify/unified_page_contract_lite_api_onchange_preview_interface_probe.py",
    "scripts/verify/unified_page_contract_lite_api_onchange_preview_intent_smoke.py",
    "scripts/verify/unified_page_contract_lite_startup_chain_negative_smoke.py",
    "scripts/verify/unified_page_contract_lite_load_contract_negative_smoke.py",
    "scripts/verify/unified_page_contract_lite_load_contract_preview_interface_probe.py",
    "scripts/verify/unified_page_contract_lite_load_contract_preview_intent_smoke.py",
    "scripts/verify/unified_page_contract_lite_frontend_runtime_negative_guard.py",
    "scripts/verify/unified_page_contract_lite_runtime_scope_closure_guard.py",
    "scripts/verify/unified_page_contract_lite_phase1_closure_guard.py",
    "verify.unified_page_contract.lite.api_onchange_live_scope.container",
    "verify.unified_page_contract.lite.phase1_closure",
)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--adapter-coverage", required=True, type=Path)
    parser.add_argument("--runtime-boundary", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()

    errors: list[str] = []
    missing_files = [relative for relative in REQUIRED_FILES if not (ROOT / relative).exists()]
    if missing_files:
        errors.append(f"missing required Phase 1 files: {missing_files}")

    makefile_text = (ROOT / "Makefile").read_text(encoding="utf-8")
    missing_make_tokens = [token for token in REQUIRED_MAKE_TOKENS if token not in makefile_text]
    if missing_make_tokens:
        errors.append(f"Makefile missing Lite readiness tokens: {missing_make_tokens}")

    coverage = load_json(args.adapter_coverage)
    if not coverage.get("ok"):
        errors.append("adapter coverage report is not ok")
    if coverage.get("contract_case_count", 0) < 3:
        errors.append("adapter coverage must include at least 3 contract cases")
    if coverage.get("patch_case_count", 0) < 2:
        errors.append("adapter coverage must include at least 2 patch cases")
    if set(coverage.get("view_types") or []) < {"form", "tree", "search"}:
        errors.append("adapter coverage must include form/tree/search view types")
    for key in ("patch_has_status", "patch_has_button_status", "patch_has_relation_status", "patch_has_data", "side_effect_free"):
        if coverage.get(key) is not True:
            errors.append(f"adapter coverage missing required true flag: {key}")

    runtime_boundary = load_json(args.runtime_boundary)
    if runtime_boundary.get("ok") is not True or runtime_boundary.get("violation_count") != 0:
        errors.append("runtime boundary report must be ok with zero violations")

    report = {
        "ok": not errors,
        "decision": "ready_for_explicit_runtime_integration_planning" if not errors else "blocked",
        "required_file_count": len(REQUIRED_FILES),
        "missing_files": missing_files,
        "required_make_token_count": len(REQUIRED_MAKE_TOKENS),
        "missing_make_tokens": missing_make_tokens,
        "adapter_coverage": {
            "contract_case_count": coverage.get("contract_case_count"),
            "patch_case_count": coverage.get("patch_case_count"),
            "view_types": coverage.get("view_types"),
            "patch_has_status": coverage.get("patch_has_status"),
            "patch_has_button_status": coverage.get("patch_has_button_status"),
            "patch_has_relation_status": coverage.get("patch_has_relation_status"),
            "patch_has_data": coverage.get("patch_has_data"),
            "side_effect_free": coverage.get("side_effect_free"),
        },
        "runtime_boundary": {
            "reference_count": runtime_boundary.get("reference_count"),
            "violation_count": runtime_boundary.get("violation_count"),
            "policy": runtime_boundary.get("policy"),
        },
        "errors": errors,
    }
    write_report(args.report, report)

    if errors:
        print("Unified Semantic Page Contract Lite Phase 1 readiness guard failed:")
        for error in errors:
            print(f"- {error}")
        print(f"- report: {args.report}")
        return 1

    print("Unified Semantic Page Contract Lite Phase 1 readiness guard passed")
    print(f"- report: {args.report}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
