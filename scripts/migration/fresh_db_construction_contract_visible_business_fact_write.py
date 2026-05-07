#!/usr/bin/env python3
"""Create invoice and receipt facts for the construction contract acceptance surface."""

from __future__ import annotations

import json
import os
from pathlib import Path


OUTPUT_JSON = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", "/mnt/artifacts/migration")) / "fresh_db_construction_contract_visible_business_fact_write_result_v1.json"
SOURCE_MODEL = "construction_contract_visible_surface"


def ensure_allowed_db() -> None:
    allowlist = {item.strip() for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_migration_fresh").split(",") if item.strip()}
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_replay": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def money(value: object) -> float:
    return round(float(value or 0.0), 2)


def close(left: float, right: float) -> bool:
    return abs(money(left) - money(right)) <= 0.01


def reset_existing(model, record_id: str) -> int:
    existing = model.with_context(active_test=False).search(
        [("legacy_source_model", "=", SOURCE_MODEL), ("legacy_record_id", "=", record_id)]
    )
    if existing:
        existing.unlink()
    return len(existing)


def create_invoice(contract, amount: float):
    record_id = f"invoice:{contract.legacy_document_no}"
    removed = reset_existing(Invoice, record_id)
    if amount <= 0:
        return None, removed
    rec = Invoice.create(
        {
            "source_origin": "legacy",
            "source_kind": "invoice_registration",
            "direction": "output" if contract.type == "out" else "input",
            "state": "legacy_confirmed",
            "project_id": contract.project_id.id,
            "partner_id": contract.partner_id.id,
            "contract_id": contract.id,
            "document_no": contract.legacy_document_no,
            "document_date": contract.date_contract or False,
            "invoice_date": contract.date_contract or False,
            "invoice_no": contract.legacy_contract_no or contract.legacy_document_no,
            "invoice_content": contract.subject,
            "amount_no_tax": amount,
            "tax_amount": 0.0,
            "amount_total": amount,
            "legacy_source_model": SOURCE_MODEL,
            "legacy_source_table": "施工合同（新）",
            "legacy_record_id": record_id,
            "legacy_document_state": contract.document_status,
            "legacy_partner_id": contract.partner_id.legacy_partner_id if "legacy_partner_id" in contract.partner_id._fields else "",
            "legacy_partner_name": contract.partner_id.display_name,
            "note": (
                "[migration:construction_contract_visible_business_fact] "
                f"document_no={contract.legacy_document_no}; source_column=累计开票"
            ),
        }
    )
    return rec, removed


def create_receipt(contract, amount: float):
    record_id = f"receipt:{contract.legacy_document_no}"
    removed = reset_existing(Receipt, record_id)
    if amount <= 0:
        return None, removed
    rec = Receipt.create(
        {
            "source_origin": "legacy",
            "source_kind": "receipt_income",
            "state": "legacy_confirmed",
            "project_id": contract.project_id.id,
            "partner_id": contract.partner_id.id,
            "contract_id": contract.id,
            "date_receipt": contract.date_contract or False,
            "document_no": contract.legacy_document_no,
            "receipt_type": "合同收款",
            "income_category": "施工合同收入",
            "invoice_ref": contract.legacy_contract_no or contract.legacy_document_no,
            "amount": amount,
            "deducted_invoice_amount": min(amount, money(contract.visible_invoice_amount)),
            "legacy_source_model": SOURCE_MODEL,
            "legacy_source_table": "施工合同（新）",
            "legacy_record_id": record_id,
            "legacy_document_state": contract.document_status,
            "note": (
                "[migration:construction_contract_visible_business_fact] "
                f"document_no={contract.legacy_document_no}; source_column=累计收款"
            ),
        }
    )
    return rec, removed


ensure_allowed_db()
Contract = env["construction.contract"].sudo()  # noqa: F821
Invoice = env["sc.invoice.registration"].sudo()  # noqa: F821
Receipt = env["sc.receipt.income"].sudo()  # noqa: F821

contracts = Contract.search([("visible_unreceived_rate", "!=", False), ("legacy_document_no", "!=", False)])
created_invoices = []
created_receipts = []
removed_existing = 0
skipped = 0

for contract in contracts:
    invoice_amount = money(contract.visible_invoice_amount)
    required_receipt = money(contract.visible_received_amount)
    invoice, removed = create_invoice(contract, invoice_amount)
    removed_existing += removed
    if invoice:
        created_invoices.append(
            {
                "id": invoice.id,
                "document_no": contract.legacy_document_no,
                "contract_no": contract.legacy_contract_no,
                "amount": invoice.amount_total,
            }
        )
    receipt, removed = create_receipt(contract, required_receipt)
    removed_existing += removed
    if receipt:
        created_receipts.append(
            {
                "id": receipt.id,
                "document_no": contract.legacy_document_no,
                "contract_no": contract.legacy_contract_no,
                "amount": receipt.amount,
            }
        )
    if not invoice and not receipt:
        skipped += 1

env.invalidate_all()  # noqa: F821
post_mismatches = []
balance_reconciliation_mismatches = []
for contract in contracts:
    expected_invoice = money(contract.visible_invoice_amount)
    expected_receipt = money(contract.visible_received_amount)
    contract.invalidate_recordset(["invoice_amount", "received_amount", "contract_unreceived_amount"])
    mismatches = {}
    if not close(contract.invoice_amount, expected_invoice):
        mismatches["累计开票"] = {"system": money(contract.invoice_amount), "expected": expected_invoice}
    if not close(contract.received_amount, expected_receipt):
        mismatches["累计收款"] = {"system": money(contract.received_amount), "expected": expected_receipt}
    if mismatches:
        post_mismatches.append(
            {
                "document_no": contract.legacy_document_no,
                "contract_no": contract.legacy_contract_no,
                "mismatches": mismatches,
            }
        )
    if not close(contract.contract_unreceived_amount, contract.visible_unreceived_amount):
        balance_reconciliation_mismatches.append(
            {
                "document_no": contract.legacy_document_no,
                "contract_no": contract.legacy_contract_no,
                "platform_unreceived": money(contract.contract_unreceived_amount),
                "visible_unreceived": money(contract.visible_unreceived_amount),
            }
        )

status = "PASS" if not post_mismatches else "REVIEW"
payload = {
    "status": status,
    "mode": "fresh_db_construction_contract_visible_business_fact_write",
    "database": env.cr.dbname,  # noqa: F821
    "source_model": SOURCE_MODEL,
    "input_contracts": len(contracts),
    "skipped_without_fact": skipped,
    "removed_existing_rows": removed_existing,
    "created_invoice_rows": len(created_invoices),
    "created_receipt_rows": len(created_receipts),
    "created_invoices": created_invoices,
    "created_receipts": created_receipts,
    "post_mismatches": post_mismatches,
    "visible_balance_reconciliation_mismatches": balance_reconciliation_mismatches,
    "visible_balance_reconciliation_mismatch_count": len(balance_reconciliation_mismatches),
}
OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
OUTPUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
env.cr.commit()  # noqa: F821
print("FRESH_DB_CONSTRUCTION_CONTRACT_VISIBLE_BUSINESS_FACT_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
