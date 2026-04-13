#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Dict, List


ROOT = Path(__file__).resolve().parents[2]
CHECKS = [
    ["python3", "scripts/verify/v2_app_reason_code_audit.py", "--json"],
    ["python3", "scripts/verify/v2_app_contract_guard_audit.py", "--json"],
    ["python3", "scripts/verify/v2_app_contract_snapshot_audit.py", "--json"],
    ["python3", "scripts/verify/v2_session_bootstrap_contract_audit.py", "--json"],
    ["python3", "scripts/verify/v2_meta_describe_model_contract_audit.py", "--json"],
    ["python3", "scripts/verify/v2_ui_contract_contract_audit.py", "--json"],
    ["python3", "scripts/verify/v2_first_scenario_contract_audit.py", "--json"],
    ["python3", "scripts/verify/v2_execute_button_contract_audit.py", "--json"],
    ["python3", "scripts/verify/v2_api_data_contract_audit.py", "--json"],
    ["python3", "scripts/verify/v2_api_onchange_contract_audit.py", "--json"],
    ["python3", "scripts/verify/v2_api_data_batch_contract_audit.py", "--json"],
    ["python3", "scripts/verify/v2_api_data_create_contract_audit.py", "--json"],
    ["python3", "scripts/verify/v2_api_data_unlink_contract_audit.py", "--json"],
    ["python3", "scripts/verify/v2_file_upload_contract_audit.py", "--json"],
    ["python3", "scripts/verify/v2_file_download_contract_audit.py", "--json"],
    ["python3", "scripts/verify/v2_load_contract_contract_audit.py", "--json"],
    ["python3", "scripts/verify/v2_intent_migration_freeze_audit.py", "--json"],
    ["python3", "scripts/verify/v2_app_intent_contract_linkage_audit.py", "--json"],
    ["python3", "scripts/verify/v2_app_ci_light_entry_audit.py", "--json"],
    ["python3", "scripts/verify/v2_boundary_audit.py", "--json"],
    ["python3", "scripts/verify/v2_rebuild_audit.py", "--json"],
    ["python3", "scripts/verify/v2_intent_comparison_audit.py", "--json"],
    ["python3", "scripts/verify/v2_focus_intent_promotion_state_machine_audit.py", "--json"],
    ["python3", "scripts/verify/v2_primary_minimum_business_smoke.py", "--json"],
    ["python3", "scripts/verify/v2_focus_intent_diff_audit.py", "--json"],
    ["python3", "scripts/verify/v2_rollback_readiness_recheck.py", "--json"],
    ["python3", "scripts/verify/v2_app_verify_all_failure_path_audit.py", "--json"],
]

NON_BLOCKING_DIAG_CHECKS = [
    ["python3", "scripts/verify/v2_focus_intent_compare_failure_summary.py", "--json"],
]


def _extract_failure_reasons(payload: Dict[str, object]) -> List[str]:
    reasons: List[str] = []
    for key in [
        "errors",
        "missing_tokens",
        "missing_files",
        "missing_builder_tokens",
        "missing_service_tokens",
        "missing_reason_tokens",
        "failed_checks",
    ]:
        value = payload.get(key)
        if isinstance(value, list):
            for item in value:
                text = str(item).strip()
                if text:
                    reasons.append(text)
    if not reasons and payload.get("status") != "PASS":
        reasons.append("check_failed_without_reason")
    return reasons


def run_audit() -> Dict[str, object]:
    details: List[Dict[str, object]] = []
    failed: List[str] = []
    failure_reasons: List[str] = []

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

        if status == "FAIL":
            for reason in _extract_failure_reasons(payload):
                failure_reasons.append(f"{name}:{reason}")

        details.append({"check": name, "status": status, "payload": payload})

    total_checks = len(CHECKS)
    fail_checks = len(failed)
    pass_checks = total_checks - fail_checks
    summary = {
        "total_checks": total_checks,
        "pass_checks": pass_checks,
        "fail_checks": fail_checks,
    }

    non_blocking_diagnostics: List[Dict[str, object]] = []
    for cmd in NON_BLOCKING_DIAG_CHECKS:
        name = Path(cmd[1]).name
        proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        payload: Dict[str, object] = {}
        status = "PASS"
        if proc.returncode != 0:
            status = "FAIL"
            payload = {"stdout": proc.stdout.strip(), "stderr": proc.stderr.strip(), "errors": ["diag_command_failed"]}
        else:
            try:
                payload = json.loads(proc.stdout or "{}")
            except json.JSONDecodeError:
                status = "FAIL"
                payload = {"stdout": proc.stdout.strip(), "stderr": proc.stderr.strip(), "errors": ["diag_invalid_json"]}
        non_blocking_diagnostics.append({"check": name, "status": status, "payload": payload})

    return {
        "gate_version": "v1",
        "gate_profile": "full",
        "status": "PASS" if not failed else "FAIL",
        "summary": summary,
        "failed_checks": failed,
        "failure_reasons": failure_reasons,
        "non_blocking_diagnostics": non_blocking_diagnostics,
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
