#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    orchestration = ROOT / "docs" / "ops" / "delivery_user_trial_orchestration_v1.md"
    issue_template = ROOT / "docs" / "ops" / "delivery_user_trial_issue_template_v1.md"

    errors: list[str] = []

    if not orchestration.exists():
      errors.append("missing_file:docs/ops/delivery_user_trial_orchestration_v1.md")
    else:
      text = orchestration.read_text(encoding="utf-8")
      for token in [
          "## Trial Objective",
          "## Trial Scope",
          "## Trial Roles",
          "## Trial Paths",
          "### Path A：项目立项主链",
          "### Path B：执行与成本链",
          "### Path C：合同与付款链",
          "## Acceptance Checklist",
          "## Issue Triage Rule",
          "## Trial Output",
      ]:
          if token not in text:
              errors.append(f"missing_token:orchestration:{token}")

    if not issue_template.exists():
      errors.append("missing_file:docs/ops/delivery_user_trial_issue_template_v1.md")
    else:
      text = issue_template.read_text(encoding="utf-8")
      for token in [
          "## Basic Info",
          "## Repro Steps",
          "## Actual vs Expected",
          "## Observability",
          "## Impact",
          "## Disposition",
          "severity: `P0 | P1 | P2 | P3`",
      ]:
          if token not in text:
              errors.append(f"missing_token:template:{token}")

    if errors:
      for item in errors:
          print(f"[delivery_user_trial_orchestration_audit] FAIL: {item}")
      return 2

    print("[delivery_user_trial_orchestration_audit] PASS")
    print("- user trial orchestration completeness: PASS")
    print("- issue template completeness: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
