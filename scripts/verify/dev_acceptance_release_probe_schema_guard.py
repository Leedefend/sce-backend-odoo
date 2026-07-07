#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
REPORT_JSON = ROOT / os.getenv(
    "ACCEPTANCE_PROBE_OUTPUT",
    "artifacts/backend/dev_acceptance_release_probe.json",
)


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _string_list(value: object) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def _nav_action_mismatch_list(value: object) -> bool:
    if not isinstance(value, list):
        return False
    for item in value:
        if not isinstance(item, dict):
            return False
        if not isinstance(item.get("path"), str) or not item.get("path"):
            return False
        if not isinstance(item.get("expected_action_id"), int):
            return False
        actual = item.get("actual_action_id")
        if actual is not None and not isinstance(actual, int):
            return False
    return True


def _check_status_block(prefix: str, value: object, errors: list[str]) -> dict:
    if not isinstance(value, dict):
        errors.append(f"{prefix} must be object")
        return {}
    status = value.get("status")
    enabled = value.get("enabled")
    if enabled is not False and status not in {"PASS", "FAIL"}:
        errors.append(f"{prefix}.status must be PASS or FAIL when enabled")
    block_errors = value.get("errors")
    if block_errors is not None and not _string_list(block_errors):
        errors.append(f"{prefix}.errors must be string list")
        block_errors = []
    if status == "PASS" and block_errors:
        errors.append(f"{prefix}.status=PASS must not contain errors")
    if status == "FAIL" and not block_errors:
        errors.append(f"{prefix}.status=FAIL must contain errors")
    return value


def _check_backup(value: object, errors: list[str]) -> str:
    backup = _check_status_block("backup", value, errors)
    if not backup:
        return "FAIL"
    enabled = backup.get("enabled")
    if not isinstance(enabled, bool):
        errors.append("backup.enabled must be bool")
    if enabled is False:
        return "PASS"
    if not isinstance(backup.get("dir"), str) or not backup.get("dir"):
        errors.append("backup.dir must be non-empty string when enabled")
    if not isinstance(backup.get("checks"), dict):
        errors.append("backup.checks must be object when enabled")
    return str(backup.get("status") or "FAIL")


def _check_frontend(value: object, errors: list[str]) -> str:
    frontend = _check_status_block("frontend", value, errors)
    if not frontend:
        return "FAIL"
    if not isinstance(frontend.get("base_url"), str) or not frontend.get("base_url"):
        errors.append("frontend.base_url must be non-empty string")
    checks = frontend.get("checks")
    if not isinstance(checks, dict):
        errors.append("frontend.checks must be object")
        return str(frontend.get("status") or "FAIL")
    for key in ("root_status", "asset_status", "intent_options_status", "intent_get_status"):
        if key in checks and not isinstance(checks.get(key), int):
            errors.append(f"frontend.checks.{key} must be int")
    for key in (
        "asset_has_db",
        "asset_has_app_env",
        "asset_has_forbidden_db_token",
        "asset_forbidden_db_is_default",
    ):
        if key in checks and not isinstance(checks.get(key), bool):
            errors.append(f"frontend.checks.{key} must be bool")
    asset_path = checks.get("asset_path")
    if frontend.get("status") == "PASS" and (not isinstance(asset_path, str) or not asset_path):
        errors.append("frontend.checks.asset_path must be non-empty string when frontend passes")
    if frontend.get("status") == "PASS":
        expected = {
            "root_status": 200,
            "asset_status": 200,
            "intent_options_status": 204,
            "intent_get_status": 405,
        }
        for key, expected_value in expected.items():
            if checks.get(key) != expected_value:
                errors.append(f"frontend.checks.{key} must be {expected_value} when frontend passes")
    return str(frontend.get("status") or "FAIL")


