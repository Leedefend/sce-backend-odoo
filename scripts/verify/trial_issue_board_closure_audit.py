#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    board = ROOT / "artifacts" / "delivery" / "user_trial_issue_board_v1.json"
    log = ROOT / "docs" / "ops" / "delivery_user_trial_execution_log_v1.md"

    errors: list[str] = []
    if not board.exists():
        errors.append("missing_file:artifacts/delivery/user_trial_issue_board_v1.json")
    else:
        payload = json.loads(board.read_text(encoding="utf-8"))
        summary = payload.get("summary") if isinstance(payload, dict) else {}
        issues = payload.get("issues") if isinstance(payload, dict) else []
        if not isinstance(summary, dict):
            errors.append("invalid_json:summary")
            summary = {}
        if not isinstance(issues, list):
            errors.append("invalid_json:issues")
            issues = []
        if int(summary.get("open", -1)) != 0:
            errors.append("summary_open_not_zero")
        unresolved = [row.get("issue_id") for row in issues if isinstance(row, dict) and str(row.get("status", "")).upper() == "OPEN"]
        if unresolved:
            errors.append(f"open_issues_remaining:{','.join(map(str, unresolved))}")

    if not log.exists():
        errors.append("missing_file:docs/ops/delivery_user_trial_execution_log_v1.md")
    else:
        text = log.read_text(encoding="utf-8")
        for token in [
            "decision: `GO`",
            "UT-20260410-002",
            "UT-20260410-003",
            "已在 `ITER-1709` 修复并验证",
            "已在 `ITER-1710` 修复并验证",
        ]:
            if token not in text:
                errors.append(f"missing_token:log:{token}")

    if errors:
        for item in errors:
            print(f"[trial_issue_board_closure_audit] FAIL: {item}")
        return 2

    print("[trial_issue_board_closure_audit] PASS")
    print("- issue board closure status is clean: PASS")
    print("- trial execution conclusion updated to GO: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
