#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from collections import Counter
from pathlib import Path
from typing import Dict, List


ROOT = Path(__file__).resolve().parents[2]
CHECKS = [
    ["python3", "scripts/verify/v2_session_bootstrap_compare_failure_diagnose.py", "--json"],
    ["python3", "scripts/verify/v2_meta_describe_model_compare_failure_diagnose.py", "--json"],
    ["python3", "scripts/verify/v2_ui_contract_compare_failure_diagnose.py", "--json"],
]


def run_audit() -> Dict[str, object]:
    details: List[Dict[str, object]] = []
    failed_commands: List[str] = []
    stages: Counter = Counter()
    status_counter: Counter = Counter()

    for cmd in CHECKS:
        name = Path(cmd[1]).name
        proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        if proc.returncode != 0:
            failed_commands.append(name)
            payload: Dict[str, object] = {"status": "FAIL", "errors": ["command_failed"], "stdout": proc.stdout, "stderr": proc.stderr}
        else:
            try:
                payload = json.loads(proc.stdout or "{}")
            except json.JSONDecodeError:
                failed_commands.append(name)
                payload = {"status": "FAIL", "errors": ["invalid_json"]}

        diagnosis = payload.get("diagnosis") if isinstance(payload.get("diagnosis"), dict) else {}
        stage = str(diagnosis.get("failure_stage") or "unknown")
        v2_status = str(diagnosis.get("v2_status") or "unknown")
        stages[stage] += 1
        status_counter[v2_status] += 1

        details.append({"check": name, "status": str(payload.get("status") or "FAIL"), "payload": payload})

    allow_v2_candidate = status_counter.get("error", 0) == 0 and status_counter.get("unknown", 0) == 0
    diagnosis_status = "READY_FOR_CANDIDATE" if allow_v2_candidate else "NEEDS_CORRECTION"

    # Non-blocking diagnosis chain: return PASS when summary is produced.
    errors: List[str] = []
    if failed_commands:
        errors.append(f"diagnose_commands_failed:{','.join(failed_commands)}")

    return {
        "gate_version": "v1",
        "gate_profile": "full",
        "status": "PASS",
        "errors": errors,
        "diagnosis_status": diagnosis_status,
        "allow_v2_candidate": allow_v2_candidate,
        "failure_stage_counts": dict(stages),
        "v2_status_counts": dict(status_counter),
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
        print(f"status={result['status']} diagnosis={result['diagnosis_status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
