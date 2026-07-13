#!/usr/bin/env python3
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "docs" / "engineering_convergence" / "p4_p0_03_contract_form_split_evidence.md"
FORM_PAGE = ROOT / "frontend" / "apps" / "web" / "src" / "pages" / "ContractFormPage.vue"
BASELINE = ROOT / "docs" / "engineering_convergence" / "complexity_baseline_lock.json"


REQUIRED_TOKENS = (
    "make ci.local.quick",
    "make ci",
    "python3 scripts/verify/web_contract_v2_frontend_architecture_guard.py",
    "python3 scripts/ci/enforce_complexity_baseline_lock.py",
    "python3 scripts/verify/frontend_page_contract_boundary_guard.py",
    "python3 scripts/verify/frontend_page_contract_orchestration_consumption_guard.py",
    "python3 scripts/verify/frontend_contract_consumer_intrusion_guard.py",
    "Current HEAD remote verification is pending until PR/merge readiness.",
)


def _line_count(path: Path) -> int:
    return len(path.read_text(encoding="utf-8", errors="ignore").splitlines())


def _git_short_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short=9", "HEAD"],
            cwd=ROOT,
            text=True,
            timeout=5,
        ).strip()
    except Exception:
        return ""


def main() -> int:
    errors: list[str] = []
    text = EVIDENCE.read_text(encoding="utf-8", errors="ignore") if EVIDENCE.is_file() else ""
    if not text:
        errors.append(f"missing evidence document: {EVIDENCE.relative_to(ROOT)}")
    if not FORM_PAGE.is_file():
        errors.append(f"missing form page: {FORM_PAGE.relative_to(ROOT)}")
    if not BASELINE.is_file():
        errors.append(f"missing complexity baseline: {BASELINE.relative_to(ROOT)}")

    if not errors:
        current_lines = _line_count(FORM_PAGE)
        expected_row = (
            f"| `{FORM_PAGE.relative_to(ROOT).as_posix()}` | 13762 | {current_lines} |"
        )
        if expected_row not in text:
            errors.append(
                "ContractFormPage line-count evidence is stale: "
                f"expected row `{expected_row}`"
            )
        line_lock = f"`ContractFormPage.vue` is line-count locked at {current_lines} lines."
        if line_lock not in text:
            errors.append(
                "ContractFormPage line-count lock wording is stale: "
                f"expected `{line_lock}`"
            )

    for token in REQUIRED_TOKENS:
        if token not in text:
            errors.append(f"evidence missing token: {token}")

    if "Remote verification completed:" in text:
        errors.append("evidence must not claim current remote verification completed before PR/merge readiness")

    head = _git_short_head()
    if head and f"on `{head}`" in text:
        errors.append(
            "current HEAD appears in historical remote verification list; "
            "move it to current remote evidence only after PR/merge remote CI passes"
        )

    if errors:
        print("[contract_form_split_evidence] FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"[contract_form_split_evidence] PASS lines={_line_count(FORM_PAGE)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
