#!/usr/bin/env python3
"""Guard the Lite frontend controlled pilot readiness decision."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]

REQUIRED_FILES = (
    "docs/architecture/unified_page_contract_lite/frontend_controlled_pilot_readiness_batch_43.md",
    "docs/architecture/unified_page_contract_lite/phase3_ui_contract_risk_review_batch_42.md",
    "scripts/verify/unified_page_contract_lite_frontend_controlled_pilot_readiness_guard.py",
)

REQUIRED_TARGETS = (
    "verify.unified_page_contract.lite.frontend_pilot_readiness",
    "verify.unified_page_contract.lite",
    "verify.unified_page_contract.lite.load_contract_live_scope.container",
    "verify.unified_page_contract.lite.frontend_runtime_negative",
    "verify.unified_page_contract.lite.startup_negative.container",
    "verify.frontend.quick.gate",
)

REQUIRED_READINESS_TOKENS = (
    "readiness design only",
    "This document is not approved for implementation.",
    "frontend_pilot_readiness_designed_implementation_not_approved",
    "project.project:tree",
    "load_contract opt-in preview",
    "VITE_LITE_CONTRACT_PILOT=0",
    "default-off",
    "legacy fallback",
    "Frontend Pilot Gate",
    "no `ui.contract`",
    "no `login`",
    "no `system.init`",
    "no `runtimeContract`",
    "verify.unified_page_contract.lite.frontend_pilot_browser.container",
    "set VITE_LITE_CONTRACT_PILOT=0 and redeploy frontend",
)

REQUIRED_RISK_TOKENS = (
    "ui_contract_not_ready_for_runtime_preview",
    "Frontend Controlled Pilot Gate",
    "frontend controlled pilot readiness design",
    "This document is not approved for implementation.",
)

FORBIDDEN_TOKENS = (
    "frontend_pilot_implementation_approved",
    "ui_contract_runtime_approved",
    "ui.contract implementation approved",
    "Lite enabled by default",
    "runtimeContract approved",
    "global frontend runtime consumption approved",
)


def write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def missing_tokens(text: str, tokens: tuple[str, ...]) -> list[str]:
    return [token for token in tokens if token not in text]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--readiness-doc", required=True, type=Path)
    parser.add_argument("--risk-review", required=True, type=Path)
    parser.add_argument("--makefile", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()

    errors: list[str] = []

    missing_files = [relative for relative in REQUIRED_FILES if not (ROOT / relative).exists()]
    if missing_files:
        errors.append(f"missing frontend pilot readiness files: {missing_files}")

    makefile_text = args.makefile.read_text(encoding="utf-8")
    missing_targets = missing_tokens(makefile_text, REQUIRED_TARGETS)
    if missing_targets:
        errors.append(f"Makefile missing frontend pilot readiness targets: {missing_targets}")

    readiness_text = args.readiness_doc.read_text(encoding="utf-8")
    missing_readiness_tokens = missing_tokens(readiness_text, REQUIRED_READINESS_TOKENS)
    if missing_readiness_tokens:
        errors.append(f"frontend pilot readiness doc missing required tokens: {missing_readiness_tokens}")

    risk_text = args.risk_review.read_text(encoding="utf-8")
    missing_risk_tokens = missing_tokens(risk_text, REQUIRED_RISK_TOKENS)
    if missing_risk_tokens:
        errors.append(f"ui.contract risk review missing prerequisite tokens: {missing_risk_tokens}")

    forbidden_hits = [token for token in FORBIDDEN_TOKENS if token in readiness_text or token in risk_text]
    if forbidden_hits:
        errors.append(f"frontend pilot readiness contains forbidden approval tokens: {forbidden_hits}")

    report = {
        "ok": not errors,
        "decision": "frontend_pilot_readiness_designed_implementation_not_approved" if not errors else "blocked",
        "pilot_candidate": "project.project:tree",
        "source_entry": "load_contract opt-in preview",
        "feature_flag": "VITE_LITE_CONTRACT_PILOT=0",
        "default_off": True,
        "legacy_fallback_required": True,
        "implementation_approved": False,
        "frontend_consumption_approved": False,
        "ui_contract_allowed": False,
        "missing_files": missing_files,
        "missing_targets": missing_targets,
        "missing_readiness_tokens": missing_readiness_tokens,
        "missing_risk_tokens": missing_risk_tokens,
        "forbidden_hits": forbidden_hits,
        "errors": errors,
    }
    write_report(args.report, report)

    if errors:
        print("Unified Semantic Page Contract Lite frontend pilot readiness guard failed:")
        for error in errors:
            print(f"- {error}")
        print(f"- report: {args.report}")
        return 1

    print("Unified Semantic Page Contract Lite frontend pilot readiness guard passed")
    print("- decision: frontend_pilot_readiness_designed_implementation_not_approved")
    print("- pilot_candidate: project.project:tree")
    print("- source_entry: load_contract opt-in preview")
    print(f"- report: {args.report}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
