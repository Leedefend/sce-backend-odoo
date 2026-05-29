#!/usr/bin/env python3
"""Backfill legacy-visible list fields that are not part of runtime workflow data."""

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path


def clean(value):
    if value in (None, False):
        return ""
    text = str(value).strip()
    return "" if text in {"False", "false", "None", "NULL"} else text


def parse_datetime(value):
    text = clean(value)
    if not text:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def ensure_column(table, column, ddl):
    env.cr.execute(  # noqa: F821
        """
        SELECT 1
          FROM information_schema.columns
         WHERE table_name = %s
           AND column_name = %s
        """,
        (table, column),
    )
    if not env.cr.fetchone():  # noqa: F821
        env.cr.execute("ALTER TABLE %s ADD COLUMN %s %s" % (table, column, ddl))  # noqa: F821


def read_csv(path):
    rows = {}
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        sample = handle.read(4096)
        handle.seek(0)
        dialect = csv.excel()
        first_line = sample.splitlines()[0] if sample else ""
        if first_line.count("|") > first_line.count(","):
            dialect.delimiter = "|"
        elif first_line.count("\t") > first_line.count(","):
            dialect.delimiter = "\t"
        reader = csv.DictReader(handle, dialect=dialect)
        if reader.fieldnames:
            reader.fieldnames = [clean(field_name) for field_name in reader.fieldnames]
        for row in reader:
            row = {clean(column): clean(value) for column, value in row.items()}
            key = clean(
                row.get("legacy_line_id")
                or row.get("legacy_record_id")
                or row.get("legacy_user_id")
                or row.get("legacy_xmid")
                or row.get("Id")
                or row.get("ID")
                or row.get("id")
            )
            if key:
                if row.get("raw_payload"):
                    try:
                        raw_payload = json.loads(row["raw_payload"])
                    except Exception:
                        raw_payload = {}
                    for raw_key, raw_value in raw_payload.items():
                        row.setdefault(raw_key, clean(raw_value))
                rows[key] = row
                if "#" in key:
                    rows.setdefault(key.split("#", 1)[0], row)
    return rows


