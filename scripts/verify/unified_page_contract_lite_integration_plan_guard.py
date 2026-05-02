#!/usr/bin/env python3
"""Guard the Lite runtime integration plan before any runtime connection."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REQUIRED_PHRASES = (
    "opt-in only",
    "non-default",
    "reversible",
    "default response remains unchanged",
    "default ui.contract remains unchanged",
    "default onchange response remains unchanged",
    "login -> system.init -> ui.contract",
    "disable opt-in flag",
    "Runtime integration is not approved by this batch",
)
FORBIDDEN_APPROVAL_PHRASES = (
    "runtime integration is approved",
    "enable by default",
    "default output changes",
    "frontend must infer",
    "enable runtimeContract",
    "introduce runtimeContract",
)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--readiness-report", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()

    errors: list[str] = []
    text = args.plan.read_text(encoding="utf-8")
    lower_text = text.lower()
    readiness = load_json(args.readiness_report)
    if readiness.get("decision") != "ready_for_explicit_runtime_integration_planning":
        errors.append("Phase 1 readiness report is not ready for integration planning")
    missing_phrases = [phrase for phrase in REQUIRED_PHRASES if phrase.lower() not in lower_text]
    if missing_phrases:
        errors.append(f"integration plan missing required phrases: {missing_phrases}")
    forbidden_hits = [phrase for phrase in FORBIDDEN_APPROVAL_PHRASES if phrase.lower() in lower_text]
    if forbidden_hits:
        errors.append(f"integration plan contains forbidden approval phrase: {forbidden_hits}")

    report = {
        "ok": not errors,
        "decision": "planning_gate_passed_runtime_still_blocked" if not errors else "blocked",
        "plan": str(args.plan),
        "readiness_decision": readiness.get("decision"),
        "missing_phrases": missing_phrases,
        "forbidden_hits": forbidden_hits,
        "errors": errors,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if errors:
        print("Unified Semantic Page Contract Lite integration plan guard failed:")
        for error in errors:
            print(f"- {error}")
        print(f"- report: {args.report}")
        return 1

    print("Unified Semantic Page Contract Lite integration plan guard passed")
    print(f"- report: {args.report}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
