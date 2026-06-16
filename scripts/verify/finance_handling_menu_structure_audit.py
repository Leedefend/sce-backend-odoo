#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TARGETS = [
    ROOT / "addons" / "smart_construction_core" / "views" / "menu_business_taxonomy.xml",
    ROOT / "addons" / "smart_construction_core" / "views" / "menu_user_acceptance_cleanup.xml",
]

EXPECTED_GROUPS = {
    "menu_sc_receipt_payment_group": ("收付款办理", "smart_construction_core.menu_sc_finance_center", "10", "1"),
    "menu_sc_invoice_tax_user_group": ("开票与税务办理", "smart_construction_core.menu_sc_finance_center", "20", "1"),
    "menu_sc_expense_reimbursement_group": ("费用与报销办理", "smart_construction_core.menu_sc_finance_center", "30", "1"),
    "menu_sc_fund_account_group": ("资金往来办理", "smart_construction_core.menu_sc_finance_center", "40", "1"),
}

EXPECTED_MENU_PARENTS = {
    "menu_sc_user_income": ("menu_sc_receipt_payment_group", "10"),
    "menu_sc_engineering_progress_income": ("menu_sc_receipt_payment_group", "15"),
    "menu_payment_request_receive": ("menu_sc_receipt_payment_group", "20"),
    "menu_sc_user_payment_apply_acceptance": ("menu_sc_receipt_payment_group", "30"),
    "menu_sc_partner_payment": ("menu_sc_receipt_payment_group", "40"),
    "menu_sc_company_finance_expense": ("menu_sc_receipt_payment_group", "50"),
    "menu_sc_arrival_confirmation": ("menu_sc_receipt_payment_group", "60"),
    "menu_sc_invoice_application_user": ("menu_sc_invoice_tax_user_group", "10"),
    "menu_sc_invoice_registration_user": ("menu_sc_invoice_tax_user_group", "20"),
    "menu_sc_invoice_prepaid_tax_user": ("menu_sc_invoice_tax_user_group", "30"),
    "menu_sc_invoice_input_report_user": ("menu_sc_invoice_tax_user_group", "40"),
    "menu_sc_tax_deduction_registration_user": ("menu_sc_invoice_tax_user_group", "50"),
    "menu_sc_tax_certificate_registration_user": ("menu_sc_invoice_tax_user_group", "60"),
    "menu_sc_reimbursement_request": ("menu_sc_expense_reimbursement_group", "10"),
    "menu_sc_project_expense_claim": ("menu_sc_expense_reimbursement_group", "20"),
    "menu_sc_deduction_bill": ("menu_sc_expense_reimbursement_group", "30"),
    "menu_sc_deduction_paid": ("menu_sc_expense_reimbursement_group", "35"),
    "menu_sc_deduction_paid_refund": ("menu_sc_expense_reimbursement_group", "40"),
    "menu_sc_bid_deposit_pay": ("menu_sc_expense_reimbursement_group", "50"),
    "menu_sc_bid_deposit_return": ("menu_sc_expense_reimbursement_group", "55"),
    "menu_sc_contract_deposit_register": ("menu_sc_expense_reimbursement_group", "60"),
    "menu_sc_contract_deposit_return": ("menu_sc_expense_reimbursement_group", "65"),
    "menu_sc_borrowing_request": ("menu_sc_fund_account_group", "10"),
    "menu_sc_repayment_registration": ("menu_sc_fund_account_group", "15"),
    "menu_sc_contractor_project_repay": ("menu_sc_fund_account_group", "20"),
    "menu_sc_contractor_project_borrow": ("menu_sc_fund_account_group", "25"),
    "menu_sc_project_borrow_company": ("menu_sc_fund_account_group", "30"),
    "menu_sc_project_repay_company": ("menu_sc_fund_account_group", "35"),
    "menu_sc_self_funding_advance_income": ("menu_sc_fund_account_group", "40"),
    "menu_sc_self_funding_advance_refund": ("menu_sc_fund_account_group", "45"),
    "menu_sc_fund_account_between_user": ("menu_sc_fund_account_group", "50"),
    "menu_sc_fund_transfer_out": ("menu_sc_fund_account_group", "55"),
    "menu_sc_fund_transfer_between": ("menu_sc_fund_account_group", "60"),
    "menu_sc_fund_balance_adjustment": ("menu_sc_fund_account_group", "65"),
    "menu_sc_fund_daily_user_report": ("menu_sc_fund_account_group", "70"),
}

HIDDEN_DUPLICATE_GROUPS = {
    "menu_sc_payment_user_group",
    "menu_sc_income_expense_user_group",
    "menu_sc_fund_loan_repayment_group",
    "menu_sc_project_fund_user_group",
    "menu_sc_receipt_user_group",
    "menu_sc_fund_daily_user_group",
    "menu_sc_deposit_management_group",
    "menu_sc_fund_account_user_group",
}

