#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Static guard for the Smart Construction business menu taxonomy."""

from __future__ import annotations

import ast
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE = "smart_construction_core"
MODULE_ROOT = REPO_ROOT / "addons" / MODULE
MANIFEST = MODULE_ROOT / "__manifest__.py"
TAXONOMY = MODULE_ROOT / "views" / "menu_business_taxonomy.xml"

EXPECTED_TAXONOMY_PATH = "views/menu_business_taxonomy.xml"
EXPECTED_FULL_COVERAGE_PATH = "data/business_menu_full_coverage.xml"

EXPECTED_ROOT = ("menu_sc_root", "智慧施工管理平台")

EXPECTED_TOP_LEVEL = {
    "menu_sc_projection_root": ("智慧大屏", 5),
    "menu_sc_workspace_center": ("工作台", 10),
    "menu_sc_project_center": ("项目中心", 20),
    "menu_sc_contract_center": ("合同中心", 30),
    "menu_sc_material_center": ("物资与分包", 40),
    "menu_sc_construction_management_center": ("施工管理", 50),
    "menu_sc_cost_center": ("成本中心", 60),
    "menu_sc_finance_center": ("财务中心", 70),
    "menu_sc_data_center": ("统计分析", 80),
    "menu_sc_business_config_center": ("基础设置", 90),
}

STRUCTURAL_CONTAINERS = [
    "menu_sc_root",
    "menu_sc_projection_root",
    "menu_sc_project_center",
    "menu_sc_contract_center",
    "menu_sc_material_center",
    "menu_sc_cost_center",
    "menu_sc_finance_center",
    "menu_sc_data_center",
    "menu_sc_business_config_center",
    "menu_sc_doc_center",
]

EXPECTED_REPARENTS = {
    "menu_sc_project_initiation": "menu_sc_project_management_group",
    "menu_sc_project_quick_create": "menu_sc_project_management_group",
    "menu_sc_project_project": "menu_sc_project_management_group",
    "menu_sc_project_wbs": "menu_sc_project_management_group",
    "menu_sc_project_management_scene": "menu_sc_project_management_group",
    "menu_sc_project_work_breakdown": "menu_sc_project_management_group",
    "menu_sc_project_structure_wbs": "menu_sc_project_management_group",
    "menu_sc_project_manage": "menu_sc_config_center",
    "menu_sc_project_tender": "menu_sc_tender_management_group",
    "menu_sc_tender_prepare": "menu_sc_tender_management_group",
    "menu_sc_tender_opening": "menu_sc_tender_management_group",
    "menu_sc_tender_won": "menu_sc_tender_management_group",
    "menu_sc_tender_guarantee": "menu_sc_tender_management_group",
    "menu_sc_project_budget_center": "menu_sc_project_budget_group",
    "menu_sc_project_boq_root": "menu_sc_project_budget_group",
    "menu_sc_construction_contract": "menu_sc_income_contract_group",
    "menu_sc_contract_income": "menu_sc_income_contract_group",
    "menu_sc_income_contract_variation": "menu_sc_income_contract_group",
    "menu_sc_income_contract_execution": "menu_sc_income_contract_group",
    "menu_sc_income_contract_settlement": "menu_sc_income_contract_group",
    "menu_sc_general_contract": "menu_sc_expense_contract_group",
    "menu_sc_contract_expense": "menu_sc_expense_contract_group",
    "menu_sc_expense_contract_variation": "menu_sc_expense_contract_group",
    "menu_sc_expense_contract_execution": "menu_sc_expense_contract_group",
    "menu_sc_expense_contract_settlement": "menu_sc_expense_contract_group",
    "menu_sc_legacy_purchase_contract_fact": "menu_sc_expense_contract_group",
    "menu_project_material_plan": "menu_sc_material_management_group",
    "menu_sc_purchase_order": "menu_sc_material_management_group",
    "menu_sc_legacy_material_category": "menu_sc_material_management_group",
    "menu_sc_material_price_library": "menu_sc_material_management_group",
    "menu_sc_settlement_center": "menu_sc_receipt_payment_group",
    "menu_payment_request_receive": "menu_sc_receipt_payment_group",
    "menu_payment_request": "menu_sc_receipt_payment_group",
    "menu_payment_request_line": "menu_sc_receipt_payment_group",
    "menu_sc_invoice_output": "menu_sc_invoice_management_group",
    "menu_sc_invoice_input": "menu_sc_invoice_management_group",
    "menu_receipt_invoice_line": "menu_sc_invoice_management_group",
    "menu_sc_funding_plan_group": "menu_sc_finance_center",
    "menu_sc_funding_plan_declaration": "menu_sc_funding_plan_group",
    "menu_sc_legacy_account_transaction_line": "menu_sc_fund_account_group",
    "menu_sc_financing_loan": "menu_sc_fund_account_group",
    "menu_sc_deposit_management_group": "menu_sc_finance_center",
    "menu_sc_bid_deposit_pay": "menu_sc_deposit_management_group",
    "menu_sc_bid_deposit_return": "menu_sc_deposit_management_group",
    "menu_sc_contract_deposit_register": "menu_sc_deposit_management_group",
    "menu_sc_contract_deposit_return": "menu_sc_deposit_management_group",
    "menu_sc_finance_history_center": "menu_sc_config_center",
    "menu_sc_project_contract_overview": "menu_sc_business_analysis_group",
    "menu_sc_legacy_user_context": "menu_sc_config_center",
    "menu_sc_ar_ap_project_summary": "menu_sc_finance_analysis_group",
    "menu_sc_ar_ap_company_summary": "menu_sc_finance_analysis_group",
    "menu_sc_treasury_ledger_income": "menu_sc_finance_analysis_group",
    "menu_payment_ledger": "menu_sc_finance_analysis_group",
    "menu_sc_account_income_expense_summary": "menu_sc_finance_analysis_group",
    "menu_sc_treasury_ledger": "menu_sc_finance_analysis_group",
    "menu_sc_financing_ledger": "menu_sc_finance_analysis_group",
    "menu_sc_fund_daily_summary": "menu_sc_finance_analysis_group",
    "menu_sc_fund_daily_line": "menu_sc_finance_analysis_group",
    "menu_sc_customer_partner": "menu_sc_business_config_center",
    "menu_sc_supplier_partner": "menu_sc_business_config_center",
}