def _check_login(value: object, errors: list[str]) -> str:
    login = _check_status_block("login", value, errors)
    if not login:
        return "FAIL"
    enabled = login.get("enabled")
    if not isinstance(enabled, bool):
        errors.append("login.enabled must be bool")
    if enabled is False:
        return "PASS"
    if not isinstance(login.get("login"), str) or not login.get("login"):
        errors.append("login.login must be non-empty string when enabled")
    checks = login.get("checks")
    if not isinstance(checks, dict):
        errors.append("login.checks must be object when enabled")
        return str(login.get("status") or "FAIL")
    for key in ("auth_status", "system_init_status"):
        if not isinstance(checks.get(key), int):
            errors.append(f"login.checks.{key} must be int")
    if not isinstance(checks.get("system_init_ok"), bool):
        errors.append("login.checks.system_init_ok must be bool")
    if checks.get("auth_uid") is not None and not isinstance(checks.get("auth_uid"), int):
        errors.append("login.checks.auth_uid must be int when present")
    for key in ("nav_count", "nav_node_count", "nav_action_count", "nav_leaf_count"):
        if checks.get(key) is not None and not isinstance(checks.get(key), int):
            errors.append(f"login.checks.{key} must be int when present")
    if checks.get("role_code") is not None and not isinstance(checks.get("role_code"), str):
        errors.append("login.checks.role_code must be string when present")
    for key in ("nav_forbidden_label_hits", "nav_required_path_misses"):
        if checks.get(key) is not None and not _string_list(checks.get(key)):
            errors.append(f"login.checks.{key} must be string list when present")
    if checks.get("nav_required_action_mismatches") is not None and not _nav_action_mismatch_list(
        checks.get("nav_required_action_mismatches")
    ):
        errors.append("login.checks.nav_required_action_mismatches must be action mismatch list when present")
    if checks.get("nav_paths_sample") is not None and not _string_list(checks.get("nav_paths_sample")):
        errors.append("login.checks.nav_paths_sample must be string list when present")
    if login.get("status") == "PASS":
        if checks.get("auth_status") != 200:
            errors.append("login.checks.auth_status must be 200 when login passes")
        if checks.get("system_init_status") != 200:
            errors.append("login.checks.system_init_status must be 200 when login passes")
        if checks.get("system_init_ok") is not True:
            errors.append("login.checks.system_init_ok must be true when login passes")
        if not checks.get("role_code"):
            errors.append("login.checks.role_code must be non-empty when login passes")
        if not isinstance(checks.get("nav_node_count"), int) or checks.get("nav_node_count") <= 0:
            errors.append("login.checks.nav_node_count must be positive when login passes")
        if not isinstance(checks.get("nav_action_count"), int) or checks.get("nav_action_count") <= 0:
            errors.append("login.checks.nav_action_count must be positive when login passes")
        if checks.get("nav_forbidden_label_hits"):
            errors.append("login.checks.nav_forbidden_label_hits must be empty when login passes")
        if checks.get("nav_required_path_misses"):
            errors.append("login.checks.nav_required_path_misses must be empty when login passes")
        if checks.get("nav_required_action_mismatches"):
            errors.append("login.checks.nav_required_action_mismatches must be empty when login passes")
    return str(login.get("status") or "FAIL")


def main() -> int:
    payload = _load_json(REPORT_JSON)
    errors: list[str] = []
    if not payload:
        errors.append(f"missing or invalid json: {REPORT_JSON.relative_to(ROOT).as_posix()}")
    else:
        if payload.get("mode") != "dev_acceptance_release_probe":
            errors.append("mode must be dev_acceptance_release_probe")
        if payload.get("status") not in {"PASS", "FAIL"}:
            errors.append("status must be PASS or FAIL")
        for key in ("db_name", "base_url", "app_env"):
            if not isinstance(payload.get(key), str) or not payload.get(key):
                errors.append(f"{key} must be non-empty string")
        statuses = [
            _check_backup(payload.get("backup"), errors),
            _check_frontend(payload.get("frontend"), errors),
            _check_login(payload.get("login"), errors),
        ]
        expected_status = "PASS" if all(status == "PASS" for status in statuses) else "FAIL"
        if payload.get("status") in {"PASS", "FAIL"} and payload.get("status") != expected_status:
            errors.append("status must match backup/frontend/login aggregate status")

    if errors:
        print("[dev_acceptance_release_probe_schema_guard] FAIL")
        for error in errors:
            print(error)
        return 2
    print("[dev_acceptance_release_probe_schema_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
