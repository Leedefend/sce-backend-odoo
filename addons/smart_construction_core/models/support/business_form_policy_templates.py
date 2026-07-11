# -*- coding: utf-8 -*-
"""Product-owned business form policy templates.

These templates belong to the construction product layer. They describe business
handling semantics for ``sc.business.category`` and are projected by smart_core
as generic form contracts. The frontend must not duplicate these rules.
"""

from __future__ import annotations

import copy
from typing import Iterable


CREATE_EDIT_READONLY = ["create", "edit", "readonly"]
EDIT_READONLY = ["edit", "readonly"]
READONLY_ONLY = ["readonly"]


def _section(
    name: str,
    title: str,
    fields: list[str],
    sequence: int,
    *,
    collapsed: bool = False,
    visible_profiles: Iterable[str] | None = None,
) -> dict:
    row = {
        "name": name,
        "title": title,
        "sequence": sequence,
        "fields": fields,
    }
    if collapsed:
        row.update({"collapsible": True, "collapsed_by_default": True})
    if visible_profiles:
        row["visible_profiles"] = list(visible_profiles)
    return row


def _field(
    name: str,
    *,
    visible: list[str] | None = None,
    readonly: list[str] | None = None,
    required: list[str] | None = None,
    group: str = "core",
) -> dict:
    row = {"name": name, "group": group}
    if visible:
        row["visible_profiles"] = list(visible)
    if readonly:
        row["readonly_profiles"] = list(readonly)
    if required:
        row["required_profiles"] = list(required)
    return row


def _policy(
    sections: list[dict],
    *,
    required: Iterable[str] = (),
    readonly_all: Iterable[str] = (),
    hide_create: Iterable[str] = (),
    readonly_only: Iterable[str] = (),
    trace: Iterable[str] = (),
    ledger: Iterable[str] = (),
) -> dict:
    field_names: list[str] = []
    for section in sections:
        for name in section.get("fields") or []:
            if name and name not in field_names:
                field_names.append(name)

    required_set = set(required)
    readonly_all_set = set(readonly_all)
    hide_create_set = set(hide_create)
    readonly_only_set = set(readonly_only)
    trace_set = set(trace)
    ledger_set = set(ledger)
    policies: list[dict] = []
    for name in field_names:
        group = "core"
        visible = None
        readonly = None
        required_profiles = None
        if name in required_set:
            required_profiles = ["create", "edit"]
        if name in readonly_all_set:
            readonly = CREATE_EDIT_READONLY
        if name in hide_create_set:
            visible = EDIT_READONLY
            readonly = CREATE_EDIT_READONLY
            group = "advanced"
        if name in readonly_only_set or name in trace_set or name in ledger_set:
            visible = READONLY_ONLY
            readonly = CREATE_EDIT_READONLY
            group = "source_trace" if name in trace_set else "ledger" if name in ledger_set else "advanced"
        policies.append(
            _field(
                name,
                visible=visible,
                readonly=readonly,
                required=required_profiles,
                group=group,
            )
        )
    return {"sections": sections, "fields": policies}


SYSTEM_FIELDS = ("name", "state")
SOURCE_TRACE_FIELDS = (
    "legacy_source_model",
    "legacy_source_table",
    "legacy_fact_model",
    "legacy_fact_id",
    "legacy_fact_type",
    "legacy_record_id",
    "legacy_document_state",
    "legacy_document_state_label",
    "legacy_attachment_ref",
    "creator_legacy_user_id",
    "creator_name",
    "created_time",
    "entry_user_id",
    "entry_data",
    "legacy_acceptance_label",
    "legacy_acceptance_sort_id",
    "active",
)
APPROVAL_FIELDS = (
    "validation_status",
    "can_review",
    "reject_reason",
)
MIGRATION_TRACE_FIELDS = (
    "legacy_source_model",
    "legacy_source_table",
    "legacy_record_id",
    "legacy_document_state",
    "creator_legacy_user_id",
    "creator_name",
    "created_time",
    "active",
)
FACT_TRACE_FIELDS = (
    "legacy_fact_model",
    "legacy_fact_id",
    "legacy_fact_type",
    "active",
)


def _settlement_policy(title: str, counterparty_title: str) -> dict:
    trace = (
        "legacy_fact_model",
        "legacy_fact_id",
        "legacy_fact_type",
        "entry_user_id",
        "entry_data",
        "legacy_acceptance_label",
        "legacy_acceptance_sort_id",
        "legacy_counterparty_name",
        "legacy_settlement_category",
        "legacy_document_state",
        "legacy_contract_no",
        "legacy_payment_state",
        "legacy_paid_amount",
        "legacy_unpaid_amount",
        "legacy_payment_request_state",
        "legacy_unrequested_amount",
        "legacy_visible_attachment",
        "active",
    )
    ledger = (
        "paid_amount",
        "remaining_amount",
        "amount_paid",
        "amount_payable",
        "invoice_amount",
        "adjustment_total",
        "amount_after_adjustment",
        "compliance_state",
        "compliance_message",
        "compliance_contract_ok",
    )
    return _policy(
        [
            _section("business_identity", "办理类型", ["business_category_id"], 5, visible_profiles=["create"]),
            _section("business_object", counterparty_title, ["project_id", "contract_id", "partner_id", "operation_strategy"], 10),
            _section("settlement_basis", "结算依据", ["title", "settlement_category_id", "settlement_stage_id", "document_date", "date_settlement", "settlement_period_start", "settlement_period_end"], 20),
            _section("amount", "结算明细与金额", ["line_ids", "amount_total", "settlement_amount", "submitted_amount", "approved_amount", "deduction_amount"], 30),
            _section("handling", "办理说明", ["settlement_description", "note"], 40),
            _section("system_identity", "系统办理信息", ["settlement_flow_label", "settlement_type", "state", "name"], 80, collapsed=True, visible_profiles=EDIT_READONLY),
            _section("execution", "执行与匹配", list(ledger), 90, collapsed=True),
            _section("source_trace", "历史与系统追溯", list(trace) + list(APPROVAL_FIELDS), 100, collapsed=True, visible_profiles=READONLY_ONLY),
        ],
        required=("business_category_id", "project_id", "contract_id", "partner_id", "line_ids"),
        readonly_all=("operation_strategy", "settlement_flow_label", "settlement_type") + SYSTEM_FIELDS,
        trace=trace + APPROVAL_FIELDS,
        ledger=ledger + ("amount_total", "deduction_amount"),
    )


