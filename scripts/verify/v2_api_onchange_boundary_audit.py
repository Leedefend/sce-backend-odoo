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
    from v2.builders.api_onchange_response_builder import ApiOnchangeResponseBuilderV2  # type: ignore
    from v2.contracts.results import ApiOnchangeResultV2  # type: ignore
    from v2.dispatcher import dispatch_intent  # type: ignore
    from v2.handlers.api.onchange import ApiOnchangeHandlerV2  # type: ignore
    from v2.services.api_onchange_service import ApiOnchangeServiceV2  # type: ignore

    handler = ApiOnchangeHandlerV2()
    if not isinstance(getattr(handler, "_service", None), ApiOnchangeServiceV2):
        errors.append("handler_missing_service_dependency")
    if not isinstance(getattr(handler, "_builder", None), ApiOnchangeResponseBuilderV2):
        errors.append("handler_missing_builder_dependency")

    service = ApiOnchangeServiceV2()
    result_object = service.execute_stub(
        payload={"model": "res.partner", "field_name": "name", "schema_validated": True},
        context={"trace_id": "api-onchange-boundary-1644", "user_id": 9, "company_id": 3},
    )
    if not isinstance(result_object, ApiOnchangeResultV2):
        errors.append("service_not_return_result_object")

    builder = ApiOnchangeResponseBuilderV2()
    contract = builder.build(result_object)
    for key in ["intent", "model", "field_name", "schema_validated", "trace_id", "status", "version", "phase"]:
        if key not in contract:
            errors.append(f"builder_missing_key:{key}")

    dispatch_result = dispatch_intent(
        intent="api.onchange",
        payload={"model": "res.partner", "field_name": "name"},
        context={"user_id": 11, "company_id": 4, "trace_id": "api-onchange-boundary-dispatch-1644"},
    )
    data = dispatch_result.get("data") if isinstance(dispatch_result.get("data"), dict) else {}
    if str(data.get("phase") or "") != "boundary_closure":
        errors.append("dispatch_phase_not_boundary_closure")

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
