# -*- coding: utf-8 -*-
from __future__ import annotations

from copy import deepcopy
from typing import Any


FINANCE_HANDLING_GROUPS: tuple[dict[str, Any], ...] = (
    {
        "key": "receipt_payment",
        "title": "收付款办理",
        "menu_xmlid": "smart_construction_core.menu_sc_receipt_payment_group",
        "description": "把收款、付款申请、实付登记和到款确认收敛到一个办理入口。",
        "default_group_by": "business_category_id",
        "items": (
            ("finance.receipt.income.project", "项目收款", "smart_construction_core.action_sc_receipt_income_user_income"),
            ("finance.receipt.income.progress", "工程进度收款", "smart_construction_core.action_sc_receipt_income_engineering_progress"),
            ("finance.payment.apply.receive", "收款申请", "smart_construction_core.action_payment_request_receive"),
            ("finance.payment.apply.pay", "付款申请", "smart_construction_core.action_payment_request_user_payment_apply"),
            ("finance.payment.execution.partner", "往来单位付款", "smart_construction_core.action_sc_payment_execution_partner_payment"),
            ("finance.payment.execution.company", "公司财务支出", "smart_construction_core.action_sc_payment_execution_company_finance_expense"),
            ("finance.responsibility.arrival_confirmation", "到款确认", "smart_construction_core.action_sc_company_contractor_responsibility_fact"),
        ),
    },
    {
        "key": "invoice_tax",
        "title": "开票与税务办理",
        "menu_xmlid": "smart_construction_core.menu_sc_invoice_tax_user_group",
        "description": "把销项开票、进项上报、预缴税和抵扣登记收敛到一个税票入口。",
        "default_group_by": "business_category_id",
        "items": (
            ("invoice.output.application", "销项开票申请", "smart_construction_core.action_sc_invoice_application_user"),
            ("invoice.output.registration", "销项开票登记", "smart_construction_core.action_sc_invoice_registration_user"),
            ("invoice.prepaid_tax", "预缴税款", "smart_construction_core.action_sc_invoice_prepaid_tax_user"),
            ("invoice.input.report", "进项税额上报", "smart_construction_core.action_sc_invoice_input_report_user"),
            ("tax.deduction.registration", "抵扣登记", "smart_construction_core.action_sc_tax_deduction_registration_user"),
            ("tax.certificate.registration", "外经证登记", "smart_construction_core.action_sc_tax_certificate_registration_user"),
        ),
    },
    {
        "key": "expense_reimbursement",
        "title": "费用与报销办理",
        "menu_xmlid": "smart_construction_core.menu_sc_expense_reimbursement_group",
        "description": "把报销、项目费用、扣款和保证金收敛到一个费用办理入口。",
        "default_group_by": "business_category_id",
        "items": (
            ("finance.expense.reimbursement", "报销申请", "smart_construction_core.action_sc_expense_claim_reimbursement_request"),
            ("finance.expense.project", "项目费用报销", "smart_construction_core.action_sc_expense_claim_project"),
            ("finance.deduction.bill", "扣款单", "smart_construction_core.action_sc_expense_claim_deduction_bill"),
            ("finance.deduction.paid", "扣款实缴登记", "smart_construction_core.action_sc_expense_claim_deduction_paid"),
            ("finance.deduction.refund", "扣款实缴退回", "smart_construction_core.action_sc_expense_claim_deduction_paid_refund"),
            ("finance.deposit.bid.pay", "投标保证金支付", "smart_construction_core.action_sc_bid_deposit_pay"),
            ("finance.deposit.bid.return", "投标保证金退回", "smart_construction_core.action_sc_bid_deposit_return"),
            ("finance.deposit.contract.pay", "合同保证金登记", "smart_construction_core.action_sc_contract_deposit_pay"),
            ("finance.deposit.contract.return", "合同保证金退回", "smart_construction_core.action_sc_contract_deposit_return"),
        ),
    },
    {
        "key": "fund_account",
        "title": "资金往来办理",
        "menu_xmlid": "smart_construction_core.menu_sc_fund_account_group",
        "description": "把借还款、项目往来、自筹、账户调拨和资金日报收敛到一个资金往来入口。",
        "default_group_by": "business_category_id",
        "items": (
            ("finance.loan.borrowing", "借款申请", "smart_construction_core.action_sc_financing_loan_borrowing_request"),
            ("finance.repayment.registration", "还款登记", "smart_construction_core.action_sc_expense_claim_repayment_registration"),
            ("finance.repayment.contractor_project", "承包人还项目款", "smart_construction_core.action_sc_expense_claim_contractor_project_repay"),
            ("finance.loan.contractor_project_borrow", "承包人借项目款", "smart_construction_core.action_sc_financing_loan_contractor_project_borrow"),
            ("finance.loan.project_borrow_company", "项目借公司款", "smart_construction_core.action_sc_financing_loan_project_borrow_company"),
            ("finance.repayment.project_company", "项目还公司款", "smart_construction_core.action_sc_expense_claim_project_repay_company"),
            ("finance.self_funding.income", "自筹垫付", "smart_construction_core.action_sc_self_funding_registration_income"),
            ("finance.self_funding.refund", "自筹退回", "smart_construction_core.action_sc_self_funding_registration_refund"),
            ("finance.fund.transfer", "账户间资金往来", "smart_construction_core.action_sc_fund_account_between_user"),
            ("finance.fund.transfer", "资金划拨", "smart_construction_core.action_sc_fund_transfer_out"),
            ("finance.fund.transfer", "资金调拨", "smart_construction_core.action_sc_fund_transfer_between"),
            ("finance.fund.balance_adjustment", "余额调整", "smart_construction_core.action_sc_fund_balance_adjustment"),
            ("finance.fund.daily_report", "资金日报表", "smart_construction_core.action_sc_fund_daily_user_report"),
        ),
    },
)