def _payment_request_policy(title: str, counterparty_title: str) -> dict:
    approval = ("validation_status", "can_review")
    trace = (
        "legacy_source_table",
        "legacy_record_id",
        "legacy_document_state",
        "creator_legacy_user_id",
        "creator_name",
        "created_time",
        "legacy_visible_document_no",
        "legacy_visible_project_name",
        "legacy_visible_request_date",
        "legacy_visible_payee_unit",
        "legacy_visible_actual_payee_unit",
        "legacy_visible_payer_unit",
        "legacy_visible_request_amount",
        "legacy_visible_actual_paid_amount",
        "legacy_visible_available_balance",
        "legacy_visible_writer",
        "legacy_visible_attachment",
        "active",
    )
    ledger = (
        "settlement_amount_total",
        "settlement_paid_amount",
        "settlement_remaining_amount",
        "settlement_amount_payable",
        "settlement_compliance_state",
        "settlement_compliance_message",
        "paid_amount_total",
        "unpaid_amount",
        "is_fully_paid",
        "is_overpay_risk",
    )
    return _policy(
        [
            _section("business_identity", "办理类型", ["business_category_id", "payment_flow_label", "state", "name"], 10),
            _section("business_object", counterparty_title, ["project_id", "operation_strategy", "partner_id", "contract_id"], 20),
            _section(
                "basis",
                "申请依据",
                [
                    "settlement_id",
                    "payment_basis_type",
                    "line_settlement_count",
                    "line_settlement_summary",
                    "legacy_relation_count",
                    "legacy_relation_summary",
                    "material_settlement_id",
                    "cost_category_name",
                ],
                25,
            ),
            _section("amount", title, ["date_request", "amount", "amount_uppercase", "accepted_amount_uppercase", "currency_id"], 30),
            _section("receipt_account", "收款账户", ["actual_payee_unit", "payment_account_name", "payment_bank_name", "payment_account_no"], 40),
            _section("payer", "付款单位", ["payer_unit"], 45),
            _section("handling", "办理说明与附件", ["note", "attachment_ids"], 50),
            _section("detail", "申请明细", ["outflow_line_ids", "receipt_invoice_line_ids"], 60, collapsed=True),
            _section("execution", "执行与额度", list(ledger) + ["ledger_line_ids"], 70, collapsed=True),
            _section("partner_account", "往来单位默认账户", ["partner_account_name", "partner_bank_name", "partner_bank_account"], 80, collapsed=True),
            _section("source_trace", "迁移来源", list(trace) + list(approval), 90, collapsed=True, visible_profiles=("readonly",)),
        ],
        required=("business_category_id", "project_id", "partner_id", "amount"),
        readonly_all=("operation_strategy", "payment_flow_label", "type", "receipt_type", "cost_category_name") + SYSTEM_FIELDS,
        hide_create=("state", "name", "type", "receipt_type", "paid_amount_total", "unpaid_amount", "is_fully_paid"),
        readonly_only=(
            "partner_account_name",
            "partner_bank_name",
            "partner_bank_account",
            "settlement_amount_total",
            "settlement_paid_amount",
            "settlement_remaining_amount",
            "settlement_amount_payable",
            "settlement_compliance_state",
            "settlement_compliance_message",
            "line_settlement_count",
            "line_settlement_summary",
            "legacy_relation_count",
            "legacy_relation_summary",
            "payment_basis_type",
            "is_overpay_risk",
        ),
        trace=trace + approval,
        ledger=ledger,
    )


