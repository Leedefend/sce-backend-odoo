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
    from v2.builders.meta_describe_model_response_builder import MetaDescribeModelResponseBuilderV2  # type: ignore
    from v2.contracts.results import MetaDescribeModelResultV2  # type: ignore
    from v2.dispatcher import dispatch_intent  # type: ignore
    from v2.handlers.meta.describe_model import MetaDescribeModelHandlerV2  # type: ignore
    from v2.services.meta_describe_model_service import MetaDescribeModelServiceV2  # type: ignore

    handler = MetaDescribeModelHandlerV2()
    if not isinstance(getattr(handler, "_service", None), MetaDescribeModelServiceV2):
        errors.append("handler_missing_service_dependency")
    if not isinstance(getattr(handler, "_builder", None), MetaDescribeModelResponseBuilderV2):
        errors.append("handler_missing_builder_dependency")

    service = MetaDescribeModelServiceV2()
    result_object = service.describe(
        payload={"model": "res.partner", "schema_validated": True},
        context={"trace_id": "meta-boundary-1627", "user_id": 9, "company_id": 3},
    )
    if not isinstance(result_object, MetaDescribeModelResultV2):
        errors.append("service_not_return_result_object")

    builder = MetaDescribeModelResponseBuilderV2()
    contract = builder.build(result_object)
    for key in [
        "intent",
        "model",
        "display_name",
        "fields",
        "capabilities",
        "source",
        "version",
        "schema_validated",
        "phase",
    ]:
        if key not in contract:
            errors.append(f"builder_missing_key:{key}")

    dispatch_result = dispatch_intent(
        intent="meta.describe_model",
        payload={"model": "res.partner"},
        context={"user_id": 11, "company_id": 4, "trace_id": "meta-boundary-dispatch-1627"},
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
