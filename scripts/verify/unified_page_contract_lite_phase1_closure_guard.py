#!/usr/bin/env python3
"""Guard the Lite Phase 1 closure report and evidence index."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]

REQUIRED_FILES = (
    "docs/architecture/unified_page_contract_lite/phase1_closure_batch_36.md",
    "docs/architecture/unified_page_contract_lite/runtime_scope_closure_batch_32.md",
    "docs/architecture/unified_page_contract_lite/integration_validation_matrix_batch_26.md",
    "scripts/verify/unified_page_contract_lite_phase1_closure_guard.py",
    "scripts/verify/unified_page_contract_lite_runtime_scope_closure_guard.py",
)

REQUIRED_TARGETS = (
    "verify.unified_page_contract.lite",
    "verify.unified_page_contract.lite.runtime_scope_closure",
    "verify.unified_page_contract.lite.api_onchange_live_scope.container",
    "verify.unified_page_contract.lite.phase1_closure",
    "verify.contract.preflight",
    "verify.boundary.guard",
    "verify.frontend.quick.gate",
)

REQUIRED_CLOSURE_TOKENS = (
    "ready_for_phase2_planning",
    "api_onchange",
    "opt-in preview",
    "runtime_scope_closed_api_onchange_only",
    "verify.unified_page_contract.lite",
    "verify.unified_page_contract.lite.api_onchange_live_scope.container",
    "verify.contract.preflight",
    "verify.boundary.guard",
    "verify.frontend.quick.gate",
    "load_contract",
    "ui.contract",
    "system.init",
    "frontend runtime",
    "not approved for runtime expansion",
)

REQUIRED_LOG_TOKENS = (
    "unified_page_contract_lite_runtime_scope_closure_batch_32",
    "unified_page_contract_lite_api_onchange_live_scope_validation_batch_33",
    "unified_page_contract_lite_live_scope_aggregate_target_batch_34",
    "unified_page_contract_lite_baseline_gate_replay_batch_35",
)

FORBIDDEN_CLOSURE_TOKENS = (
    "runtime_expansion_approved",
    "frontend_runtime_enabled",
    "load_contract_enabled",
    "ui_contract_enabled",
    "startup_enabled",
)


def write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def missing_tokens(text: str, tokens: tuple[str, ...]) -> list[str]:
    return [token for token in tokens if token not in text]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--closure-doc", required=True, type=Path)
    parser.add_argument("--iteration-log", required=True, type=Path)
    parser.add_argument("--makefile", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()

    errors: list[str] = []

    missing_files = [relative for relative in REQUIRED_FILES if not (ROOT / relative).exists()]
    if missing_files:
        errors.append(f"missing Phase 1 closure files: {missing_files}")

    makefile_text = args.makefile.read_text(encoding="utf-8")
    missing_targets = missing_tokens(makefile_text, REQUIRED_TARGETS)
    if missing_targets:
        errors.append(f"Makefile missing Phase 1 closure targets: {missing_targets}")

    closure_text = args.closure_doc.read_text(encoding="utf-8")
    missing_closure_tokens = missing_tokens(closure_text, REQUIRED_CLOSURE_TOKENS)
    if missing_closure_tokens:
        errors.append(f"closure doc missing required tokens: {missing_closure_tokens}")

    forbidden_hits = [token for token in FORBIDDEN_CLOSURE_TOKENS if token in closure_text]
    if forbidden_hits:
        errors.append(f"closure doc contains forbidden expansion tokens: {forbidden_hits}")

    iteration_log_text = args.iteration_log.read_text(encoding="utf-8")
    missing_log_tokens = missing_tokens(iteration_log_text, REQUIRED_LOG_TOKENS)
    if missing_log_tokens:
        errors.append(f"iteration log missing closure evidence batches: {missing_log_tokens}")

    report = {
        "ok": not errors,
        "decision": "ready_for_phase2_planning" if not errors else "blocked",
        "runtime_scope": "api_onchange_opt_in_preview_only",
        "blocked_entries": ["load_contract", "ui.contract", "system.init", "frontend runtime"],
        "required_file_count": len(REQUIRED_FILES),
        "missing_files": missing_files,
        "required_target_count": len(REQUIRED_TARGETS),
        "missing_targets": missing_targets,
        "missing_closure_tokens": missing_closure_tokens,
        "missing_log_tokens": missing_log_tokens,
        "forbidden_hits": forbidden_hits,
        "errors": errors,
    }
    write_report(args.report, report)

    if errors:
        print("Unified Semantic Page Contract Lite Phase 1 closure guard failed:")
        for error in errors:
            print(f"- {error}")
        print(f"- report: {args.report}")
        return 1

    print("Unified Semantic Page Contract Lite Phase 1 closure guard passed")
    print("- decision: ready_for_phase2_planning")
    print("- runtime scope: api_onchange opt-in preview only")
    print(f"- report: {args.report}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
