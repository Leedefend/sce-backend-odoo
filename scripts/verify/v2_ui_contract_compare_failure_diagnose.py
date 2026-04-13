#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT = ROOT / "artifacts" / "v2" / "v2_focus_intent_compare_failure_snapshot_v1.json"


def _extract_error(v2_result: Any) -> tuple[str, str]:
    if not isinstance(v2_result, dict):
        return "", ""
    err = v2_result.get("error")
    if not isinstance(err, dict):
        return "", ""
    return str(err.get("code") or ""), str(err.get("message") or "")


def _stage_from_error(code: str) -> str:
    if not code:
        return "none"
    if code == "INTENT_NOT_FOUND":
        return "registry_lookup"
    if code == "VALIDATION_FAILED":
        return "schema_validate"
    if code == "DISPATCH_FAILED":
        return "handler_execute"
    if code == "PERMISSION_DENIED":
        return "handler_execute"
    return "envelope_build"


def _suggested_fix(stage: str, code: str) -> str:
    if not code:
        return "none"
    if code == "PERMISSION_DENIED":
        return "v2.permission_policy and compare context enrichment"
    if stage == "registry_lookup":
        return "v2.intent registry closure"
    if stage == "schema_validate":
        return "v2 request schema / payload normalization"
    if stage == "handler_execute":
        return "v2 handler/service/builder execution chain"
    return "v2 envelope and dispatcher response build"


def run_audit() -> Dict[str, object]:
    errors: List[str] = []
    if not SNAPSHOT.exists():
        return {"gate_version": "v1", "gate_profile": "full", "status": "FAIL", "errors": ["missing_failure_snapshot"]}

    snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    required = list(snap.get("required_failure_fields") or [])

    sys.path.insert(0, str(ROOT / "addons" / "smart_core"))
    from core.intent_route_mode_policy import resolve_intent_route_mode  # type: ignore
    from core.intent_shadow_compare_executor import run_shadow_compare  # type: ignore
    from v2.dispatcher import dispatch_intent  # type: ignore

    intent = "ui.contract"
    route_mode = str(resolve_intent_route_mode(intent).get("mode") or "legacy_only")
    payload = {"model": "res.partner", "view_type": "form"}
    context = {"trace_id": "diag-ui-contract-1675", "user_id": 1, "company_id": 1}

    v2_result = dispatch_intent(intent=intent, payload=payload, context=context)
    error_code, error_message = _extract_error(v2_result)
    failure_stage = _stage_from_error(error_code)

    compare = run_shadow_compare(
        intent=intent,
        route_mode=route_mode,
        params=payload,
        context=context,
        v1_result={"ok": True, "data": {"view": {}}, "meta": {"intent": intent}},
        v2_runner=lambda i, p, c: dispatch_intent(intent=i, payload=p, context=c),
    )

    diagnosis = {
        "intent": intent,
        "route_mode": route_mode,
        "v1_status": str(compare.get("v1_status") or "unknown"),
        "v2_status": str(compare.get("v2_status") or "unknown"),
        "failure_stage": failure_stage,
        "error_code": error_code,
        "error_message": error_message,
        "minimal_repro_payload": {"intent": intent, "payload": payload, "context": context},
        "suggested_fix_area": _suggested_fix(failure_stage, error_code),
        "diff_summary": compare.get("diff_summary") if isinstance(compare.get("diff_summary"), list) else [],
    }

    for key in required:
        if key not in diagnosis:
            errors.append(f"missing_failure_field:{key}")

    return {
        "gate_version": "v1",
        "gate_profile": "full",
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "diagnosis": diagnosis,
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