ensure_column("sc_hr_payroll_document", "legacy_visible_creator_name", "varchar")
ensure_column("sc_hr_payroll_document", "legacy_visible_created_time", "timestamp")
ensure_column("sc_hr_payroll_document", "legacy_visible_people_count", "varchar")
ensure_column("sc_hr_payroll_document", "legacy_visible_type", "varchar")
ensure_column("sc_hr_payroll_document", "legacy_visible_note", "text")
ensure_column("sc_hr_payroll_document", "legacy_visible_certificate_fee", "varchar")
ensure_column("sc_hr_payroll_document", "legacy_visible_item_type", "varchar")
ensure_column("sc_expense_claim", "legacy_visible_title", "varchar")
ensure_column("sc_expense_claim", "legacy_visible_project_name", "varchar")
ensure_column("sc_expense_claim", "legacy_visible_document_state", "varchar")
ensure_column("sc_expense_claim", "legacy_visible_document_no", "varchar")
ensure_column("sc_expense_claim", "legacy_visible_date", "timestamp")
ensure_column("sc_expense_claim", "legacy_visible_department", "varchar")
ensure_column("sc_expense_claim", "legacy_visible_summary", "text")
ensure_column("sc_expense_claim", "legacy_visible_amount", "varchar")
ensure_column("sc_expense_claim", "legacy_visible_adjustment_item", "varchar")
ensure_column("sc_expense_claim", "legacy_visible_returned_flag", "varchar")
ensure_column("sc_expense_claim", "legacy_visible_borrower", "varchar")
ensure_column("sc_expense_claim", "legacy_visible_loan_amount", "varchar")
ensure_column("sc_expense_claim", "legacy_visible_repayment_amount", "varchar")
ensure_column("sc_expense_claim", "legacy_visible_loan_rate", "varchar")
ensure_column("sc_expense_claim", "legacy_visible_interest", "varchar")
ensure_column("sc_expense_claim", "legacy_visible_repayment_time", "timestamp")
ensure_column("sc_fund_account_operation", "legacy_visible_document_no", "varchar")
ensure_column("sc_fund_account_operation", "legacy_visible_project_name", "varchar")
ensure_column("sc_fund_account_operation", "legacy_visible_account_name", "varchar")
ensure_column("sc_fund_account_operation", "legacy_visible_counterparty_account_name", "varchar")
ensure_column("sc_fund_account_operation", "legacy_visible_transfer_type", "varchar")
ensure_column("sc_fund_account_operation", "legacy_visible_reason", "varchar")
ensure_column("sc_fund_account_operation", "legacy_visible_note", "text")
ensure_column("sc_financing_loan", "legacy_visible_project_name", "varchar")
ensure_column("sc_financing_loan", "legacy_visible_request_department", "varchar")
ensure_column("sc_financing_loan", "legacy_visible_request_time", "timestamp")
ensure_column("sc_financing_loan", "legacy_visible_applicant", "varchar")
ensure_column("sc_financing_loan", "legacy_visible_budget_included", "varchar")
ensure_column("sc_financing_loan", "legacy_visible_actual_loan_amount", "varchar")
ensure_column("sc_financing_loan", "legacy_visible_fund_usage_plan", "text")
ensure_column("sc_financing_loan", "legacy_visible_payee", "varchar")
ensure_column("sc_financing_loan", "legacy_visible_receipt_account", "varchar")
ensure_column("sc_financing_loan", "legacy_visible_bank_name", "varchar")
ensure_column("sc_financing_loan", "legacy_visible_company_name", "varchar")
ensure_column("sc_financing_loan", "legacy_visible_note", "text")
ensure_column("sc_financing_loan", "legacy_visible_payer_unit", "varchar")
ensure_column("sc_financing_loan", "legacy_visible_receiver_unit", "varchar")
ensure_column("sc_financing_loan", "legacy_visible_counterparty_name", "varchar")
ensure_column("sc_financing_loan", "legacy_visible_counterparty_account", "varchar")
ensure_column("sc_financing_loan", "legacy_visible_loan_account", "varchar")
ensure_column("sc_financing_loan", "legacy_visible_approved_amount", "varchar")
ensure_column("sc_financing_loan", "legacy_visible_request_amount", "varchar")
ensure_column("sc_financing_loan", "legacy_visible_expected_return_time", "timestamp")
ensure_column("sc_financing_loan", "legacy_visible_loan_type", "varchar")
ensure_column("sc_financing_loan", "legacy_visible_loan_bank", "varchar")
ensure_column("sc_financing_loan", "legacy_visible_due_interest", "varchar")
ensure_column("sc_financing_loan", "legacy_visible_repayment_amount", "varchar")
ensure_column("sc_financing_loan", "legacy_visible_unpaid_amount", "varchar")
ensure_column("sc_financing_loan", "legacy_visible_loan_date", "timestamp")
ensure_column("sc_financing_loan", "legacy_visible_repayment_date", "timestamp")
ensure_column("sc_financing_loan", "legacy_visible_loan_days", "varchar")
ensure_column("sc_financing_loan", "legacy_visible_annual_rate", "varchar")
ensure_column("sc_financing_loan", "legacy_visible_repayment_account", "varchar")
ensure_column("sc_financing_loan", "legacy_visible_writer", "varchar")
ensure_column("sc_financing_loan", "legacy_visible_actual_repayment_days", "varchar")
ensure_column("sc_financing_loan", "legacy_visible_actual_annual_rate", "varchar")
ensure_column("sc_financing_loan", "legacy_visible_loan_interest", "varchar")
ensure_column("sc_invoice_registration", "legacy_visible_contract_no", "varchar")
ensure_column("sc_invoice_registration", "legacy_visible_application_date", "timestamp")
ensure_column("sc_invoice_registration", "legacy_visible_invoice_state", "varchar")
ensure_column("sc_invoice_registration", "legacy_visible_partner_name", "varchar")
ensure_column("sc_invoice_registration", "legacy_visible_cumulative_invoice_amount", "varchar")
ensure_column("sc_invoice_registration", "legacy_visible_invoice_count", "varchar")
ensure_column("sc_invoice_registration", "legacy_visible_current_invoice_amount", "varchar")
ensure_column("sc_invoice_registration", "legacy_visible_note", "text")
ensure_column("sc_invoice_registration", "legacy_visible_kingdee_no", "varchar")
ensure_column("sc_invoice_registration", "legacy_visible_surcharge_amount", "varchar")
ensure_column("sc_invoice_registration", "legacy_visible_tax_rate", "varchar")
ensure_column("sc_invoice_registration", "legacy_visible_related_receipt_amount", "varchar")
ensure_column("sc_invoice_registration", "legacy_visible_invoice_no", "varchar")
ensure_column("sc_invoice_registration", "legacy_visible_invoice_type", "varchar")
ensure_column("sc_invoice_registration", "legacy_visible_invoice_issue_company", "varchar")
ensure_column("tender_doc_purchase", "legacy_visible_applicant_name", "varchar")
ensure_column("tender_doc_purchase", "legacy_visible_document_state", "varchar")
ensure_column("tender_bid", "legacy_visible_document_state", "varchar")
ensure_column("tender_bid", "legacy_visible_opening_time", "timestamp")
ensure_column("tender_bid", "legacy_visible_project_name", "varchar")
ensure_column("tender_bid", "legacy_visible_registration_time", "timestamp")
ensure_column("tender_bid", "legacy_visible_creator_name", "varchar")
ensure_column("tender_guarantee", "legacy_visible_document_state", "varchar")
ensure_column("tender_guarantee", "legacy_visible_document_no", "varchar")
ensure_column("tender_guarantee", "legacy_visible_project_name", "varchar")
ensure_column("tender_guarantee", "legacy_visible_creator_name", "varchar")
ensure_column("tender_guarantee", "legacy_visible_created_time", "timestamp")
ensure_column("sc_business_entity", "legacy_visible_creator_name", "varchar")
ensure_column("sc_business_entity", "legacy_visible_created_time", "timestamp")
ensure_column("construction_contract", "legacy_visible_document_state", "varchar")
ensure_column("construction_contract", "legacy_visible_document_no", "varchar")
ensure_column("construction_contract", "legacy_visible_contract_date", "date")
ensure_column("construction_contract", "legacy_visible_archived", "varchar")
ensure_column("construction_contract", "legacy_visible_counterparty", "varchar")
ensure_column("construction_contract", "legacy_visible_project_name", "varchar")
ensure_column("construction_contract", "legacy_visible_title", "varchar")
ensure_column("construction_contract", "legacy_visible_category", "varchar")
ensure_column("construction_contract", "legacy_visible_contract_no", "varchar")
ensure_column("construction_contract", "legacy_visible_amount", "varchar")
ensure_column("construction_contract", "legacy_visible_settlement_amount", "varchar")
ensure_column("construction_contract", "legacy_visible_invoice_amount", "varchar")
ensure_column("construction_contract", "legacy_visible_received_amount", "varchar")
ensure_column("construction_contract", "legacy_visible_unreceived_amount", "varchar")
ensure_column("construction_contract", "legacy_visible_unreceived_rate", "varchar")
ensure_column("construction_contract", "legacy_visible_affiliated_person", "varchar")
ensure_column("construction_contract", "legacy_visible_engineering_address", "varchar")
ensure_column("construction_contract", "legacy_visible_engineering_content", "text")
ensure_column("construction_contract", "legacy_visible_creator_name", "varchar")
ensure_column("construction_contract", "legacy_visible_created_time", "timestamp")
ensure_column("sc_document_admin_document", "legacy_visible_project_name", "varchar")
ensure_column("sc_document_admin_document", "legacy_visible_document_type", "varchar")
ensure_column("sc_document_admin_document", "legacy_visible_description", "text")
ensure_column("sc_document_admin_document", "legacy_visible_creator_name", "varchar")
ensure_column("sc_document_admin_document", "legacy_visible_note", "text")
ensure_column("sc_document_admin_document", "legacy_visible_created_time", "timestamp")
ensure_column("sc_document_admin_document", "legacy_visible_application_date", "date")
ensure_column("sc_document_admin_document", "legacy_visible_department", "varchar")
ensure_column("sc_document_admin_document", "legacy_visible_borrower", "varchar")
ensure_column("sc_document_admin_document", "legacy_visible_contact", "varchar")
ensure_column("sc_document_admin_document", "legacy_visible_borrow_form", "varchar")
ensure_column("sc_document_admin_document", "legacy_visible_borrow_date", "date")
ensure_column("sc_document_admin_document", "legacy_visible_responsible_person", "varchar")
ensure_column("sc_document_admin_document", "legacy_visible_return_request_date", "date")
ensure_column("sc_document_admin_document", "legacy_visible_return_apply_time", "timestamp")
ensure_column("sc_document_admin_document", "legacy_visible_returned", "varchar")
ensure_column("sc_document_admin_document", "legacy_visible_return_confirm_time", "timestamp")
ensure_column("sc_document_admin_document", "legacy_visible_return_date", "date")
ensure_column("sc_document_admin_document", "legacy_visible_modifier", "varchar")
ensure_column("sc_document_admin_document", "legacy_visible_modified_date", "timestamp")
ensure_column("sc_document_admin_document", "legacy_visible_modify_note", "text")
ensure_column("sc_document_admin_document", "legacy_visible_reviewer", "varchar")
ensure_column("sc_document_admin_document", "legacy_visible_review_time", "timestamp")
ensure_column("sc_document_admin_document", "legacy_visible_review_opinion", "text")
ensure_column("sc_office_admin_document", "legacy_visible_project_name", "varchar")
ensure_column("sc_office_admin_document", "legacy_visible_applicant", "varchar")
ensure_column("sc_office_admin_document", "legacy_visible_department", "varchar")
ensure_column("sc_office_admin_document", "legacy_visible_leave_days", "varchar")
ensure_column("sc_office_admin_document", "legacy_visible_leave_type", "varchar")
ensure_column("sc_office_admin_document", "legacy_visible_leave_time", "varchar")
ensure_column("sc_office_admin_document", "legacy_visible_cancel_time", "varchar")
ensure_column("sc_office_admin_document", "legacy_visible_note", "text")
ensure_column("sc_office_admin_document", "legacy_visible_leave_duration", "varchar")
ensure_column("sc_office_admin_document", "legacy_visible_creator_name", "varchar")
ensure_column("sc_office_admin_document", "legacy_visible_created_time", "timestamp")
ensure_column("sc_office_admin_document", "legacy_visible_seal_use_time", "date")
ensure_column("sc_office_admin_document", "legacy_visible_department_manager_sign", "varchar")
ensure_column("sc_office_admin_document", "legacy_visible_seal_type", "varchar")
ensure_column("sc_office_admin_document", "legacy_visible_seal_text", "varchar")
ensure_column("sc_office_admin_document", "legacy_visible_handler_sign", "varchar")
ensure_column("sc_office_admin_document", "legacy_visible_leader_sign", "varchar")
ensure_column("sc_office_admin_document", "legacy_visible_copy_count", "varchar")
ensure_column("sc_office_admin_document", "legacy_visible_return_time", "date")
ensure_column("sc_office_admin_document", "legacy_visible_contract_amount", "varchar")
ensure_column("sc_office_admin_document", "legacy_visible_contract_no", "varchar")
ensure_column("sc_office_admin_document", "legacy_visible_company", "varchar")
ensure_column("sc_office_admin_document", "legacy_visible_seal_company", "varchar")
ensure_column("sc_office_admin_document", "legacy_visible_take_out", "varchar")

