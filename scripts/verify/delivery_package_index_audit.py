#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    index_doc = ROOT / "docs" / "ops" / "delivery_package_index_v1.md"
    errors: list[str] = []

    if not index_doc.exists():
        errors.append("missing_file:docs/ops/delivery_package_index_v1.md")
    else:
        text = index_doc.read_text(encoding="utf-8")
        for token in [
            "## Core Decisions",
            "## Trial & Remediation",
            "## Verification Entry",
            "## Latest Smoke Evidence",
            "final_go_decision: `docs/ops/delivery_readiness_final_check_v1.md`",
            "trial_issue_board: `artifacts/delivery/user_trial_issue_board_v1.json`",
            "governance_gate: `python3 scripts/verify/v2_app_governance_gate_audit.py --json`",
        ]:
            if token not in text:
                errors.append(f"missing_token:index_doc:{token}")

    if errors:
        for item in errors:
            print(f"[delivery_package_index_audit] FAIL: {item}")
        return 2

    print("[delivery_package_index_audit] PASS")
    print("- delivery package index completeness: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
