# -*- coding: utf-8 -*-
"""Audit interfund handling entries and form semantics.

Run inside ``odoo shell``.  The audit is read-only: it verifies that formal
handling actions still route to the intended models and that the forms expose
business-facing direction fields instead of only generic technical fields.
"""

from __future__ import annotations

import ast
import json
import os
from collections import OrderedDict
from pathlib import Path


MODULE = "smart_construction_core"
EXPECTED_ACTIONS = OrderedDict(
    [
        (
            f"{MODULE}.action_sc_fund_account_between_user",
            {
                "name": "账户间资金往来",
                "model": "sc.fund.account.operation",
                "context": {
                    "default_operation_type": "transfer_between",
                    "default_operation_reason": "账户间资金往来",
                },
            },
        ),
        (
            f"{MODULE}.action_sc_financing_loan_contractor_project_borrow",
            {
                "name": "承包人借项目款",
                "model": "sc.financing.loan",
                "context": {
                    "default_loan_type": "borrowing_request",
                    "default_direction": "borrowed_fund",
                    "default_purpose": "承包人借项目款",
                },
            },
        ),
        (
            f"{MODULE}.action_sc_financing_loan_project_borrow_company",
            {
                "name": "项目借公司款登记",
                "model": "sc.financing.loan",
                "context": {
                    "default_loan_type": "borrowing_request",
                    "default_direction": "borrowed_fund",
                    "default_purpose": "项目借公司款登记",
                },
            },
        ),
        (
            f"{MODULE}.action_sc_expense_claim_contractor_project_repay",
            {
                "name": "承包人还项目款",
                "model": "sc.expense.claim",
                "context": {
                    "default_claim_type": "deposit_receive",
                    "default_expense_type": "承包人还项目款",
                    "default_summary": "承包人还项目款",
                },
            },
        ),
        (
            f"{MODULE}.action_sc_expense_claim_project_repay_company",
            {
                "name": "项目还公司款登记",
                "model": "sc.expense.claim",
                "context": {
                    "default_claim_type": "project_company_repay",
                    "default_expense_type": "项目还公司款登记",
                    "default_summary": "项目还公司款登记",
                },
            },
        ),
        (
            f"{MODULE}.action_sc_expense_claim_deduction_bill",
            {
                "name": "扣款登记",
                "model": "sc.expense.claim",
                "context": {
                    "default_claim_type": "expense",
                    "default_expense_type": "扣款登记",
                    "default_summary": "扣款登记",
                },
            },
        ),
        (
            f"{MODULE}.action_sc_expense_claim_deduction_paid",
            {
                "name": "扣款实缴登记",
                "model": "sc.expense.claim",
                "context": {
                    "default_claim_type": "expense",
                    "default_expense_type": "扣款实缴登记",
                    "default_summary": "扣款实缴登记",
                },
            },
        ),
        (
            f"{MODULE}.action_sc_expense_claim_deduction_paid_refund",
            {
                "name": "扣款实缴退回",
                "model": "sc.expense.claim",
                "context": {
                    "default_claim_type": "deduction_refund",
                    "default_expense_type": "扣款实缴退回",
                    "default_summary": "扣款实缴退回",
                },
            },
        ),
        (
            f"{MODULE}.action_sc_expense_claim_deposit",
            {
                "name": "保证金管理",
                "model": "sc.expense.claim",
                "context": {
                    "default_claim_type": "deposit_pay",
                },
            },
        ),
        (
            f"{MODULE}.action_payment_request_user_payment_apply",
            {
                "name": "支付申请",
                "model": "payment.request",
                "context": {
                    "default_type": "pay",
                },
            },
        ),
        (
            f"{MODULE}.action_sc_payment_execution_company_finance_expense",
            {
                "name": "公司财务支出",
                "model": "sc.payment.execution",
                "context": {
                    "default_source_kind": "actual_outflow",
                    "default_payment_family": "公司财务支出",
                },
            },
        ),
        (
            f"{MODULE}.action_sc_payment_execution_partner_payment",
            {
                "name": "往来单位付款",
                "model": "sc.payment.execution",
                "context": {
                    "default_source_kind": "actual_outflow",
                    "default_payment_family": "往来单位付款",
                },
            },
        ),
        (
            f"{MODULE}.action_sc_receipt_income_user_income",
            {
                "name": "收入",
                "model": "sc.receipt.income",
                "context": {
                    "default_source_kind": "receipt_income",
                    "default_income_category": "收入",
                },
            },
        ),
        (
            f"{MODULE}.action_sc_receipt_income_engineering_progress",
            {
                "name": "工程进度款收入登记",
                "model": "sc.receipt.income",
                "context": {
                    "default_source_kind": "receipt_income",
                    "default_receipt_type": "正常类型收款",
                    "default_income_category": "工程进度款收入",
                },
            },
        ),
        (
            f"{MODULE}.action_sc_invoice_application_user",
            {
                "name": "销项开票申请",
                "model": "sc.invoice.registration",
                "context": {
                    "default_source_kind": "output_invoice_tax",
                    "default_direction": "output",
                    "default_invoice_content": "销项开票申请",
                },
            },
        ),
        (
            f"{MODULE}.action_sc_invoice_input_report_user",
            {
                "name": "进项发票",
                "model": "sc.invoice.registration",
                "context": {
                    "default_source_kind": "input_invoice_tax",
                    "default_direction": "input",
                    "default_invoice_content": "进项税额上报",
                },
            },
        ),
        (
            f"{MODULE}.action_sc_invoice_prepaid_tax_user",
            {
                "name": "预缴税款",
                "model": "sc.invoice.registration",
                "context": {
                    "default_source_kind": "prepaid_tax",
                    "default_direction": "prepaid",
                    "default_invoice_content": "预缴税款",
                },
            },
        ),
        (
            f"{MODULE}.action_sc_tax_deduction_registration_user",
            {
                "name": "抵扣登记",
                "model": "sc.tax.deduction.registration",
                "context": {
                    "search_default_group_project": 1,
                },
            },
        ),
        (
            f"{MODULE}.action_sc_settlement_order_income",
            {
                "name": "收入合同结算",
                "model": "sc.settlement.order",
                "context": {
                    "default_settlement_type": "in",
                },
            },
        ),
        (
            f"{MODULE}.action_sc_settlement_order_expense",
            {
                "name": "支出合同结算",
                "model": "sc.settlement.order",
                "context": {
                    "default_settlement_type": "out",
                },
            },
        ),
        (
            f"{MODULE}.action_project_cost_ledger",
            {
                "name": "成本归集台账",
                "model": "project.cost.ledger",
                "context": {},
            },
        ),
    ]
)

