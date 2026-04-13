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
    from v2.builders.session_bootstrap_response_builder import SessionBootstrapResponseBuilderV2  # type: ignore
    from v2.contracts.results import SessionBootstrapResultV2  # type: ignore
    from v2.dispatcher import dispatch_intent  # type: ignore
    from v2.handlers.system.session_bootstrap import SessionBootstrapHandlerV2  # type: ignore
    from v2.services.session_bootstrap_service import SessionBootstrapServiceV2  # type: ignore

    handler = SessionBootstrapHandlerV2()
    if not isinstance(getattr(handler, "_service", None), SessionBootstrapServiceV2):
        errors.append("handler_missing_service_dependency")
    if not isinstance(getattr(handler, "_builder", None), SessionBootstrapResponseBuilderV2):
        errors.append("handler_missing_builder_dependency")

    service = SessionBootstrapServiceV2()
    result_object = service.bootstrap(
        payload={"app_key": "workspace", "schema_validated": True},
        context={"trace_id": "boundary-1623", "user_id": 9, "company_id": 3, "registry_snapshot": ("a", "b")},
    )
    if not isinstance(result_object, SessionBootstrapResultV2):
        errors.append("service_not_return_result_object")

    builder = SessionBootstrapResponseBuilderV2()
    contract = builder.build(result_object)
    for key in [
        "intent",
        "session_status",
        "bootstrap_ready",
        "schema_validated",
        "app_key",
        "user_id",
        "company_id",
        "trace_id",
        "registry_count",
        "phase",
        "version",
    ]:
        if key not in contract:
            errors.append(f"builder_missing_key:{key}")

    dispatch_result = dispatch_intent(
        intent="session.bootstrap",
        payload={"app_key": "workspace"},
        context={"user_id": 11, "company_id": 4, "trace_id": "boundary-dispatch-1623"},
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
