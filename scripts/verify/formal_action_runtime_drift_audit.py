#!/usr/bin/env python3
"""Audit high-risk formal action overrides for runtime drift.

The user-confirmed formal list files load after the product taxonomy and can
override action domains and view bindings. This gate catches the recurrent
failure mode where an override leaves a formal menu bound to an empty legacy
domain or an unexpected list view.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from xml.etree import ElementTree as ET

from odoo.tools.safe_eval import safe_eval


OUTPUT_JSON_NAME = "formal_action_runtime_drift_audit_v1.json"
MODULE = "smart_construction_core"
ADDON_ROOT_CANDIDATES = [
    Path("/mnt/extra-addons/smart_construction_core"),
    Path.cwd() / "addons" / "smart_construction_core",
]
HIGH_RISK_XML_FILES = [
    "views/support/user_confirmed_formal_list_alignment_views.xml",
    "views/support/user_confirmed_formal_list_views.xml",
]
EXPECTED_NON_EMPTY_ACTIONS = {
    "action_sc_labor_usage_ticket",
    "action_sc_labor_usage_casual",
    "action_sc_expense_claim_deduction_bill",
    "action_sc_payment_execution_company_finance_expense",
    "action_sc_payment_deposit_return",
    "action_sc_salary_registration",
    "action_construction_contract_expense_execution",
    "action_sc_material_quote_user_confirmed",
    "action_sc_subcontract_request_user_confirmed",
    "action_sc_equipment_usage_shift_user_confirmed",
    "action_payment_request_user_payment_apply",
    "action_sc_payment_execution_partner_payment",
    "action_sc_legacy_fuel_card_fact",
    "action_sc_legacy_fuel_card_recharge_fact",
    "action_sc_legacy_fuel_card_refuel_fact",
    "action_construction_contract_income_construction",
    "action_sc_material_inbound",
    "action_sc_material_rental_in_acceptance",
    "action_sc_material_rental_return_acceptance",
    "action_sc_construction_diary",
    "action_sc_receipt_income_engineering_progress",
    "action_sc_invoice_input_report_user",
    "action_sc_invoice_registration_user",
    "action_sc_settlement_order_income",
    "action_sc_settlement_order_expense",
}
EXPECTED_ACTION_CONTRACTS = {
    "action_construction_contract_income_construction": {
        "name": "施工合同",
        "res_model": "construction.contract.income",
        "view_name": "construction.contract.income.construction.user.confirmed.tree",
        "field_names": [
            "document_status",
            "legacy_document_no",
            "partner_id",
            "company_id",
            "project_id",
            "subject",
            "visible_contract_amount",
            "visible_invoice_amount",
            "visible_received_amount",
            "visible_invoice_unreceived_amount",
            "visible_unreceived_amount",
            "visible_unreceived_rate",
            "legacy_contract_no",
            "date_contract",
            "engineering_address",
            "engineering_content",
            "contract_duration_text",
            "entry_user_text",
            "entry_time",
            "attachment_text",
        ],
    },
    "action_sc_equipment_usage_shift_user_confirmed": {
        "name": "机械台班记录",
        "res_model": "sc.equipment.usage",
        "view_name": "sc.equipment.usage.shift.formal.tree",
        "field_names": [
            "state",
            "project_id",
            "name",
            "document_date",
            "supplier_id",
            "former_supplier_name",
            "equipment_name",
            "specification",
            "uom_text",
            "work_hours",
            "price_unit",
            "amount",
            "attachment_ids",
            "note",
            "source_created_by",
            "source_created_at",
        ],
    },
    "action_sc_material_inbound": {
        "name": "入库",
        "res_model": "sc.material.inbound",
        "view_name": "sc.material.inbound.user.confirmed.tree",
        "field_names": [
            "document_status",
            "name",
            "inbound_date",
            "supplier_id",
            "material_name_summary",
            "material_spec_summary",
            "quantity_summary",
            "unit_price_summary",
            "tax_rate_text",
            "tax_included_amount",
            "total_qty",
            "payment_status_text",
            "payment_paid_amount",
            "payment_unpaid_amount",
            "settlement_status_text",
            "settlement_settled_amount",
            "project_name_display",
            "line_note_summary",
            "attachment_ids",
            "source_created_by",
            "source_created_at",
            "buyer_name",
        ],
    },
    "action_sc_material_quote_user_confirmed": {
        "name": "报价单",
        "res_model": "sc.material.rfq",
        "view_name": "sc.material.rfq.quote.formal.tree",
        "field_names": [
            "quote_status_display",
            "quote_document_no",
            "quote_supplier_name",
            "quote_inquiry_time",
            "quote_material_name",
            "quote_material_spec",
            "quote_quantity_display",
            "quote_tax_price_display",
            "quote_tax_amount_display",
            "quote_total_quantity_display",
            "quote_total_amount_display",
            "quote_note_display",
            "quote_contact_name",
            "quote_contact_phone",
            "quote_attachment_text",
            "quote_selected_text",
            "quote_project_name",
            "quote_source_created_by",
            "quote_source_created_at",
        ],
    },
    "action_payment_request_user_payment_apply": {
        "name": "支付申请",
        "res_model": "payment.request",
        "view_name": "payment.request.formal.payment.apply.tree",
        "field_names": [
            "document_status_display",
            "name",
            "date_request",
            "project_name_display",
            "payee_unit_display",
            "actual_payee_unit_display",
            "payer_unit_display",
            "request_amount_display",
            "actual_paid_amount_display",
            "cost_type_display",
            "note_display",
            "related_document_text",
            "payment_account_no_display",
            "amount_uppercase_display",
            "payee_account_name_display",
            "payee_bank_name_display",
            "payee_account_no_display",
            "attachment_ids",
            "source_created_by",
            "source_created_at",
        ],
    },
    "action_sc_payment_deposit_return": {
        "name": "付款还保证金",
        "res_model": "tender.guarantee",
        "view_name": "tender.guarantee.formal.payment.deposit.return.tree",
        "field_names": [
            "deposit_status_display",
            "deposit_push_result",
            "deposit_kingdee_document_no",
            "deposit_document_no",
            "deposit_bid_project_name",
            "deposit_engineering_project_name",
            "deposit_type_display",
            "deposit_company_name",
            "deposit_amount_display",
            "deposit_returned_amount_display",
            "deposit_unreturned_amount_display",
            "deposit_need_return_text",
            "deposit_payee_unit",
            "deposit_payment_account",
            "deposit_note_display",
            "deposit_attachment_text",
            "deposit_source_created_by",
            "deposit_source_created_at",
        ],
    },
    "action_sc_payment_execution_partner_payment": {
        "name": "往来单位付款",
        "res_model": "sc.payment.execution",
        "view_name": "sc.payment.execution.partner.formal.tree",
        "field_names": [
            "partner_payment_status_display",
            "partner_payment_date_display",
            "partner_payment_payee_unit",
            "partner_payment_actual_payee_unit",
            "partner_payment_amount_display",
            "partner_payment_category_display",
            "partner_payment_content_display",
            "partner_payment_method_display",
            "partner_payment_cost_type_display",
            "partner_payment_account_name_display",
            "partner_payment_attachment_text",
            "partner_payment_voucher_no",
            "partner_payment_writer",
            "partner_payment_source_created_by",
            "partner_payment_project_name",
            "partner_payment_source_text",
            "partner_payment_document_no",
        ],
    },
    "action_sc_payment_execution_company_finance_expense": {
        "name": "公司财务支出",
        "res_model": "sc.payment.execution",
        "view_name": "sc.payment.execution.formal.company.finance.expense.tree",
        "field_names": [
            "company_finance_status_display",
            "company_finance_push_result",
            "company_finance_document_no",
            "company_finance_amount_display",
            "company_finance_cost_type_display",
            "company_finance_payee_unit",
            "company_finance_payment_account_name",
            "company_finance_note_display",
            "company_finance_source_created_by",
            "company_finance_source_created_at",
            "company_finance_attachment_text",
        ],
    },
    "action_sc_receipt_income_engineering_progress": {
        "name": "工程进度款收入登记",
        "res_model": "sc.receipt.income",
        "view_name": "sc.receipt.income.engineering.progress.formal.tree",
        "field_names": [
            "state",
            "project_id",
            "partner_id",
            "company_id",
            "legacy_contract_no",
            "name",
            "creator_name",
            "receiving_account",
            "amount",
            "income_category",
            "date_receipt",
            "note",
            "receipt_income_attachment_text_display",
            "creator_name",
            "created_time",
        ],
    },
    "action_sc_invoice_input_report_user": {
        "name": "进项发票",
        "res_model": "sc.invoice.registration",
        "view_name": "sc.invoice.registration.input.tax.user.confirmed.tree",
        "field_names": [
            "document_status_display",
            "document_no",
            "project_name_display",
            "invoice_date",
            "recipient_unit_display",
            "invoice_issue_company_display",
            "actual_invoice_issue_company_display",
            "amount_total",
            "tax_amount",
            "amount_no_tax",
            "invoice_no",
            "invoice_quantity_display",
            "tax_rate",
            "invoice_type",
            "note_display",
            "source_created_by",
            "invoice_attachment_text",
            "source_created_at",
        ],
    },
    "action_sc_invoice_registration_user": {
        "name": "销项开票登记",
        "res_model": "sc.invoice.registration",
        "view_name": "sc.invoice.registration.output.registration.formal.tree",
        "field_names": [
            "document_status_display",
            "document_no",
            "invoice_date",
            "invoice_issue_company_display",
            "project_name_display",
            "recipient_unit_display",
            "actual_invoice_amount",
            "amount_no_tax",
            "tax_amount",
            "tax_rate",
            "surcharge_amount",
            "invoice_quantity_display",
            "related_receipt_amount",
            "invoice_no",
            "invoice_type",
            "invoice_attachment_text",
            "source_created_by",
            "source_created_at",
        ],
    },
}


def artifact_root() -> Path:
    raw = os.getenv("MIGRATION_ARTIFACT_ROOT") or os.getenv("ARTIFACT_ROOT")
    candidates = [Path(raw)] if raw else []
    candidates.extend([Path("/mnt/artifacts/backend"), Path(f"/tmp/formal_action_runtime_drift/{env.cr.dbname}")])  # noqa: F821
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


def addon_root() -> Path:
    for candidate in ADDON_ROOT_CANDIDATES:
        if candidate.exists():
            return candidate
    raise RuntimeError({"addon_root_missing": [str(item) for item in ADDON_ROOT_CANDIDATES]})


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def action_records() -> dict[str, dict[str, object]]:
    records: dict[str, dict[str, object]] = {}
    root = addon_root()
    for relative in HIGH_RISK_XML_FILES:
        path = root / relative
        xml_root = ET.fromstring(path.read_text(encoding="utf-8"))
        for node in xml_root.findall(".//record[@model='ir.actions.act_window']"):
            action_id = node.get("id") or ""
            if not action_id:
                continue
            fields = {field.get("name") or "": (field.text or "").strip() for field in node.findall("field")}
            records[action_id] = {
                "file": relative,
                "xml_domain": fields.get("domain", ""),
                "xml_name": fields.get("name", ""),
                "has_view_override": "view_id" in fields or "view_ids" in fields,
            }
    return records


def tree_field_names(view) -> list[str]:
    if not view:
        return []
    root = ET.fromstring(view.arch_db.encode("utf-8"))
    return [node.get("name") or "" for node in root.iter("field")]


rows = []
failures = []
for action_id, spec in sorted(action_records().items()):
    xmlid = f"{MODULE}.{action_id}"
    action = env.ref(xmlid, raise_if_not_found=False)  # noqa: F821
    if not action:
        failures.append({"action_xmlid": xmlid, "reason": "missing_action", **spec})
        continue
    domain = safe_eval(action.domain or "[]")
    count = None
    count_error = None
    if action.res_model in env:  # noqa: F821
        try:
            count = int(env[action.res_model].sudo().search_count(domain))  # noqa: F821
        except Exception as exc:  # pragma: no cover - executed inside Odoo shell
            count_error = f"{type(exc).__name__}: {str(exc)[:240]}"
    else:
        count_error = "missing_res_model"

    tree_bindings = action.view_ids.filtered(lambda item: item.view_mode == "tree").sorted("sequence")
    primary_tree = action.view_id if action.view_id.type == "tree" else (tree_bindings[0].view_id if tree_bindings else False)
    row = {
        "action_xmlid": xmlid,
        "action_id": int(action.id),
        "name": action.name,
        "res_model": action.res_model,
        "domain": action.domain or "",
        "record_count": count,
        "count_error": count_error,
        "primary_tree": primary_tree.name if primary_tree else "",
        "field_count": len(tree_field_names(primary_tree)) if primary_tree else 0,
        **spec,
    }
    rows.append(row)

    if count_error:
        failures.append({"reason": "domain_count_error", **row})
    if action_id in EXPECTED_NON_EMPTY_ACTIONS and count == 0:
        failures.append({"reason": "empty_high_risk_formal_action_domain", **row})

    expected = EXPECTED_ACTION_CONTRACTS.get(action_id)
    if expected:
        actual_fields = tree_field_names(primary_tree)
        for key in ("name", "res_model"):
            if row[key] != expected[key]:
                failures.append({"reason": f"wrong_{key}", "expected": expected[key], **row})
        if row["primary_tree"] != expected["view_name"]:
            failures.append({"reason": "wrong_primary_tree", "expected": expected["view_name"], **row})
        if actual_fields != expected["field_names"]:
            failures.append(
                {
                    "reason": "wrong_tree_fields",
                    "expected_fields": expected["field_names"],
                    "actual_fields": actual_fields,
                    **row,
                }
            )

payload = {
    "status": "FAIL" if failures else "PASS",
    "database": env.cr.dbname,  # noqa: F821
    "mode": "formal_action_runtime_drift_audit",
    "audited_actions": len(rows),
    "failure_count": len(failures),
    "failures": failures,
    "rows": rows,
}
write_json(artifact_root() / OUTPUT_JSON_NAME, payload)
print("FORMAL_ACTION_RUNTIME_DRIFT_AUDIT=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
if failures:
    raise RuntimeError({"formal_action_runtime_drift_audit_failed": failures})
