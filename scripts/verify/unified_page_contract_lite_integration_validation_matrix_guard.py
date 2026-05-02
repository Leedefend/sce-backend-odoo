#!/usr/bin/env python3
"""Guard the Lite integration validation matrix before broader runtime work."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REQUIRED_MODELS = (
    "construction.contract",
    "sc.general.contract",
    "sc.legacy.purchase.contract.fact",
    "payment.request",
    "sc.expense.claim",
    "project.material.plan",
    "sc.settlement.order",
    "purchase.order",
    "sc.receipt.income",
    "sc.payment.execution",
    "sc.invoice.registration",
    "sc.financing.loan",
    "sc.treasury.reconciliation",
    "sc.settlement.adjustment",
)
REQUIRED_SEGMENTS = (
    "BROWSER_CLOSURE_CASE_OFFSET=0 BROWSER_CLOSURE_CASE_LIMIT=2",
    "BROWSER_CLOSURE_CASE_OFFSET=2 BROWSER_CLOSURE_CASE_LIMIT=2",
    "BROWSER_CLOSURE_CASE_OFFSET=4 BROWSER_CLOSURE_CASE_LIMIT=2",
    "BROWSER_CLOSURE_CASE_OFFSET=6 BROWSER_CLOSURE_CASE_LIMIT=2",
    "BROWSER_CLOSURE_CASE_OFFSET=8 BROWSER_CLOSURE_CASE_LIMIT=2",
    "BROWSER_CLOSURE_CASE_OFFSET=10 BROWSER_CLOSURE_CASE_LIMIT=2",
    "BROWSER_CLOSURE_CASE_OFFSET=12 BROWSER_CLOSURE_CASE_LIMIT=2",
)
REQUIRED_GATES = (
    "make verify.unified_page_contract.lite",
    "make verify.contract.preflight",
    "make verify.boundary.guard",
    "make verify.frontend.quick.gate",
    "make verify.docs.all",
    "git diff --check",
    "make verify.portal.execute_button_smoke.container",
    "make verify.portal.envelope_smoke.container",
    "make verify.portal.view_contract_coverage_smoke.container",
    "make verify.portal.view_contract_shape.container",
    "make verify.portal.view_render_mode_smoke.container",
    "make ps",
    "DB_NAME=sc_demo make verify.unified_page_contract.lite.api_onchange_interface",
    "DB_NAME=sc_demo E2E_LOGIN=cost1 E2E_PASSWORD=123456 make verify.unified_page_contract.lite.api_onchange_intent.container",
    "DB_NAME=sc_demo E2E_LOGIN=cost1 E2E_PASSWORD=123456 make verify.unified_page_contract.lite.startup_negative.container",
    "DB_NAME=sc_demo E2E_LOGIN=cost1 E2E_PASSWORD=123456 make verify.unified_page_contract.lite.load_contract_negative.container",
    "make verify.unified_page_contract.lite.frontend_runtime_negative",
)
REQUIRED_RUNTIME_TOKENS = (
    "Allowed current runtime entry:",
    "api_onchange",
    "Blocked runtime entries:",
    "legacy_default",
    "payloadType=lite_patch",
    "rollback remains `disable opt-in flag`",
)
FORBIDDEN_APPROVAL_PHRASES = (
    "runtime expansion is approved",
    "enable Lite preview by default is approved",
    "frontend consumption is approved",
)
REQUIRED_FORBIDDEN_ITEMS = (
    "enable Lite preview by default",
    "change `login`",
    "change `system.init`",
    "change `ui.contract`",
    "change `load_contract`",
    "change frontend runtime",
    "introduce `runtimeContract`",
    "add component registry",
    "add dependency graph",
    "add selector status",
    "add realtime or streaming behavior",
)


def write_report(path: Path, report: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--matrix", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()

    text = args.matrix.read_text(encoding="utf-8")
    errors: list[str] = []

    missing_models = [model for model in REQUIRED_MODELS if model not in text]
    missing_segments = [segment for segment in REQUIRED_SEGMENTS if segment not in text]
    missing_gates = [gate for gate in REQUIRED_GATES if gate not in text]
    missing_runtime_tokens = [token for token in REQUIRED_RUNTIME_TOKENS if token not in text]

    if missing_models:
        errors.append(f"matrix missing demo models: {missing_models}")
    if missing_segments:
        errors.append(f"matrix missing segmented commands: {missing_segments}")
    if missing_gates:
        errors.append(f"matrix missing required gates: {missing_gates}")
    if missing_runtime_tokens:
        errors.append(f"matrix missing runtime boundary tokens: {missing_runtime_tokens}")

    if "## 6. Forbidden Expansion" not in text:
        errors.append("matrix must include forbidden expansion section")
        forbidden_section = ""
    else:
        forbidden_section = text.split("## 6. Forbidden Expansion", 1)[-1]

    missing_forbidden_items = [item for item in REQUIRED_FORBIDDEN_ITEMS if item not in forbidden_section]
    if missing_forbidden_items:
        errors.append(f"forbidden expansion section missing items: {missing_forbidden_items}")

    forbidden_hits = [phrase for phrase in FORBIDDEN_APPROVAL_PHRASES if phrase in text]
    if forbidden_hits:
        errors.append(f"matrix contains forbidden approval phrases: {forbidden_hits}")

    report = {
        "ok": not errors,
        "decision": "integration_validation_matrix_ready_runtime_scope_still_limited" if not errors else "blocked",
        "matrix": str(args.matrix),
        "model_count": len(REQUIRED_MODELS),
        "segment_count": len(REQUIRED_SEGMENTS),
        "gate_count": len(REQUIRED_GATES),
        "errors": errors,
    }
    write_report(args.report, report)

    if errors:
        print("Unified Semantic Page Contract Lite integration validation matrix guard failed:")
        for error in errors:
            print(f"- {error}")
        print(f"- report: {args.report}")
        return 1

    print("Unified Semantic Page Contract Lite integration validation matrix guard passed")
    print(f"- report: {args.report}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
