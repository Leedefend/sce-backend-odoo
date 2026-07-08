#!/usr/bin/env python3
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "addons/smart_construction_custom"
ASSET = MODULE / "data/lowcode_customer_config_contracts_v1.json"
HOOKS = MODULE / "hooks.py"
USER_PREFERENCES = MODULE / "models/user_preferences.py"

SCHEMA_VERSION = "lowcode_customer_config_contracts.v1"
SOURCE_DRAFT_SCHEMA = "lowcode_customer_config_module_asset_draft.v1"
TARGET_MODULE = "smart_construction_custom"
ALLOWED_SOURCE_STATUSES = {"tenant_runtime"}


def _parse_python(path: Path):
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _function_by_name(tree: ast.AST, name: str):
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return node
    return None


def _call_names(function) -> list[str]:
    if function is None:
        return []
    names: list[str] = []
    for node in ast.walk(function):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Attribute):
            names.append(node.func.attr)
        elif isinstance(node.func, ast.Name):
            names.append(node.func.id)
    return names


def verify_asset() -> list[str]:
    failures: list[str] = []
    if not ASSET.exists():
        return ["accepted low-code customer module asset file is missing"]
    payload = json.loads(ASSET.read_text(encoding="utf-8"))
    if payload.get("schema_version") != SCHEMA_VERSION:
        failures.append("accepted low-code customer module asset schema_version mismatch")
    if payload.get("source_draft_schema") != SOURCE_DRAFT_SCHEMA:
        failures.append("accepted low-code customer module asset must declare its review draft source schema")
    if payload.get("target_module") != TARGET_MODULE:
        failures.append("accepted low-code customer module asset target_module mismatch")
    if payload.get("artifact_status") != "accepted_module_asset":
        failures.append("accepted low-code customer module asset artifact_status mismatch")
    records = payload.get("accepted_contracts")
    if not isinstance(records, list):
        failures.append("accepted low-code customer module asset accepted_contracts must be a list")
        return failures
    keys: set[str] = set()
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            failures.append(f"accepted contract #{index} must be an object")
            continue
        key = str(record.get("contract_key") or record.get("name") or "").strip()
        if not key:
            failures.append(f"accepted contract #{index} must declare contract_key or name")
        elif key in keys:
            failures.append(f"accepted contract key duplicated: {key}")
        keys.add(key)
        if str(record.get("source_status") or "").strip() not in ALLOWED_SOURCE_STATUSES:
            failures.append(f"accepted contract {key or index} must keep tenant_runtime source_status")
        if not isinstance(record.get("contract_json"), dict):
            failures.append(f"accepted contract {key or index} must carry contract_json")
    return failures


def verify_replay_binding() -> list[str]:
    failures: list[str] = []
    hooks_tree = _parse_python(HOOKS)
    apply_user_preferences = _function_by_name(hooks_tree, "apply_user_preferences")
    calls = _call_names(apply_user_preferences)
    if "apply_user_menu_preferences" not in calls:
        failures.append("hooks.apply_user_preferences must replay user menu preferences")
    if "apply_user_form_preferences" not in calls:
        failures.append("hooks.apply_user_preferences must replay user form preferences")
    if "apply_customer_lowcode_contract_assets" not in calls:
        failures.append("hooks.apply_user_preferences must replay accepted customer low-code contract assets")
    if "backfill_lowcode_contract_source_status" not in calls:
        failures.append("hooks.apply_user_preferences must backfill low-code contract source_status after replay")
    if all(name in calls for name in ("apply_user_form_preferences", "apply_customer_lowcode_contract_assets")):
        if calls.index("apply_customer_lowcode_contract_assets") < calls.index("apply_user_form_preferences"):
            failures.append("accepted customer low-code contract assets must replay after default form preferences")

    user_pref_text = USER_PREFERENCES.read_text(encoding="utf-8")
    for token in (
        "CUSTOMER_LOWCODE_CONTRACT_ASSET_SOURCE",
        "CUSTOMER_LOWCODE_CONTRACT_ASSET_PATH",
        "def apply_customer_lowcode_contract_assets",
        "def _load_customer_lowcode_contract_asset",
        "def _upsert_customer_lowcode_contract_asset_record",
        "def _stamp_customer_lowcode_contract_asset_source",
        "lowcode_customer_config_contracts.v1",
        "smart_construction_custom.lowcode_customer_config_contracts",
        "ensure_lowcode_contract_source_status",
        "action_publish",
    ):
        if token not in user_pref_text:
            failures.append(f"customer low-code contract asset replay binding missing {token}")
    return failures


def main() -> int:
    failures = verify_asset() + verify_replay_binding()
    if failures:
        print("[lowcode_customer_config_module_asset_replay_guard] FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("[lowcode_customer_config_module_asset_replay_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