def _load_manifest_data() -> list[str]:
    tree = ast.parse(MANIFEST.read_text(encoding="utf-8"))
    manifest = ast.literal_eval(tree.body[0].value)
    return list(manifest.get("data") or [])


def _normalize_xmlid(value: str) -> str:
    value = value.strip()
    if "." in value:
        return value.split(".", 1)[1] if value.startswith(f"{MODULE}.") else value
    return value


def _field_text(record: ET.Element, name: str) -> str | None:
    for field in record.findall("field"):
        if field.attrib.get("name") == name:
            return field.text or ""
    return None


def _field_attr(record: ET.Element, name: str, attr: str) -> str | None:
    for field in record.findall("field"):
        if field.attrib.get("name") == name:
            return field.attrib.get(attr)
    return None


def _field_eval(record: ET.Element, name: str) -> str | None:
    return _field_attr(record, name, "eval")


def _collect_entries(root: ET.Element) -> dict[str, dict[str, str | None]]:
    entries: dict[str, dict[str, str | None]] = {}
    for node in root.iter():
        node_id = node.attrib.get("id")
        if not node_id:
            continue
        if node.tag == "record" and node.attrib.get("model") == "ir.ui.menu":
            entries[node_id] = {
                "tag": "record",
                "name": _field_text(node, "name"),
                "parent": _normalize_xmlid(_field_attr(node, "parent_id", "ref") or ""),
                "sequence": _field_text(node, "sequence"),
                "action": _field_eval(node, "action"),
                "groups": _field_eval(node, "groups_id"),
            }
        elif node.tag == "menuitem":
            entries[node_id] = {
                "tag": "menuitem",
                "name": node.attrib.get("name"),
                "parent": _normalize_xmlid(node.attrib.get("parent") or ""),
                "sequence": node.attrib.get("sequence"),
                "action": node.attrib.get("action"),
                "groups": node.attrib.get("groups"),
            }
    return entries


