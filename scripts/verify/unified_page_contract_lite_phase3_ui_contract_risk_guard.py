#!/usr/bin/env python3
"""Guard the Lite ui.contract risk review decision."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]

REQUIRED_FILES = (
    "docs/architecture/unified_page_contract_lite/phase2_load_contract_preview_batch_39.md",
    "docs/architecture/unified_page_contract_lite/phase3_ui_contract_risk_review_batch_42.md",
    "scripts/verify/unified_page_contract_lite_phase3_ui_contract_risk_guard.py",
)

REQUIRED_TARGETS = (
    "verify.unified_page_contract.lite.phase3_ui_contract_risk",
    "verify.unified_page_contract.lite",
    "verify.unified_page_contract.lite.load_contract_live_scope.container",
    "verify.unified_page_contract.lite.frontend_runtime_negative",
    "verify.unified_page_contract.lite.startup_negative.container",
)

REQUIRED_REVIEW_TOKENS = (
    "risk review only",
    "This document is not approved for implementation.",
    "ui_contract_not_ready_for_runtime_preview",
    "api_onchange",
    "load_contract",
    "ui.contract",
    "login",
    "system.init",
    "frontend runtime",
    "runtimeContract",
    "Frontend Controlled Pilot Gate",
    "frontend controlled pilot readiness design",
    "make verify.unified_page_contract.lite.load_contract_live_scope.container",
    "make verify.unified_page_contract.lite.frontend_runtime_negative",
    "make verify.contract.preflight",
    "make verify.boundary.guard",
    "make verify.frontend.quick.gate",
)

REQUIRED_PREVIEW_TOKENS = (
    "api_onchange opt-in preview",
    "load_contract opt-in preview",
    "Frontend consumption remains blocked.",
)

FORBIDDEN_TOKENS = (
    "ui_contract_runtime_approved",
    "ui.contract implementation approved",
    "frontend runtime enabled",
    "Lite default page contract",
    "runtimeContract approved",
)


def write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def missing_tokens(text: str, tokens: tuple[str, ...]) -> list[str]:
    return [token for token in tokens if token not in text]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--review", required=True, type=Path)
    parser.add_argument("--preview-doc", required=True, type=Path)
    parser.add_argument("--makefile", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()

    errors: list[str] = []

    missing_files = [relative for relative in REQUIRED_FILES if not (ROOT / relative).exists()]
    if missing_files:
        errors.append(f"missing ui.contract risk review files: {missing_files}")

    makefile_text = args.makefile.read_text(encoding="utf-8")
    missing_targets = missing_tokens(makefile_text, REQUIRED_TARGETS)
    if missing_targets:
        errors.append(f"Makefile missing ui.contract risk targets: {missing_targets}")

    review_text = args.review.read_text(encoding="utf-8")
    missing_review_tokens = missing_tokens(review_text, REQUIRED_REVIEW_TOKENS)
    if missing_review_tokens:
        errors.append(f"ui.contract risk review missing required tokens: {missing_review_tokens}")

    preview_text = args.preview_doc.read_text(encoding="utf-8")
    missing_preview_tokens = missing_tokens(preview_text, REQUIRED_PREVIEW_TOKENS)
    if missing_preview_tokens:
        errors.append(f"load_contract preview doc missing prerequisite tokens: {missing_preview_tokens}")

    forbidden_hits = [token for token in FORBIDDEN_TOKENS if token in review_text]
    if forbidden_hits:
        errors.append(f"ui.contract risk review contains forbidden approval tokens: {forbidden_hits}")

    report = {
        "ok": not errors,
        "decision": "ui_contract_not_ready_for_runtime_preview" if not errors else "blocked",
        "recommended_next_step": "frontend controlled pilot readiness design",
        "implementation_approved": False,
        "frontend_consumption_approved": False,
        "missing_files": missing_files,
        "missing_targets": missing_targets,
        "missing_review_tokens": missing_review_tokens,
        "missing_preview_tokens": missing_preview_tokens,
        "forbidden_hits": forbidden_hits,
        "errors": errors,
    }
    write_report(args.report, report)

    if errors:
        print("Unified Semantic Page Contract Lite ui.contract risk guard failed:")
        for error in errors:
            print(f"- {error}")
        print(f"- report: {args.report}")
        return 1

    print("Unified Semantic Page Contract Lite ui.contract risk guard passed")
    print("- decision: ui_contract_not_ready_for_runtime_preview")
    print("- next: frontend controlled pilot readiness design")
    print(f"- report: {args.report}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