salary_rows = read_csv("/mnt/artifacts/migration/fresh_db_legacy_salary_line_replay_payload_v1.csv")
profile_rows = read_csv("/mnt/artifacts/migration/fresh_db_legacy_user_profile_replay_payload_v1.csv")
social_person_rows = read_csv("/mnt/artifacts/migration/scbs_legacy_social_person_visible_payload_v1.tsv")
subsidy_rows = read_csv("/mnt/artifacts/migration/scbs_legacy_subsidy_visible_payload_v1.tsv")
deduction_rows = read_csv("/mnt/artifacts/migration/fresh_db_legacy_deduction_adjustment_line_replay_payload_v1.csv")
expense_reimbursement_rows = read_csv("/mnt/artifacts/migration/fresh_db_legacy_expense_reimbursement_line_replay_payload_v1.csv")
account_transaction_rows = read_csv("/mnt/artifacts/migration/fresh_db_legacy_account_transaction_replay_payload_v1.csv")
employee_loan_visible_rows = read_csv("/mnt/artifacts/migration/BGGL_JHK_JKSQ_visible.tsv")
employee_repayment_visible_rows = read_csv("/mnt/artifacts/migration/BGGL_JHK_HKDJ_visible.tsv")
contractor_loan_visible_rows = read_csv("/mnt/artifacts/migration/ZJGL_ZCDFSZ_FXJK_JK_visible.tsv")
project_company_loan_visible_rows = read_csv("/mnt/artifacts/migration/ZJGL_ZJSZ_DKGL_DKDJ_visible.tsv")
project_company_repayment_visible_rows = read_csv("/mnt/artifacts/migration/ZJGL_ZJSZ_DKGL_HKDJ_visible.tsv")
contractor_project_repay_visible_rows = read_csv("/mnt/artifacts/migration/ZJGL_ZCDFSZ_FXJK_HK_visible.tsv")
invoice_request_visible_rows = read_csv("/mnt/artifacts/migration/C_JXXP_KJFPSQ_visible.tsv")
invoice_registration_visible_rows = read_csv("/mnt/artifacts/migration/C_JXXP_XXKPDJ_visible.tsv")
tender_rows = read_csv("/mnt/artifacts/migration/fresh_db_legacy_tender_doc_purchase_payload_v1.csv")
tender_bid_rows = {}
with Path("/mnt/artifacts/migration/fresh_db_legacy_tender_registration_replay_payload_v1.csv").open(
    encoding="utf-8-sig", newline=""
) as handle:
    for row in csv.DictReader(handle):
        document_no = clean(row.get("document_no"))
        if document_no:
            tender_bid_rows[document_no] = row
tender_registration_fact_rows = read_csv("/mnt/artifacts/migration/scbs_tender_registration_fact_visible_payload_v1.csv")
business_entity_rows = read_csv("/mnt/artifacts/migration/scbs_business_entity_candidates_v1.csv")
contract_visible_rows = read_csv("/mnt/artifacts/migration/T_ProjectContract_Out_visible.tsv")
business_residual_rows = read_csv("/mnt/artifacts/migration/fresh_db_legacy_business_fact_residual_replay_payload_v1.csv")
borrow_visible_rows = read_csv("/mnt/artifacts/migration/BGGL_TZXX_document_borrow_visible.tsv")

hr_updated = 0
for legacy_id, row in salary_rows.items():
    note = clean(row.get("line_note") or row.get("source_note"))
    env.cr.execute(  # noqa: F821
        """
        UPDATE sc_hr_payroll_document
           SET legacy_visible_creator_name = %s,
               legacy_visible_created_time = %s,
               legacy_visible_people_count = %s,
               legacy_visible_type = %s,
               legacy_visible_note = %s
         WHERE legacy_source_id = %s
           AND fact_type IN ('salary_registration', 'social_registration')
        """,
        (
            clean(row.get("creator_name")) or None,
            parse_datetime(row.get("created_time")),
            clean(row.get("payment_people_count") or row.get("header_people_count")) or None,
            clean(row.get("source_dataset")) or None,
            note or None,
            legacy_id,
        ),
    )
    hr_updated += env.cr.rowcount  # noqa: F821

profile_department_updated = 0
for legacy_id, row in profile_rows.items():
    env.cr.execute(  # noqa: F821
        """
        UPDATE sc_legacy_user_profile
           SET department_name = %s,
               department_scope_summary = %s
         WHERE legacy_user_id = %s
        """,
        (
            clean(row.get("department_name")) or None,
            clean(row.get("department_scope_summary")) or None,
            legacy_id,
        ),
    )
    profile_department_updated += env.cr.rowcount  # noqa: F821

social_person_updated = 0
for legacy_id, row in social_person_rows.items():
    env.cr.execute(  # noqa: F821
        """
        UPDATE sc_hr_payroll_document
           SET legacy_document_state = %s,
               legacy_visible_creator_name = %s,
               legacy_visible_created_time = %s,
               legacy_visible_note = %s,
               legacy_visible_certificate_fee = %s
         WHERE split_part(legacy_source_id, '#', 1) = %s
           AND fact_type = 'social_person_registration'
        """,
        (
            clean(row.get("DJZT")) or None,
            clean(row.get("LRR")) or None,
            parse_datetime(row.get("LRSJ")),
            clean(row.get("BZ")) or None,
            clean(row.get("ZSFY")) or None,
            legacy_id,
        ),
    )
    social_person_updated += env.cr.rowcount  # noqa: F821

subsidy_updated = 0
for legacy_id, row in subsidy_rows.items():
    env.cr.execute(  # noqa: F821
        """
        UPDATE sc_hr_payroll_document
           SET legacy_document_no = %s,
               legacy_document_state = %s,
               payer_unit = %s,
               legacy_visible_creator_name = %s,
               legacy_visible_created_time = %s,
               legacy_visible_item_type = %s
         WHERE split_part(legacy_source_id, '#', 1) = %s
           AND fact_type = 'subsidy'
        """,
        (
            clean(row.get("DJBH")) or None,
            clean(row.get("DJZT")) or None,
            clean(row.get("XMMC")) or None,
            clean(row.get("LRR")) or None,
            parse_datetime(row.get("LRSJ")),
            clean(row.get("D_SCBSJS_BZSX") or row.get("SY")) or None,
            legacy_id,
        ),
    )
    subsidy_updated += env.cr.rowcount  # noqa: F821

deduction_updated = 0
for legacy_id, row in deduction_rows.items():
    env.cr.execute(  # noqa: F821
        """
        UPDATE sc_expense_claim
           SET legacy_visible_title = %s,
               legacy_visible_project_name = %s,
               legacy_visible_adjustment_item = %s,
               legacy_visible_returned_flag = %s
         WHERE split_part(legacy_record_id, ':', 1) = %s
           AND claim_type = 'expense'
           AND expense_type = '扣款实缴登记'
        """,
        (
            clean(row.get("title")) or None,
            clean(row.get("project_name")) or None,
            clean(row.get("adjustment_item_name")) or None,
            clean(row.get("returned_flag")) or None,
            legacy_id,
        ),
    )
    deduction_updated += env.cr.rowcount  # noqa: F821

deduction_refund_updated = 0
for legacy_id, row in account_transaction_rows.items():
    env.cr.execute(  # noqa: F821
        """
        UPDATE sc_expense_claim
           SET legacy_visible_adjustment_item = %s,
               legacy_visible_returned_flag = %s,
               legacy_visible_project_name = %s,
               legacy_visible_note = %s
         WHERE split_part(legacy_record_id, ':', 1) = %s
           AND claim_type = 'deduction_refund'
           AND expense_type = '扣款实缴退回'
        """,
        (
            clean(row.get("category") or row.get("counterparty_account_name")) or None,
            "是",
            clean(row.get("project_name")) or None,
            clean(row.get("note")) or None,
            legacy_id,
        ),
    )
    deduction_refund_updated += env.cr.rowcount  # noqa: F821

