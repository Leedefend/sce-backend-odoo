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
    from v2.dispatcher import dispatch_intent  # type: ignore

    result = dispatch_intent(
        intent="file.download",
        payload={"model": "res.partner", "res_id": 1, "name": "demo.txt"},
        context={"user_id": 7, "company_id": 2, "trace_id": "file-download-1663"},
    )

    if result.get("ok") is not True:
        errors.append("expected_ok_true")

    data = result.get("data") if isinstance(result.get("data"), dict) else {}
    meta = result.get("meta") if isinstance(result.get("meta"), dict) else {}

    if str(data.get("intent") or "") != "file.download":
        errors.append("intent_mismatch")
    if str(data.get("model") or "") != "res.partner":
        errors.append("model_mismatch")
    if int(data.get("res_id") or 0) != 1:
        errors.append("res_id_mismatch")
    if bool(data.get("schema_validated")) is not True:
        errors.append("schema_not_called")
    if str(data.get("status") or "") != "execution_closure":
        errors.append("status_mismatch")
    if str(data.get("phase") or "") != "boundary_closure":
        errors.append("phase_mismatch")

    for key in ["intent", "trace_id", "contract_version", "schema_version", "latency_ms"]:
        if key not in meta:
            errors.append(f"missing_meta:{key}")

    if str(meta.get("intent") or "") != "file.download":
        errors.append("meta_intent_mismatch")

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
