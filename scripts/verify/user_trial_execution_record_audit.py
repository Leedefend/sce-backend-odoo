#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    issue_board = ROOT / "artifacts" / "delivery" / "user_trial_issue_board_v1.json"
    execution_log = ROOT / "docs" / "ops" / "delivery_user_trial_execution_log_v1.md"

    errors: list[str] = []

    if not issue_board.exists():
        errors.append("missing_file:artifacts/delivery/user_trial_issue_board_v1.json")
    else:
        payload = json.loads(issue_board.read_text(encoding="utf-8"))
        summary = payload.get("summary") if isinstance(payload, dict) else None
        issues = payload.get("issues") if isinstance(payload, dict) else None
        if not isinstance(summary, dict):
            errors.append("invalid_json:summary")
        if not isinstance(issues, list) or not issues:
            errors.append("invalid_json:issues")

    if not execution_log.exists():
        errors.append("missing_file:docs/ops/delivery_user_trial_execution_log_v1.md")
    else:
        text = execution_log.read_text(encoding="utf-8")
        for token in [
            "## Execution Context",
            "## Trial Result Snapshot",
            "## Path-Level Outcome",
            "## Key Findings",
            "## Trial Decision",
            "decision: `GO_WITH_FIXES`",
            "UT-20260410-001",
        ]:
            if token not in text:
                errors.append(f"missing_token:execution_log:{token}")

    if errors:
        for item in errors:
            print(f"[user_trial_execution_record_audit] FAIL: {item}")
        return 2

    print("[user_trial_execution_record_audit] PASS")
    print("- user trial issue board baseline: PASS")
    print("- user trial execution log completeness: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