def _all_module_xmlids() -> set[str]:
    xmlids: set[str] = set()
    for path in MODULE_ROOT.rglob("*.xml"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for match in re.finditer(r'\bid="([A-Za-z0-9_\.]+)"', text):
            value = match.group(1)
            xmlids.add(value if "." in value else f"{MODULE}.{value}")
    return xmlids


def _taxonomy_refs() -> list[tuple[str, str]]:
    text = TAXONOMY.read_text(encoding="utf-8")
    refs: list[tuple[str, str]] = []
    for attr in ("ref", "parent", "action", "groups"):
        for match in re.finditer(attr + r'="([^"]+)"', text):
            for raw_token in match.group(1).split(","):
                token = raw_token.strip()
                if token and not token.startswith("base."):
                    refs.append((attr, token if "." in token else f"{MODULE}.{token}"))
    return refs


def main() -> int:
    failures: list[dict[str, object]] = []
    if not TAXONOMY.exists():
        failures.append({"check": "taxonomy_file", "missing": str(TAXONOMY.relative_to(REPO_ROOT))})
        print(json.dumps({"ok": False, "failures": failures}, ensure_ascii=False, indent=2))
        return 1

    manifest_data = _load_manifest_data()
    if EXPECTED_TAXONOMY_PATH not in manifest_data:
        failures.append({"check": "manifest_load", "missing": EXPECTED_TAXONOMY_PATH})
    elif EXPECTED_FULL_COVERAGE_PATH in manifest_data:
        if manifest_data[-2:] != [EXPECTED_TAXONOMY_PATH, EXPECTED_FULL_COVERAGE_PATH]:
            failures.append(
                {
                    "check": "manifest_load_order",
                    "expected_tail": [EXPECTED_TAXONOMY_PATH, EXPECTED_FULL_COVERAGE_PATH],
                    "actual_tail": manifest_data[-2:],
                }
            )
    elif manifest_data[-1] != EXPECTED_TAXONOMY_PATH:
        failures.append(
            {
                "check": "manifest_load_order",
                "expected_last": EXPECTED_TAXONOMY_PATH,
                "actual_last": manifest_data[-1],
            }
        )

    root = ET.parse(TAXONOMY).getroot()
    entries = _collect_entries(root)

    root_id, root_name = EXPECTED_ROOT
    if entries.get(root_id, {}).get("name") != root_name:
        failures.append({"check": "root_name", "expected": root_name, "actual": entries.get(root_id)})

    for menu_id, (expected_name, expected_sequence) in EXPECTED_TOP_LEVEL.items():
        entry = entries.get(menu_id)
        if not entry:
            failures.append({"check": "top_level_missing", "menu_id": menu_id})
            continue
        if entry.get("name") != expected_name:
            failures.append(
                {
                    "check": "top_level_name",
                    "menu_id": menu_id,
                    "expected": expected_name,
                    "actual": entry.get("name"),
                }
            )
        if entry.get("parent") != "menu_sc_root":
            failures.append(
                {
                    "check": "top_level_parent",
                    "menu_id": menu_id,
                    "expected": "menu_sc_root",
                    "actual": entry.get("parent"),
                }
            )
        if str(entry.get("sequence") or "") != str(expected_sequence):
            failures.append(
                {
                    "check": "top_level_sequence",
                    "menu_id": menu_id,
                    "expected": expected_sequence,
                    "actual": entry.get("sequence"),
                }
            )

    for menu_id in STRUCTURAL_CONTAINERS:
        entry = entries.get(menu_id)
        if not entry:
            failures.append({"check": "container_missing", "menu_id": menu_id})
            continue
        if entry.get("action") not in (None, "", "False"):
            failures.append({"check": "container_action", "menu_id": menu_id, "actual": entry.get("action")})
        if menu_id != "menu_sc_doc_center" and entry.get("groups") not in (None, "", "[(5, 0, 0)]"):
            failures.append({"check": "container_groups", "menu_id": menu_id, "actual": entry.get("groups")})

    for menu_id, expected_parent in EXPECTED_REPARENTS.items():
        entry = entries.get(menu_id)
        if not entry:
            failures.append({"check": "reparent_missing", "menu_id": menu_id})
            continue
        if entry.get("parent") != expected_parent:
            failures.append(
                {
                    "check": "reparent",
                    "menu_id": menu_id,
                    "expected_parent": expected_parent,
                    "actual_parent": entry.get("parent"),
                }
            )

    module_xmlids = _all_module_xmlids()
    missing_refs = [
        {"attr": attr, "xmlid": xmlid}
        for attr, xmlid in _taxonomy_refs()
        if xmlid.startswith(f"{MODULE}.") and xmlid not in module_xmlids
    ]
    if missing_refs:
        failures.append({"check": "xmlid_refs", "missing": missing_refs})

    result = {
        "ok": not failures,
        "taxonomy": str(TAXONOMY.relative_to(REPO_ROOT)),
        "top_level": [menu_id for menu_id in EXPECTED_TOP_LEVEL],
        "checked_reparents": len(EXPECTED_REPARENTS),
        "failures": failures,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
