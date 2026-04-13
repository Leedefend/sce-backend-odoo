#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT = ROOT / "artifacts" / "v2" / "meta_describe_model_contract_snapshot_v1.json"


def _missing_keys(data: Dict[str, Any], required: List[str]) -> List[str]:
    return [key for key in required if key not in data]


def run_audit() -> Dict[str, object]:
    errors: List[str] = []

    if not SNAPSHOT.exists():
        return {
            "gate_version": "v1",
            "gate_profile": "full",
            "status": "FAIL",
            "errors": ["missing snapshot file"],
        }

    snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    if snapshot.get("snapshot_id") != "meta_describe_model_contract_snapshot_v1":
        errors.append("invalid_snapshot_id")

    sys.path.insert(0, str(ROOT / "addons" / "smart_core"))
    from v2.dispatcher import dispatch_intent  # type: ignore

    success = dispatch_intent(
        intent="meta.describe_model",
        payload={"model": "res.partner"},
        context={"user_id": 17, "company_id": 5, "trace_id": "meta-contract-1628-pass"},
    )

    missing_root = _missing_keys(success, snapshot.get("required_envelope_fields") or [])
    if missing_root:
        errors.append(f"missing_root_fields:{','.join(missing_root)}")

    meta = success.get("meta") if isinstance(success.get("meta"), dict) else {}
    missing_meta = _missing_keys(meta, snapshot.get("required_meta_fields") or [])
    if missing_meta:
        errors.append(f"missing_meta_fields:{','.join(missing_meta)}")

    data = success.get("data") if isinstance(success.get("data"), dict) else {}
    missing_data = _missing_keys(data, snapshot.get("required_data_fields") or [])
    if missing_data:
        errors.append(f"missing_data_fields:{','.join(missing_data)}")

    if success.get("ok") is not True:
        errors.append("success_ok_not_true")
    if str(meta.get("intent") or "") != "meta.describe_model":
        errors.append("meta_intent_mismatch")
    if str(data.get("phase") or "") != str(snapshot.get("expected_phase") or ""):
        errors.append("phase_mismatch")

    failure = dispatch_intent(
        intent="meta.describe_model",
        payload={"model": ""},
        context={"user_id": 17, "company_id": 5, "trace_id": "meta-contract-1628-fail"},
    )
    if failure.get("ok") is not False:
        errors.append("failure_ok_not_false")
    err = failure.get("error") if isinstance(failure.get("error"), dict) else {}
    for key in ["code", "message"]:
        if key not in err:
            errors.append(f"missing_failure_error_{key}")

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