expense_reimbursement_updated = 0
for legacy_id, row in expense_reimbursement_rows.items():
    env.cr.execute(  # noqa: F821
        """
        UPDATE sc_expense_claim
           SET legacy_visible_project_name = %s,
               legacy_visible_document_state = %s,
               legacy_visible_document_no = %s,
               legacy_visible_date = %s,
               legacy_visible_department = %s,
               legacy_visible_summary = %s,
               legacy_visible_amount = %s,
               legacy_visible_note = %s,
               creator_name = %s,
               created_time = %s
         WHERE legacy_source_table = 'CWGL_FYBX_CB'
           AND legacy_record_id = %s
        """,
        (
            clean(row.get("project_name")) or None,
            clean(row.get("document_state")) or None,
            clean(row.get("document_no")) or None,
            parse_datetime(row.get("document_date")),
            clean(row.get("department_name")) or None,
            clean(row.get("summary")) or None,
            clean(row.get("amount")) or None,
            clean(row.get("note") or row.get("header_note")) or None,
            clean(row.get("creator_name")) or None,
            parse_datetime(row.get("created_time")),
            legacy_id,
        ),
    )
    expense_reimbursement_updated += env.cr.rowcount  # noqa: F821

contractor_project_repay_updated = 0
for legacy_id, row in contractor_project_repay_visible_rows.items():
    env.cr.execute(  # noqa: F821
        """
        UPDATE sc_expense_claim
           SET legacy_visible_project_name = %s,
               legacy_visible_borrower = %s,
               legacy_visible_loan_amount = %s,
               legacy_visible_repayment_amount = %s,
               legacy_visible_summary = %s,
               legacy_visible_loan_rate = %s,
               legacy_visible_interest = %s,
               legacy_visible_repayment_time = %s,
               legacy_visible_note = %s,
               creator_name = %s,
               created_time = %s
         WHERE legacy_source_table = 'ZJGL_ZCDFSZ_FXJK_HK'
           AND split_part(legacy_record_id, ':', 1) = %s
        """,
        (
            clean(row.get("XMMC")) or None,
            clean(row.get("JKR")) or None,
            clean(row.get("JKJE")) or None,
            clean(row.get("HKJE")) or None,
            clean(row.get("YT")) or None,
            clean(row.get("JKLX")) or None,
            clean(row.get("LX")) or None,
            parse_datetime(row.get("HKSJ")),
            clean(row.get("BZ")) or None,
            clean(row.get("LRR")) or None,
            parse_datetime(row.get("LRSJ")),
            legacy_id,
        ),
    )
    contractor_project_repay_updated += env.cr.rowcount  # noqa: F821

fund_account_between_updated = 0
for legacy_id, row in account_transaction_rows.items():
    if clean(row.get("source_table")) != "C_FKGL_ZHJZJWL":
        continue
    env.cr.execute(  # noqa: F821
        """
        UPDATE sc_fund_account_operation
           SET legacy_visible_document_no = %s,
               legacy_visible_project_name = %s,
               legacy_visible_account_name = %s,
               legacy_visible_counterparty_account_name = %s,
               legacy_visible_transfer_type = %s,
               legacy_visible_reason = %s,
               legacy_visible_note = %s
         WHERE split_part(legacy_record_id, ':', 1) = %s
           AND legacy_source_table = 'C_FKGL_ZHJZJWL'
        """,
        (
            clean(row.get("document_no")) or None,
            clean(row.get("project_name")) or None,
            clean(row.get("account_name")) or None,
            clean(row.get("counterparty_account_name")) or None,
            clean(row.get("source_summary") or row.get("category")) or None,
            clean(row.get("note") or row.get("source_summary")) or None,
            clean(row.get("note")) or None,
            legacy_id,
        ),
    )
    fund_account_between_updated += env.cr.rowcount  # noqa: F821

financing_employee_loan_updated = 0
for legacy_id, row in employee_loan_visible_rows.items():
    env.cr.execute(  # noqa: F821
        """
        UPDATE sc_financing_loan
           SET legacy_visible_project_name = %s,
               legacy_visible_request_department = %s,
               legacy_visible_request_time = %s,
               legacy_visible_applicant = %s,
               legacy_visible_budget_included = %s,
               legacy_visible_actual_loan_amount = %s,
               legacy_visible_fund_usage_plan = %s,
               legacy_visible_payee = %s,
               legacy_visible_receipt_account = %s,
               legacy_visible_bank_name = %s,
               legacy_visible_company_name = %s,
               legacy_visible_note = %s,
               legacy_visible_payer_unit = %s,
               legacy_visible_receiver_unit = %s,
               legacy_visible_counterparty_name = %s,
               legacy_visible_counterparty_account = %s,
               legacy_visible_loan_account = %s,
               legacy_visible_approved_amount = %s,
               legacy_visible_request_amount = %s,
               legacy_visible_expected_return_time = %s,
               legacy_visible_loan_type = %s
         WHERE legacy_source_table = 'BGGL_JHK_JKSQ'
           AND regexp_replace(legacy_record_id, '^BGGL_JHK_JKSQ:', '') = %s
        """,
        (
            clean(row.get("XMMC")) or None,
            clean(row.get("SQBM")) or None,
            parse_datetime(row.get("SQSJ")),
            clean(row.get("SQR")) or None,
            clean(row.get("SFYSN")) or None,
            clean(row.get("JKJE")) or None,
            clean(row.get("ZYZJSYAP")) or None,
            clean(row.get("SKR")) or None,
            clean(row.get("SKZH")) or None,
            clean(row.get("KHYH")) or None,
            clean(row.get("GSMC")) or None,
            clean(row.get("BZ")) or None,
            clean(row.get("FKDW")) or None,
            clean(row.get("SKDW")) or None,
            clean(row.get("WLDWMC")) or None,
            clean(row.get("WLDWZH")) or None,
            clean(row.get("ZKZH")) or None,
            clean(row.get("SJPFJE")) or None,
            clean(row.get("SQJE")) or None,
            parse_datetime(row.get("YJGHSJ")),
            clean(row.get("SJBMC")) or None,
            legacy_id,
        ),
    )
    financing_employee_loan_updated += env.cr.rowcount  # noqa: F821

financing_employee_repayment_updated = 0
for legacy_id, row in employee_repayment_visible_rows.items():
    env.cr.execute(  # noqa: F821
        """
        UPDATE sc_financing_loan
           SET legacy_visible_project_name = %s,
               legacy_visible_request_department = %s,
               legacy_visible_request_time = %s,
               legacy_visible_applicant = %s,
               legacy_visible_budget_included = %s,
               legacy_visible_actual_loan_amount = %s,
               legacy_visible_fund_usage_plan = %s,
               legacy_visible_counterparty_name = %s,
               legacy_visible_counterparty_account = %s,
               legacy_visible_repayment_account = %s,
               legacy_visible_payee = %s,
               legacy_visible_repayment_amount = %s,
               legacy_visible_note = %s,
               legacy_visible_loan_type = %s
         WHERE legacy_source_table = 'BGGL_JHK_HKDJ'
           AND regexp_replace(legacy_record_id, '^BGGL_JHK_HKDJ:', '') = %s
        """,
        (
            clean(row.get("XMMC")) or None,
            clean(row.get("SQBM")) or None,
            parse_datetime(row.get("SQSJ")),
            clean(row.get("SQR")) or None,
            clean(row.get("SFYSN")) or None,
            clean(row.get("JKJE")) or None,
            clean(row.get("ZYZJSYAP")) or None,
            clean(row.get("WLDWMC")) or None,
            clean(row.get("WLDWZH")) or None,
            clean(row.get("HKZH")) or None,
            clean(row.get("HKR")) or None,
            clean(row.get("HKJE")) or None,
            clean(row.get("BZ")) or None,
            clean(row.get("SJBMC")) or None,
            legacy_id,
        ),
    )
    financing_employee_repayment_updated += env.cr.rowcount  # noqa: F821

