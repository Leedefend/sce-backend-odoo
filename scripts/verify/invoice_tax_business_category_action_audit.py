#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TARGETS = [
    ROOT / "addons" / "smart_construction_core" / "views" / "menu_business_taxonomy.xml",
    ROOT / "addons" / "smart_construction_core" / "views" / "support" / "p1_daily_business_visible_alias_views.xml",
    ROOT / "addons" / "smart_construction_core" / "views" / "support" / "user_confirmed_formal_list_views.xml",
]


CATEGORY_ACTIONS = {
    "invoice.output.application": {
        "label": "销项开票申请",
        "model": "sc.invoice.registration",
        "action": "action_sc_invoice_application_user",
        "menus": ["menu_sc_invoice_application_user"],
        "context": {
            "default_source_kind": "output_invoice_tax",
            "default_direction": "output",
            "default_invoice_content": "销项开票申请",
            "default_business_category_code": "invoice.output.application",
        },
        "domain_tokens": ["business_category_id.code", "invoice.output.application"],
        "new_record_tokens": ["business_category_id.code", "invoice.output.application"],
    },
    "invoice.output.registration": {
        "label": "销项开票登记",
        "model": "sc.invoice.registration",
        "action": "action_sc_invoice_registration_user",
        "menus": ["menu_sc_invoice_registration_user"],
        "context": {
            "default_source_kind": "output_invoice_tax",
            "default_direction": "output",
            "default_invoice_content": "销项开票登记",
            "default_business_category_code": "invoice.output.registration",
        },
        "domain_tokens": ["business_category_id.code", "invoice.output.registration"],
        "new_record_tokens": ["business_category_id.code", "invoice.output.registration"],
    },
    "invoice.prepaid_tax": {
        "label": "预缴税款",
        "model": "sc.invoice.registration",
        "action": "action_sc_invoice_prepaid_tax_user",
        "menus": ["menu_sc_invoice_prepaid_tax_user"],
        "context": {
            "default_source_kind": "prepaid_tax",
            "default_direction": "prepaid",
            "default_invoice_content": "预缴税款",
            "default_business_category_code": "invoice.prepaid_tax",
        },
        "domain_tokens": ["business_category_id.code", "invoice.prepaid_tax"],
        "new_record_tokens": ["business_category_id.code", "invoice.prepaid_tax"],
    },
    "invoice.input.report": {
        "label": "进项税额上报",
        "model": "sc.invoice.registration",
        "action": "action_sc_invoice_input_report_user",
        "menus": ["menu_sc_invoice_input_report_user"],
        "context": {
            "default_source_kind": "input_invoice_tax",
            "default_direction": "input",
            "default_invoice_content": "进项税额上报",
            "default_business_category_code": "invoice.input.report",
        },
        "domain_tokens": ["business_category_id.code", "invoice.input.report"],
        "new_record_tokens": ["business_category_id.code", "invoice.input.report"],
    },
    "tax.deduction.registration": {
        "label": "抵扣登记",
        "model": "sc.tax.deduction.registration",
        "action": "action_sc_tax_deduction_registration_user",
        "menus": ["menu_sc_tax_deduction_registration_user"],
        "context": {
            "default_is_transfer_out": False,
            "default_deduction_reason": "抵扣登记",
            "default_business_category_code": "tax.deduction.registration",
        },
        "domain_tokens": ["business_category_id.code", "tax.deduction.registration"],
        "new_record_tokens": ["business_category_id.code", "tax.deduction.registration"],
    },
}


def _parse_context(raw: str) -> dict:
    try:
        value = ast.literal_eval(raw or "{}")
    except (SyntaxError, ValueError) as exc:
        raise AssertionError(f"invalid context literal: {raw!r}: {exc}") from exc
    if not isinstance(value, dict):
        raise AssertionError(f"context is not a dict: {raw!r}")
    return value


def _field_value(field: ET.Element) -> str:
    if "ref" in field.attrib:
        return field.attrib["ref"].strip()
    if "eval" in field.attrib:
        return field.attrib["eval"].strip()
    return (field.text or "").strip()


def _collect() -> tuple[dict[str, dict[str, str]], dict[str, dict[str, str]]]:
    records: dict[str, dict[str, str]] = {}
    menus: dict[str, dict[str, str]] = {}
    for target in TARGETS:
        tree = ET.parse(target)
        root = tree.getroot()
        for node in root.findall(".//record"):
            xmlid = node.attrib.get("id")
            if not xmlid:
                continue
            if node.attrib.get("model") == "ir.ui.menu":
                menu = menus.setdefault(xmlid, {})
                for field in node.findall("field"):
                    if field.attrib.get("name") == "action":
                        menu["action"] = _field_value(field)
                continue
            record = records.setdefault(xmlid, {})
            if node.attrib.get("model"):
                record["_model"] = node.attrib["model"]
            for field in node.findall("field"):
                name = field.attrib.get("name")
                if name:
                    record[name] = _field_value(field)
        for node in root.findall(".//menuitem"):
            xmlid = node.attrib.get("id")
            if not xmlid:
                continue
            menu = menus.setdefault(xmlid, {})
            action = node.attrib.get("action")
            if action:
                menu["action"] = action
    return records, menus


def main() -> int:
    records, menus = _collect()
    failures: list[str] = []
    rows: list[dict] = []

    for code, expected in CATEGORY_ACTIONS.items():
        action_id = expected["action"]
        record = records.get(action_id)
        if record is None:
            failures.append(f"{code}: missing action {action_id}")
            continue

        name = record.get("name", "")
        model = record.get("res_model", "")
        context = _parse_context(record.get("context", "{}"))
        domain = record.get("domain", "")
        if not domain:
            failures.append(f"{code}: action domain is empty")
        if name != expected["label"]:
            failures.append(f"{code}: expected action name {expected['label']!r}, got {name!r}")
        if model != expected["model"]:
            failures.append(f"{code}: expected model {expected['model']!r}, got {model!r}")
        for key, value in expected["context"].items():
            if context.get(key) != value:
                failures.append(f"{code}: context[{key}] expected {value!r}, got {context.get(key)!r}")
        for token in expected["domain_tokens"]:
            if token not in domain:
                failures.append(f"{code}: domain missing token {token!r}")
        for token in expected["new_record_tokens"]:
            if token not in domain:
                failures.append(f"{code}: domain does not cover new-record token {token!r}")
        for menu_id in expected["menus"]:
            menu = menus.get(menu_id)
            if not menu:
                failures.append(f"{code}: missing menu {menu_id}")
                continue
            expected_action_ref = f"smart_construction_core.{action_id}"
            if menu.get("action") != expected_action_ref:
                failures.append(f"{code}: menu {menu_id} expected action {expected_action_ref!r}, got {menu.get('action')!r}")
        rows.append({"code": code, "label": name, "model": model, "action": action_id, "menus": expected["menus"]})

    result = {
        "audit": "invoice_tax_business_category_action_audit",
        "targets": [str(target.relative_to(ROOT)) for target in TARGETS],
        "status": "PASS" if not failures else "FAIL",
        "category_count": len(CATEGORY_ACTIONS),
        "rows": rows,
        "failures": failures,
    }
    print("INVOICE_TAX_BUSINESS_CATEGORY_ACTION_AUDIT: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