def _expense_claim_policy(title: str) -> dict:
    trace = MIGRATION_TRACE_FIELDS + (
        "legacy_document_no",
        "legacy_visible_project_name",
        "legacy_visible_document_state",
        "legacy_visible_title",
        "legacy_visible_summary",
        "legacy_visible_amount",
        "legacy_visible_date",
    )
    responsibility = (
        "company_contractor_responsibility_summary_id",
        "company_contractor_responsibility_state",
        "company_contractor_arrival_unprocessed_amount",
        "company_contractor_arrival_over_processed_amount",
        "company_contractor_self_funding_balance",
        "company_contractor_responsibility_notice",
    )
    return _policy(
        [
            _section(
                "business_identity",
                "办理类型",
                [
                    "business_category_id",
                    "business_axis",
                    "handling_kind",
                    "financial_flow",
                    "payment_anchor_policy",
                    "expense_type",
                    "claim_type",
                    "state",
                    "name",
                ],
                10,
            ),
            _section("business_object", "项目与往来单位", ["project_id", "operation_strategy", "partner_id", "payment_request_id"], 20),
            _section("amount", title, ["date_claim", "amount", "currency_id", "summary"], 30),
            _section("account", "收付款信息", ["payee", "receipt_account_name", "payee_account", "payment_account_name", "payer_account"], 40),
            _section("handling", "办理说明", ["note", "attachment_ids"], 50),
            _section("responsibility", "责任与余额", list(responsibility), 70, collapsed=True),
            _section("source_trace", "来源与系统追溯", list(trace) + list(APPROVAL_FIELDS), 90, collapsed=True),
        ],
        required=("business_category_id", "project_id", "amount"),
        readonly_all=(
            "operation_strategy",
            "business_axis",
            "handling_kind",
            "financial_flow",
            "payment_anchor_policy",
            "expense_type",
            "claim_type",
        )
        + SYSTEM_FIELDS,
        trace=trace + APPROVAL_FIELDS,
        ledger=responsibility,
    )


def _deduction_bill_policy() -> dict:
    policy = _expense_claim_policy("扣款单明细")
    sections = policy.get("sections") if isinstance(policy.get("sections"), list) else []
    kept_sections = []
    for section in sections:
        if not isinstance(section, dict):
            continue
        name = section.get("name")
        if name == "business_identity":
            section["fields"] = ["state", "name"]
            kept_sections.append(section)
            continue
        if name == "business_object":
            section["fields"] = ["project_id", "operation_strategy", "partner_id"]
            kept_sections.append(section)
            continue
        if name == "amount":
            section["title"] = "扣款登记信息"
            section["fields"] = ["date_claim", "summary", "currency_id"]
            kept_sections.append(section)
            continue
        if name in {"handling", "responsibility", "source_trace"}:
            kept_sections.append(section)
    sections = kept_sections
    sections.append(_section("deduction_lines", "扣款单明细", ["deduction_line_ids"], 35))
    sections.append(
        _section(
            "deduction_amount_summary",
            "金额由扣款单明细汇总",
            ["deduction_line_amount_total", "amount", "approved_amount"],
            40,
        )
    )
    policy["sections"] = sections
    required = {"business_category_id", "project_id", "partner_id", "deduction_line_ids"}
    readonly = {"amount", "approved_amount", "deduction_line_amount_total"}
    field_policies = policy.get("fields") if isinstance(policy.get("fields"), list) else []
    for field_policy in policy.get("fields") or []:
        if not isinstance(field_policy, dict):
            continue
        name = field_policy.get("name")
        if name == "amount":
            field_policy.pop("required_profiles", None)
        if name == "deduction_line_ids":
            field_policy["one2many_columns"] = ["item_name", "deduction_category", "amount", "note"]
        if name in required:
            field_policy["required_profiles"] = ["create", "edit"]
        if name in readonly:
            field_policy["readonly_profiles"] = CREATE_EDIT_READONLY
    existing = {field.get("name") for field in field_policies if isinstance(field, dict)}
    for name in ("deduction_line_ids", "deduction_line_amount_total", "approved_amount"):
        if name in existing:
            continue
        field_policy = {"name": name, "group": "core"}
        if name == "deduction_line_ids":
            field_policy["one2many_columns"] = ["item_name", "deduction_category", "amount", "note"]
        if name in required:
            field_policy["required_profiles"] = ["create", "edit"]
        if name in readonly:
            field_policy["readonly_profiles"] = CREATE_EDIT_READONLY
        field_policies.append(field_policy)
    policy["fields"] = field_policies
    return policy


def _loan_policy(title: str) -> dict:
    account_trace = (
        "legacy_visible_bank_name",
        "legacy_visible_counterparty_account",
        "legacy_visible_loan_account",
        "legacy_visible_repayment_account",
    )
    trace = MIGRATION_TRACE_FIELDS + (
        "legacy_attachment_ref",
        "legacy_counterparty_name",
        "legacy_amount_field",
        "legacy_visible_project_name",
        "legacy_visible_request_amount",
        "legacy_visible_approved_amount",
        "legacy_visible_expected_return_time",
        *account_trace,
    )
    return _policy(
        [
            _section("business_identity", "办理类型", ["business_category_id", "loan_flow_label", "loan_type", "direction", "state", "name"], 10),
            _section("business_object", "项目与借款方", ["project_id", "operation_strategy", "partner_id"], 20),
            _section("amount", title, ["document_date", "due_date", "amount", "currency_id", "purpose"], 30),
            _section("account", "历史账户线索", list(account_trace), 40, collapsed=True),
            _section("handling", "办理说明", ["note", "attachment_ids"], 50),
            _section("source_trace", "来源与系统追溯", list(trace) + list(APPROVAL_FIELDS), 90, collapsed=True),
        ],
        required=("business_category_id", "project_id", "partner_id", "document_date", "amount"),
        readonly_all=("operation_strategy", "loan_flow_label", "loan_type", "direction") + SYSTEM_FIELDS,
        trace=trace + APPROVAL_FIELDS,
    )