EXPECTED_MODEL_FIELDS = OrderedDict(
    [
        (
            "sc.fund.account.operation",
            {
                "fields": {"fund_flow_label", "source_project_id", "target_project_id"},
                "trace_fields": {"state", "attachment_ids"},
                "workflow_methods": {"action_confirm", "action_done", "action_cancel"},
                "views": [
                    f"{MODULE}.view_sc_fund_account_operation_tree",
                    f"{MODULE}.view_sc_fund_account_operation_form",
                ],
                "tokens": {"账户资金办理", "办理说明"},
            },
        ),
        (
            "sc.financing.loan",
            {
                "fields": {"loan_flow_label"},
                "trace_fields": {"state", "attachment_ids"},
                "workflow_methods": {"action_confirm", "action_done", "action_cancel"},
                "views": [
                    f"{MODULE}.view_sc_financing_loan_tree",
                    f"{MODULE}.view_sc_financing_loan_form",
                ],
                "tokens": {"借款办理", "办理说明"},
            },
        ),
        (
            "sc.expense.claim",
            {
                "fields": {"claim_flow_label"},
                "trace_fields": {"state", "attachment_ids"},
                "workflow_methods": {"action_submit", "action_approve", "action_done", "action_cancel"},
                "views": [
                    f"{MODULE}.view_sc_expense_claim_tree",
                    f"{MODULE}.view_sc_expense_claim_form",
                ],
                "tokens": {"费用、保证金与还款办理", "业务方向", "项目与往来单位", "付款账户", "事项说明"},
            },
        ),
        (
            "payment.request",
            {
                "fields": {"payment_flow_label"},
                "trace_fields": {"state", "attachment_ids"},
                "workflow_methods": {"action_submit", "action_approve", "action_done", "action_cancel"},
                "views": [
                    f"{MODULE}.view_payment_request_tree",
                    f"{MODULE}.view_payment_request_form",
                ],
                "tokens": {"付款与收款申请办理", "往来单位", "申请金额"},
            },
        ),
        (
            "sc.payment.execution",
            {
                "fields": {"execution_flow_label"},
                "trace_fields": {"state", "attachment_ids"},
                "workflow_methods": {"action_confirm", "action_paid", "action_cancel"},
                "views": [
                    f"{MODULE}.view_sc_payment_execution_tree",
                    f"{MODULE}.view_sc_payment_execution_form",
                ],
                "tokens": {"付款登记办理", "付款账户", "收款账户", "付款金额"},
            },
        ),
        (
            "sc.receipt.income",
            {
                "fields": {"receipt_flow_label"},
                "trace_fields": {"state", "attachment_ids"},
                "workflow_methods": {"action_confirm", "action_received", "action_cancel"},
                "views": [
                    f"{MODULE}.view_sc_receipt_income_tree",
                    f"{MODULE}.view_sc_receipt_income_form",
                ],
                "tokens": {"收款与收入办理", "业务方向", "项目与往来单位", "收款账户", "收款金额", "办理说明"},
            },
        ),
        (
            "sc.invoice.registration",
            {
                "fields": {"invoice_flow_label"},
                "trace_fields": {"state", "attachment_ids"},
                "workflow_methods": {"action_confirm", "action_register", "action_cancel"},
                "views": [
                    f"{MODULE}.view_sc_invoice_registration_tree",
                    f"{MODULE}.view_sc_invoice_registration_form",
                ],
                "tokens": {"发票税务办理", "业务方向", "项目与往来单位", "发票与税务信息", "发票金额与税额", "办理说明"},
            },
        ),
        (
            "sc.tax.deduction.registration",
            {
                "fields": {"deduction_flow_label"},
                "trace_fields": {"state", "attachment_ids"},
                "workflow_methods": {"action_confirm", "action_deduct", "action_cancel"},
                "views": [
                    f"{MODULE}.view_sc_tax_deduction_registration_tree",
                    f"{MODULE}.view_sc_tax_deduction_registration_form",
                ],
                "tokens": {"抵扣税务办理", "业务方向", "项目与往来单位", "发票信息", "抵扣金额与税额", "办理说明"},
            },
        ),
        (
            "sc.settlement.order",
            {
                "fields": {"settlement_flow_label"},
                "trace_fields": {"state", "attachment_ids", "attachment_count"},
                "workflow_methods": {"action_submit", "action_approve", "action_done", "action_cancel"},
                "views": [
                    f"{MODULE}.view_sc_settlement_order_tree",
                    f"{MODULE}.view_sc_settlement_order_form",
                ],
                "tokens": {"合同结算办理", "项目与合同", "结算金额", "办理说明"},
            },
        ),
        (
            "project.cost.ledger",
            {
                "fields": {"cost_flow_label"},
                "trace_fields": set(),
                "workflow_methods": set(),
                "views": [
                    f"{MODULE}.view_project_cost_ledger_tree",
                    f"{MODULE}.view_project_cost_ledger_form",
                ],
                "tokens": {"成本归集台账", "成本归集", "项目与成本科目", "发生金额", "来源追溯", "办理说明"},
            },
        ),
    ]
)


