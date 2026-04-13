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
    from v2.builders.file_upload_response_builder import FileUploadResponseBuilderV2  # type: ignore
    from v2.contracts.results import FileUploadResultV2  # type: ignore
    from v2.dispatcher import dispatch_intent  # type: ignore
    from v2.handlers.api.file_upload import FileUploadHandlerV2  # type: ignore
    from v2.services.file_upload_service import FileUploadServiceV2  # type: ignore

    handler = FileUploadHandlerV2()
    if not isinstance(getattr(handler, "_service", None), FileUploadServiceV2):
        errors.append("handler_missing_service_dependency")
    if not isinstance(getattr(handler, "_builder", None), FileUploadResponseBuilderV2):
        errors.append("handler_missing_builder_dependency")

    service = FileUploadServiceV2()
    result_object = service.execute_stub(
        payload={"model": "res.partner", "res_id": 1, "name": "demo.txt", "schema_validated": True},
        context={"trace_id": "file-upload-boundary-1660", "user_id": 9, "company_id": 3},
    )
    if not isinstance(result_object, FileUploadResultV2):
        errors.append("service_not_return_result_object")

    builder = FileUploadResponseBuilderV2()
    contract = builder.build(result_object)
    for key in ["intent", "model", "res_id", "name", "schema_validated", "trace_id", "status", "version", "phase"]:
        if key not in contract:
            errors.append(f"builder_missing_key:{key}")

    dispatch_result = dispatch_intent(
        intent="file.upload",
        payload={"model": "res.partner", "res_id": 1, "name": "demo.txt", "data": "dGVzdA=="},
        context={"user_id": 11, "company_id": 4, "trace_id": "file-upload-boundary-dispatch-1660"},
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
