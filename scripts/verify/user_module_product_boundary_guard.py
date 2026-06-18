#!/usr/bin/env python3
from __future__ import annotations

import ast
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "addons/smart_construction_custom"
INDUSTRY_MODULES = [
    ROOT / "addons/smart_construction_core",
    ROOT / "addons/smart_construction_scene",
    ROOT / "addons/smart_construction_bootstrap",
]
MANIFEST = MODULE / "__manifest__.py"
HOOKS = MODULE / "hooks.py"
PARTNER_LOCATION = MODULE / "models/partner_location.py"
USER_DATA_BASELINE_PY = MODULE / "models/user_data_baseline.py"
MODELS_INIT = MODULE / "models/__init__.py"
USER_DATA_BASELINE_XML = MODULE / "data/user_data_baseline.xml"
LEGACY_USER_MASTER_XML = MODULE / "data/user_master_v1.xml"
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
    if "data/user_master_v1.xml" in data_files:
        failures.append("legacy user master payload must be loaded by the idempotent data baseline loader, not direct XML data")

    baseline_index = _index(data_files, baseline)
    preference_index = _index(data_files, preferences)
    if baseline_index >= 0 and preference_index >= 0 and baseline_index > preference_index:
        failures.append("user data baseline must load before user preference contracts")

    return failures


def verify_xml_boundary() -> list[str]:
    failures: list[str] = []
    if not USER_DATA_BASELINE_XML.exists():
        failures.append("user data baseline XML must exist as an explicit P2 data carrier")
    else:
        source = USER_DATA_BASELINE_XML.read_text(encoding="utf-8")
        if 'noupdate="1"' in source or "noupdate='1'" in source:
            failures.append("user data baseline XML must be upgrade-replayable; noupdate=1 is forbidden")
        if _xml_function_names(USER_DATA_BASELINE_XML) != ["apply_user_data_baseline"]:
            failures.append("user data baseline XML may only call apply_user_data_baseline")

    if _xml_function_names(USER_PREFERENCES_XML) != ["apply_user_form_preferences"]:
        failures.append("user preference XML may only call apply_user_form_preferences")
    if not LEGACY_USER_MASTER_XML.exists():
        failures.append("user module must carry the real legacy user master payload")
    else:
        root = ET.parse(LEGACY_USER_MASTER_XML).getroot()
        user_records = [
            node
            for node in root.iter("record")
            if str(node.attrib.get("model") or "").strip() == "res.users"
        ]
        if len(user_records) < 100:
            failures.append(f"legacy user master payload is too small: {len(user_records)} < 100")
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


def verify_user_data_baseline_boundary() -> list[str]:
    failures: list[str] = []
    if not USER_DATA_BASELINE_PY.exists():
        return ["user module must provide models/user_data_baseline.py"]

    tree = _parse_python(USER_DATA_BASELINE_PY)
    required_functions = {
        "apply_user_data_baseline",
        "apply_legacy_user_master_data_baseline",
        "apply_partner_business_data_baseline",
        "_find_existing_legacy_user",
        "_ensure_user_baseline_xmlid",
    }
    missing = sorted(name for name in required_functions if _function_by_name(tree, name) is None)
    if missing:
        failures.append(f"user data baseline missing required functions: {missing}")

    apply_data = _function_by_name(tree, "apply_user_data_baseline")
    calls = set(_call_names(apply_data))
    for required in ["apply_legacy_user_master_data_baseline", "apply_partner_business_data_baseline"]:
        if required not in calls:
            failures.append(f"apply_user_data_baseline must call {required}")

    source = USER_DATA_BASELINE_PY.read_text(encoding="utf-8")
    required_snippets = [
        '("smart_construction_custom", "migration_assets")',
        '("login", "=", login)',
        "no_reset_password=True",
        '"noupdate": True',
        "demote_no_fact=False",
    ]
    for snippet in required_snippets:
        if snippet not in source:
            failures.append(f"user data baseline must keep idempotent/non-destructive rule: {snippet}")
    if ".create(vals)" not in source or ".write(vals)" not in source:
        failures.append("legacy user baseline loader must update existing users and create only missing users")
    init_source = MODELS_INIT.read_text(encoding="utf-8")
    if "user_data_baseline" not in init_source:
        failures.append("models/__init__.py must import user_data_baseline")
    return failures


def verify_industry_modules_do_not_carry_user_data() -> list[str]:
    failures: list[str] = []
    forbidden_names = {"user_master_v1.xml"}
    forbidden_text = ("legacy_user_sc_",)
    for module_path in INDUSTRY_MODULES:
        if not module_path.exists():
            continue
        for path in module_path.rglob("*"):
            if not path.is_file():
                continue
            rel = path.relative_to(ROOT).as_posix()
            if path.name in forbidden_names:
                failures.append(f"P1 industry module must not carry P2 real-user payload file: {rel}")
                continue
            if path.suffix.lower() not in {".xml", ".csv", ".json", ".py", ".md"}:
                continue
            try:
                source = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            if any(token in source for token in forbidden_text):
                failures.append(f"P1 industry module must not carry P2 real-user payload token in {rel}")
    return failures


def main() -> int:
    failures = (
        verify_manifest_boundary()
        + verify_xml_boundary()
        + verify_hook_boundary()
        + verify_partner_location_boundary()
        + verify_user_data_baseline_boundary()
        + verify_industry_modules_do_not_carry_user_data()
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