def _fund_operation_policy(title: str) -> dict:
    trace = MIGRATION_TRACE_FIELDS + (
        "legacy_attachment_ref",
        "legacy_acceptance_label",
        "legacy_acceptance_sort_id",
        "legacy_visible_document_no",
        "legacy_visible_project_name",
        "legacy_visible_transfer_type",
        "legacy_visible_account_name",
        "legacy_visible_counterparty_account_name",
        "legacy_visible_reason",
    )
    return _policy(
        [
            _section("business_identity", "办理类型", ["business_category_id", "fund_flow_label", "operation_type", "state", "name"], 10),
            _section("business_object", "项目与账户", ["project_id", "operation_strategy", "source_account_id", "target_account_id"], 20),
            _section("amount", title, ["operation_date", "amount", "currency_id"], 30),
            _section("handling", "办理说明", ["operation_reason", "note", "attachment_ids"], 40),
            _section("balance", "账户余额", ["before_balance", "after_balance", "account_balance", "bank_balance", "daily_income", "daily_expense"], 70, collapsed=True),
            _section("source_trace", "来源与系统追溯", list(trace), 90, collapsed=True),
        ],
        required=("business_category_id", "operation_date", "amount"),
        readonly_all=("operation_strategy", "fund_flow_label", "operation_type") + SYSTEM_FIELDS,
        trace=trace,
        ledger=("before_balance", "after_balance", "account_balance", "bank_balance", "daily_income", "daily_expense"),
    )


def _payment_execution_policy(title: str) -> dict:
    trace = MIGRATION_TRACE_FIELDS + (
        "legacy_attachment_ref",
        "legacy_residual_reason",
        "legacy_visible_document_no",
        "legacy_visible_project_name",
        "legacy_visible_supplier_name",
        "legacy_visible_payment_date",
        "legacy_visible_payment_amount",
        "legacy_visible_payment_method",
        "legacy_visible_payment_content",
        "legacy_visible_request_no",
        "legacy_visible_voucher_no",
    )
    return _policy(
        [
            _section("business_identity", "办理类型", ["business_category_id", "execution_flow_label", "state", "name"], 10),
            _section("business_object", "付款依据", ["payment_request_id", "project_id", "operation_strategy", "partner_id", "contract_id"], 20),
            _section("amount", title, ["date_payment", "paid_amount", "planned_amount", "invoice_amount", "currency_id"], 30),
            _section("receipt_account", "收款账户", ["receipt_account_name", "receipt_bank_name", "receipt_account_no"], 40),
            _section("payment_account", "付款账户", ["payment_account_name", "payment_bank_name", "payment_account_no", "bank_account"], 50),
            _section("handling", "办理说明", ["payment_method", "handler_name", "document_no", "note", "attachment_ids"], 60),
            _section(
                "responsibility_balance",
                "公司-承包人资金责任",
                [
                    "company_contractor_responsibility_state",
                    "company_contractor_arrival_unprocessed_amount",
                    "company_contractor_arrival_over_processed_amount",
                    "company_contractor_self_funding_balance",
                    "company_contractor_responsibility_notice",
                ],
                70,
                collapsed=True,
            ),
            _section("source_trace", "来源与系统追溯", ["payment_family", "source_kind", "push_result", "kingdee_document_no"] + list(trace), 90, collapsed=True),
        ],
        required=(
            "business_category_id",
            "payment_request_id",
            "project_id",
            "partner_id",
            "paid_amount",
            "receipt_account_name",
            "receipt_account_no",
            "payment_account_name",
            "payment_account_no",
        ),
        readonly_all=("operation_strategy", "execution_flow_label", "payment_family", "source_kind") + SYSTEM_FIELDS,
        hide_create=("payment_family", "source_kind", "push_result", "kingdee_document_no"),
        readonly_only=(
            "push_result",
            "kingdee_document_no",
            "company_contractor_responsibility_state",
            "company_contractor_arrival_unprocessed_amount",
            "company_contractor_arrival_over_processed_amount",
            "company_contractor_self_funding_balance",
            "company_contractor_responsibility_notice",
        ),
        trace=trace,
    )


def _receipt_policy(title: str) -> dict:
    trace = (
        "legacy_source_model",
        "legacy_source_table",
        "legacy_record_id",
        "legacy_document_state",
        "legacy_document_state_label",
        "legacy_attachment_ref",
        "legacy_acceptance_label",
        "legacy_acceptance_sort_id",
        "creator_legacy_user_id",
        "creator_name",
        "created_time",
        "legacy_project_name",
        "legacy_company_name",
        "legacy_partner_name",
        "legacy_contract_no",
        "legacy_receipt_type",
        "legacy_receipt_subtype",
        "legacy_residual_reason",
        "active",
    )
    return _policy(
        [
            _section("business_identity", "办理类型", ["business_category_id", "receipt_flow_label", "source_kind", "state", "name"], 10),
            _section("business_object", "项目与收款申请", ["project_id", "operation_strategy", "payment_request_id", "contract_id", "partner_id"], 20),
            _section("receipt", title, ["date_receipt", "amount", "income_category", "receipt_type", "payment_method", "bill_no", "invoice_ref", "currency_id"], 30),
            _section("account", "收款账户", ["receiving_account_name", "receiving_account_no", "receiving_bank_name", "receiving_account"], 40),
            _section("handling", "办理说明", ["note", "attachment_ids"], 50),
            _section("source_trace", "迁移来源", list(trace), 90, collapsed=True, visible_profiles=("readonly",)),
        ],
        required=("business_category_id", "project_id", "partner_id", "date_receipt", "amount"),
        readonly_all=("operation_strategy", "receipt_flow_label", "source_kind") + SYSTEM_FIELDS,
        trace=trace,
    )


