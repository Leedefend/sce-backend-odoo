#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List


ROOT = Path(__file__).resolve().parents[2]


def run_audit() -> Dict[str, object]:
    errors: List[str] = []

    sys.path.insert(0, str(ROOT / "addons" / "smart_core"))
    from core.intent_shadow_compare_executor import run_shadow_compare  # type: ignore

    # Case 1: same shape and same reason code
    sample_ok = run_shadow_compare(
        intent="session.bootstrap",
        route_mode="v2_shadow",
        params={"a": 1},
        context={"trace_id": "shadow-compare-1673-1"},
        v1_result={"ok": True, "data": {"x": 1}, "meta": {"intent": "session.bootstrap"}, "error": None},
        v2_runner=lambda _i, _p, _c: {"ok": True, "data": {"x": 2}, "meta": {"intent": "session.bootstrap"}, "error": None},
    )
    if sample_ok.get("same_shape") is not True:
        errors.append("same_shape_expected_true")
    if sample_ok.get("same_reason_code") is not True:
        errors.append("same_reason_code_expected_true")

    # Case 2: error code mismatch
    sample_diff = run_shadow_compare(
        intent="ui.contract",
        route_mode="v2_shadow",
        params={"m": "res.partner"},
        context={"trace_id": "shadow-compare-1673-2"},
        v1_result={"ok": False, "error": {"code": "A", "message": "err"}},
        v2_runner=lambda _i, _p, _c: {"ok": False, "error": {"code": "B", "message": "err"}},
    )
    if sample_diff.get("same_reason_code") is not False:
        errors.append("same_reason_code_expected_false")
    diff_summary = sample_diff.get("diff_summary") if isinstance(sample_diff.get("diff_summary"), list) else []
    if "error_code_mismatch" not in diff_summary:
        errors.append("missing_error_code_mismatch")

    # Case 3: v2 runner exception should be tolerated
    sample_exception = run_shadow_compare(
        intent="meta.describe_model",
        route_mode="v2_shadow",
        params={"model": "res.partner"},
        context={"trace_id": "shadow-compare-1673-3"},
        v1_result={"ok": True, "data": {}},
        v2_runner=lambda _i, _p, _c: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    if str(sample_exception.get("v2_status") or "") != "error":
        errors.append("v2_exception_not_captured")

    return {
        "gate_version": "v1",
        "gate_profile": "full",
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "samples": {
            "same_shape": sample_ok,
            "reason_code_diff": sample_diff,
            "exception_capture": sample_exception,
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
