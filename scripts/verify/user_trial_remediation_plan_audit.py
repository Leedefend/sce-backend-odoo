#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    issue_board = ROOT / "artifacts" / "delivery" / "user_trial_issue_board_v1.json"
    plan_doc = ROOT / "docs" / "ops" / "delivery_user_trial_remediation_plan_v1.md"
    errors: list[str] = []

    open_issues: list[str] = []
    if not issue_board.exists():
        errors.append("missing_file:artifacts/delivery/user_trial_issue_board_v1.json")
    else:
        payload = json.loads(issue_board.read_text(encoding="utf-8"))
        issues = payload.get("issues") if isinstance(payload, dict) else []
        if not isinstance(issues, list):
            errors.append("invalid_json:issues")
            issues = []
        for item in issues:
            if not isinstance(item, dict):
                continue
            if str(item.get("status", "")).upper() == "OPEN" and str(item.get("severity", "")).upper() in {"P2", "P3"}:
                open_issues.append(str(item.get("issue_id", "")).strip())

    if not plan_doc.exists():
        errors.append("missing_file:docs/ops/delivery_user_trial_remediation_plan_v1.md")
    else:
        text = plan_doc.read_text(encoding="utf-8")
        for token in [
            "## Input Baseline",
            "## Planning Principle",
            "## Remediation Backlog",
            "## Batch Plan",
            "### ITER-2026-04-10-1709",
            "### ITER-2026-04-10-1710",
            "## Exit Criteria",
        ]:
            if token not in text:
                errors.append(f"missing_token:plan:{token}")

        for issue_id in open_issues:
            if issue_id and issue_id not in text:
                errors.append(f"missing_open_issue_mapping:{issue_id}")

    if errors:
        for item in errors:
            print(f"[user_trial_remediation_plan_audit] FAIL: {item}")
        return 2

    print("[user_trial_remediation_plan_audit] PASS")
    print("- open P2/P3 issues are mapped into remediation plan: PASS")
    print("- remediation batches and exit criteria are complete: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
