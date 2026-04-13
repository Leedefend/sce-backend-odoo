#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    check_doc = ROOT / "docs" / "ops" / "delivery_readiness_final_check_v1.md"
    issue_board = ROOT / "artifacts" / "delivery" / "user_trial_issue_board_v1.json"
    errors: list[str] = []

    if not check_doc.exists():
        errors.append("missing_file:docs/ops/delivery_readiness_final_check_v1.md")
    else:
        text = check_doc.read_text(encoding="utf-8")
        for token in [
            "## Final Decision",
            "readiness: `GO`",
            "## Final Gate Checklist",
            "## Evidence Index",
            "## Operator Checklist",
            "## Stop Rules",
            "trial_issue_board: `artifacts/delivery/user_trial_issue_board_v1.json`",
        ]:
            if token not in text:
                errors.append(f"missing_token:check_doc:{token}")

    if not issue_board.exists():
        errors.append("missing_file:artifacts/delivery/user_trial_issue_board_v1.json")
    else:
        payload = json.loads(issue_board.read_text(encoding="utf-8"))
        summary = payload.get("summary") if isinstance(payload, dict) else {}
        if not isinstance(summary, dict):
            errors.append("invalid_json:issue_board.summary")
        elif int(summary.get("open", -1)) != 0:
            errors.append("issue_board_not_closed:open_must_be_0")

    if errors:
        for item in errors:
            print(f"[delivery_readiness_final_check_audit] FAIL: {item}")
        return 2

    print("[delivery_readiness_final_check_audit] PASS")
    print("- final check document completeness: PASS")
    print("- trial issue board closure consistency: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
