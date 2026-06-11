# -*- coding: utf-8 -*-
"""Static guard for finance/interfund readonly projections."""

from __future__ import annotations

import ast
import csv
import json
from collections import OrderedDict
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[2]

PROJECTIONS = {
    "sc.finance.business.fact": {
        "model": "addons/smart_construction_core/models/projection/finance_business_fact.py",
        "view": "addons/smart_construction_core/views/projection/finance_business_fact_views.xml",
        "manifest_view": "views/projection/finance_business_fact_views.xml",
        "table": "sc_finance_business_fact",
        "action": "action_sc_finance_business_fact",
        "menu": "menu_sc_finance_business_fact",
    },
    "sc.finance.business.project.summary": {
        "model": "addons/smart_construction_core/models/projection/finance_business_project_summary.py",
        "view": "addons/smart_construction_core/views/projection/finance_business_project_summary_views.xml",
        "manifest_view": "views/projection/finance_business_project_summary_views.xml",
        "table": "sc_finance_business_project_summary",
        "action": "action_sc_finance_business_project_summary",
        "menu": "menu_sc_finance_business_project_summary",
    },
    "sc.interfund.movement.fact": {
        "model": "addons/smart_construction_core/models/projection/interfund_movement_fact.py",
        "view": "addons/smart_construction_core/views/projection/interfund_movement_fact_views.xml",
        "manifest_view": "views/projection/interfund_movement_fact_views.xml",
        "table": "sc_interfund_movement_fact",
        "action": "action_sc_interfund_movement_fact",
        "menu": "menu_sc_interfund_movement_fact",
    },
    "sc.interfund.movement.project.summary": {
        "model": "addons/smart_construction_core/models/projection/interfund_movement_project_summary.py",
        "view": "addons/smart_construction_core/views/projection/interfund_movement_project_summary_views.xml",
        "manifest_view": "views/projection/interfund_movement_project_summary_views.xml",
        "table": "sc_interfund_movement_project_summary",
        "action": "action_sc_interfund_movement_project_summary",
        "menu": "menu_sc_interfund_movement_project_summary",
    },
    "sc.finance.project.capital.position": {
        "model": "addons/smart_construction_core/models/projection/finance_project_capital_position.py",
        "view": "addons/smart_construction_core/views/projection/finance_project_capital_position_views.xml",
        "manifest_view": "views/projection/finance_project_capital_position_views.xml",
        "table": "sc_finance_project_capital_position",
        "action": "action_sc_finance_project_capital_position",
        "menu": "menu_sc_finance_project_capital_position",
    },
    "sc.finance.project.counterparty.position": {
        "model": "addons/smart_construction_core/models/projection/finance_project_counterparty_position.py",
        "view": "addons/smart_construction_core/views/projection/finance_project_counterparty_position_views.xml",
        "manifest_view": "views/projection/finance_project_counterparty_position_views.xml",
        "table": "sc_finance_project_counterparty_position",
        "action": "action_sc_finance_project_counterparty_position",
        "menu": "menu_sc_finance_project_counterparty_position",
    },
    "sc.finance.counterparty.position.summary": {
        "model": "addons/smart_construction_core/models/projection/finance_counterparty_position_summary.py",
        "view": "addons/smart_construction_core/views/projection/finance_counterparty_position_summary_views.xml",
        "manifest_view": "views/projection/finance_counterparty_position_summary_views.xml",
        "table": "sc_finance_counterparty_position_summary",
        "action": "action_sc_finance_counterparty_position_summary",
        "menu": "menu_sc_finance_counterparty_position_summary",
    },
    "sc.company.contractor.responsibility.fact": {
        "model": "addons/smart_construction_core/models/projection/company_contractor_responsibility_fact.py",
        "view": "addons/smart_construction_core/views/projection/company_contractor_responsibility_fact_views.xml",
        "manifest_view": "views/projection/company_contractor_responsibility_fact_views.xml",
        "table": "sc_company_contractor_responsibility_fact",
        "action": "action_sc_company_contractor_responsibility_fact",
        "menu": "menu_sc_company_contractor_responsibility_fact",
    },
    "sc.company.contractor.responsibility.summary": {
        "model": "addons/smart_construction_core/models/projection/company_contractor_responsibility_summary.py",
        "view": "addons/smart_construction_core/views/projection/company_contractor_responsibility_summary_views.xml",
        "manifest_view": "views/projection/company_contractor_responsibility_summary_views.xml",
        "table": "sc_company_contractor_responsibility_summary",
        "action": "action_sc_company_contractor_responsibility_summary",
        "menu": "menu_sc_company_contractor_responsibility_summary",
    },
}

MENU_VIEW = "views/projection/finance_interfund_position_menu.xml"


def constant_value(node):
    return node.value if isinstance(node, ast.Constant) else None


def class_has_method(class_node, name):
    return any(isinstance(item, ast.FunctionDef) and item.name == name for item in class_node.body)


def method_raises_readonly(class_node, method_name):
    for item in class_node.body:
        if not isinstance(item, ast.FunctionDef) or item.name != method_name:
            continue
        for stmt in ast.walk(item):
            if (
                isinstance(stmt, ast.Call)
                and isinstance(stmt.func, ast.Attribute)
                and stmt.func.attr == "_raise_readonly_projection"
            ):
                return True
        return False
    return False


errors = []
summary = OrderedDict()