def _self_funding_policy(title: str) -> dict:
    responsibility = (
        "company_contractor_responsibility_summary_id",
        "company_contractor_responsibility_state",
        "company_contractor_arrival_unprocessed_amount",
        "company_contractor_arrival_over_processed_amount",
        "company_contractor_self_funding_balance",
        "company_contractor_responsibility_notice",
    )
    trace = ("document_no", "active")
    return _policy(
        [
            _section("business_identity", "办理类型", ["business_category_id", "funding_type", "source_origin", "state", "name"], 10),
            _section("business_object", "项目与承包人", ["project_id", "operation_strategy", "partner_id"], 20),
            _section("amount", title, ["document_date", "amount", "currency_id"], 30),
            _section("account", "账户信息", ["payment_account_name", "partner_account_name", "bank_name", "bank_account"], 40),
            _section("handling", "办理说明", ["summary", "note", "attachment_ids"], 50),
            _section("responsibility", "责任与余额", list(responsibility), 70, collapsed=True),
            _section("source_trace", "来源与系统追溯", list(trace) + list(APPROVAL_FIELDS), 90, collapsed=True),
        ],
        required=("business_category_id", "project_id", "partner_id", "document_date", "amount"),
        readonly_all=("operation_strategy", "funding_type", "source_origin") + SYSTEM_FIELDS,
        trace=trace + APPROVAL_FIELDS,
        ledger=responsibility,
    )


def _tax_deduction_policy() -> dict:
    trace = (
        "legacy_visible_project_name",
        "legacy_source_model",
        "legacy_source_table",
        "legacy_record_id",
        "legacy_document_state",
        "creator_legacy_user_id",
        "creator_name",
        "created_time",
        "source_created_by",
        "source_created_at",
        "active",
    )
    return _policy(
        [
            _section("business_identity", "办理类型", ["business_category_id", "deduction_flow_label", "source_origin", "state", "name"], 10),
            _section("business_object", "项目与开票单位", ["project_id", "operation_strategy", "partner_id", "partner_name"], 20),
            _section("invoice", "发票信息", ["invoice_date", "invoice_no", "invoice_code", "tax_rate_text", "invoice_amount_untaxed", "invoice_tax_amount", "invoice_amount_total"], 30),
            _section("deduction", "抵扣信息", ["deduction_confirm_date", "deduction_amount", "deduction_tax_amount", "deduction_surcharge_amount", "is_transfer_out"], 40),
            _section("handling", "办理说明", ["deduction_unit_name", "withholding_amount", "deduction_reason", "note", "attachment_ids"], 50),
            _section("responsibility", "责任与余额", ["company_contractor_responsibility_state", "company_contractor_responsibility_notice"], 70, collapsed=True),
            _section("source_trace", "来源与系统追溯", list(trace), 90, collapsed=True),
        ],
        required=("business_category_id", "project_id", "invoice_no", "invoice_date", "deduction_tax_amount"),
        readonly_all=("operation_strategy", "deduction_flow_label", "source_origin") + SYSTEM_FIELDS,
        trace=trace,
        ledger=("company_contractor_responsibility_state", "company_contractor_responsibility_notice"),
    )


def _tax_certificate_policy() -> dict:
    trace = (
        "source_table",
        "legacy_record_id",
        "legacy_pid",
        "residual_reason",
        "document_state",
        "document_state_label",
        "deleted_flag",
        "project_legacy_id",
        "partner_legacy_id",
        "contract_legacy_id",
        "request_legacy_id",
        "creator_legacy_user_id",
        "creator_name",
        "created_time",
        "attachment_ref",
        "active",
    )
    return _policy(
        [
            _section("business_identity", "办理类型", ["payment_family_label", "document_state_label", "document_no"], 10),
            _section("business_object", "项目与合同", ["project_id", "project_name", "partner_id", "partner_name", "contract_no", "contract_name"], 20),
            _section("certificate", "外经证信息", ["document_date", "taxpayer_name", "taxpayer_identifier", "counterparty_tax_identifier", "tax_report_management_no", "operation_address"], 30),
            _section("contact", "经办与税务联系人", ["handler_name", "handler_phone", "regional_tax_contact", "regional_tax_contact_phone"], 40),
            _section("amount", "合同与票款", ["planned_amount", "paid_amount", "invoice_amount", "payment_method", "bank_account"], 50),
            _section("handling", "办理说明", ["note", "attachment_ids", "attachment_links"], 60),
            _section("source_trace", "来源与系统追溯", list(trace), 90, collapsed=True),
        ],
        required=("project_id", "document_date", "taxpayer_name", "tax_report_management_no"),
        readonly_all=("payment_family", "payment_family_label", "document_state_label"),
        hide_create=("payment_family_label",),
        trace=trace,
    )


