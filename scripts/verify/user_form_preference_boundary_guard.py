#!/usr/bin/env python3
from __future__ import annotations

import ast
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PREFERENCE_PY = ROOT / "addons/smart_construction_custom/models/user_preferences.py"
PREFERENCE_XML = ROOT / "addons/smart_construction_custom/data/user_preferences.xml"

ALLOWED_PARTNER_XMLIDS = {
    "smart_construction_core.action_sc_customer_partner",
    "smart_construction_core.action_sc_supplier_partner",
}

MIN_FORMAL_MENU_COUNT = 40
REQUIRED_DISCOVERED_MENU_XMLID = "smart_construction_core.menu_sc_project_project"


class Failure(Exception):
    pass


def _literal(node: ast.AST):
    try:
        return ast.literal_eval(node)
    except Exception:
        return None


def _iter_functions(tree: ast.AST):
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            yield node


def _function_by_name(tree: ast.AST, name: str):
    for node in _iter_functions(tree):
        if node.name == name:
            return node
    return None


def _call_name(call: ast.Call) -> str:
    func = call.func
    if isinstance(func, ast.Attribute):
        return func.attr
    if isinstance(func, ast.Name):
        return func.id
    return ""


def _keyword_literal(call: ast.Call, name: str):
    for keyword in call.keywords:
        if keyword.arg == name:
            return _literal(keyword.value)
    return None


def _string_nodes(tree: ast.AST):
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            yield node


def _line_in_function(function: ast.FunctionDef | ast.AsyncFunctionDef, lineno: int) -> bool:
    end = getattr(function, "end_lineno", function.lineno)
    return function.lineno <= lineno <= end


def verify_python_boundary() -> list[str]:
    failures: list[str] = []
    tree = ast.parse(PREFERENCE_PY.read_text(encoding="utf-8"), filename=str(PREFERENCE_PY))

    if _function_by_name(tree, "apply_all_user_form_preferences"):
        failures.append("apply_all_user_form_preferences must not exist; user preference is business user-form governance")
    if _function_by_name(tree, "apply_generic_user_form_preferences"):
        failures.append("apply_generic_user_form_preferences must not exist; user preference must stay inside business menu discovery")

    partner_actions = None
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "PARTNER_ACTIONS":
                    partner_actions = _literal(node.value)
    if not isinstance(partner_actions, dict):
        failures.append("PARTNER_ACTIONS must remain a literal dict so its boundary is auditable")
    else:
        xmlids = {
            str(config.get("xmlid") or "").strip()
            for config in partner_actions.values()
            if isinstance(config, dict)
        }
        if xmlids != ALLOWED_PARTNER_XMLIDS:
            failures.append(
                "PARTNER_ACTIONS may only target customer/supplier partner actions; "
                f"found {sorted(xmlids)}"
            )

    apply_partner = _function_by_name(tree, "apply_partner_form_preferences")
    if not apply_partner:
        failures.append("apply_partner_form_preferences must exist for explicit customer/supplier preferences")
    else:
        calls_deactivate = any(
            isinstance(node, ast.Call) and _call_name(node) == "_deactivate_generic_user_form_preferences"
            for node in ast.walk(apply_partner)
        )
        if not calls_deactivate:
            failures.append("apply_partner_form_preferences must deactivate stale generic user form contracts first")

    apply_user = _function_by_name(tree, "apply_user_form_preferences")
    if not apply_user:
        failures.append("apply_user_form_preferences must exist as the published form preference initializer")
    else:
        expected_calls = {"_deactivate_generic_user_form_preferences", "_upsert_partner_form_contract", "_formal_handling_form_targets"}
        found_calls = {
            _call_name(node)
            for node in ast.walk(apply_user)
            if isinstance(node, ast.Call)
        }
        missing = sorted(expected_calls - found_calls)
        if missing:
            failures.append(f"apply_user_form_preferences missing required calls: {missing}")

    formal_menu_xmlids = None
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "FORMAL_HANDLING_MENU_XMLIDS":
                    formal_menu_xmlids = _literal(node.value)
    if not isinstance(formal_menu_xmlids, tuple) or len(formal_menu_xmlids) < MIN_FORMAL_MENU_COUNT:
        failures.append("FORMAL_HANDLING_MENU_XMLIDS must list the user-confirmed formal handling menus")
    elif REQUIRED_DISCOVERED_MENU_XMLID in formal_menu_xmlids:
        failures.append(
            f"{REQUIRED_DISCOVERED_MENU_XMLID} must be covered by business menu discovery, not patched into FORMAL_HANDLING_MENU_XMLIDS"
        )

    discovery_fn = _function_by_name(tree, "_user_form_preference_menu_entries")
    if not discovery_fn:
        failures.append("_user_form_preference_menu_entries must exist so user form preferences discover business menus")
    else:
        found_calls = {
            _call_name(node)
            for node in ast.walk(discovery_fn)
            if isinstance(node, ast.Call)
        }
        if "search" not in found_calls:
            failures.append("_user_form_preference_menu_entries must search root business menus, not rely only on static xmlids")
        discovery_text = ast.get_source_segment(PREFERENCE_PY.read_text(encoding="utf-8"), discovery_fn) or ""
        if "child_of" not in discovery_text or "USER_FORM_PREFERENCE_ROOT_MENU_XMLID" not in discovery_text:
            failures.append("_user_form_preference_menu_entries must discover menus under USER_FORM_PREFERENCE_ROOT_MENU_XMLID")

    business_filter_fn = _function_by_name(tree, "_is_user_business_form_action")
    if not business_filter_fn:
        failures.append("_is_user_business_form_action must exist to keep preference coverage inside user business forms")

    deactivate_fn = _function_by_name(tree, "_deactivate_generic_user_form_preferences")
    if not deactivate_fn:
        failures.append("_deactivate_generic_user_form_preferences must exist to clean historical generic overrides")
    else:
        for node in _string_nodes(tree):
            if "custom_user_default" in node.value and not _line_in_function(deactivate_fn, node.lineno):
                failures.append(
                    "custom_user_default may only appear in _deactivate_generic_user_form_preferences "
                    f"(line {node.lineno})"
                )

    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and _call_name(node) == "_upsert_form_contract":
            model_name = _keyword_literal(node, "model_name")
            if model_name not in {"res.partner", None}:
                failures.append(
                    "_upsert_form_contract must use explicit res.partner or runtime formal-menu model scope; "
                    f"line {node.lineno} uses {model_name!r}"
                )

    return failures


def verify_xml_boundary() -> list[str]:
    failures: list[str] = []
    root = ET.parse(PREFERENCE_XML).getroot()
    function_names = [
        str(node.attrib.get("name") or "").strip()
        for node in root.iter("function")
        if str(node.attrib.get("model") or "").strip() == "sc.user.preference.initialization"
    ]
    if function_names != ["apply_user_form_preferences"]:
        failures.append(
            "user preference data XML may only call apply_user_form_preferences; "
            f"found {function_names}"
        )
    return failures


def main() -> int:
    failures = verify_python_boundary() + verify_xml_boundary()
    if failures:
        print("[user_form_preference_boundary_guard] FAIL")
        for item in failures:
            print(f"- {item}")
        return 1
    print("[user_form_preference_boundary_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
