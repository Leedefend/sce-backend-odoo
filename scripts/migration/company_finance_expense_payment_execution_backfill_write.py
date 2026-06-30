#!/usr/bin/env python3
"""Backfill accepted company-finance expenses into the formal payment execution model.

Run through ``odoo shell``. The script is intentionally scoped to the old
company-finance expense acceptance source and writes only formal
``sc.payment.execution`` records. It does not make the industry module depend
on migration input fields at runtime.
"""

from __future__ import annotations

import json
import os


SOURCE_MODEL = "online_old_scbs:C_CWSFK_GSCWZC:list876"
SOURCE_TABLE = "C_CWSFK_GSCWZC"
PAYMENT_FAMILY = "公司财务支出"


def clean(value):
    if value is None or value is False:
        return ""
    text = str(value).replace("\u3000", " ").strip()
    return "" if text in {"False", "false", "None", "NULL"} else text


def ensure_allowed_db():
    allowlist = {
        item.strip()
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_demo").split(",")
        if item.strip()
    }
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_company_finance_backfill": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def amount_value(claim):
    return abs(claim.paid_amount or claim.approved_amount or claim.amount or 0.0)


def date_value(claim):
    return claim.legacy_visible_payment_time or claim.date_claim or False


def document_no_value(claim):
    return clean(claim.legacy_visible_document_no) or clean(claim.legacy_document_no) or clean(claim.name)


def state_value(claim):
    state = clean(claim.legacy_visible_document_state) or clean(claim.legacy_document_state)
    return "legacy_confirmed" if state in {"2", "审核通过", "已审核", "历史已确认"} else "draft"


def values_for(claim, category_id):
    amount = amount_value(claim)
    document_no = document_no_value(claim)
    return {
        "name": document_no or clean(claim.legacy_record_id),
        "source_origin": "legacy",
        "source_kind": "actual_outflow",
        "state": state_value(claim),
        "project_id": claim.project_id.id,
        "business_category_id": category_id,
        "date_payment": date_value(claim),
        "document_no": document_no or False,
        "payment_family": PAYMENT_FAMILY,
        "payment_method": clean(claim.legacy_visible_expense_type) or clean(claim.expense_type) or False,
        "payment_account_name": clean(claim.payment_account_name) or False,
        "receipt_account_name": clean(claim.receipt_account_name) or False,
        "planned_amount": amount,
        "paid_amount": amount,
        "currency_id": claim.currency_id.id,
        "legacy_source_model": SOURCE_MODEL,
        "legacy_source_table": claim.legacy_source_table or SOURCE_TABLE,
        "legacy_record_id": clean(claim.legacy_record_id),
        "legacy_document_state": clean(claim.legacy_visible_document_state) or clean(claim.legacy_document_state) or False,
        "push_result": clean(claim.legacy_visible_push_result) or False,
        "creator_legacy_user_id": clean(claim.creator_legacy_user_id) or False,
        "creator_name": clean(claim.creator_name) or False,
        "created_time": claim.created_time or False,
        "note": claim.note or claim.summary or False,
        "active": claim.active,
        "attachment_ids": [(6, 0, claim.attachment_ids.ids)],
    }


def safe_values(model, values):
    return {key: value for key, value in values.items() if key in model._fields}


ensure_allowed_db()

Claim = env["sc.expense.claim"].sudo().with_context(active_test=False)  # noqa: F821
Execution = env["sc.payment.execution"].sudo().with_context(active_test=False)  # noqa: F821
Category = env["sc.business.category"].sudo()  # noqa: F821

category = Category.search(
    [("code", "=", "finance.payment.execution.company"), ("target_model", "=", "sc.payment.execution")],
    limit=1,
)
if not category:
    raise RuntimeError({"missing_business_category": "finance.payment.execution.company"})

claims = Claim.search([("legacy_source_model", "=", SOURCE_MODEL)], order="created_time asc, id asc")
stats = {
    "source_rows": len(claims),
    "created": 0,
    "existing": 0,
    "skipped_missing_legacy_record_id": 0,
}

for claim in claims:
    legacy_record_id = clean(claim.legacy_record_id)
    if not legacy_record_id:
        stats["skipped_missing_legacy_record_id"] += 1
        continue
    record = Execution.search(
        [("legacy_source_model", "=", SOURCE_MODEL), ("legacy_record_id", "=", legacy_record_id)],
        limit=1,
    )
    if record:
        stats["existing"] += 1
        continue
    Execution.create(safe_values(Execution, values_for(claim, category.id)))
    stats["created"] += 1

env.cr.commit()  # noqa: F821
print(
    "COMPANY_FINANCE_EXPENSE_PAYMENT_EXECUTION_BACKFILL="
    + json.dumps(
        {
            "database": env.cr.dbname,  # noqa: F821
            "mode": "company_finance_expense_payment_execution_backfill_write",
            "status": "PASS",
            **stats,
            "decision": "accepted_company_finance_expense_history_projected_to_formal_sc_payment_execution",
        },
        ensure_ascii=False,
        sort_keys=True,
    )
)
