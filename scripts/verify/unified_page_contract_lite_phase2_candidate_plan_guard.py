#!/usr/bin/env python3
"""Guard the Lite Phase 2 candidate planning document."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]

REQUIRED_FILES = (
    "docs/architecture/unified_page_contract_lite/phase1_closure_batch_36.md",
    "docs/architecture/unified_page_contract_lite/phase2_candidate_plan_batch_37.md",
    "docs/architecture/unified_page_contract_lite/phase2_load_contract_gate_batch_38.md",
    "scripts/verify/unified_page_contract_lite_phase1_closure_guard.py",
    "scripts/verify/unified_page_contract_lite_phase2_candidate_plan_guard.py",
    "scripts/verify/unified_page_contract_lite_phase2_load_contract_gate_guard.py",
)

REQUIRED_TARGETS = (
    "verify.unified_page_contract.lite.phase1_closure",
    "verify.unified_page_contract.lite.phase2_candidate_plan",
    "verify.unified_page_contract.lite.phase2_load_contract_gate",
    "verify.unified_page_contract.lite",
)

REQUIRED_PLAN_TOKENS = (
    "phase2_candidate_selected_planning_only",
    "load_contract opt-in preview",
    "backend-only preview, no frontend consumption",
    "This document is not approved for implementation.",
    "default `load_contract` response remains unchanged",
    "Lite preview requires explicit opt-in",
    "no `ui.contract` change",
    "no `system.init` change",
    "no `login` change",
    "no frontend runtime change",
    "no `runtimeContract`",
    "disable load_contract opt-in preview branch",
    "make verify.unified_page_contract.lite.load_contract_preview_interface",
    "make verify.unified_page_contract.lite.load_contract_preview_intent.container",
    "make verify.unified_page_contract.lite.load_contract_negative.container",
    "make verify.contract.preflight",
    "make verify.boundary.guard",
    "make verify.frontend.quick.gate",
)

REQUIRED_PHASE1_TOKENS = (
    "ready_for_phase2_planning",
    "runtime_scope_closed_api_onchange_only",
    "not approved for runtime expansion",
)

FORBIDDEN_TOKENS = (
    "implementation approved",
    "frontend runtime enabled",
    "default load_contract changed",
    "ui.contract propagation approved",
    "startup-chain propagation approved",
    "runtimeContract approved",
)


def write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def missing_tokens(text: str, tokens: tuple[str, ...]) -> list[str]:
    return [token for token in tokens if token not in text]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--phase1-closure", required=True, type=Path)
    parser.add_argument("--makefile", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()

    errors: list[str] = []

    missing_files = [relative for relative in REQUIRED_FILES if not (ROOT / relative).exists()]
    if missing_files:
        errors.append(f"missing Phase 2 planning files: {missing_files}")

    makefile_text = args.makefile.read_text(encoding="utf-8")
    missing_targets = missing_tokens(makefile_text, REQUIRED_TARGETS)
    if missing_targets:
        errors.append(f"Makefile missing Phase 2 planning targets: {missing_targets}")

    plan_text = args.plan.read_text(encoding="utf-8")
    missing_plan_tokens = missing_tokens(plan_text, REQUIRED_PLAN_TOKENS)
    if missing_plan_tokens:
        errors.append(f"Phase 2 plan missing required tokens: {missing_plan_tokens}")

    phase1_text = args.phase1_closure.read_text(encoding="utf-8")
    missing_phase1_tokens = missing_tokens(phase1_text, REQUIRED_PHASE1_TOKENS)
    if missing_phase1_tokens:
        errors.append(f"Phase 1 closure missing prerequisite tokens: {missing_phase1_tokens}")

    forbidden_hits = [token for token in FORBIDDEN_TOKENS if token in plan_text]
    if forbidden_hits:
        errors.append(f"Phase 2 plan contains forbidden approval tokens: {forbidden_hits}")

    report = {
        "ok": not errors,
        "decision": "phase2_candidate_selected_planning_only" if not errors else "blocked",
        "candidate": "load_contract opt-in preview",
        "implementation_approved": False,
        "frontend_consumption_approved": False,
        "missing_files": missing_files,
        "missing_targets": missing_targets,
        "missing_plan_tokens": missing_plan_tokens,
        "missing_phase1_tokens": missing_phase1_tokens,
        "forbidden_hits": forbidden_hits,
        "errors": errors,
    }
    write_report(args.report, report)

    if errors:
        print("Unified Semantic Page Contract Lite Phase 2 candidate plan guard failed:")
        for error in errors:
            print(f"- {error}")
        print(f"- report: {args.report}")
        return 1

    print("Unified Semantic Page Contract Lite Phase 2 candidate plan guard passed")
    print("- candidate: load_contract opt-in preview")
    print("- decision: planning only")
    print(f"- report: {args.report}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