financing_contractor_loan_updated = 0
for legacy_id, row in contractor_loan_visible_rows.items():
    env.cr.execute(  # noqa: F821
        """
        UPDATE sc_financing_loan
           SET legacy_visible_project_name = %s,
               legacy_visible_applicant = %s,
               legacy_visible_actual_loan_amount = %s,
               legacy_visible_fund_usage_plan = %s,
               legacy_visible_expected_return_time = %s,
               legacy_visible_loan_interest = %s,
               legacy_visible_note = %s,
               legacy_visible_receipt_account = %s,
               legacy_visible_bank_name = %s,
               legacy_visible_receiver_unit = %s,
               creator_name = %s,
               created_time = %s
         WHERE legacy_source_table = 'ZJGL_ZCDFSZ_FXJK_JK'
           AND legacy_record_id = %s
        """,
        (
            clean(row.get("XMMC")) or None,
            clean(row.get("JKR")) or None,
            clean(row.get("JKJE")) or None,
            clean(row.get("YT")) or None,
            parse_datetime(row.get("YDQX")),
            clean(row.get("JKLX")) or None,
            clean(row.get("BZ")) or None,
            clean(row.get("SKZH")) or None,
            clean(row.get("SKKHH")) or None,
            clean(row.get("SKDW")) or None,
            clean(row.get("LRR")) or None,
            parse_datetime(row.get("LRSJ")),
            legacy_id,
        ),
    )
    financing_contractor_loan_updated += env.cr.rowcount  # noqa: F821

financing_project_company_loan_updated = 0
for legacy_id, row in project_company_loan_visible_rows.items():
    env.cr.execute(  # noqa: F821
        """
        UPDATE sc_financing_loan
           SET legacy_visible_project_name = %s,
               legacy_visible_actual_loan_amount = %s,
               legacy_visible_due_interest = %s,
               legacy_visible_repayment_amount = NULL,
               legacy_visible_unpaid_amount = NULL,
               legacy_visible_loan_date = %s,
               legacy_visible_repayment_date = %s,
               legacy_visible_loan_days = %s,
               legacy_visible_annual_rate = %s,
               legacy_visible_loan_account = %s,
               legacy_visible_loan_bank = %s,
               legacy_visible_note = %s,
               creator_name = %s,
               created_time = %s
         WHERE legacy_source_table = 'ZJGL_ZJSZ_DKGL_DKDJ'
           AND legacy_record_id = %s
        """,
        (
            clean(row.get("XMMC")) or None,
            clean(row.get("DKJE")) or None,
            clean(row.get("LX")) or None,
            parse_datetime(row.get("DKRQ")),
            parse_datetime(row.get("HKRQ")),
            clean(row.get("DKSJ")) or None,
            clean(row.get("DKLL")) or None,
            clean(row.get("DKZH")) or None,
            clean(row.get("DKYH")) or None,
            clean(row.get("BZ")) or None,
            clean(row.get("LRR")) or None,
            parse_datetime(row.get("LRSJ")),
            legacy_id,
        ),
    )
    financing_project_company_loan_updated += env.cr.rowcount  # noqa: F821

financing_project_company_repayment_updated = 0
for legacy_id, row in project_company_repayment_visible_rows.items():
    env.cr.execute(  # noqa: F821
        """
        UPDATE sc_financing_loan
           SET legacy_visible_project_name = %s,
               legacy_visible_repayment_amount = %s,
               legacy_visible_actual_repayment_days = %s,
               legacy_visible_actual_annual_rate = %s,
               legacy_visible_loan_interest = %s,
               legacy_visible_loan_bank = %s,
               legacy_visible_loan_account = %s,
               legacy_visible_repayment_account = %s,
               legacy_visible_writer = %s,
               legacy_visible_note = %s,
               creator_name = %s,
               created_time = %s
         WHERE legacy_source_table = 'ZJGL_ZJSZ_DKGL_HKDJ'
           AND split_part(legacy_record_id, ':', 1) = %s
        """,
        (
            clean(row.get("XMMC")) or None,
            clean(row.get("HKJE")) or None,
            clean(row.get("D_SCBSJS_SJHKTS")) or None,
            clean(row.get("D_SCBSJS_SJNLL")) or None,
            clean(row.get("DKLX")) or None,
            clean(row.get("DKYH")) or None,
            clean(row.get("DKZH")) or None,
            clean(row.get("HKZH")) or None,
            clean(row.get("TXR")) or None,
            clean(row.get("BZ")) or None,
            clean(row.get("LRR")) or None,
            parse_datetime(row.get("LRSJ")),
            legacy_id,
        ),
    )
    financing_project_company_repayment_updated += env.cr.rowcount  # noqa: F821

invoice_request_updated = 0
for legacy_id, row in invoice_request_visible_rows.items():
    env.cr.execute(  # noqa: F821
        """
        UPDATE sc_invoice_registration
           SET legacy_visible_project_name = %s,
               legacy_visible_contract_no = %s,
               legacy_visible_application_date = %s,
               legacy_visible_invoice_state = %s,
               legacy_visible_partner_name = %s,
               legacy_visible_cumulative_invoice_amount = %s,
               legacy_visible_invoice_count = %s,
               legacy_visible_current_invoice_amount = %s,
               legacy_visible_note = %s,
               expected_receipt_date = %s,
               applicant_name = %s,
               contract_amount = COALESCE(NULLIF(%s, '')::numeric, 0),
               creator_name = %s,
               created_time = %s
         WHERE legacy_source_table = 'C_JXXP_KJFPSQ'
           AND legacy_record_id = %s
        """,
        (
            clean(row.get("XMMC")) or None,
            clean(row.get("HTBH")) or None,
            parse_datetime(row.get("SQRQ")),
            clean(row.get("DJZT")) or None,
            clean(row.get("SPF_MC")) or None,
            clean(row.get("LJKPJE")) or None,
            clean(row.get("SQKPCS") or row.get("BCKP_ZS")) or None,
            clean(row.get("BCKPJE") or row.get("BCKP_JE")) or None,
            clean(row.get("BZ") or row.get("KPF_BZ")) or None,
            parse_datetime(row.get("YJHKRQ")),
            clean(row.get("SQR")) or None,
            clean(row.get("HTE")),
            clean(row.get("LRR")) or None,
            parse_datetime(row.get("LRSJ")),
            legacy_id,
        ),
    )
    invoice_request_updated += env.cr.rowcount  # noqa: F821

