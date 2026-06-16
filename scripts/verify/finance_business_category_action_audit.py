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
    ROOT / "addons" / "smart_construction_core" / "views" / "core" / "payment_request_views.xml",
    ROOT / "addons" / "smart_construction_core" / "views" / "core" / "fund_account_operation_views.xml",
    ROOT / "addons" / "smart_construction_core" / "views" / "core" / "self_funding_registration_views.xml",
    ROOT / "addons" / "smart_construction_core" / "views" / "support" / "user_confirmed_formal_list_views.xml",
]


CATEGORY_ACTIONS = {
    "finance.payment.apply.pay": {
        "label": "支付申请",
        "model": "payment.request",
        "action": "action_payment_request_user_payment_apply",
        "menus": [
            "menu_sc_user_payment_apply",
            "menu_sc_user_payment_apply_acceptance",
        ],
        "context": {
            "default_type": "pay",
            "default_business_category_code": "finance.payment.apply.pay",
        },
        "domain_tokens": ["business_category_id.code", "finance.payment.apply.pay"],
        "forbidden_domain_tokens": ["type"],
        "new_record_tokens": ["business_category_id.code", "finance.payment.apply.pay"],
    },
    "finance.payment.apply.receive": {
        "label": "收款申请",
        "model": "payment.request",
        "action": "action_payment_request_receive",
        "menus": ["menu_payment_request_receive"],
        "context": {
            "default_type": "receive",
            "default_business_category_code": "finance.payment.apply.receive",
        },
        "domain_tokens": ["business_category_id.code", "finance.payment.apply.receive"],
        "forbidden_domain_tokens": ["type"],
        "new_record_tokens": ["business_category_id.code", "finance.payment.apply.receive"],
    },
    "finance.payment.execution.partner": {
        "label": "往来单位付款",
        "model": "sc.payment.execution",
        "action": "action_sc_payment_execution_partner_payment",
        "menus": ["menu_sc_partner_payment"],
        "context": {
            "default_source_kind": "actual_outflow",
            "default_payment_family": "往来单位付款",
            "default_business_category_code": "finance.payment.execution.partner",
        },
        "domain_tokens": ["source_kind", "actual_outflow", "business_category_id.code", "finance.payment.execution.partner"],
        "new_record_tokens": ["business_category_id.code", "finance.payment.execution.partner"],
    },
    "finance.payment.execution.company": {
        "label": "公司财务支出",
        "model": "sc.payment.execution",
        "action": "action_sc_payment_execution_company_finance_expense",
        "menus": ["menu_sc_company_finance_expense"],
        "context": {
            "default_source_kind": "actual_outflow",
            "default_payment_family": "公司财务支出",
            "default_business_category_code": "finance.payment.execution.company",
        },
        "domain_tokens": ["source_kind", "actual_outflow", "business_category_id.code", "finance.payment.execution.company"],
        "new_record_tokens": ["business_category_id.code", "finance.payment.execution.company"],
    },
    "finance.receipt.income.project": {
        "label": "收入",
        "model": "sc.receipt.income",
        "action": "action_sc_receipt_income_user_income",
        "menus": ["menu_sc_user_income"],
        "context": {
            "default_source_kind": "receipt_income",
            "default_income_category": "收入",
            "default_business_category_code": "finance.receipt.income.project",
        },
        "domain_tokens": ["business_category_id.code", "finance.receipt.income.project"],
        "new_record_tokens": ["business_category_id.code", "finance.receipt.income.project"],
    },
    "finance.receipt.income.progress": {
        "label": "工程进度款收入登记",
        "model": "sc.receipt.income",
        "action": "action_sc_receipt_income_engineering_progress",
        "menus": ["menu_sc_engineering_progress_income"],
        "context": {
            "default_source_kind": "receipt_income",
            "default_income_category": "工程进度款收入",
            "default_business_category_code": "finance.receipt.income.progress",
        },
        "domain_tokens": ["business_category_id.code", "finance.receipt.income.progress"],
        "new_record_tokens": ["business_category_id.code", "finance.receipt.income.progress"],
    },
    "finance.expense.reimbursement": {
        "label": "报销申请",
        "model": "sc.expense.claim",
        "action": "action_sc_expense_claim_reimbursement_request",
        "menus": ["menu_sc_reimbursement_request"],
        "context": {
            "default_claim_type": "expense",
            "default_expense_type": "报销申请",
            "default_summary": "报销申请",
            "default_business_category_code": "finance.expense.reimbursement",
        },
        "domain_tokens": ["business_category_id.code", "finance.expense.reimbursement"],
        "new_record_tokens": ["business_category_id.code", "finance.expense.reimbursement"],
    },
    "finance.expense.project": {
        "label": "项目费用报销单",
        "model": "sc.expense.claim",
        "action": "action_sc_expense_claim_project",
        "menus": ["menu_sc_project_expense_claim"],
        "context": {
            "default_claim_type": "expense",
            "default_expense_type": "项目费用报销单",
            "default_summary": "项目费用报销单",
            "default_business_category_code": "finance.expense.project",
        },
        "domain_tokens": ["business_category_id.code", "finance.expense.project"],
        "new_record_tokens": ["business_category_id.code", "finance.expense.project"],
    },
    "finance.deposit.bid.pay": {
        "label": "投标保证金缴纳",
        "model": "sc.expense.claim",
        "action": "action_sc_bid_deposit_pay",
        "menus": ["menu_sc_bid_deposit_pay"],
        "context": {
            "default_claim_type": "deposit_pay",
            "default_guarantee_type": "bid",
            "default_expense_type": "投标保证金缴纳",
            "default_business_category_code": "finance.deposit.bid.pay",
        },
        "domain_tokens": ["business_category_id.code", "finance.deposit.bid.pay"],
        "new_record_tokens": ["business_category_id.code", "finance.deposit.bid.pay"],
    },
    "finance.deposit.bid.return": {
        "label": "投标保证金退回",
        "model": "sc.expense.claim",
        "action": "action_sc_bid_deposit_return",
        "menus": ["menu_sc_bid_deposit_return"],
        "context": {
            "default_claim_type": "deposit_refund",
            "default_guarantee_type": "bid",
            "default_expense_type": "投标保证金退回",
            "default_business_category_code": "finance.deposit.bid.return",
        },
        "domain_tokens": ["business_category_id.code", "finance.deposit.bid.return"],
        "new_record_tokens": ["business_category_id.code", "finance.deposit.bid.return"],
    },
    "finance.deposit.contract.pay": {
        "label": "合同保证金登记",
        "model": "sc.expense.claim",
        "action": "action_sc_contract_deposit_pay",
        "menus": ["menu_sc_contract_deposit_register"],
        "context": {
            "default_claim_type": "deposit_pay",
            "default_guarantee_type": "contract",
            "default_expense_type": "合同保证金登记",
            "default_business_category_code": "finance.deposit.contract.pay",
        },
        "domain_tokens": ["business_category_id.code", "finance.deposit.contract.pay"],
        "new_record_tokens": ["business_category_id.code", "finance.deposit.contract.pay"],
    },
    "finance.deposit.contract.return": {
        "label": "合同保证金退回",
        "model": "sc.expense.claim",
        "action": "action_sc_contract_deposit_return",
        "menus": ["menu_sc_contract_deposit_return"],
        "context": {
            "default_claim_type": "deposit_refund",
            "default_guarantee_type": "contract",
            "default_expense_type": "合同保证金退回",
            "default_business_category_code": "finance.deposit.contract.return",
        },
        "domain_tokens": ["business_category_id.code", "finance.deposit.contract.return"],
        "new_record_tokens": ["business_category_id.code", "finance.deposit.contract.return"],
    },
    "finance.deduction.bill": {
        "label": "扣款单",
        "model": "sc.expense.claim",
        "action": "action_sc_expense_claim_deduction_bill",
        "menus": ["menu_sc_deduction_bill"],
        "context": {
            "default_claim_type": "expense",
            "default_expense_type": "扣款单",
            "default_summary": "扣款单",
            "default_business_category_code": "finance.deduction.bill",
        },
        "domain_tokens": ["business_category_id.code", "finance.deduction.bill"],
        "new_record_tokens": ["business_category_id.code", "finance.deduction.bill"],
    },
    "finance.deduction.paid": {
        "label": "扣款实缴登记",
        "model": "sc.expense.claim",
        "action": "action_sc_expense_claim_deduction_paid",
        "menus": ["menu_sc_deduction_paid"],
        "context": {
            "default_claim_type": "expense",
            "default_expense_type": "扣款实缴登记",
            "default_summary": "扣款实缴登记",
            "default_business_category_code": "finance.deduction.paid",
        },
        "domain_tokens": ["business_category_id.code", "finance.deduction.paid"],
        "new_record_tokens": ["business_category_id.code", "finance.deduction.paid"],
    },
    "finance.deduction.refund": {
        "label": "扣款实缴退回",
        "model": "sc.expense.claim",
        "action": "action_sc_expense_claim_deduction_paid_refund",
        "menus": ["menu_sc_deduction_paid_refund"],
        "context": {
            "default_claim_type": "deduction_refund",
            "default_expense_type": "扣款实缴退回",
            "default_summary": "扣款实缴退回",
            "default_business_category_code": "finance.deduction.refund",
        },
        "domain_tokens": ["business_category_id.code", "finance.deduction.refund"],
        "new_record_tokens": ["business_category_id.code", "finance.deduction.refund"],
    },
    "finance.fund.transfer": {
        "label": "账户间资金往来",
        "model": "sc.fund.account.operation",
        "action": "action_sc_fund_account_between_user",
        "menus": ["menu_sc_fund_account_between_user"],
        "context": {
            "default_operation_type": "transfer_between",
            "default_operation_reason": "账户间资金往来",
            "default_business_category_code": "finance.fund.transfer",
        },
        "domain_tokens": ["operation_type", "transfer_between", "business_category_id.code", "finance.fund.transfer"],
        "new_record_tokens": ["business_category_id.code", "finance.fund.transfer"],
    },
    "finance.fund.daily_report": {
        "label": "资金日报表",
        "model": "sc.fund.account.operation",
        "action": "action_sc_fund_daily_user_report",
        "menus": ["menu_sc_fund_daily_user_report"],
        "context": {
            "default_operation_type": "fund_daily_report",
            "default_operation_reason": "资金日报表",
            "default_business_category_code": "finance.fund.daily_report",
        },
        "domain_tokens": ["business_category_id.code", "finance.fund.daily_report"],
        "forbidden_domain_tokens": ["operation_type"],
        "new_record_tokens": ["business_category_id.code", "finance.fund.daily_report"],
    },
    "finance.fund.balance_adjustment": {
        "label": "余额调整",
        "model": "sc.fund.account.operation",
        "action": "action_sc_fund_balance_adjustment",
        "menus": ["menu_sc_fund_balance_adjustment"],
        "context": {
            "default_operation_type": "balance_adjustment",
            "default_business_category_code": "finance.fund.balance_adjustment",
        },
        "domain_tokens": ["business_category_id.code", "finance.fund.balance_adjustment"],
        "forbidden_domain_tokens": ["operation_type"],
        "new_record_tokens": ["business_category_id.code", "finance.fund.balance_adjustment"],
    },
    "finance.loan.borrowing": {
        "label": "借款申请",
        "model": "sc.financing.loan",
        "action": "action_sc_financing_loan_borrowing_request",
        "menus": ["menu_sc_borrowing_request"],
        "context": {
            "default_loan_type": "borrowing_request",
            "default_direction": "borrowed_fund",
            "default_business_category_code": "finance.loan.borrowing",
        },
        "domain_tokens": ["loan_type", "borrowing_request", "business_category_id.code", "finance.loan.borrowing"],
        "new_record_tokens": ["business_category_id.code", "finance.loan.borrowing"],
    },
    "finance.loan.contractor_project_borrow": {
        "label": "承包人借项目款",
        "model": "sc.financing.loan",
        "action": "action_sc_financing_loan_contractor_project_borrow",
        "menus": ["menu_sc_contractor_project_borrow"],
        "context": {
            "default_loan_type": "borrowing_request",
            "default_direction": "borrowed_fund",
            "default_business_category_code": "finance.loan.contractor_project_borrow",
            "default_purpose": "承包人借项目款",
        },
        "domain_tokens": ["loan_type", "borrowing_request", "business_category_id.code", "finance.loan.contractor_project_borrow"],
        "new_record_tokens": ["business_category_id.code", "finance.loan.contractor_project_borrow"],
    },
    "finance.loan.project_borrow_company": {
        "label": "项目借公司款登记",
        "model": "sc.financing.loan",
        "action": "action_sc_financing_loan_project_borrow_company",
        "menus": ["menu_sc_project_borrow_company"],
        "context": {
            "default_loan_type": "borrowing_request",
            "default_direction": "borrowed_fund",
            "default_business_category_code": "finance.loan.project_borrow_company",
            "default_purpose": "项目借公司款登记",
        },
        "domain_tokens": ["loan_type", "borrowing_request", "business_category_id.code", "finance.loan.project_borrow_company"],
        "new_record_tokens": ["business_category_id.code", "finance.loan.project_borrow_company"],
    },
    "finance.self_funding.income": {
        "label": "自筹垫付办理",
        "model": "sc.self.funding.registration",
        "action": "action_sc_self_funding_registration_income",
        "menus": ["menu_sc_self_funding_advance_income"],
        "context": {
            "default_funding_type": "income",
            "default_business_category_code": "finance.self_funding.income",
        },
        "domain_tokens": ["business_category_id.code", "finance.self_funding.income"],
        "forbidden_domain_tokens": ["funding_type"],
        "new_record_tokens": ["business_category_id.code", "finance.self_funding.income"],
    },
    "finance.self_funding.refund": {
        "label": "自筹退回办理",
        "model": "sc.self.funding.registration",
        "action": "action_sc_self_funding_registration_refund",
        "menus": ["menu_sc_self_funding_advance_refund"],
        "context": {
            "default_funding_type": "refund",
            "default_business_category_code": "finance.self_funding.refund",
        },
        "domain_tokens": ["business_category_id.code", "finance.self_funding.refund"],
        "forbidden_domain_tokens": ["funding_type"],
        "new_record_tokens": ["business_category_id.code", "finance.self_funding.refund"],
    },
    "finance.repayment.registration": {
        "label": "还款登记",
        "model": "sc.expense.claim",
        "action": "action_sc_expense_claim_repayment_registration",
        "menus": ["menu_sc_repayment_registration"],
        "context": {
            "default_claim_type": "project_company_repay",
            "default_expense_type": "还款登记",
            "default_summary": "还款登记",
            "default_business_category_code": "finance.repayment.registration",
        },
        "domain_tokens": ["business_category_id.code", "finance.repayment.registration"],
        "new_record_tokens": ["business_category_id.code", "finance.repayment.registration"],
    },
    "finance.repayment.contractor_project": {
        "label": "承包人还项目款",
        "model": "sc.expense.claim",
        "action": "action_sc_expense_claim_contractor_project_repay",
        "menus": ["menu_sc_contractor_project_repay"],
        "context": {
            "default_claim_type": "deposit_receive",
            "default_expense_type": "承包人还项目款",
            "default_summary": "承包人还项目款",
            "default_business_category_code": "finance.repayment.contractor_project",
        },
        "domain_tokens": ["business_category_id.code", "finance.repayment.contractor_project"],
        "new_record_tokens": ["business_category_id.code", "finance.repayment.contractor_project"],
    },
    "finance.repayment.project_company": {
        "label": "项目还公司款登记",
        "model": "sc.expense.claim",
        "action": "action_sc_expense_claim_project_repay_company",
        "menus": ["menu_sc_project_repay_company"],
        "context": {
            "default_claim_type": "project_company_repay",
            "default_expense_type": "项目还公司款登记",
            "default_summary": "项目还公司款登记",
            "default_business_category_code": "finance.repayment.project_company",
        },
        "domain_tokens": ["business_category_id.code", "finance.repayment.project_company"],
        "new_record_tokens": ["business_category_id.code", "finance.repayment.project_company"],
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


def _collect_records() -> tuple[dict[str, ET.Element], dict[str, dict[str, str]]]:
    records: dict[str, ET.Element] = {}
    menus: dict[str, dict[str, str]] = {}
    for target in TARGETS:
        tree = ET.parse(target)
        root = tree.getroot()
        for node in root.findall(".//record"):
            xmlid = node.attrib.get("id")
            if not xmlid:
                continue
            existing = records.get(xmlid)
            if existing is not None and node.attrib.get("model") == existing.attrib.get("model"):
                for field in node.findall("field"):
                    name = field.attrib.get("name")
                    if not name:
                        continue
                    for old_field in list(existing.findall("field")):
                        if old_field.attrib.get("name") == name:
                            existing.remove(old_field)
                    existing.append(field)
            else:
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
    return records, menus


def main() -> int:
    records, menus = _collect_records()
    failures: list[str] = []
    rows: list[dict] = []

    for code, expected in CATEGORY_ACTIONS.items():
        action_id = expected["action"]
        record = records.get(action_id)
        if record is None:
            failures.append(f"{code}: missing action {action_id}")
            continue

        name = _field_text(record, "name")
        model = _field_text(record, "res_model")
        context = _parse_context(_field_text(record, "context"))
        domain = _field_text(record, "domain")
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
        for token in expected.get("forbidden_domain_tokens", []):
            if token in domain:
                failures.append(f"{code}: domain still contains fallback token {token!r}")
        for token in expected["new_record_tokens"]:
            if token not in domain:
                failures.append(f"{code}: domain does not cover new-record token {token!r}")
        for menu_id in expected["menus"]:
            menu = menus.get(menu_id)
            if not menu:
                failures.append(f"{code}: missing menu {menu_id}")
                continue
            menu_action = menu.get("action")
            expected_action_ref = f"smart_construction_core.{action_id}"
            if menu_action not in {expected_action_ref, action_id}:
                failures.append(
                    f"{code}: menu {menu_id} expected action {expected_action_ref!r} or {action_id!r}, "
                    f"got {menu_action!r}"
                )
        rows.append(
            {
                "code": code,
                "label": name,
                "model": model,
                "action": action_id,
                "menus": expected["menus"],
            }
        )

    result = {
        "audit": "finance_business_category_action_audit",
        "targets": [str(target.relative_to(ROOT)) for target in TARGETS],
        "status": "PASS" if not failures else "FAIL",
        "category_count": len(CATEGORY_ACTIONS),
        "rows": rows,
        "failures": failures,
    }
    print("FINANCE_BUSINESS_CATEGORY_ACTION_AUDIT: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
