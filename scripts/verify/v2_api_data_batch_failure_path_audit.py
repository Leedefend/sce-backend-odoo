#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List


ROOT = Path(__file__).resolve().parents[2]


def _assert_failure_shape(result: Dict[str, object], errors: List[str], label: str) -> None:
    if result.get("ok") is not False:
        errors.append(f"{label}:expected_ok_false")
    error = result.get("error") if isinstance(result.get("error"), dict) else {}
    meta = result.get("meta") if isinstance(result.get("meta"), dict) else {}
    for key in ["code", "message"]:
        if key not in error:
            errors.append(f"{label}:missing_error_{key}")
    if str(meta.get("intent") or "") != "api.data.batch":
        errors.append(f"{label}:missing_meta_intent")


def run_audit() -> Dict[str, object]:
    errors: List[str] = []

    sys.path.insert(0, str(ROOT / "addons" / "smart_core"))
    from v2.dispatcher import dispatch_intent  # type: ignore

    schema_fail = dispatch_intent(
        intent="api.data.batch",
        payload={"model": "", "operations": [{"op": "read"}]},
        context={"user_id": 7, "company_id": 2, "trace_id": "api-data-batch-fail-schema-1647"},
    )
    _assert_failure_shape(schema_fail, errors, "schema_fail")

    handler_fail = dispatch_intent(
        intent="api.data.batch",
        payload={"model": "res.partner", "operations": [{"op": "read"}], "raise_handler_error": True},
        context={"user_id": 7, "company_id": 2, "trace_id": "api-data-batch-fail-handler-1647"},
    )
    _assert_failure_shape(handler_fail, errors, "handler_fail")

    return {
        "gate_version": "v1",
        "gate_profile": "full",
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
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