HIDDEN_TECHNICAL_MENUS = {
    "menu_payment_request",
    "menu_payment_request_line",
    "menu_sc_user_payment_apply",
    "menu_sc_financing_loan",
}


def _field_value(record: ET.Element, name: str) -> str:
    for field in record.findall("field"):
        if field.attrib.get("name") == name:
            return (field.attrib.get("ref") or field.attrib.get("eval") or (field.text or "")).strip()
    return ""


def _apply_field(menu: dict[str, str], name: str, value: str) -> None:
    if name == "parent_id":
        menu["parent_id"] = value
    elif name == "sequence":
        menu["sequence"] = value
    elif name == "name":
        menu["name"] = value
    elif name == "active":
        menu["active"] = value
    elif name == "action":
        menu["action"] = value


def _collect_menus() -> dict[str, dict[str, str]]:
    menus: dict[str, dict[str, str]] = {}
    for target in TARGETS:
        tree = ET.parse(target)
        root = tree.getroot()
        for node in root.findall(".//menuitem"):
            xmlid = node.attrib.get("id")
            if not xmlid:
                continue
            menu = menus.setdefault(xmlid, {})
            for attr in ("name", "parent", "action", "sequence", "groups"):
                value = node.attrib.get(attr)
                if not value:
                    continue
                key = "parent_id" if attr == "parent" else attr
                _apply_field(menu, key, value)
            menu.setdefault("active", "1")
        for node in root.findall(".//record"):
            if node.attrib.get("model") != "ir.ui.menu":
                continue
            xmlid = node.attrib.get("id")
            if not xmlid:
                continue
            menu = menus.setdefault(xmlid, {})
            for field in node.findall("field"):
                name = field.attrib.get("name")
                if not name:
                    continue
                _apply_field(menu, name, _field_value(node, name))
            menu.setdefault("active", "1")
    return menus


def _is_active(value: str) -> bool:
    return value not in {"0", "False", "false"}


def main() -> int:
    menus = _collect_menus()
    failures: list[str] = []
    rows: list[dict[str, str]] = []

    for xmlid, (name, parent, sequence, active) in EXPECTED_GROUPS.items():
        menu = menus.get(xmlid)
        if not menu:
            failures.append(f"{xmlid}: missing handling group")
            continue
        if menu.get("name") != name:
            failures.append(f"{xmlid}: expected name {name!r}, got {menu.get('name')!r}")
        if menu.get("parent_id") != parent:
            failures.append(f"{xmlid}: expected parent {parent!r}, got {menu.get('parent_id')!r}")
        if menu.get("sequence") != sequence:
            failures.append(f"{xmlid}: expected sequence {sequence}, got {menu.get('sequence')!r}")
        if str(int(_is_active(menu.get("active", "1")))) != active:
            failures.append(f"{xmlid}: expected active {active}, got {menu.get('active')!r}")
        rows.append({"xmlid": xmlid, "name": menu.get("name", ""), "parent": menu.get("parent_id", "")})

    for xmlid, (parent, sequence) in EXPECTED_MENU_PARENTS.items():
        menu = menus.get(xmlid)
        if not menu:
            failures.append(f"{xmlid}: missing handling menu")
            continue
        expected_parent = f"smart_construction_core.{parent}"
        actual_parent = menu.get("parent_id")
        if actual_parent not in {parent, expected_parent}:
            failures.append(f"{xmlid}: expected parent {expected_parent!r}, got {actual_parent!r}")
        if menu.get("sequence") != sequence:
            failures.append(f"{xmlid}: expected sequence {sequence}, got {menu.get('sequence')!r}")
        if not _is_active(menu.get("active", "1")):
            failures.append(f"{xmlid}: formal handling menu must stay active")

    for xmlid in sorted(HIDDEN_DUPLICATE_GROUPS | HIDDEN_TECHNICAL_MENUS):
        menu = menus.get(xmlid)
        if not menu:
            failures.append(f"{xmlid}: missing duplicate/technical menu")
            continue
        if _is_active(menu.get("active", "1")):
            failures.append(f"{xmlid}: duplicate/technical menu should be hidden from daily handling")

    payload = {
        "audit": "finance_handling_menu_structure_audit",
        "group_count": len(EXPECTED_GROUPS),
        "formal_menu_count": len(EXPECTED_MENU_PARENTS),
        "hidden_menu_count": len(HIDDEN_DUPLICATE_GROUPS | HIDDEN_TECHNICAL_MENUS),
        "rows": rows,
        "failures": failures,
        "status": "PASS" if not failures else "FAIL",
    }
    print("FINANCE_HANDLING_MENU_STRUCTURE_AUDIT:", json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
