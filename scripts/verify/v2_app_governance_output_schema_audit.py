#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT = ROOT / "artifacts" / "v2" / "v2_app_governance_output_schema_v1.json"


def _missing_keys(obj: Dict[str, Any], keys: List[str]) -> List[str]:
    return [key for key in keys if key not in obj]


def run_audit() -> Dict[str, Any]:
    errors: List[str] = []

    if not SNAPSHOT.exists():
        return {
            "gate_version": "v1",
            "gate_profile": "full",
            "status": "FAIL",
            "errors": ["missing snapshot file"],
        }

    snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    if snapshot.get("snapshot_id") != "v2_app_governance_output_schema_v1":
        errors.append("invalid snapshot_id")

    proc = subprocess.run(
        ["python3", "scripts/verify/v2_app_governance_gate_audit.py", "--json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        errors.append("governance gate command failed")
    try:
        result = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        result = {}
        errors.append("invalid governance gate json output")

    required_root = snapshot.get("required_root_fields") if isinstance(snapshot.get("required_root_fields"), list) else []
    required_summary = snapshot.get("required_summary_fields") if isinstance(snapshot.get("required_summary_fields"), list) else []
    required_detail = snapshot.get("required_detail_fields") if isinstance(snapshot.get("required_detail_fields"), list) else []
    expected_checks = snapshot.get("expected_checks") if isinstance(snapshot.get("expected_checks"), list) else []
    status_enum = snapshot.get("status_enum") if isinstance(snapshot.get("status_enum"), list) else []
    gate_profile_enum = snapshot.get("gate_profile_enum") if isinstance(snapshot.get("gate_profile_enum"), list) else []

    missing_root = _missing_keys(result if isinstance(result, dict) else {}, required_root)
    if missing_root:
        errors.append("missing root fields: " + ",".join(missing_root))

    summary = result.get("summary") if isinstance(result, dict) and isinstance(result.get("summary"), dict) else {}
    missing_summary = _missing_keys(summary, required_summary)
    if missing_summary:
        errors.append("missing summary fields: " + ",".join(missing_summary))

    if isinstance(result, dict) and result.get("status") not in status_enum:
        errors.append("status not in enum")
    if isinstance(result, dict) and result.get("gate_profile") not in gate_profile_enum:
        errors.append("gate_profile not in enum")

    details = result.get("details") if isinstance(result, dict) and isinstance(result.get("details"), list) else []
    if not details:
        errors.append("details is empty")
    else:
        actual_checks: List[str] = []
        for idx, detail in enumerate(details):
            if not isinstance(detail, dict):
                errors.append(f"detail[{idx}] is not object")
                continue
            missing_detail = _missing_keys(detail, required_detail)
            if missing_detail:
                errors.append(f"detail[{idx}] missing fields: {','.join(missing_detail)}")
            check_name = detail.get("check")
            if isinstance(check_name, str) and check_name.strip():
                actual_checks.append(check_name)

        if expected_checks:
            missing_checks = sorted(set(expected_checks) - set(actual_checks))
            extra_checks = sorted(set(actual_checks) - set(expected_checks))
            if missing_checks:
                errors.append("missing expected checks: " + ",".join(missing_checks))
            if extra_checks:
                errors.append("unexpected checks: " + ",".join(extra_checks))

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