manifest_path = ROOT / "addons/smart_construction_core/__manifest__.py"
manifest_text = manifest_path.read_text(encoding="utf-8")
if MENU_VIEW not in manifest_text:
    errors.append({"key": "menu_view_not_in_manifest", "view": MENU_VIEW})

menu_path = ROOT / "addons/smart_construction_core" / MENU_VIEW
menu_actions = {}
menu_parent = {}
if not menu_path.exists():
    errors.append({"key": "missing_menu_view_file", "view": MENU_VIEW})
else:
    menu_root = ET.parse(menu_path).getroot()
    for elem in menu_root.iter("menuitem"):
        menu_id = elem.attrib.get("id")
        if menu_id:
            menu_actions[menu_id] = elem.attrib.get("action", "")
            menu_parent[menu_id] = elem.attrib.get("parent", "")
    root_parent = menu_parent.get("menu_sc_finance_interfund_analysis")
    if root_parent != "smart_construction_core.menu_sc_finance_center":
        errors.append(
            {
                "key": "finance_interfund_menu_wrong_parent",
                "menu": "menu_sc_finance_interfund_analysis",
                "expected": "smart_construction_core.menu_sc_finance_center",
                "actual": root_parent,
            }
        )

access_path = ROOT / "addons/smart_construction_core/security/ir.model.access.csv"
with access_path.open(encoding="utf-8") as fh:
    access_rows = list(csv.DictReader(fh))

for model_name, spec in PROJECTIONS.items():
    model_path = ROOT / spec["model"]
    view_path = ROOT / spec["view"]
    model_external = f"model_{model_name.replace('.', '_')}"
    row_summary = OrderedDict(
        [
            ("model", model_name),
            ("model_path", spec["model"]),
            ("view_path", spec["view"]),
        ]
    )

    if not model_path.exists():
        errors.append({"key": "missing_model_file", "model": model_name, "path": spec["model"]})
        continue
    if not view_path.exists():
        errors.append({"key": "missing_view_file", "model": model_name, "path": spec["view"]})
        continue

    tree = ast.parse(model_path.read_text(encoding="utf-8"), filename=str(model_path))
    model_classes = []
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        attrs = {}
        for stmt in node.body:
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Name):
                        attrs[target.id] = constant_value(stmt.value)
        if attrs.get("_name") == model_name:
            model_classes.append((node, attrs))
    if len(model_classes) != 1:
        errors.append({"key": "model_class_count", "model": model_name, "actual": len(model_classes)})
        continue

    class_node, attrs = model_classes[0]
    row_summary["auto_false"] = attrs.get("_auto") is False
    if attrs.get("_auto") is not False:
        errors.append({"key": "projection_not_auto_false", "model": model_name})
    for method_name in ["create", "write", "unlink"]:
        ok = method_raises_readonly(class_node, method_name)
        row_summary[f"{method_name}_readonly"] = ok
        if not ok:
            errors.append({"key": "missing_readonly_method_guard", "model": model_name, "method": method_name})
    if not class_has_method(class_node, "init"):
        errors.append({"key": "missing_sql_view_init", "model": model_name})

    xml_root = ET.parse(view_path).getroot()
    menu_nodes = [elem for elem in xml_root.iter() if elem.tag == "menuitem"]
    row_summary["menuitem_count"] = len(menu_nodes)
    if menu_nodes:
        errors.append({"key": "projection_view_has_menuitem", "model": model_name, "count": len(menu_nodes)})
    forbidden_records = []
    for rec in xml_root.iter("record"):
        if rec.attrib.get("model") == "ir.ui.menu":
            forbidden_records.append(rec.attrib.get("id"))
    row_summary["ir_ui_menu_record_count"] = len(forbidden_records)
    if forbidden_records:
        errors.append({"key": "projection_view_has_menu_records", "model": model_name, "records": forbidden_records})

    if spec["manifest_view"] not in manifest_text:
        errors.append({"key": "view_not_in_manifest", "model": model_name, "view": spec["manifest_view"]})

    expected_menu = spec["menu"]
    expected_action = spec["action"]
    actual_action = menu_actions.get(expected_menu)
    row_summary["business_menu"] = expected_menu
    row_summary["business_menu_action"] = actual_action or ""
    if actual_action != expected_action:
        errors.append(
            {
                "key": "missing_or_wrong_business_menu_action",
                "model": model_name,
                "menu": expected_menu,
                "expected_action": expected_action,
                "actual_action": actual_action,
            }
        )

    access_matches = [row for row in access_rows if row.get("model_id:id") == model_external]
    row_summary["access_rows"] = len(access_matches)
    if not access_matches:
        errors.append({"key": "missing_access_rows", "model": model_name, "model_id": model_external})
    for row in access_matches:
        if row.get("perm_read") != "1" or row.get("perm_write") != "1" or row.get("perm_create") != "0" or row.get("perm_unlink") != "0":
            errors.append(
                {
                    "key": "projection_access_not_page_load_safe",
                    "model": model_name,
                    "access": row.get("id"),
                    "expected": {"read": "1", "write": "1", "create": "0", "unlink": "0"},
                    "actual": {
                        "read": row.get("perm_read"),
                        "write": row.get("perm_write"),
                        "create": row.get("perm_create"),
                        "unlink": row.get("perm_unlink"),
                    },
                }
            )

    summary[model_name] = row_summary

result = OrderedDict()
result["status"] = "PASS" if not errors else "FAIL"
result["summary"] = summary
result["errors"] = errors

print(json.dumps(result, ensure_ascii=False, indent=2))
if errors:
    raise SystemExit(1)