def _responsibility_fact_policy(title: str) -> dict:
    trace = ("source_model", "source_res_id", "source_document_no", "source_menu_hint")
    ledger = (
        "arrival_amount",
        "paid_amount",
        "deducted_amount",
        "self_funding_income_amount",
        "self_funding_refund_amount",
        "self_funding_balance_effect",
        "project_fund_status_effect",
        "contractor_responsibility_effect",
        "coverage_note",
    )
    return _policy(
        [
            _section("business_identity", "责任口径", ["responsibility_type", "responsibility_scope", "balance_policy"], 10),
            _section("business_object", "项目与承包人", ["project_id", "partner_id", "partner_name", "document_date"], 20),
            _section("amount", title, ["amount"] + list(ledger), 30),
            _section("source_trace", "来源与系统追溯", list(trace), 90, collapsed=True),
        ],
        readonly_all=("responsibility_type", "responsibility_scope", "balance_policy"),
        ledger=ledger,
        trace=trace,
    )


def _responsibility_summary_policy() -> dict:
    ledger = (
        "source_line_count",
        "arrival_line_count",
        "self_funding_income_line_count",
        "self_funding_refund_line_count",
        "arrival_amount",
        "paid_amount",
        "deducted_amount",
        "arrival_processed_amount",
        "arrival_unprocessed_amount",
        "arrival_over_processed_amount",
        "self_funding_income_amount",
        "self_funding_refund_amount",
        "self_funding_balance",
        "project_fund_status_effect",
        "contractor_responsibility_effect",
        "responsibility_state",
        "coverage_note",
    )
    return _policy(
        [
            _section("business_object", "项目与承包人", ["project_id", "partner_id", "partner_name"], 10),
            _section("balance", "责任余额", list(ledger), 20),
        ],
        readonly_all=("project_id", "partner_id", "partner_name"),
        ledger=ledger,
    )


def _contract_handling_policy(title: str, *, supplement: bool = False, expense: bool = False) -> dict:
    trace = (
        "legacy_source_model",
        "legacy_source_table",
        "legacy_fact_model",
        "legacy_fact_id",
        "legacy_fact_type",
        "legacy_record_id",
        "legacy_document_no",
        "legacy_external_contract_no",
        "legacy_contract_no",
        "legacy_status",
        "legacy_document_state",
        "legacy_document_state_label",
        "legacy_attachment_ref",
        "creator_legacy_user_id",
        "creator_name",
        "created_time",
        "entry_user_id",
        "entry_data",
        "active",
    )
    ledger = (
        "settlement_amount",
        "invoice_amount",
        "uninvoiced_amount",
        "received_amount",
        "unreceived_amount",
        "paid_amount",
        "unpaid_amount",
        "payment_request_count",
        "settlement_count",
        "is_locked",
    )
    identity_fields = ["business_category_id"]
    required = ["business_category_id", "project_id", "partner_id", "subject", "tax_id"]
    if supplement:
        identity_fields.append("original_contract_id")
        required.append("original_contract_id")
    basic_fields = ["subject", "date_contract", "category_id"]
    if expense:
        basic_fields.append("expense_contract_category_id")
    basic_fields.append("engineering_address")
    return _policy(
        [
            _section("business_identity", "办理类型", identity_fields, 10),
            _section("business_object", "项目与往来单位", ["project_id", "partner_id", "operation_strategy"], 20),
            _section("contract_basic", title, basic_fields, 30),
            _section("amount", "金额与税率", ["tax_id", "currency_id", "amount_untaxed", "amount_tax", "amount_total"], 40),
            _section("period", "履约与管理", ["date_start", "date_end", "budget_id", "archived", "handler_id"], 50),
            _section("handling", "备注与附件", ["note", "attachment_ids"], 60),
            _section("contract_detail", "合同明细", ["line_ids"], 70),
            _section("execution", "执行结果", list(ledger), 80, collapsed=True),
            _section("system_identity", "系统信息", ["type", "state", "name"], 85, collapsed=True, visible_profiles=EDIT_READONLY),
            _section("source_trace", "来源与系统追溯", list(trace) + list(APPROVAL_FIELDS), 90, collapsed=True, visible_profiles=READONLY_ONLY),
        ],
        required=tuple(required),
        readonly_all=("operation_strategy", "type", "state", "name") + SYSTEM_FIELDS,
        trace=trace + APPROVAL_FIELDS,
        ledger=ledger + ("amount_untaxed", "amount_tax", "amount_total"),
    )


def _material_policy(
    title: str,
    detail_fields: list[str],
    *,
    object_fields: list[str] | None = None,
    handling_fields: list[str] | None = None,
    readonly_fields: Iterable[str] = (),
    ledger_fields: Iterable[str] = (),
) -> dict:
    trace = FACT_TRACE_FIELDS
    object_fields = object_fields or ["project_id"]
    handling_fields = handling_fields or ["note"]
    sections = [
        _section("business_identity", "办理类型", ["business_category_id", "state", "name"], 10),
        _section("business_object", "项目与业务对象", object_fields, 20),
        _section("document", title, detail_fields, 30),
        _section("handling", "办理说明", handling_fields, 50),
    ]
    if ledger_fields:
        sections.append(_section("execution", "执行结果", list(ledger_fields), 70, collapsed=True))
    sections.append(_section("source_trace", "来源与系统追溯", list(trace), 90, collapsed=True))
    return _policy(
        sections,
        required=("business_category_id", "project_id"),
        readonly_all=tuple(readonly_fields) + SYSTEM_FIELDS,
        trace=trace,
        ledger=ledger_fields,
    )


