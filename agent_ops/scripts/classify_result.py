#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

from common import LAST_RUN_PATH, load_json, load_task, stop_condition_ids


def main() -> int:
    parser = argparse.ArgumentParser(description="Classify the latest iteration result.")
    parser.add_argument("task", help="Task yaml path")
    args = parser.parse_args()

    _, task = load_task(args.task)
    run = load_json(LAST_RUN_PATH, default={})
    if run.get("task_id") != task.get("task_id"):
        payload = {
            "status": "FAIL",
            "classification": "FAIL",
            "reason": "last_run does not match the requested task",
        }
        print(json.dumps(payload, ensure_ascii=True, indent=2))
        return 1

    verify_passed = bool(run.get("verify", {}).get("passed"))
    acceptance_results = run.get("verify", {}).get("results", [])
    risk = run.get("risk_scan", {})
    validate = run.get("validate", {})
    outcomes = task.get("user_visible_outcome", [])
    uncertainty = bool(run.get("uncertainty_detected")) or bool(task.get("risk", {}).get("manual_approval_required"))
    stop_ids = stop_condition_ids()
    triggered_stop_conditions: list[str] = []
    triggered_stop_conditions.extend(
        item for item in risk.get("matched_rules", []) if item in stop_ids and item not in triggered_stop_conditions
    )
    if not verify_passed and "verify_failed" in stop_ids and "verify_failed" not in triggered_stop_conditions:
        triggered_stop_conditions.append("verify_failed")
    if not outcomes and "no_user_visible_progress" in stop_ids and "no_user_visible_progress" not in triggered_stop_conditions:
        triggered_stop_conditions.append("no_user_visible_progress")
    if uncertainty and "uncertain_business_decision" in stop_ids and "uncertain_business_decision" not in triggered_stop_conditions:
        triggered_stop_conditions.append("uncertain_business_decision")

    classification = "PASS"
    reasons: list[str] = []
    if not validate.get("passed"):
        classification = "FAIL"
        reasons.append("task_contract_invalid")
    elif risk.get("stop_required"):
        classification = "FAIL" if not verify_passed else "PASS_WITH_RISK"
        reasons.append("repo_level_risk_triggered")
    elif not verify_passed or any(item.get("exit_code") != 0 for item in acceptance_results):
        classification = "FAIL"
        reasons.append("any_acceptance_failed")
    elif not outcomes:
        classification = "FAIL"
        reasons.append("no_user_visible_progress")
    elif uncertainty:
        classification = "PASS_WITH_RISK"
        reasons.append("high_risk_or_uncertainty_detected")
    else:
        reasons.extend(["all_acceptance_passed", "no_high_risk_change", "user_visible_progress"])

    payload = {
        "status": "PASS" if classification != "FAIL" else "FAIL",
        "task_id": task.get("task_id"),
        "classification": classification,
        "reasons": reasons,
        "triggered_stop_conditions": triggered_stop_conditions,
    }
    print(json.dumps(payload, ensure_ascii=True, indent=2))
    return 0 if classification != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
