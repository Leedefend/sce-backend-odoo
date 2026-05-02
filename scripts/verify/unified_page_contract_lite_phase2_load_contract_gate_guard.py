#!/usr/bin/env python3
"""Guard the Phase 2 load_contract implementation gate design."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]

REQUIRED_FILES = (
    "docs/architecture/unified_page_contract_lite/phase2_candidate_plan_batch_37.md",
    "docs/architecture/unified_page_contract_lite/phase2_load_contract_gate_batch_38.md",
    "scripts/verify/unified_page_contract_lite_phase2_candidate_plan_guard.py",
    "scripts/verify/unified_page_contract_lite_phase2_load_contract_gate_guard.py",
)

REQUIRED_TARGETS = (
    "verify.unified_page_contract.lite.phase2_candidate_plan",
    "verify.unified_page_contract.lite.phase2_load_contract_gate",
    "verify.unified_page_contract.lite",
)

REQUIRED_GATE_TOKENS = (
    "implementation gate design only",
    "This document is not approved for implementation.",
    "load_contract",
    "addons/smart_core/handlers/load_contract.py",
    "backend-only preview",
    "not allowed",
    "\"contractMode\": \"lite_preview\"",
    "\"contractVersion\": \"2.0.0\"",
    "\"entryPoint\": \"load_contract\"",
    "\"fallbackMode\": \"legacy_default\"",
    "top-level",
    "lite_preview",
    "lite_contract",
    "legacy `data` remains unchanged",
    "make verify.unified_page_contract.lite.load_contract_preview_interface",
    "make verify.unified_page_contract.lite.load_contract_preview_intent.container",
    "make verify.unified_page_contract.lite.load_contract_negative.container",
    "make verify.unified_page_contract.lite.startup_negative.container",
    "make verify.unified_page_contract.lite.frontend_runtime_negative",
    "make verify.contract.preflight",
    "make verify.boundary.guard",
    "make verify.frontend.quick.gate",
    "disable load_contract opt-in preview branch",
    "After the positive preview guard exists, this negative guard must not send a",
)

REQUIRED_CANDIDATE_TOKENS = (
    "phase2_candidate_selected_planning_only",
    "load_contract opt-in preview",
    "backend-only preview, no frontend consumption",
)

FORBIDDEN_GATE_TOKENS = (
    "implementation approved",
    "frontend consumption allowed",
    "default `load_contract` response may change",
    "runtimeContract enabled",
    "ui.contract propagation approved",
)


def write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def missing_tokens(text: str, tokens: tuple[str, ...]) -> list[str]:
    return [token for token in tokens if token not in text]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gate", required=True, type=Path)
    parser.add_argument("--candidate-plan", required=True, type=Path)
    parser.add_argument("--makefile", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()

    errors: list[str] = []

    missing_files = [relative for relative in REQUIRED_FILES if not (ROOT / relative).exists()]
    if missing_files:
        errors.append(f"missing load_contract gate files: {missing_files}")

    makefile_text = args.makefile.read_text(encoding="utf-8")
    missing_targets = missing_tokens(makefile_text, REQUIRED_TARGETS)
    if missing_targets:
        errors.append(f"Makefile missing load_contract gate targets: {missing_targets}")

    gate_text = args.gate.read_text(encoding="utf-8")
    missing_gate_tokens = missing_tokens(gate_text, REQUIRED_GATE_TOKENS)
    if missing_gate_tokens:
        errors.append(f"load_contract gate missing required tokens: {missing_gate_tokens}")

    candidate_text = args.candidate_plan.read_text(encoding="utf-8")
    missing_candidate_tokens = missing_tokens(candidate_text, REQUIRED_CANDIDATE_TOKENS)
    if missing_candidate_tokens:
        errors.append(f"candidate plan missing required prerequisite tokens: {missing_candidate_tokens}")

    forbidden_hits = [token for token in FORBIDDEN_GATE_TOKENS if token in gate_text]
    if forbidden_hits:
        errors.append(f"load_contract gate contains forbidden approval tokens: {forbidden_hits}")

    report = {
        "ok": not errors,
        "decision": "load_contract_gate_designed_implementation_not_approved" if not errors else "blocked",
        "entry_point": "load_contract",
        "response_field": "lite_preview",
        "payload_type": "lite_contract",
        "implementation_approved": False,
        "frontend_consumption_approved": False,
        "missing_files": missing_files,
        "missing_targets": missing_targets,
        "missing_gate_tokens": missing_gate_tokens,
        "missing_candidate_tokens": missing_candidate_tokens,
        "forbidden_hits": forbidden_hits,
        "errors": errors,
    }
    write_report(args.report, report)

    if errors:
        print("Unified Semantic Page Contract Lite load_contract gate guard failed:")
        for error in errors:
            print(f"- {error}")
        print(f"- report: {args.report}")
        return 1

    print("Unified Semantic Page Contract Lite load_contract gate guard passed")
    print("- entry point: load_contract")
    print("- decision: implementation gate designed; implementation not approved")
    print(f"- report: {args.report}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