def _site_issue_policy(title: str, *, kind: str) -> dict:
    trace = ("legacy_fact_model", "legacy_fact_id", "legacy_fact_type", "active")
    if kind == "issue":
        sections = [
            _section("business_identity", "办理类型", ["name", "state", "issue_category", "source_channel"], 10),
            _section("business_object", "项目与位置", ["project_id", "location", "coordinate", "issue_date"], 20),
            _section("issue", title, ["issue_level", "responsible_party_id", "owner_id", "rectification_deadline", "description", "voice_text"], 30),
            _section("handling", "附件与闭环", ["attachment_ids", "rectification_ids", "recheck_ids", "photo_batch_ids"], 50),
            _section("source_trace", "来源与系统追溯", list(trace), 90, collapsed=True),
        ]
        required = ("project_id", "name", "location", "description")
    elif kind == "rectification":
        sections = [
            _section("business_identity", "办理类型", ["issue_id", "name", "issue_state", "source_channel"], 10),
            _section("business_object", "项目与责任", ["project_id", "issue_level", "responsible_party_id", "rectification_deadline"], 20),
            _section("handling", title, ["rectification_date", "handler_id", "result", "attachment_ids", "photo_batch_ids"], 30),
            _section("source_trace", "来源与系统追溯", list(trace), 90, collapsed=True),
        ]
        required = ("issue_id", "result")
    else:
        sections = [
            _section("business_identity", "办理类型", ["issue_id", "name", "issue_state", "source_channel"], 10),
            _section("business_object", "项目与责任", ["project_id", "issue_level", "responsible_party_id"], 20),
            _section("handling", title, ["recheck_date", "recheck_user_id", "result", "comment", "attachment_ids", "photo_batch_ids"], 30),
            _section("source_trace", "来源与系统追溯", list(trace), 90, collapsed=True),
        ]
        required = ("issue_id", "result")
    return _policy(
        sections,
        required=required,
        readonly_all=("issue_state", "source_channel"),
        trace=trace,
    )


def _construction_diary_policy() -> dict:
    trace = (
        "legacy_source_model",
        "legacy_document_state",
        "legacy_attachment_ref",
        "legacy_acceptance_label",
        "legacy_acceptance_sort_id",
        "active",
    )
    return _policy(
        [
            _section("business_identity", "办理类型", ["title", "diary_type", "state", "source_origin"], 10),
            _section("business_object", "项目与日期", ["project_id", "date_diary", "weather"], 20),
            _section("site_status", "现场情况", ["construction_unit", "project_manager", "manpower_count", "attendance_equipment", "description"], 30),
            _section("quality_safety", "质量安全", ["material_inspection_note", "safety_note", "test_block_note", "design_change_note", "next_plan"], 40),
            _section("handling", "附件", ["attachment_ids", "note"], 50),
            _section("source_trace", "来源与系统追溯", list(trace), 90, collapsed=True),
        ],
        required=("project_id", "date_diary", "title", "diary_type"),
        readonly_all=("source_origin",) + SYSTEM_FIELDS,
        trace=trace,
    )


