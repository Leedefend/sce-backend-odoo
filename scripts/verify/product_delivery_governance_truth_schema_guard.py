#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
REPORT_JSON = ROOT / "artifacts" / "backend" / "product_delivery_governance_truth_guard_report.json"
REPORT_MD = ROOT / "docs" / "ops" / "audit" / "product_delivery_governance_truth_guard_report.md"


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
        if not isinstance(payload.get("ok"), bool):
            errors.append("ok must be bool")

        summary = payload.get("summary")
        if not isinstance(summary, dict):
            errors.append("summary must be object")
        else:
            required_summary_keys = {
                "backlog_row_count": int,
                "backlog_unresolved_count": int,
                "scoreboard_module_rows": int,
                "scoreboard_journey_rows": int,
                "scoreboard_snapshot_max_age_hours": int,
                "context_log_pending_commit_count": int,
                "context_log_recent_pending_commit_count": int,
                "context_log_pending_window_lines": int,
                "error_count": int,
                "warning_count": int,
            }
            for key, expected_type in required_summary_keys.items():
                if not isinstance(summary.get(key), expected_type):
                    errors.append(f"summary.{key} must be {expected_type.__name__}")
            age = summary.get("scoreboard_snapshot_age_hours")
            if age is not None and not isinstance(age, (int, float)):
                errors.append("summary.scoreboard_snapshot_age_hours must be number or null")

        snapshot = payload.get("snapshot")
        if not isinstance(snapshot, dict):
            errors.append("snapshot must be object")
        else:
            for key in ("generated_at_utc", "branch", "commit_ref", "current_head_short_sha", "gate_result"):
                if not isinstance(snapshot.get(key), str):
                    errors.append(f"snapshot.{key} must be string")
            changed_files = snapshot.get("post_snapshot_changed_files")
            if not isinstance(changed_files, list) or not all(isinstance(item, str) for item in changed_files):
                errors.append("snapshot.post_snapshot_changed_files must be string list")

        for key in ("errors", "warnings"):
            value = payload.get(key)
            if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
                errors.append(f"{key} must be string list")

        summary_obj = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
        report_errors = payload.get("errors") if isinstance(payload.get("errors"), list) else []
        report_warnings = payload.get("warnings") if isinstance(payload.get("warnings"), list) else []
        if isinstance(summary_obj.get("error_count"), int) and summary_obj["error_count"] != len(report_errors):
            errors.append("summary.error_count must match errors length")
        if isinstance(summary_obj.get("warning_count"), int) and summary_obj["warning_count"] != len(report_warnings):
            errors.append("summary.warning_count must match warnings length")
        if payload.get("ok") is True and report_errors:
            errors.append("ok=true report must not contain errors")
        if payload.get("ok") is False and not report_errors:
            errors.append("ok=false report must contain errors")

    if not REPORT_MD.is_file():
        errors.append(f"missing markdown report: {REPORT_MD.relative_to(ROOT).as_posix()}")
    else:
        md_text = REPORT_MD.read_text(encoding="utf-8")
        for token in (
            "# Product Delivery Governance Truth Guard",
            "- backlog_row_count:",
            "- error_count:",
            "- warning_count:",
            "## Errors",
            "## Warnings",
        ):
            if token not in md_text:
                errors.append(f"markdown report missing token: {token}")

    if errors:
        print("[product_delivery_governance_truth_schema_guard] FAIL")
        for error in errors:
            print(error)
        return 2

    print("[product_delivery_governance_truth_schema_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
