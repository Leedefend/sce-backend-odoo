#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
REPORT_JSON = ROOT / "artifacts" / "backend" / "delivery_mainline_run_summary.json"
REPORT_MD = ROOT / "artifacts" / "backend" / "delivery_mainline_run_summary.md"
ALLOWED_STATUS = {"PASS", "FAIL", "SKIP"}
REQUIRED_STEPS = (
    "frontend_gate",
    "scene_delivery_readiness",
    "action_closure_smoke",
    "module_capability_smoke",
    "module9_smoke",
    "governance_truth",
)


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def main() -> int:
    payload = _load_json(REPORT_JSON)
    errors: list[str] = []

    if not payload:
        errors.append(f"missing or invalid json: {REPORT_JSON.relative_to(ROOT).as_posix()}")
    else:
        for key in ("generated_at_utc", "branch", "commit_ref", "profile"):
            if not isinstance(payload.get(key), str) or not payload.get(key):
                errors.append(f"{key} must be non-empty string")
        if not isinstance(payload.get("ok"), bool):
            errors.append("ok must be bool")

        steps = payload.get("steps")
        if not isinstance(steps, dict):
            errors.append("steps must be object")
        else:
            for key in REQUIRED_STEPS:
                if steps.get(key) not in ALLOWED_STATUS:
                    errors.append(f"steps.{key} must be PASS|FAIL|SKIP")
            if steps.get("module9_smoke") != steps.get("module_capability_smoke"):
                errors.append("steps.module9_smoke must mirror steps.module_capability_smoke")
            expected_ok = all(steps.get(key) == "PASS" for key in REQUIRED_STEPS)
            if isinstance(payload.get("ok"), bool) and payload["ok"] != expected_ok:
                errors.append("ok must match all required steps PASS")

    if not REPORT_MD.is_file():
        errors.append(f"missing markdown report: {REPORT_MD.relative_to(ROOT).as_posix()}")
    else:
        md_text = REPORT_MD.read_text(encoding="utf-8")
        for token in (
            "# Delivery Mainline Run Summary",
            "- generated_at_utc:",
            "- branch:",
            "- commit_ref:",
            "| step | status |",
            "| governance_truth |",
        ):
            if token not in md_text:
                errors.append(f"markdown report missing token: {token}")

    if errors:
        print("[delivery_mainline_run_summary_schema_guard] FAIL")
        for error in errors:
            print(error)
        return 2

    print("[delivery_mainline_run_summary_schema_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
