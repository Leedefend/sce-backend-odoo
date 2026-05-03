#!/usr/bin/env python3
"""Guard the Lite all_tree mainline readiness conclusion."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]

DOC_PATH = ROOT / "docs/architecture/unified_page_contract_lite/mainline_readiness_batch_53.md"
MAKEFILE_PATH = ROOT / "Makefile"
ROLLOUT_GUARD_PATH = ROOT / "scripts/verify/unified_page_contract_lite_rollout_switch_guard.py"
RUNTIME_PATH = ROOT / "frontend/apps/web/src/app/runtime/unifiedPageContractLitePilot.ts"

DOC_REQUIRED = (
    "Status: ready for mainline review",
    "allowed to merge while Lite remains default-off",
    "VITE_LITE_CONTRACT_ROLLOUT is unset by default",
    "make verify.unified_page_contract.lite",
    "make verify.frontend.quick.gate",
    "make verify.docs.all",
    "make verify.unified_page_contract.lite.all_tree_acceptance_browser.host",
    "does not make Lite the default",
    "does not change `login`",
    "does not change `system.init`",
    "does not remove legacy fallback",
    "default runtime remains off",
)

MAKEFILE_REQUIRED = (
    "verify.unified_page_contract.lite.all_tree_acceptance_browser.host",
    "verify.unified_page_contract.lite.rollout_switch",
    "verify.unified_page_contract.lite",
)

ROLLOUT_GUARD_REQUIRED = (
    "lite_rollout_switch_default_off",
    "all_tree_acceptance_browser_smoke",
)

RUNTIME_REQUIRED = (
    "return String(import.meta.env.VITE_LITE_CONTRACT_PILOT || '').trim() === '1' ? 'pilot' : 'off';",
    "if (rollout === 'all_tree') return 'all_tree';",
)

FORBIDDEN_DOC_RUNTIME = (
    "Lite is now the default",
    "VITE_LITE_CONTRACT_ROLLOUT=all_tree by default",
    "system.init Lite default",
    "login Lite default",
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def missing_tokens(text: str, tokens: tuple[str, ...]) -> list[str]:
    return [token for token in tokens if token not in text]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()

    errors: list[str] = []
    for path in (DOC_PATH, MAKEFILE_PATH, ROLLOUT_GUARD_PATH, RUNTIME_PATH):
        if not path.exists():
            errors.append(f"missing file: {path.relative_to(ROOT)}")

    doc = read_text(DOC_PATH) if DOC_PATH.exists() else ""
    makefile = read_text(MAKEFILE_PATH) if MAKEFILE_PATH.exists() else ""
    rollout_guard = read_text(ROLLOUT_GUARD_PATH) if ROLLOUT_GUARD_PATH.exists() else ""
    runtime = read_text(RUNTIME_PATH) if RUNTIME_PATH.exists() else ""

    for label, text, tokens in (
        ("doc", doc, DOC_REQUIRED),
        ("makefile", makefile, MAKEFILE_REQUIRED),
        ("rollout_guard", rollout_guard, ROLLOUT_GUARD_REQUIRED),
        ("runtime", runtime, RUNTIME_REQUIRED),
    ):
        missing = missing_tokens(text, tokens)
        if missing:
            errors.append(f"{label} missing tokens: {missing}")

    searched = (doc, runtime)
    forbidden = sorted({token for token in FORBIDDEN_DOC_RUNTIME if any(token in text for text in searched)})
    if forbidden:
        errors.append(f"forbidden readiness tokens found: {forbidden}")

    report = {
        "ok": not errors,
        "decision": "ready_for_mainline_review_default_off" if not errors else "blocked",
        "runtime_default": "off",
        "all_tree_gate": "verify.unified_page_contract.lite.all_tree_acceptance_browser.host",
        "errors": errors,
    }
    write_report(args.report, report)

    if errors:
        print("Unified Semantic Page Contract Lite mainline readiness guard failed:")
        for error in errors:
            print(f"- {error}")
        print(f"- report: {args.report}")
        return 1

    print("Unified Semantic Page Contract Lite mainline readiness guard passed")
    print("- decision: ready_for_mainline_review_default_off")
    print("- runtime default: off")
    print(f"- report: {args.report}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
