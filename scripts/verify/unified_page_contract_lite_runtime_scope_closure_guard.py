#!/usr/bin/env python3
"""Guard the current Lite runtime scope closure evidence.

This guard is intentionally static. It does not approve a broader runtime
integration; it verifies that the documented evidence still closes the current
scope around api_onchange-only Lite preview validation.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]

REQUIRED_DOCS = (
    "docs/architecture/unified_page_contract_lite/integration_validation_matrix_batch_26.md",
    "docs/architecture/unified_page_contract_lite/api_onchange_preview_behavior_batch_20.md",
    "docs/architecture/unified_page_contract_lite/api_onchange_preview_interface_batch_27.md",
    "docs/architecture/unified_page_contract_lite/api_onchange_preview_intent_smoke_batch_28.md",
    "docs/architecture/unified_page_contract_lite/startup_chain_negative_smoke_batch_29.md",
    "docs/architecture/unified_page_contract_lite/load_contract_negative_smoke_batch_30.md",
    "docs/architecture/unified_page_contract_lite/frontend_runtime_negative_batch_31.md",
    "docs/architecture/unified_page_contract_lite/runtime_scope_closure_batch_32.md",
    "docs/architecture/unified_page_contract_lite/phase2_load_contract_preview_batch_39.md",
)

REQUIRED_SCRIPTS = (
    "scripts/verify/unified_page_contract_lite_api_onchange_preview_behavior_guard.py",
    "scripts/verify/unified_page_contract_lite_api_onchange_preview_interface_probe.py",
    "scripts/verify/unified_page_contract_lite_api_onchange_preview_intent_smoke.py",
    "scripts/verify/unified_page_contract_lite_startup_chain_negative_smoke.py",
    "scripts/verify/unified_page_contract_lite_load_contract_negative_smoke.py",
    "scripts/verify/unified_page_contract_lite_load_contract_preview_interface_probe.py",
    "scripts/verify/unified_page_contract_lite_load_contract_preview_intent_smoke.py",
    "scripts/verify/unified_page_contract_lite_frontend_runtime_negative_guard.py",
    "scripts/verify/unified_page_contract_lite_runtime_scope_closure_guard.py",
)

REQUIRED_TARGETS = (
    "verify.unified_page_contract.lite.api_onchange_interface",
    "verify.unified_page_contract.lite.api_onchange_intent.container",
    "verify.unified_page_contract.lite.startup_negative.container",
    "verify.unified_page_contract.lite.load_contract_negative.container",
    "verify.unified_page_contract.lite.load_contract_preview_interface",
    "verify.unified_page_contract.lite.load_contract_preview_intent.container",
    "verify.unified_page_contract.lite.frontend_runtime_negative",
    "verify.unified_page_contract.lite.api_onchange_live_scope.container",
    "verify.unified_page_contract.lite.load_contract_live_scope.container",
    "verify.unified_page_contract.lite.runtime_scope_closure",
)

REQUIRED_MATRIX_TOKENS = (
    "Allowed current runtime entry:",
    "api_onchange",
    "Blocked runtime entries:",
    "load_contract",
    "ui_contract",
    "login",
    "system_init",
    "frontend_runtime",
    "make verify.unified_page_contract.lite",
    "DB_NAME=sc_demo make verify.unified_page_contract.lite.api_onchange_interface",
    "DB_NAME=sc_demo E2E_LOGIN=cost1 E2E_PASSWORD=123456 make verify.unified_page_contract.lite.api_onchange_intent.container",
    "DB_NAME=sc_demo E2E_LOGIN=cost1 E2E_PASSWORD=123456 make verify.unified_page_contract.lite.startup_negative.container",
    "DB_NAME=sc_demo E2E_LOGIN=cost1 E2E_PASSWORD=123456 make verify.unified_page_contract.lite.load_contract_negative.container",
    "DB_NAME=sc_demo make verify.unified_page_contract.lite.load_contract_preview_interface",
    "DB_NAME=sc_demo E2E_LOGIN=cost1 E2E_PASSWORD=123456 make verify.unified_page_contract.lite.load_contract_preview_intent.container",
    "make verify.unified_page_contract.lite.frontend_runtime_negative",
    "DB_NAME=sc_demo E2E_LOGIN=cost1 E2E_PASSWORD=123456 make verify.unified_page_contract.lite.api_onchange_live_scope.container",
    "DB_NAME=sc_demo E2E_LOGIN=cost1 E2E_PASSWORD=123456 make verify.unified_page_contract.lite.load_contract_live_scope.container",
)

REQUIRED_CLOSURE_TOKENS = (
    "api_onchange",
    "load_contract",
    "ui_contract",
    "login",
    "system_init",
    "frontend_runtime",
    "runtimeContract",
    "not approval to expand",
)
REQUIRED_PHASE2_TOKENS = (
    "load_contract opt-in preview",
    "payloadType=lite_contract",
    "backend-only preview",
    "frontend runtime",
)

FORBIDDEN_APPROVAL_PHRASES = (
    "runtime expansion is approved",
    "frontend consumption is approved",
    "load_contract Lite runtime is approved",
    "ui.contract Lite runtime is approved",
    "enable Lite preview by default is approved",
)


def write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def missing_tokens(text: str, tokens: tuple[str, ...]) -> list[str]:
    return [token for token in tokens if token not in text]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--matrix", required=True, type=Path)
    parser.add_argument("--closure-doc", required=True, type=Path)
    parser.add_argument("--readiness-script", required=True, type=Path)
    parser.add_argument("--makefile", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()

    errors: list[str] = []

    missing_docs = [relative for relative in REQUIRED_DOCS if not (ROOT / relative).exists()]
    if missing_docs:
        errors.append(f"missing runtime scope docs: {missing_docs}")

    missing_scripts = [relative for relative in REQUIRED_SCRIPTS if not (ROOT / relative).exists()]
    if missing_scripts:
        errors.append(f"missing runtime scope scripts: {missing_scripts}")

    makefile_text = args.makefile.read_text(encoding="utf-8")
    makefile_missing_targets = missing_tokens(makefile_text, REQUIRED_TARGETS)
    if makefile_missing_targets:
        errors.append(f"Makefile missing runtime scope targets: {makefile_missing_targets}")

    readiness_text = args.readiness_script.read_text(encoding="utf-8")
    readiness_required = REQUIRED_DOCS + REQUIRED_SCRIPTS
    readiness_missing = missing_tokens(readiness_text, readiness_required)
    if readiness_missing:
        errors.append(f"Phase readiness guard missing runtime scope references: {readiness_missing}")

    matrix_text = args.matrix.read_text(encoding="utf-8")
    matrix_missing = missing_tokens(matrix_text, REQUIRED_MATRIX_TOKENS)
    if matrix_missing:
        errors.append(f"integration matrix missing required runtime scope tokens: {matrix_missing}")

    closure_text = args.closure_doc.read_text(encoding="utf-8")
    closure_missing = missing_tokens(closure_text, REQUIRED_CLOSURE_TOKENS)
    if closure_missing:
        errors.append(f"runtime scope closure doc missing required tokens: {closure_missing}")

    phase2_doc = ROOT / "docs/architecture/unified_page_contract_lite/phase2_load_contract_preview_batch_39.md"
    phase2_text = phase2_doc.read_text(encoding="utf-8") if phase2_doc.exists() else ""
    phase2_missing = missing_tokens(phase2_text, REQUIRED_PHASE2_TOKENS)
    if phase2_missing:
        errors.append(f"Phase 2 load_contract preview doc missing required tokens: {phase2_missing}")

    forbidden_hits = [
        phrase
        for phrase in FORBIDDEN_APPROVAL_PHRASES
        if phrase in matrix_text or phrase in closure_text or phrase in readiness_text
    ]
    if forbidden_hits:
        errors.append(f"forbidden runtime expansion approval phrase found: {forbidden_hits}")

    report = {
        "ok": not errors,
        "decision": "runtime_scope_closed_explicit_opt_in_only" if not errors else "blocked",
        "allowed_runtime_entries": ["api_onchange", "load_contract"],
        "blocked_runtime_entries": [
            "ui_contract",
            "login",
            "system_init",
            "frontend_runtime",
        ],
        "required_doc_count": len(REQUIRED_DOCS),
        "missing_docs": missing_docs,
        "required_script_count": len(REQUIRED_SCRIPTS),
        "missing_scripts": missing_scripts,
        "required_target_count": len(REQUIRED_TARGETS),
        "makefile_missing_targets": makefile_missing_targets,
        "readiness_missing": readiness_missing,
        "matrix_missing": matrix_missing,
        "closure_missing": closure_missing,
        "phase2_missing": phase2_missing,
        "forbidden_hits": forbidden_hits,
        "errors": errors,
    }
    write_report(args.report, report)

    if errors:
        print("Unified Semantic Page Contract Lite runtime scope closure guard failed:")
        for error in errors:
            print(f"- {error}")
        print(f"- report: {args.report}")
        return 1

    print("Unified Semantic Page Contract Lite runtime scope closure guard passed")
    print("- allowed runtime entries: api_onchange, load_contract")
    print("- blocked runtime entries: ui_contract, login, system_init, frontend_runtime")
    print(f"- report: {args.report}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
