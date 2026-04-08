#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[2]
MODEL_FILE = ROOT / "addons/smart_construction_core/models/support/base_dictionary.py"
VIEW_FILE = ROOT / "addons/smart_construction_core/views/support/sc_dictionary_views.xml"
MENU_FILE = ROOT / "addons/smart_construction_core/views/support/dictionary_views.xml"


def _assert_model_surface(failures: list[str], details: list[str]) -> None:
    source = MODEL_FILE.read_text(encoding="utf-8")
    required_types = ["system_param", "role_entry", "home_block"]
    for item in required_types:
        if f"('{item}'," not in source:
            failures.append(f"missing dictionary type: {item}")
    required_fields = ["value_text", "value_json", "scope_type", "scope_ref", "note"]
    for field_name in required_fields:
        if not re.search(rf"\b{field_name}\s*=\s*fields\.", source):
            failures.append(f"missing model field: {field_name}")
    if not failures:
        details.append("model surface ok")


def _text(node: ET.Element, xpath: str) -> str:
    hit = node.find(xpath)
    return (hit.text or "").strip() if hit is not None else ""


def _assert_action_surface(failures: list[str], details: list[str]) -> None:
    tree = ET.parse(VIEW_FILE)
    root = tree.getroot()

    checks = [
        ("action_sc_config_system_param", "system_param"),
        ("action_sc_config_role_entry", "role_entry"),
        ("action_sc_config_home_block", "home_block"),
    ]
    for action_id, expected_type in checks:
        action = root.find(f".//record[@id='{action_id}']")
        if action is None:
            failures.append(f"missing action record: {action_id}")
            continue
        view_mode = _text(action, "field[@name='view_mode']")
        if view_mode != "tree,form":
            failures.append(f"{action_id} view_mode != tree,form")
        domain = _text(action, "field[@name='domain']")
        if expected_type not in domain:
            failures.append(f"{action_id} domain missing type {expected_type}")
        context = _text(action, "field[@name='context']")
        if expected_type not in context:
            failures.append(f"{action_id} context missing default_type {expected_type}")

    if not failures:
        details.append("action surface ok")


def _assert_menu_surface(failures: list[str], details: list[str]) -> None:
    tree = ET.parse(MENU_FILE)
    root = tree.getroot()

    root_menu = root.find(".//menuitem[@id='menu_sc_business_admin_config_root']")
    if root_menu is None:
        failures.append("missing root menu: menu_sc_business_admin_config_root")
        return

    mapping = {
        "menu_sc_config_system_param": "smart_construction_core.action_sc_config_system_param",
        "menu_sc_config_role_entry": "smart_construction_core.action_sc_config_role_entry",
        "menu_sc_config_home_block": "smart_construction_core.action_sc_config_home_block",
    }
    for menu_id, expected_action in mapping.items():
        node = root.find(f".//menuitem[@id='{menu_id}']")
        if node is None:
            failures.append(f"missing menu: {menu_id}")
            continue
        action = (node.get("action") or "").strip()
        if action != expected_action:
            failures.append(f"{menu_id} action mismatch: {action}")
        parent = (node.get("parent") or "").strip()
        if parent != "menu_sc_business_admin_config_root":
            failures.append(f"{menu_id} parent mismatch: {parent}")

    if not failures:
        details.append("menu surface ok")


def main() -> None:
    failures: list[str] = []
    details: list[str] = []

    _assert_model_surface(failures, details)
    _assert_action_surface(failures, details)
    _assert_menu_surface(failures, details)

    if failures:
        raise SystemExit(
            "[native_business_admin_config_center_operability_verify] FAIL " + "; ".join(failures)
        )

    print("[native_business_admin_config_center_operability_verify] PASS " + " | ".join(details))


if __name__ == "__main__":
    main()
