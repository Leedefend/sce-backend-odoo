#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List


ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "artifacts" / "v2" / "v2_intent_route_policy_v1.json"


def run_audit() -> Dict[str, object]:
    errors: List[str] = []

    if not POLICY_PATH.exists():
        return {
            "gate_version": "v1",
            "gate_profile": "full",
            "status": "FAIL",
            "errors": ["missing_route_policy_snapshot"],
        }

    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    if str(policy.get("snapshot_id") or "") != "v2_intent_route_policy_v1":
        errors.append("invalid_snapshot_id")

    allowed_modes = set(policy.get("allowed_modes") or [])
    if allowed_modes != {"legacy_only", "v2_shadow", "v2_primary"}:
        errors.append("allowed_modes_mismatch")

    intents = policy.get("intents") if isinstance(policy.get("intents"), dict) else {}
    for key in ["session.bootstrap", "meta.describe_model", "ui.contract"]:
        mode = str(intents.get(key) or "")
        if mode not in {"legacy_only", "v2_shadow", "v2_primary"}:
            errors.append(f"invalid_mode_for:{key}")

    sys.path.insert(0, str(ROOT / "addons" / "smart_core"))
    from core.intent_route_mode_policy import resolve_intent_route_mode  # type: ignore

    session_decision = resolve_intent_route_mode("session.bootstrap")
    if str(session_decision.get("mode") or "") != str(intents.get("session.bootstrap") or ""):
        errors.append("resolver_mismatch_session_bootstrap")

    unknown_decision = resolve_intent_route_mode("unknown.intent.example")
    if str(unknown_decision.get("mode") or "") != str(policy.get("default_mode") or "legacy_only"):
        errors.append("resolver_default_mode_mismatch")

    return {
        "gate_version": "v1",
        "gate_profile": "full",
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "focus_decisions": {
            "session.bootstrap": resolve_intent_route_mode("session.bootstrap"),
            "meta.describe_model": resolve_intent_route_mode("meta.describe_model"),
            "ui.contract": resolve_intent_route_mode("ui.contract"),
        },
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
