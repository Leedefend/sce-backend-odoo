#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _delegate_command() -> list[str]:
    override = os.environ.get("V2_APP_VERIFY_ALL_DELEGATE_CMD", "").strip()
    if override:
        return shlex.split(override)
    return ["python3", "scripts/verify/v2_app_governance_gate_audit.py", "--json"]


def run() -> dict:
    delegate_cmd = _delegate_command()
    proc = subprocess.run(
        delegate_cmd,
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    payload = {}
    try:
        payload = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        payload = {"status": "FAIL", "stdout": proc.stdout.strip(), "stderr": proc.stderr.strip()}
    status = "PASS" if proc.returncode == 0 and payload.get("status") == "PASS" else "FAIL"
    errors = []
    if status != "PASS":
        failure_reasons = payload.get("failure_reasons") if isinstance(payload, dict) else []
        if isinstance(failure_reasons, list) and failure_reasons:
            errors = [str(item) for item in failure_reasons if str(item).strip()]
        if not errors:
            errors = ["delegate_failed:" + " ".join(delegate_cmd)]
    return {
        "gate_version": payload.get("gate_version") if isinstance(payload, dict) else "",
        "gate_profile": "ci_light",
        "status": status,
        "errors": errors,
        "delegate": " ".join(delegate_cmd),
        "summary": payload.get("summary") if isinstance(payload, dict) else {},
        "failure_reasons": payload.get("failure_reasons") if isinstance(payload, dict) else [],
        "payload": payload,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = run()
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"status={result['status']}")
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