invoice_registration_updated = 0
for legacy_id, row in invoice_registration_visible_rows.items():
    env.cr.execute(  # noqa: F821
        """
        UPDATE sc_invoice_registration
           SET legacy_visible_project_name = %s,
               legacy_visible_application_date = %s,
               legacy_visible_invoice_state = %s,
               legacy_visible_partner_name = %s,
               legacy_visible_invoice_count = %s,
               legacy_visible_current_invoice_amount = %s,
               legacy_visible_note = %s,
               legacy_visible_kingdee_no = %s,
               legacy_visible_surcharge_amount = %s,
               legacy_visible_related_receipt_amount = %s,
               legacy_visible_invoice_type = %s,
               legacy_visible_invoice_issue_company = %s,
               legacy_visible_contract_no = %s,
               push_result = %s,
               amount_total = COALESCE(NULLIF(%s, '')::numeric, 0),
               amount_no_tax = COALESCE(NULLIF(%s, '')::numeric, 0),
               tax_amount = COALESCE(NULLIF(%s, '')::numeric, 0),
               surcharge_amount = COALESCE(NULLIF(%s, '')::numeric, 0),
               invoice_count = COALESCE(NULLIF(%s, '')::numeric, 0)::integer,
               invoice_date = %s,
               creator_name = %s,
               created_time = %s
         WHERE legacy_source_table = 'C_JXXP_XXKPDJ'
           AND legacy_record_id = %s
        """,
        (
            clean(row.get("XMMC")) or None,
            parse_datetime(row.get("SQRQ")),
            clean(row.get("DJZT")) or None,
            clean(row.get("SPFMC")) or None,
            clean(row.get("KPZS") or row.get("KPZS_1")) or None,
            clean(row.get("KPZJE") or row.get("KPZJE_1")) or None,
            clean(row.get("BZ")) or None,
            clean(row.get("OTHER_SYSTEM_CODE") or row.get("GJID")) or None,
            clean(row.get("D_SCBSJS_FJS")) or None,
            clean(row.get("SKZJE")) or None,
            clean(row.get("FPZL")) or None,
            clean(row.get("KPDW")) or None,
            clean(row.get("D_JCLY_HTBH")) or None,
            clean(row.get("D_SCBSJS_IsPush")) or None,
            clean(row.get("KPZJE") or row.get("KPZJE_1")),
            clean(row.get("BHSJE")),
            clean(row.get("ZSE")),
            clean(row.get("D_SCBSJS_FJS")),
            clean(row.get("KPZS") or row.get("KPZS_1")),
            parse_datetime(row.get("FPKJRQ")),
            clean(row.get("LRR")) or None,
            parse_datetime(row.get("LRSJ")),
            legacy_id,
        ),
    )
    invoice_registration_updated += env.cr.rowcount  # noqa: F821

tender_updated = 0
for legacy_id, row in tender_rows.items():
    env.cr.execute(  # noqa: F821
        """
        UPDATE tender_doc_purchase
           SET legacy_visible_applicant_name = %s,
               legacy_visible_document_state = %s
         WHERE legacy_record_id = %s
        """,
        (clean(row.get("applicant_name")) or None, clean(row.get("document_state")) or None, legacy_id),
    )
    tender_updated += env.cr.rowcount  # noqa: F821

tender_bid_updated = 0
for document_no, row in tender_bid_rows.items():
    env.cr.execute(  # noqa: F821
        """
        UPDATE tender_bid
           SET legacy_visible_document_state = %s,
               legacy_visible_opening_time = %s,
               legacy_visible_project_name = %s,
               legacy_visible_registration_time = %s,
               legacy_visible_creator_name = %s
         WHERE name = %s
        """,
        (
            clean(row.get("document_state")) or None,
            parse_datetime(row.get("opening_time") or row.get("bid_time")),
            clean(row.get("project_name")) or None,
            parse_datetime(row.get("registration_time") or row.get("created_time")),
            clean(row.get("creator_name")) or None,
            document_no,
        ),
    )
    tender_bid_updated += env.cr.rowcount  # noqa: F821

tender_guarantee_updated = 0
for _, row in tender_registration_fact_rows.items():
    legacy_id = clean(row.get("id"))
    if not legacy_id:
        continue
    env.cr.execute(  # noqa: F821
        """
        UPDATE tender_guarantee tg
           SET legacy_visible_document_state = %s,
               legacy_visible_document_no = %s,
               legacy_visible_project_name = %s,
               legacy_visible_creator_name = %s,
               legacy_visible_created_time = %s
          FROM tender_bid tb
         WHERE tg.bid_id = tb.id
           AND tb.legacy_fact_id = %s
        """,
        (
            clean(row.get("document_state")) or None,
            clean(row.get("document_no")) or None,
            clean(row.get("project_name")) or None,
            clean(row.get("creator_name")) or None,
            parse_datetime(row.get("created_time")),
            int(legacy_id),
        ),
    )
    tender_guarantee_updated += env.cr.rowcount  # noqa: F821

business_entity_updated = 0
for legacy_id, row in business_entity_rows.items():
    env.cr.execute(  # noqa: F821
        """
        UPDATE sc_business_entity
           SET legacy_visible_creator_name = %s,
               legacy_visible_created_time = %s
         WHERE legacy_xmid = %s
        """,
        (
            clean(row.get("LRR") or row.get("creator_name")) or None,
            parse_datetime(row.get("LRSJ") or row.get("created_time")),
            legacy_id,
        ),
    )
    business_entity_updated += env.cr.rowcount  # noqa: F821
business_entity_visible_csv = Path("/mnt/artifacts/migration/scbs_business_entity_visible_unified.tsv")
env.cr.execute(  # noqa: F821
    """
    SELECT COALESCE(legacy_xmid, '') AS legacy_xmid,
           COALESCE(legacy_xmmc, name, '') AS legacy_xmmc
      FROM sc_business_entity
     WHERE active IS TRUE
    """
)
with business_entity_visible_csv.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.writer(handle, delimiter="\t")
    writer.writerow(["legacy_xmid", "legacy_xmmc"])
    writer.writerows(env.cr.fetchall())  # noqa: F821

construction_contract_visible_updated = 0
for legacy_id, row in contract_visible_rows.items():
    contract_amount = clean(row.get("GCYSZJ") or row.get("f_YZXMJE") or row.get("D_SCBSJS_QYHTJ"))
    received_amount = clean(row.get("GCLJYSK_1") or row.get("GCLJYSK_2"))
    unreceived_amount = clean(row.get("GCQK"))
    env.cr.execute(  # noqa: F821
        """
        UPDATE construction_contract
           SET legacy_visible_document_state = %s,
               legacy_visible_document_no = %s,
               legacy_visible_contract_date = %s,
               legacy_visible_archived = %s,
               legacy_visible_counterparty = %s,
               legacy_visible_project_name = %s,
               legacy_visible_title = %s,
               legacy_visible_category = %s,
               legacy_visible_contract_no = %s,
               legacy_visible_amount = %s,
               legacy_visible_settlement_amount = %s,
               legacy_visible_invoice_amount = %s,
               legacy_visible_received_amount = %s,
               legacy_visible_unreceived_amount = %s,
               legacy_visible_unreceived_rate = %s,
               legacy_visible_affiliated_person = %s,
               legacy_visible_engineering_address = %s,
               legacy_visible_engineering_content = %s,
               legacy_visible_creator_name = %s,
               legacy_visible_created_time = %s
         WHERE legacy_contract_id = %s
        """,
        (
            clean(row.get("DJZT")) or None,
            clean(row.get("DJBH")) or None,
            parse_datetime(row.get("f_HTDLRQ") or row.get("f_HTGSRQ") or row.get("LRRQ")),
            clean(row.get("D_SCBSJS_SFGD")) or None,
            clean(row.get("FBF") or row.get("CBF") or row.get("f_JSDW")) or None,
            clean(row.get("f_XMMC") or row.get("XMMC")) or None,
            clean(row.get("HTBT") or row.get("f_XMMC")) or None,
            clean(row.get("HTLX") or row.get("f_GCXZ")) or None,
            clean(row.get("HTBH") or row.get("legacy_contract_no")) or None,
            contract_amount or None,
            clean(row.get("D_SCBSJS_JSJE") or row.get("GCJSZJ")) or None,
            clean(row.get("GCLJKPJE")) or None,
            received_amount or None,
            unreceived_amount or None,
            clean(row.get("WSKBL") or row.get("visible_unreceived_rate")) or None,
            clean(row.get("GKR")) or None,
            clean(row.get("f_GCDZ")) or None,
            clean(row.get("f_GCNR") or row.get("GCCBFW")) or None,
            clean(row.get("LRR") or row.get("f_LRR")) or None,
            parse_datetime(row.get("LRRQ") or row.get("f_LRSJ")),
            legacy_id,
        ),
    )
    construction_contract_visible_updated += env.cr.rowcount  # noqa: F821
