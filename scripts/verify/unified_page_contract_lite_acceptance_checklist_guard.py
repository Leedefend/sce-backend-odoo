#!/usr/bin/env python3
"""Guard the first Lite runtime acceptance checklist."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REQUIRED_PHRASES = (
    "api.onchange",
    "\"entryPoint\": \"api_onchange\"",
    "\"payloadType\": \"lite_patch\"",
    "default `api.onchange` request returns unchanged legacy response",
    "incomplete Lite preview request returns unchanged legacy response",
    "valid Lite preview request returns opt-in response envelope",
    "no `ui.contract` output changes",
    "no `login` output changes",
    "no `system.init` output changes",
    "rollback is `disable opt-in flag`",
    "Batch-19: api.onchange Lite opt-in preview runtime validation",
)
FORBIDDEN_PHRASES = (
    "enable Lite preview by default",
    "change frontend runtime",
    "introduce `runtimeContract`",
)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checklist", required=True, type=Path)
    parser.add_argument("--readiness-report", required=True, type=Path)
    parser.add_argument("--integration-plan-report", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()

    errors: list[str] = []
    checklist = args.checklist.read_text(encoding="utf-8")
    readiness = load_json(args.readiness_report)
    integration_plan = load_json(args.integration_plan_report)

    if readiness.get("ok") is not True:
        errors.append("readiness report is not ok")
    if integration_plan.get("decision") != "planning_gate_passed_runtime_still_blocked":
        errors.append("integration plan gate is not in expected blocked state")
    missing = [phrase for phrase in REQUIRED_PHRASES if phrase not in checklist]
    if missing:
        errors.append(f"acceptance checklist missing required phrases: {missing}")
    # Forbidden items must appear only under the explicit forbidden section.
    if "## 7. Forbidden In First Runtime Batch" not in checklist:
        errors.append("acceptance checklist must include forbidden section")
    forbidden_section = checklist.split("## 7. Forbidden In First Runtime Batch", 1)[-1]
    for phrase in FORBIDDEN_PHRASES:
        if phrase not in forbidden_section:
            errors.append(f"forbidden phrase must be listed in forbidden section: {phrase}")

    report = {
        "ok": not errors,
        "decision": "acceptance_checklist_ready_batch_19_still_not_started" if not errors else "blocked",
        "checklist": str(args.checklist),
        "readiness_ok": readiness.get("ok"),
        "integration_plan_decision": integration_plan.get("decision"),
        "errors": errors,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if errors:
        print("Unified Semantic Page Contract Lite acceptance checklist guard failed:")
        for error in errors:
            print(f"- {error}")
        print(f"- report: {args.report}")
        return 1

    print("Unified Semantic Page Contract Lite acceptance checklist guard passed")
    print(f"- report: {args.report}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