def artifact_root() -> Path:
    raw = os.getenv("MIGRATION_ARTIFACT_ROOT") or os.getenv("FINANCE_INTERFUND_HANDLING_ARTIFACT_ROOT")
    candidates = [Path(raw)] if raw else []
    candidates.extend([Path("/mnt/artifacts/backend"), Path(f"/tmp/finance_interfund_handling/{env.cr.dbname}")])  # noqa: F821
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return candidate
        except OSError:
            continue
    return Path("/tmp")


def ref_or_error(xmlid, errors, key):
    try:
        return env.ref(xmlid)  # noqa: F821
    except ValueError:
        errors.append({"key": key, "xmlid": xmlid})
        return None


def parse_context(raw):
    if not raw:
        return {}
    try:
        parsed = ast.literal_eval(raw)
    except (SyntaxError, ValueError):
        return {"__parse_error__": raw}
    return parsed if isinstance(parsed, dict) else {"__invalid_context__": raw}


def _action_default_fields(model, context):
    return sorted(
        key.removeprefix("default_")
        for key in context
        if key.startswith("default_") and key.removeprefix("default_") in model._fields
    )


def _audit_action_default_get(xmlid, model_name, context, expected_context):
    model = env[model_name]  # noqa: F821
    field_names = _action_default_fields(model, expected_context)
    defaults = model.with_context(**context).default_get(field_names) if field_names else {}
    mismatches = []
    for context_key, expected_value in expected_context.items():
        if not context_key.startswith("default_"):
            continue
        field_name = context_key.removeprefix("default_")
        if field_name not in model._fields:
            mismatches.append(
                {
                    "field": field_name,
                    "expected": expected_value,
                    "actual": None,
                    "reason": "missing_model_field",
                }
            )
            continue
        actual_value = defaults.get(field_name)
        if actual_value != expected_value:
            mismatches.append(
                {
                    "field": field_name,
                    "expected": expected_value,
                    "actual": actual_value,
                    "reason": "default_get_mismatch",
                }
            )
    if mismatches:
        errors.append({"key": "handling_action_default_get_drift", "xmlid": xmlid, "mismatches": mismatches})
    return OrderedDict(
        [
            ("requested_fields", field_names),
            ("defaults", {field_name: defaults.get(field_name) for field_name in field_names}),
            ("mismatches", mismatches),
        ]
    )