env.cr.execute(  # noqa: F821
    """
    UPDATE construction_contract c
       SET legacy_visible_document_state = COALESCE(c.legacy_visible_document_state, c.legacy_status),
           legacy_visible_document_no = COALESCE(c.legacy_visible_document_no, c.legacy_document_no, c.name),
           legacy_visible_contract_date = COALESCE(c.legacy_visible_contract_date, c.date_contract),
           legacy_visible_archived = COALESCE(c.legacy_visible_archived, CASE WHEN c.archived THEN '是' ELSE '' END),
           legacy_visible_counterparty = COALESCE(c.legacy_visible_counterparty, NULLIF(c.legacy_counterparty_text, ''), rp.name),
           legacy_visible_project_name = COALESCE(c.legacy_visible_project_name, pp.name->>'zh_CN', pp.name->>'en_US'),
           legacy_visible_title = COALESCE(c.legacy_visible_title, c.subject),
           legacy_visible_category = COALESCE(c.legacy_visible_category, c.engineering_category_text),
           legacy_visible_contract_no = COALESCE(c.legacy_visible_contract_no, c.legacy_contract_no),
           legacy_visible_amount = COALESCE(c.legacy_visible_amount, c.visible_contract_amount::text),
           legacy_visible_settlement_amount = COALESCE(c.legacy_visible_settlement_amount, ''),
           legacy_visible_invoice_amount = COALESCE(c.legacy_visible_invoice_amount, c.visible_invoice_amount::text),
           legacy_visible_received_amount = COALESCE(c.legacy_visible_received_amount, c.visible_received_amount::text),
           legacy_visible_unreceived_amount = COALESCE(c.legacy_visible_unreceived_amount, c.visible_unreceived_amount::text),
           legacy_visible_unreceived_rate = COALESCE(c.legacy_visible_unreceived_rate, c.visible_unreceived_rate),
           legacy_visible_affiliated_person = COALESCE(c.legacy_visible_affiliated_person, c.affiliated_person),
           legacy_visible_engineering_address = COALESCE(c.legacy_visible_engineering_address, c.engineering_address),
           legacy_visible_engineering_content = COALESCE(c.legacy_visible_engineering_content, c.engineering_content),
           legacy_visible_creator_name = COALESCE(c.legacy_visible_creator_name, c.entry_user_text),
           legacy_visible_created_time = COALESCE(c.legacy_visible_created_time, c.entry_time)
      FROM project_project pp,
           res_partner rp
     WHERE c.project_id = pp.id
       AND c.partner_id = rp.id
       AND c.legacy_contract_id IS NOT NULL
    """
)
construction_contract_visible_updated += env.cr.rowcount  # noqa: F821
contract_visible_csv = Path("/mnt/artifacts/migration/scbs_construction_contract_visible_unified.tsv")
env.cr.execute(  # noqa: F821
    """
    SELECT legacy_contract_id,
           COALESCE(legacy_visible_document_state, '') AS legacy_visible_document_state,
           COALESCE(legacy_visible_document_no, '') AS legacy_visible_document_no,
           COALESCE(legacy_visible_contract_date::text, '') AS legacy_visible_contract_date,
           COALESCE(legacy_visible_archived, '') AS legacy_visible_archived,
           COALESCE(legacy_visible_counterparty, '') AS legacy_visible_counterparty,
           COALESCE(legacy_visible_project_name, '') AS legacy_visible_project_name,
           COALESCE(legacy_visible_title, '') AS legacy_visible_title,
           COALESCE(legacy_visible_category, '') AS legacy_visible_category,
           COALESCE(legacy_visible_contract_no, '') AS legacy_visible_contract_no,
           COALESCE(legacy_visible_amount, '') AS legacy_visible_amount,
           COALESCE(legacy_visible_settlement_amount, '') AS legacy_visible_settlement_amount,
           COALESCE(legacy_visible_invoice_amount, '') AS legacy_visible_invoice_amount,
           COALESCE(legacy_visible_received_amount, '') AS legacy_visible_received_amount,
           COALESCE(legacy_visible_unreceived_amount, '') AS legacy_visible_unreceived_amount,
           COALESCE(legacy_visible_unreceived_rate, '') AS legacy_visible_unreceived_rate,
           COALESCE(legacy_visible_affiliated_person, '') AS legacy_visible_affiliated_person,
           COALESCE(legacy_visible_engineering_address, '') AS legacy_visible_engineering_address,
           COALESCE(legacy_visible_engineering_content, '') AS legacy_visible_engineering_content,
           COALESCE(legacy_visible_creator_name, '') AS legacy_visible_creator_name,
           COALESCE(legacy_visible_created_time::text, '') AS legacy_visible_created_time
      FROM construction_contract
     WHERE active IS TRUE
       AND legacy_contract_id IS NOT NULL
    """
)
with contract_visible_csv.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.writer(handle, delimiter="\t")
    writer.writerow(
        [
            "legacy_contract_id",
            "legacy_visible_document_state",
            "legacy_visible_document_no",
            "legacy_visible_contract_date",
            "legacy_visible_archived",
            "legacy_visible_counterparty",
            "legacy_visible_project_name",
            "legacy_visible_title",
            "legacy_visible_category",
            "legacy_visible_contract_no",
            "legacy_visible_amount",
            "legacy_visible_settlement_amount",
            "legacy_visible_invoice_amount",
            "legacy_visible_received_amount",
            "legacy_visible_unreceived_amount",
            "legacy_visible_unreceived_rate",
            "legacy_visible_affiliated_person",
            "legacy_visible_engineering_address",
            "legacy_visible_engineering_content",
            "legacy_visible_creator_name",
            "legacy_visible_created_time",
        ]
    )
    writer.writerows(env.cr.fetchall())  # noqa: F821

document_archive_visible_updated = 0
env.cr.execute(  # noqa: F821
    """
    UPDATE sc_document_admin_document d
       SET legacy_visible_document_type = '公司资料存档',
           legacy_visible_description = d.document_title,
           legacy_visible_creator_name = NULLIF(split_part(d.description, '上传人: ', 2), ''),
           legacy_visible_note = d.description,
           legacy_visible_created_time = d.business_date::timestamp
     WHERE d.fact_type = 'company_document_archive'
    """
)
document_archive_visible_updated = env.cr.rowcount  # noqa: F821
archive_visible_csv = Path("/mnt/artifacts/migration/scbs_document_admin_archive_visible.tsv")
env.cr.execute(  # noqa: F821
    """
    SELECT legacy_source_id,
           legacy_document_state,
           COALESCE(legacy_visible_project_name, '') AS legacy_visible_project_name,
           COALESCE(legacy_visible_document_type, '') AS legacy_visible_document_type,
           COALESCE(legacy_visible_description, '') AS legacy_visible_description,
           COALESCE(legacy_visible_creator_name, '') AS legacy_visible_creator_name,
           COALESCE(legacy_visible_note, '') AS legacy_visible_note,
           COALESCE(legacy_visible_created_time::text, '') AS legacy_visible_created_time
      FROM sc_document_admin_document
     WHERE fact_type = 'company_document_archive'
       AND legacy_source_id IS NOT NULL
    """
)
with archive_visible_csv.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.writer(handle, delimiter="\t")
    writer.writerow(
        [
            "legacy_source_id",
            "legacy_document_state",
            "legacy_visible_project_name",
            "legacy_visible_document_type",
            "legacy_visible_description",
            "legacy_visible_creator_name",
            "legacy_visible_note",
            "legacy_visible_created_time",
        ]
    )
    writer.writerows(env.cr.fetchall())  # noqa: F821

