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
    ROOT / "addons" / "smart_construction_core" / "views" / "core" / "expense_business_fact_taxonomy_views.xml",
]


EXPECTED_ACTIONS = {
    "action_sc_expense_claim_project": {
        "name": "项目费用报销单",
        "context": {
            "default_claim_type": "expense",
            "default_expense_type": "项目费用报销单",
            "default_summary": "项目费用报销单",
        },
        "domain_tokens": ["claim_type", "expense", "expense_type", "项目费用报销单"],
    },
    "action_sc_expense_claim_deduction_paid": {
        "name": "扣款实缴登记",
        "context": {
            "default_claim_type": "expense",
            "default_expense_type": "扣款实缴登记",
            "default_summary": "扣款实缴登记",
        },
        "domain_tokens": ["online_old_scbs:T_KK_SJDJB:list897", "expense_type", "扣款实缴登记"],
    },
    "action_sc_expense_claim_deduction_paid_refund": {
        "name": "扣款实缴退回",
        "context": {
            "default_claim_type": "deduction_refund",
            "default_expense_type": "扣款实缴退回",
            "default_summary": "扣款实缴退回",
        },
        "domain_tokens": ["online_old_scbs:T_KK_SJTHB:list898", "expense_type", "扣款实缴退回"],
    },
    "action_sc_bid_deposit_pay": {
        "name": "投标保证金缴纳",
        "context": {
            "default_claim_type": "deposit_pay",
            "default_guarantee_type": "bid",
            "default_expense_type": "投标保证金缴纳",
            "default_summary": "投标保证金缴纳",
        },
        "domain_tokens": ["claim_type", "deposit_pay", "guarantee_type", "bid"],
    },
    "action_sc_bid_deposit_return": {
        "name": "投标保证金退回",
        "context": {
            "default_claim_type": "deposit_refund",
            "default_guarantee_type": "bid",
            "default_expense_type": "投标保证金退回",
            "default_summary": "投标保证金退回",
        },
        "domain_tokens": ["claim_type", "deposit_refund", "guarantee_type", "bid"],
    },
    "action_sc_contract_deposit_pay": {
        "name": "合同保证金登记",
        "context": {
            "default_claim_type": "deposit_pay",
            "default_guarantee_type": "contract",
            "default_expense_type": "合同保证金登记",
            "default_summary": "合同保证金登记",
        },
        "domain_tokens": ["claim_type", "deposit_pay", "guarantee_type", "contract"],
    },
    "action_sc_contract_deposit_return": {
        "name": "合同保证金退回",
        "context": {
            "default_claim_type": "deposit_refund",
            "default_guarantee_type": "contract",
            "default_expense_type": "合同保证金退回",
            "default_summary": "合同保证金退回",
        },
        "domain_tokens": ["claim_type", "deposit_refund", "guarantee_type", "contract"],
    },
}


EXPECTED_MENUS = {
    "menu_sc_project_expense_claim": "smart_construction_core.action_sc_expense_claim_project",
    "menu_sc_deduction_paid": "smart_construction_core.action_sc_expense_claim_deduction_paid",
    "menu_sc_deduction_paid_refund": "smart_construction_core.action_sc_expense_claim_deduction_paid_refund",
    "menu_sc_bid_deposit_pay": "smart_construction_core.action_sc_bid_deposit_pay",
    "menu_sc_bid_deposit_return": "smart_construction_core.action_sc_bid_deposit_return",
    "menu_sc_contract_deposit_register": "smart_construction_core.action_sc_contract_deposit_pay",
    "menu_sc_contract_deposit_return": "smart_construction_core.action_sc_contract_deposit_return",
}


def _parse_context(raw: str) -> dict:
    try:
        value = ast.literal_eval(raw or "{}")
    except (SyntaxError, ValueError) as exc:
        raise AssertionError(f"invalid context literal: {raw!r}: {exc}") from exc
    if not isinstance(value, dict):
        raise AssertionError(f"context is not a dict: {raw!r}")
    return value


def _field_text(record: ET.Element, name: str) -> str:
    for field in record.findall("field"):
        if field.attrib.get("name") == name:
            return (field.text or "").strip()
    return ""


def _field_ref(record: ET.Element, name: str) -> str:
    for field in record.findall("field"):
        if field.attrib.get("name") == name:
            return (field.attrib.get("ref") or "").strip()
    return ""


def main() -> int:
    records: dict[str, ET.Element] = {}
    menus: dict[str, dict[str, str]] = {}
    for target in TARGETS:
        tree = ET.parse(target)
        root = tree.getroot()
        for node in root.findall(".//record"):
            xmlid = node.attrib.get("id")
            if not xmlid:
                continue
            records[xmlid] = node
            if node.attrib.get("model") == "ir.ui.menu":
                menu = menus.setdefault(xmlid, {})
                action = _field_ref(node, "action")
                if action:
                    menu["action"] = action
        for node in root.findall(".//menuitem"):
            xmlid = node.attrib.get("id")
            if not xmlid:
                continue
            menu = menus.setdefault(xmlid, {})
            action = node.attrib.get("action")
            if action:
                menu["action"] = action
    failures: list[str] = []
    rows: list[dict] = []

    for action_id, expected in EXPECTED_ACTIONS.items():
        record = records.get(action_id)
        if record is None:
            failures.append(f"missing action {action_id}")
            continue
        name = _field_text(record, "name")
        if name != expected["name"]:
            failures.append(f"{action_id}: expected name={expected['name']!r}, got {name!r}")
        if _field_text(record, "res_model") != "sc.expense.claim":
            failures.append(f"{action_id}: res_model is not sc.expense.claim")
        context = _parse_context(_field_text(record, "context"))
        for key, value in expected["context"].items():
            if context.get(key) != value:
                failures.append(f"{action_id}: context[{key}] expected {value!r}, got {context.get(key)!r}")
        domain = _field_text(record, "domain")
        for token in expected["domain_tokens"]:
            if token not in domain:
                failures.append(f"{action_id}: domain missing {token!r}")
        rows.append({"action": action_id, "name": name, "context": context, "domain": domain})

    for menu_id, expected_action in EXPECTED_MENUS.items():
        menu = menus.get(menu_id)
        if not menu:
            failures.append(f"missing menu {menu_id}")
            continue
        action = menu.get("action")
        if action != expected_action:
            failures.append(f"{menu_id}: expected action={expected_action!r}, got {action!r}")

    result = {
        "audit": "finance_expense_claim_entry_context_audit",
        "targets": [str(target.relative_to(ROOT)) for target in TARGETS],
        "status": "PASS" if not failures else "FAIL",
        "action_count": len(EXPECTED_ACTIONS),
        "menu_count": len(EXPECTED_MENUS),
        "rows": rows,
        "failures": failures,
    }
    print("FINANCE_EXPENSE_CLAIM_ENTRY_CONTEXT_AUDIT: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