CANONICAL_CATEGORY_ACTION_XMLIDS = {
    "finance.fund.transfer": "smart_construction_core.action_sc_fund_account_between_user",
}


def _entry_payload(group: dict[str, Any], index: int, row: tuple[str, str, str]) -> dict[str, Any]:
    category_code, label, action_xmlid = row
    category_action_xmlid = CANONICAL_CATEGORY_ACTION_XMLIDS.get(category_code, action_xmlid)
    return {
        "key": f"{group['key']}.{index + 1}",
        "label": label,
        "business_category_code": category_code,
        "category_action_xmlid": category_action_xmlid,
        "action_xmlid": action_xmlid,
        "target": {
            "type": "action",
            "action_xmlid": action_xmlid,
            "category_action_xmlid": category_action_xmlid,
            "business_category_code": category_code,
        },
        "preserved_user_recognition": True,
    }


def build_finance_handling_entry_catalog() -> dict[str, Any]:
    groups = []
    for sequence, group in enumerate(FINANCE_HANDLING_GROUPS, start=1):
        item_rows = tuple(group.get("items") or ())
        groups.append(
            {
                "key": group["key"],
                "title": group["title"],
                "menu_xmlid": group["menu_xmlid"],
                "sequence": sequence * 10,
                "description": group["description"],
                "entry_mode": "integrated_handling",
                "default_group_by": group["default_group_by"],
                "items": [_entry_payload(group, index, row) for index, row in enumerate(item_rows)],
            }
        )
    return {
        "contract_version": "handling_entry_catalog.v1",
        "domain": "finance",
        "entry_mode": "integrated_handling",
        "source_authority": "sc.business.category",
        "groups": groups,
        "group_count": len(groups),
        "item_count": sum(len(group["items"]) for group in groups),
        "preserve_data_policy": {
            "delete_business_records": False,
            "delete_actions": False,
            "delete_business_categories": False,
            "legacy_recognition_carrier": "business_category_code",
        },
    }


def clone_finance_handling_entry_catalog() -> dict[str, Any]:
    return deepcopy(build_finance_handling_entry_catalog())
