#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parents[2]
ROUTE_POLICY = ROOT / "artifacts" / "v2" / "v2_intent_route_policy_v1.json"
ROLLBACK_POLICY = ROOT / "artifacts" / "v2" / "v2_focus_intent_route_policy_rollback_v1.json"
OUTPUT = ROOT / "artifacts" / "v2" / "v2_rollback_readiness_recheck_v1.json"


def _load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _run_smoke() -> Dict[str, Any]:
    proc = subprocess.run(
        ["python3", "scripts/verify/v2_primary_minimum_business_smoke.py", "--json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return {"status": "FAIL", "errors": ["smoke_command_failed"], "stdout": proc.stdout, "stderr": proc.stderr}
    try:
        payload = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        return {"status": "FAIL", "errors": ["smoke_invalid_json"], "stdout": proc.stdout, "stderr": proc.stderr}
    return payload if isinstance(payload, dict) else {"status": "FAIL", "errors": ["smoke_payload_not_object"]}


def _resolve_focus_modes() -> Dict[str, str]:
    sys.path.insert(0, str(ROOT / "addons" / "smart_core"))
    from core.intent_route_mode_policy import resolve_intent_route_mode  # type: ignore

    return {
        "session.bootstrap": str(resolve_intent_route_mode("session.bootstrap").get("mode") or ""),
        "meta.describe_model": str(resolve_intent_route_mode("meta.describe_model").get("mode") or ""),
        "ui.contract": str(resolve_intent_route_mode("ui.contract").get("mode") or ""),
    }


def run_audit() -> Dict[str, Any]:
    errors: List[str] = []

    route_policy = _load_json(ROUTE_POLICY)
    rollback_policy = _load_json(ROLLBACK_POLICY)
    rollback_intents = rollback_policy.get("focus_intents") if isinstance(rollback_policy.get("focus_intents"), dict) else {}

    if not route_policy or not rollback_intents:
        if not route_policy:
            errors.append("missing_route_policy")
        if not rollback_intents:
            errors.append("missing_rollback_policy")
        report = {"rollback_applied": False, "shadow_mode_smoke": "FAIL", "consistency": False, "errors": errors}
        OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"gate_version": "v1", "gate_profile": "full", "status": "FAIL", "errors": errors, "report": report}

    original_text = ROUTE_POLICY.read_text(encoding="utf-8")
    rollback_applied = False
    consistency = False
    smoke_status = "FAIL"
    mode_snapshot: Dict[str, str] = {}

    try:
        intents = route_policy.get("intents") if isinstance(route_policy.get("intents"), dict) else {}
        for intent_name, mode in rollback_intents.items():
            intents[str(intent_name)] = str(mode)
        route_policy["intents"] = intents
        ROUTE_POLICY.write_text(json.dumps(route_policy, ensure_ascii=False, indent=2), encoding="utf-8")
        rollback_applied = True

        mode_snapshot = _resolve_focus_modes()
        consistency = all(mode == "v2_shadow" for mode in mode_snapshot.values())
        if not consistency:
            errors.append("rollback_mode_not_shadow")

        smoke = _run_smoke()
        smoke_status = "PASS" if smoke.get("status") == "PASS" else "FAIL"
        if smoke_status != "PASS":
            errors.append("shadow_mode_smoke_fail")
    finally:
        ROUTE_POLICY.write_text(original_text, encoding="utf-8")

    report = {
        "rollback_applied": rollback_applied,
        "shadow_mode_smoke": smoke_status,
        "consistency": consistency,
        "focus_modes_after_rollback": mode_snapshot,
        "errors": errors,
    }
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "gate_version": "v1",
        "gate_profile": "full",
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "report": report,
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