BUSINESS_CATEGORY_FORM_POLICY_TEMPLATES = {
    "contract.income": _contract_handling_policy("收入合同信息"),
    "contract.income.supplement": _contract_handling_policy("收入补充合同信息", supplement=True),
    "contract.expense": _contract_handling_policy("支出合同信息", expense=True),
    "contract.expense.supplement": _contract_handling_policy("支出补充合同信息", supplement=True, expense=True),
    "settlement.income": _settlement_policy("收入结算金额", "项目与发包人"),
    "settlement.expense": _settlement_policy("支出结算金额", "项目与供应商/分包方"),
    "finance.payment.apply.pay": _payment_request_policy("付款申请金额", "项目与收款单位"),
    "finance.payment.apply.receive": _payment_request_policy("收款申请金额", "项目与付款单位"),
    "finance.payment.execution.partner": _payment_execution_policy("往来单位付款金额"),
    "finance.payment.execution.company": _payment_execution_policy("公司财务支出金额"),
    "finance.receipt.income.project": _receipt_policy("到款确认"),
    "finance.receipt.income.progress": _receipt_policy("工程进度款收入"),
    "finance.receipt.income.residual": _receipt_policy("其他/残余收款"),
    "finance.self_funding.income": _self_funding_policy("自筹垫付金额"),
    "finance.self_funding.refund": _self_funding_policy("自筹退回金额"),
    "finance.responsibility.arrival_confirmation": _responsibility_fact_policy("到款确认责任"),
    "finance.responsibility.self_funding_income": _responsibility_fact_policy("自筹垫付责任"),
    "finance.responsibility.self_funding_refund": _responsibility_fact_policy("自筹退回责任"),
    "finance.responsibility.company_contractor.balance": _responsibility_summary_policy(),
    "finance.loan.borrowing": _loan_policy("借款金额"),
    "finance.loan.contractor_project_borrow": _loan_policy("承包人借项目款"),
    "finance.loan.project_borrow_company": _loan_policy("项目借公司款"),
    "finance.fund.transfer": _fund_operation_policy("账户间资金往来"),
    "finance.fund.daily_report": _fund_operation_policy("资金日报"),
    "finance.fund.balance_adjustment": _fund_operation_policy("余额调整"),
    "finance.expense.reimbursement": _expense_claim_policy("报销金额"),
    "finance.expense.project": _expense_claim_policy("项目费用金额"),
    "finance.deposit.bid.pay": _expense_claim_policy("投标保证金支付"),
    "finance.deposit.bid.return": _expense_claim_policy("投标保证金退回"),
    "finance.deposit.self_funding.return": _expense_claim_policy("自筹保证金退回"),
    "finance.deposit.contract.pay": _expense_claim_policy("合同保证金登记"),
    "finance.deposit.contract.return": _expense_claim_policy("合同保证金退回"),
    "finance.deduction.bill": _deduction_bill_policy(),
    "finance.deduction.paid": _expense_claim_policy("扣款实缴金额"),
    "finance.deduction.refund": _expense_claim_policy("扣款实缴退回"),
    "finance.repayment.registration": _expense_claim_policy("还款登记金额"),
    "finance.repayment.contractor_project": _expense_claim_policy("承包人还项目款"),
    "finance.repayment.project_company": _expense_claim_policy("项目还公司款"),
    "tax.certificate.registration": _tax_certificate_policy(),
    "tax.deduction.registration": _tax_deduction_policy(),
    "material.plan": _material_policy(
        "材料计划明细",
        ["date_plan", "material_name_summary", "material_spec_summary", "material_uom_summary", "total_plan_qty", "line_ids"],
        handling_fields=["line_note_summary", "attachment_ids"],
        ledger_fields=["total_bill_qty", "total_unplanned_qty", "purchase_request_count", "purchase_order_count"],
    ),
    "material.purchase.request": _material_policy(
        "采购申请明细",
        ["request_date", "required_date", "requester_id", "department_id", "purpose", "source_material_plan_id", "supplier_id", "line_ids"],
        handling_fields=["note", "attachment_ids"],
        ledger_fields=["rfq_count", "purchase_order_count"],
    ),
    "material.acceptance": _material_policy(
        "进场验收明细",
        ["acceptance_date", "acceptance_flow", "purchase_request_id", "purchase_order_id", "supplier_id", "warehouse_id", "dest_location_id", "inspector_id", "line_ids"],
        handling_fields=["sampling_required", "sampling_report_ref", "rejection_reason", "note", "attachment_ids"],
    ),
    "material.inbound": _material_policy(
        "入库明细",
        ["inbound_date", "acceptance_id", "supplier_id", "warehouse_id", "dest_location_id", "keeper_id", "material_name_summary", "material_spec_summary", "material_uom_summary", "total_qty", "amount_total", "line_ids"],
        handling_fields=["line_note_summary", "note", "attachment_ids"],
        readonly_fields=["operation_strategy"],
    ),
    "material.outbound": _material_policy(
        "出库明细",
        ["outbound_date", "outbound_type", "warehouse_id", "receiver_id", "receiver_user_id", "purpose", "line_ids"],
        handling_fields=["note", "attachment_ids"],
        ledger_fields=["amount_total", "stock_picking_id"],
    ),
    "material.return": _material_policy(
        "退库明细",
        ["outbound_date", "outbound_type", "warehouse_id", "receiver_id", "receiver_user_id", "purpose", "line_ids"],
        handling_fields=["note", "attachment_ids"],
        ledger_fields=["amount_total", "stock_picking_id"],
    ),
    "material.transfer": _material_policy(
        "调拨明细",
        ["outbound_date", "outbound_type", "source_location_id", "dest_location_id", "warehouse_id", "dest_warehouse_id", "line_ids"],
        handling_fields=["note", "attachment_ids"],
        ledger_fields=["transfer_inbound_id", "stock_picking_id"],
    ),
    "material.loss": _material_policy(
        "损耗明细",
        ["outbound_date", "outbound_type", "warehouse_id", "purpose", "line_ids"],
        handling_fields=["note", "attachment_ids"],
        ledger_fields=["amount_total", "stock_picking_id"],
    ),
    "material.rfq": _material_policy(
        "询比价明细",
        ["rfq_date", "due_date", "purchase_request_id", "source_material_plan_id", "supplier_ids", "selected_supplier_id", "contact_name", "contact_phone", "line_ids"],
        handling_fields=["note", "attachment_ids"],
    ),
    "material.settlement": _material_policy(
        "材料结算明细",
        ["settlement_date", "supplier_id", "purchase_order_id", "amount_untaxed", "tax_amount", "amount_total", "line_ids"],
        handling_fields=["note", "attachment_ids"],
        ledger_fields=["payment_request_id", "payment_requested_amount", "payment_paid_amount", "payment_remaining_amount"],
    ),
    "site.construction.diary": _construction_diary_policy(),
    "site.quality.issue": _site_issue_policy("质量问题", kind="issue"),
    "site.quality.rectification": _site_issue_policy("质量整改", kind="rectification"),
    "site.quality.recheck": _site_issue_policy("质量复验", kind="recheck"),
    "site.safety.issue": _site_issue_policy("安全问题", kind="issue"),
    "site.safety.rectification": _site_issue_policy("安全整改", kind="rectification"),
    "site.safety.recheck": _site_issue_policy("安全复验", kind="recheck"),
}


def get_business_category_form_policy_templates() -> dict[str, dict]:
    return copy.deepcopy(BUSINESS_CATEGORY_FORM_POLICY_TEMPLATES)
