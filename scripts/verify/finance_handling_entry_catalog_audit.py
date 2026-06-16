#!/usr/bin/env python3
from __future__ import annotations

import ast
import importlib.util
import json
import sys
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[2]
CATALOG_PATH = ROOT / "addons/smart_construction_scene/services/handling_entry_catalog.py"
BUSINESS_CATEGORY_MODEL = ROOT / "addons/smart_construction_core/models/support/business_category.py"
BUSINESS_CATEGORY_SEED = ROOT / "addons/smart_construction_core/data/business_category_seed.xml"


def load_catalog_module():
    spec = importlib.util.spec_from_file_location("handling_entry_catalog_audit_target", CATALOG_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load catalog module: {CATALOG_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_action_bindings() -> dict[str, str]:
    tree = ast.parse(BUSINESS_CATEGORY_MODEL.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "BUSINESS_CATEGORY_ACTION_BINDINGS":
                    value = ast.literal_eval(node.value)
                    if isinstance(value, dict):
                        return {str(k): str(v) for k, v in value.items()}
    raise RuntimeError("BUSINESS_CATEGORY_ACTION_BINDINGS not found")


def load_seed_codes() -> set[str]:
    root = ET.parse(BUSINESS_CATEGORY_SEED).getroot()
    codes: set[str] = set()
    for record in root.findall(".//record[@model='sc.business.category']"):
        for field in record.findall("field"):
            if field.attrib.get("name") == "code" and (field.text or "").strip():
                codes.add((field.text or "").strip())
    return codes


def main() -> int:
    module = load_catalog_module()
    catalog = module.build_finance_handling_entry_catalog()
    bindings = load_action_bindings()
    seed_codes = load_seed_codes()

    failures: list[dict[str, str]] = []
    groups = catalog.get("groups") or []
    items = [item for group in groups for item in group.get("items", [])]
    category_options = [
        option
        for item in items
        for option in (item.get("business_category_options") or [])
        if isinstance(option, dict)
    ]
    category_rows = [
        *[
            {
                "business_category_code": item.get("business_category_code"),
                "category_action_xmlid": item.get("category_action_xmlid"),
                "action_xmlid": (item.get("target") or {}).get("action_xmlid") or item.get("action_xmlid"),
                "label": item.get("label"),
            }
            for item in items
            if item.get("business_category_code")
        ],
        *[
            {
                "business_category_code": option.get("code"),
                "category_action_xmlid": option.get("category_action_xmlid"),
                "action_xmlid": option.get("action_xmlid"),
                "label": option.get("label"),
            }
            for option in category_options
        ],
    ]
    if catalog.get("group_count") != 4 or len(groups) != 4:
        failures.append({"code": "group_count_mismatch", "actual": str(catalog.get("group_count"))})
    if catalog.get("item_count") != 13 or len(items) != 13:
        failures.append({"code": "item_count_mismatch", "actual": str(catalog.get("item_count"))})

    for item in items:
        if not str(item.get("business_category_code") or "").strip() and not (item.get("business_category_options") or []):
            failures.append({"code": "missing_category_carrier", "label": str(item.get("label") or "")})
        if not str((item.get("target") or {}).get("action_xmlid") or item.get("action_xmlid") or "").strip():
            failures.append({"code": "missing_entry_action", "label": str(item.get("label") or "")})

    for row in category_rows:
        category_code = str(row.get("business_category_code") or "")
        action_xmlid = str(row.get("action_xmlid") or "")
        if not category_code:
            failures.append({"code": "missing_category_code", "label": str(row.get("label") or "")})
            continue
        if category_code not in seed_codes:
            failures.append({"code": "category_seed_missing", "category_code": category_code})
        bound_action = bindings.get(category_code)
        category_action = str(row.get("category_action_xmlid") or action_xmlid)
        if not bound_action:
            failures.append({"code": "action_binding_missing", "category_code": category_code})
        elif bound_action != category_action:
            failures.append({
                "code": "action_binding_mismatch",
                "category_code": category_code,
                "expected": bound_action,
                "actual": category_action,
            })

    summary = {
        "status": "FAIL" if failures else "PASS",
        "group_count": len(groups),
        "item_count": len(items),
        "unique_category_count": len({str(row.get("business_category_code") or "") for row in category_rows}),
        "failures": failures,
    }
    print("FINANCE_HANDLING_ENTRY_CATALOG_AUDIT " + json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
