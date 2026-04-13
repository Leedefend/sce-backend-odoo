#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path
from typing import Dict, List


ROOT = Path(__file__).resolve().parents[2]


def run_audit() -> Dict[str, object]:
    env = os.environ.copy()
    env["V2_APP_VERIFY_ALL_DELEGATE_CMD"] = "python3 scripts/verify/nonexistent_delegate.py --json"

    proc = subprocess.run(
        ["python3", "scripts/verify/v2_app_verify_all.py", "--json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        env=env,
    )

    errors: List[str] = []
    payload: Dict[str, object] = {}
    try:
        payload = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        errors.append("invalid_json_output")

    status = payload.get("status") if isinstance(payload, dict) else None
    root_errors = payload.get("errors") if isinstance(payload, dict) else None
    delegate = payload.get("delegate") if isinstance(payload, dict) else None

    if status != "FAIL":
        errors.append("expected_status_fail")
    if not isinstance(root_errors, list) or not root_errors:
        errors.append("expected_non_empty_root_errors")
    if not isinstance(delegate, str) or "nonexistent_delegate.py" not in delegate:
        errors.append("delegate_override_not_effective")
    if proc.returncode == 0:
        errors.append("expected_non_zero_exit_code")

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