document_borrow_visible_updated = 0
for legacy_id, row in borrow_visible_rows.items():
    env.cr.execute(  # noqa: F821
        """
        UPDATE sc_document_admin_document
           SET legacy_visible_project_name = %s,
               legacy_visible_document_type = %s,
               legacy_visible_description = %s,
               legacy_visible_application_date = %s,
               legacy_visible_department = %s,
               legacy_visible_borrower = %s,
               legacy_visible_borrow_form = %s,
               legacy_visible_borrow_date = %s,
               legacy_visible_returned = %s,
               legacy_visible_return_request_date = %s,
               legacy_visible_return_apply_time = %s,
               legacy_visible_return_confirm_time = %s,
               legacy_visible_return_date = %s,
               legacy_visible_note = %s,
               legacy_visible_creator_name = %s,
               legacy_visible_created_time = %s,
               legacy_visible_modifier = %s,
               legacy_visible_modified_date = %s
         WHERE fact_type = 'document_borrow'
           AND legacy_source_id = %s
        """,
        (
            clean(row.get("XMMC")) or None,
            clean(row.get("LXMC") or row.get("WJLX")) or None,
            clean(row.get("WJNR") or row.get("WJBT") or row.get("WJMC")) or None,
            parse_datetime(row.get("DJRQ") or row.get("WJTJRQ")),
            clean(row.get("SSDW") or row.get("SS单位") or row.get("FWBM")) or None,
            clean(row.get("QSR") or row.get("WJNGR")) or None,
            clean(row.get("JJCD") or row.get("WJLX") or row.get("LXMC")) or None,
            parse_datetime(row.get("DJRQ") or row.get("WJTJRQ")),
            "是" if clean(row.get("HQWCSJ")) else "否",
            parse_datetime(row.get("HQWCSJ")),
            parse_datetime(row.get("HQWCSJ")),
            parse_datetime(row.get("HQWCSJ")),
            parse_datetime(row.get("HQWCSJ")),
            clean(row.get("WJNR")) or None,
            clean(row.get("LRR")) or None,
            parse_datetime(row.get("LRSJ")),
            clean(row.get("XGR")) or None,
            parse_datetime(row.get("XGSJ")),
            legacy_id,
        ),
    )
    document_borrow_visible_updated += env.cr.rowcount  # noqa: F821

office_leave_visible_updated = 0
for legacy_id, row in business_residual_rows.items():
    if clean(row.get("source_table")) != "BGGL_HBZJ_XZD_QJXJSPB":
        continue
    env.cr.execute(  # noqa: F821
        """
        UPDATE sc_office_admin_document
           SET legacy_visible_project_name = %s,
               legacy_visible_applicant = %s,
               legacy_visible_department = %s,
               legacy_visible_leave_days = %s,
               legacy_visible_leave_type = %s,
               legacy_visible_leave_time = %s,
               legacy_visible_cancel_time = %s,
               legacy_visible_note = %s,
               legacy_visible_leave_duration = %s,
               legacy_visible_creator_name = %s,
               legacy_visible_created_time = %s
         WHERE fact_type = 'leave_request'
           AND legacy_source_table = 'BGGL_HBZJ_XZD_QJXJSPB'
           AND legacy_source_id = %s
        """,
        (
            clean(row.get("XMMC") or row.get("project_name")) or None,
            clean(row.get("SQRXM")) or None,
            clean(row.get("SZBM")) or None,
            clean(row.get("QJTS")) or None,
            clean(row.get("QJLX")) or None,
            clean(row.get("QJSJ")) or None,
            clean(row.get("SJXJSJ") or row.get("XJSJ")) or None,
            clean(row.get("BZ")) or None,
            clean(row.get("QJSC")) or None,
            clean(row.get("LRR")) or None,
            parse_datetime(row.get("LRSJ")),
            legacy_id,
        ),
    )
    office_leave_visible_updated += env.cr.rowcount  # noqa: F821

office_seal_visible_updated = 0
for legacy_id, row in business_residual_rows.items():
    if clean(row.get("source_table")) != "BGGL_XZD_YZSYSPB":
        continue
    env.cr.execute(  # noqa: F821
        """
        UPDATE sc_office_admin_document
           SET legacy_visible_project_name = %s,
               legacy_visible_applicant = %s,
               legacy_visible_department = %s,
               legacy_visible_seal_use_time = %s,
               legacy_visible_department_manager_sign = %s,
               legacy_visible_seal_type = %s,
               legacy_visible_seal_text = %s,
               legacy_visible_handler_sign = %s,
               legacy_visible_leader_sign = %s,
               legacy_visible_copy_count = %s,
               legacy_visible_return_time = %s,
               legacy_visible_contract_amount = %s,
               legacy_visible_contract_no = %s,
               legacy_visible_company = %s,
               legacy_visible_seal_company = %s,
               legacy_visible_take_out = %s,
               legacy_visible_note = %s,
               legacy_visible_creator_name = %s,
               legacy_visible_created_time = %s
         WHERE fact_type = 'seal_use'
           AND legacy_source_table = 'BGGL_XZD_YZSYSPB'
           AND legacy_source_id = %s
        """,
        (
            clean(row.get("XMMC") or row.get("project_name")) or None,
            clean(row.get("YYSQR")) or None,
            clean(row.get("YYBM")) or None,
            parse_datetime(row.get("YYSJ")),
            clean(row.get("YYBMFZRQZ")) or None,
            clean(row.get("YYZL")) or None,
            clean(row.get("YYWBMCJWH") or row.get("GZWJNBGY")) or None,
            clean(row.get("JBRQZ")) or None,
            clean(row.get("LDQZ")) or None,
            clean(row.get("FS")) or None,
            parse_datetime(row.get("GHSJ")),
            clean(row.get("HTJE")) or None,
            clean(row.get("HTBH")) or None,
            clean(row.get("SSGS")) or None,
            clean(row.get("D_JCLY_SYYZGS")) or None,
            clean(row.get("D_JCLY_SFWD")) or None,
            clean(row.get("BZ")) or None,
            clean(row.get("LRR")) or None,
            parse_datetime(row.get("LRSJ")),
            legacy_id,
        ),
    )
    office_seal_visible_updated += env.cr.rowcount  # noqa: F821

env.cr.commit()  # noqa: F821
print(
    {
        "hr_updated": hr_updated,
        "social_person_updated": social_person_updated,
        "subsidy_updated": subsidy_updated,
        "profile_department_updated": profile_department_updated,
        "deduction_updated": deduction_updated,
        "deduction_refund_updated": deduction_refund_updated,
        "expense_reimbursement_updated": expense_reimbursement_updated,
        "contractor_project_repay_updated": contractor_project_repay_updated,
        "fund_account_between_updated": fund_account_between_updated,
        "financing_employee_loan_updated": financing_employee_loan_updated,
        "financing_employee_repayment_updated": financing_employee_repayment_updated,
        "financing_contractor_loan_updated": financing_contractor_loan_updated,
        "financing_project_company_loan_updated": financing_project_company_loan_updated,
        "financing_project_company_repayment_updated": financing_project_company_repayment_updated,
        "invoice_request_updated": invoice_request_updated,
        "invoice_registration_updated": invoice_registration_updated,
        "tender_updated": tender_updated,
        "tender_bid_updated": tender_bid_updated,
        "tender_guarantee_updated": tender_guarantee_updated,
        "business_entity_updated": business_entity_updated,
        "construction_contract_visible_updated": construction_contract_visible_updated,
        "document_archive_visible_updated": document_archive_visible_updated,
        "document_borrow_visible_updated": document_borrow_visible_updated,
        "office_leave_visible_updated": office_leave_visible_updated,
        "office_seal_visible_updated": office_seal_visible_updated,
    }
)
