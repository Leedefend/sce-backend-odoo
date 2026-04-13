#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Dict, List


ROOT = Path(__file__).resolve().parents[2]
CHECKS = [
    ["python3", "scripts/verify/v2_session_bootstrap_compare_audit.py", "--json"],
    ["python3", "scripts/verify/v2_meta_describe_model_compare_audit.py", "--json"],
    ["python3", "scripts/verify/v2_ui_contract_compare_audit.py", "--json"],
]


def run_audit() -> Dict[str, object]:
    details: List[Dict[str, object]] = []
    failed: List[str] = []
    for cmd in CHECKS:
        proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        name = Path(cmd[1]).name
        status = "PASS"
        payload: Dict[str, object] = {}
        if proc.returncode != 0:
            status = "FAIL"
            failed.append(name)
        try:
            payload = json.loads(proc.stdout or "{}")
            if payload.get("status") != "PASS":
                status = "FAIL"
                if name not in failed:
                    failed.append(name)
        except json.JSONDecodeError:
            status = "FAIL"
            if name not in failed:
                failed.append(name)
            payload = {"stdout": proc.stdout.strip(), "stderr": proc.stderr.strip()}
        details.append({"check": name, "status": status, "payload": payload})

    return {
        "gate_version": "v1",
        "gate_profile": "full",
        "status": "PASS" if not failed else "FAIL",
        "summary": {"total_checks": len(CHECKS), "fail_checks": len(failed), "pass_checks": len(CHECKS) - len(failed)},
        "failed_checks": failed,
        "details": details,
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