errors = []
summary = OrderedDict()

action_rows = []
for xmlid, spec in EXPECTED_ACTIONS.items():
    action = ref_or_error(xmlid, errors, "missing_handling_action")
    row = OrderedDict([("xmlid", xmlid), ("expected_name", spec["name"]), ("expected_model", spec["model"])])
    if action:
        context = parse_context(action.context)
        row.update(
            [
                ("actual_name", action.name),
                ("actual_model", action.res_model),
                ("context", context),
            ]
        )
        if action.name != spec["name"]:
            errors.append({"key": "handling_action_wrong_name", "xmlid": xmlid, "expected": spec["name"], "actual": action.name})
        if action.res_model != spec["model"]:
            errors.append({"key": "handling_action_wrong_model", "xmlid": xmlid, "expected": spec["model"], "actual": action.res_model})
        for key, expected_value in spec["context"].items():
            if context.get(key) != expected_value:
                errors.append(
                    {
                        "key": "handling_action_context_drift",
                        "xmlid": xmlid,
                        "context_key": key,
                        "expected": expected_value,
                        "actual": context.get(key),
                    }
                )
        if "__parse_error__" not in context and "__invalid_context__" not in context and action.res_model == spec["model"]:
            row["default_get"] = _audit_action_default_get(xmlid, action.res_model, context, spec["context"])
    action_rows.append(row)
summary["actions"] = action_rows

model_rows = []
for model_name, spec in EXPECTED_MODEL_FIELDS.items():
    model = env[model_name]  # noqa: F821
    fields_missing = sorted(field_name for field_name in spec["fields"] if field_name not in model._fields)
    trace_fields = set(spec.get("trace_fields", set()))
    workflow_methods = set(spec.get("workflow_methods", set()))
    trace_fields_missing = sorted(field_name for field_name in trace_fields if field_name not in model._fields)
    workflow_methods_missing = sorted(method_name for method_name in workflow_methods if not hasattr(model, method_name))
    row = OrderedDict(
        [
            ("model", model_name),
            ("required_fields", sorted(spec["fields"])),
            ("missing_fields", fields_missing),
            ("trace_fields", sorted(trace_fields)),
            ("missing_trace_fields", trace_fields_missing),
            ("workflow_methods", sorted(workflow_methods)),
            ("missing_workflow_methods", workflow_methods_missing),
        ]
    )
    if fields_missing:
        errors.append({"key": "handling_model_missing_fields", "model": model_name, "missing_fields": fields_missing})
    if trace_fields_missing:
        errors.append({"key": "handling_model_missing_trace_fields", "model": model_name, "missing_fields": trace_fields_missing})
    if workflow_methods_missing:
        errors.append({"key": "handling_model_missing_workflow_methods", "model": model_name, "missing_methods": workflow_methods_missing})
    view_rows = []
    combined_arch = ""
    for view_xmlid in spec["views"]:
        view = ref_or_error(view_xmlid, errors, "missing_handling_view")
        view_row = OrderedDict([("xmlid", view_xmlid)])
        if view:
            arch = view.arch_db or ""
            combined_arch += "\n" + arch
            missing_field_refs = sorted(field_name for field_name in spec["fields"] if f'name="{field_name}"' not in arch)
            view_row.update(
                [
                    ("name", view.name),
                    ("missing_field_refs", missing_field_refs),
                ]
            )
            if missing_field_refs:
                errors.append({"key": "handling_view_missing_field_refs", "view": view_xmlid, "missing_fields": missing_field_refs})
        view_rows.append(view_row)
    missing_tokens = sorted(token for token in spec["tokens"] if token not in combined_arch)
    row["missing_tokens"] = missing_tokens
    if missing_tokens:
        errors.append({"key": "handling_model_missing_business_tokens", "model": model_name, "missing_tokens": missing_tokens})
    missing_trace_field_refs = sorted(field_name for field_name in trace_fields if f'name="{field_name}"' not in combined_arch)
    row["missing_trace_field_refs"] = missing_trace_field_refs
    row["views"] = view_rows
    model_rows.append(row)
summary["models"] = model_rows

output_dir = artifact_root()
artifact = output_dir / "finance_interfund_handling_entry_audit.json"
artifact.write_text(json.dumps({"status": "PASS" if not errors else "FAIL", "errors": errors, "summary": summary}, ensure_ascii=False, indent=2), encoding="utf-8")

print(json.dumps({"status": "PASS" if not errors else "FAIL", "error_count": len(errors), "artifact": str(artifact)}, ensure_ascii=False, indent=2))
if errors:
    raise SystemExit(1)
