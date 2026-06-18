#!/usr/bin/env python3
from __future__ import annotations

import ast
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "addons/smart_construction_custom"
MANIFEST = MODULE / "__manifest__.py"
HOOKS = MODULE / "hooks.py"
PARTNER_LOCATION = MODULE / "models/partner_location.py"
USER_DATA_BASELINE_XML = MODULE / "data/user_data_baseline.xml"
USER_PREFERENCES_XML = MODULE / "data/user_preferences.xml"


def _parse_python(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _function_by_name(tree: ast.AST, name: str) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return node
    return None


def _call_name(call: ast.Call) -> str:
    func = call.func
    if isinstance(func, ast.Attribute):
        return func.attr
    if isinstance(func, ast.Name):
        return func.id
    return ""


def _call_names(node: ast.AST | None) -> list[str]:
    if node is None:
        return []
    return [_call_name(call) for call in ast.walk(node) if isinstance(call, ast.Call)]


def _manifest_data_files() -> list[str]:
    manifest = ast.literal_eval(MANIFEST.read_text(encoding="utf-8"))
    return [str(item) for item in manifest.get("data", [])]


def _xml_function_names(path: Path) -> list[str]:
    root = ET.parse(path).getroot()
    return [
        str(node.attrib.get("name") or "").strip()
        for node in root.iter("function")
        if str(node.attrib.get("model") or "").strip() == "sc.user.preference.initialization"
    ]


def _index(items: list[str], item: str) -> int:
    try:
        return items.index(item)
    except ValueError:
        return -1


def verify_manifest_boundary() -> list[str]:
    failures: list[str] = []
    data_files = _manifest_data_files()
    baseline = "data/user_data_baseline.xml"
    preferences = "data/user_preferences.xml"
    menu_preferences = "data/user_menu_preferences.xml"

    for item in [baseline, preferences, menu_preferences]:
        if item not in data_files:
            failures.append(f"smart_construction_custom manifest must include {item}")

    baseline_index = _index(data_files, baseline)
    preference_index = _index(data_files, preferences)
    if baseline_index >= 0 and preference_index >= 0 and baseline_index > preference_index:
        failures.append("user data baseline must load before user preference contracts")

    return failures


def verify_xml_boundary() -> list[str]:
    failures: list[str] = []
    if not USER_DATA_BASELINE_XML.exists():
        failures.append("user data baseline XML must exist as an explicit P2 data carrier")
    elif _xml_function_names(USER_DATA_BASELINE_XML) != ["apply_user_data_baseline"]:
        failures.append("user data baseline XML may only call apply_user_data_baseline")

    if _xml_function_names(USER_PREFERENCES_XML) != ["apply_user_form_preferences"]:
        failures.append("user preference XML may only call apply_user_form_preferences")
    return failures


def verify_hook_boundary() -> list[str]:
    failures: list[str] = []
    tree = _parse_python(HOOKS)
    post_init = _function_by_name(tree, "post_init_hook")
    calls = _call_names(post_init)
    if "apply_user_data_baseline" not in calls:
        failures.append("post_init_hook must call apply_user_data_baseline explicitly")
    if "apply_user_preferences" not in calls:
        failures.append("post_init_hook must call apply_user_preferences explicitly")
    if "apply_user_data_baseline" in calls and "apply_user_preferences" in calls:
        if calls.index("apply_user_data_baseline") > calls.index("apply_user_preferences"):
            failures.append("post_init_hook must apply user data baseline before user preferences")

    apply_user_data = _function_by_name(tree, "apply_user_data_baseline")
    if apply_user_data is None:
        failures.append("hooks.py must expose apply_user_data_baseline")
    else:
        if "apply_user_data_baseline" not in _call_names(apply_user_data):
            failures.append("hooks.apply_user_data_baseline must delegate to sc.user.preference.initialization")
    return failures


def verify_partner_location_boundary() -> list[str]:
    failures: list[str] = []
    tree = _parse_python(PARTNER_LOCATION)
    apply_data = _function_by_name(tree, "apply_user_data_baseline")
    apply_location = _function_by_name(tree, "apply_partner_location_data_baseline")
    if apply_data is None:
        failures.append("partner location data must publish apply_user_data_baseline")
    elif "apply_partner_location_data_baseline" not in _call_names(apply_data):
        failures.append("apply_user_data_baseline must call apply_partner_location_data_baseline")

    if apply_location is None:
        failures.append("partner location data must publish apply_partner_location_data_baseline")
    else:
        calls = set(_call_names(apply_location))
        for required in ["_ensure_partner_city_data", "_backfill_partner_sc_city_ids"]:
            if required not in calls:
                failures.append(f"apply_partner_location_data_baseline must call {required}")

    apply_partner_form = _function_by_name(tree, "apply_partner_form_preferences")
    if apply_partner_form is not None:
        forbidden = {"_ensure_partner_city_data", "_backfill_partner_sc_city_ids"}
        found = sorted(forbidden.intersection(_call_names(apply_partner_form)))
        if found:
            failures.append(
                "apply_partner_form_preferences must not mutate user data baseline; "
                f"found calls {found}"
            )
    return failures


def main() -> int:
    failures = (
        verify_manifest_boundary()
        + verify_xml_boundary()
        + verify_hook_boundary()
        + verify_partner_location_boundary()
    )
    if failures:
        print("[user_module_product_boundary_guard] FAIL")
        for item in failures:
            print(f"- {item}")
        return 1
    print("[user_module_product_boundary_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
