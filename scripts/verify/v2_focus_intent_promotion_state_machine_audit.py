#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parents[2]
ROUTE_POLICY = ROOT / "artifacts" / "v2" / "v2_intent_route_policy_v1.json"
STATE_MACHINE = ROOT / "artifacts" / "v2" / "v2_focus_intent_promotion_state_machine_v1.json"
ROLLBACK_POLICY = ROOT / "artifacts" / "v2" / "v2_focus_intent_route_policy_rollback_v1.json"


def _run_json_command(cmd: List[str]) -> Dict[str, Any]:
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    if proc.returncode != 0:
        return {
            "status": "FAIL",
            "errors": ["command_failed"],
            "stdout": proc.stdout,
            "stderr": proc.stderr,
        }
    try:
        payload = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        return {
            "status": "FAIL",
            "errors": ["invalid_json"],
            "stdout": proc.stdout,
            "stderr": proc.stderr,
        }
    if not isinstance(payload, dict):
        return {"status": "FAIL", "errors": ["payload_not_object"]}
    return payload


def _load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _resolve_target_mode(current_mode: str, allow_v2_candidate: bool) -> str:
    if allow_v2_candidate:
        if current_mode in {"v2_primary", "v2_shadow"}:
            return "v2_primary"
        return "v2_shadow"
    if current_mode == "v2_primary":
        return "v2_shadow"
    return current_mode


def _resolve_state(current_mode: str, target_mode: str, allow_v2_candidate: bool) -> str:
    if not allow_v2_candidate and current_mode == "v2_primary":
        return "rollback_required"
    if target_mode == "v2_primary" and current_mode == "v2_shadow":
        return "candidate_ready"
    if target_mode == "v2_primary" and current_mode == "v2_primary":
        return "promoted"
    if target_mode == "v2_shadow" and current_mode == "legacy_only":
        return "shadow_bootstrap_required"
    if target_mode == "v2_shadow" and current_mode == "v2_shadow":
        return "shadow_observing"
    return "legacy_stable"


def _resolve_action(current_mode: str, target_mode: str) -> str:
    if current_mode == target_mode:
        return "keep"
    if target_mode == "v2_primary":
        return "promote_to_v2_primary"
    if target_mode == "v2_shadow":
        return "rollback_to_v2_shadow"
    return "keep"


def run_audit() -> Dict[str, Any]:
    errors: List[str] = []

    state_machine_snapshot = _load_json(STATE_MACHINE)
    if state_machine_snapshot.get("snapshot_id") != "v2_focus_intent_promotion_state_machine_v1":
        errors.append("invalid_state_machine_snapshot")

    focus_intents = state_machine_snapshot.get("focus_intents")
    if not isinstance(focus_intents, list) or not focus_intents:
        errors.append("missing_focus_intents")
        focus_intents = ["session.bootstrap", "meta.describe_model", "ui.contract"]

    policy = _load_json(ROUTE_POLICY)
    route_intents = policy.get("intents") if isinstance(policy.get("intents"), dict) else {}

    failure_summary = _run_json_command(
        ["python3", "scripts/verify/v2_focus_intent_compare_failure_summary.py", "--json"]
    )
    if failure_summary.get("status") != "PASS":
        errors.append("failure_summary_not_pass")

    allow_v2_candidate = bool(failure_summary.get("allow_v2_candidate"))
    diagnosis_status = str(failure_summary.get("diagnosis_status") or "")

    transitions: List[Dict[str, Any]] = []
    for intent in [str(value) for value in focus_intents]:
        current_mode = str(route_intents.get(intent) or policy.get("default_mode") or "legacy_only")
        target_mode = _resolve_target_mode(current_mode, allow_v2_candidate)
        state = _resolve_state(current_mode, target_mode, allow_v2_candidate)
        action = _resolve_action(current_mode, target_mode)
        transitions.append(
            {
                "intent": intent,
                "current_mode": current_mode,
                "target_mode": target_mode,
                "state": state,
                "action": action,
                "allow_v2_candidate": allow_v2_candidate,
                "diagnosis_status": diagnosis_status,
            }
        )

    if any(item.get("current_mode") == "v2_primary" and not allow_v2_candidate for item in transitions):
        errors.append("v2_primary_without_candidate")

    allowed_actions = state_machine_snapshot.get("allowed_actions")
    if isinstance(allowed_actions, list) and allowed_actions:
        for item in transitions:
            if str(item.get("action") or "") not in {str(v) for v in allowed_actions}:
                errors.append(f"action_not_allowed:{item.get('intent')}:{item.get('action')}")

    rollback_policy = _load_json(ROLLBACK_POLICY)
    if rollback_policy:
        rollback_intents = rollback_policy.get("focus_intents") if isinstance(rollback_policy.get("focus_intents"), dict) else {}
        for intent in [str(value) for value in focus_intents]:
            if str(rollback_intents.get(intent) or "") != "v2_shadow":
                errors.append(f"rollback_mode_not_shadow:{intent}")

    return {
        "gate_version": "v1",
        "gate_profile": "full",
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "allow_v2_candidate": allow_v2_candidate,
        "diagnosis_status": diagnosis_status,
        "transition_plan": transitions,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = run_audit()
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"status={result['status']}")
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
