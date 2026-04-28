#!/usr/bin/env python3
"""Project legacy receipt income and residual receipt facts into runtime receipt income."""

from __future__ import annotations

import json
import os
from pathlib import Path


def resolve_artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.append(Path("/mnt/artifacts/migration"))
    candidates.append(Path(f"/tmp/history_continuity/{env.cr.dbname}/adhoc"))  # noqa: F821
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return candidate
        except Exception:
            continue
    return Path(f"/tmp/history_continuity/{env.cr.dbname}/adhoc")  # noqa: F821


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def scalar(sql: str) -> object:
    env.cr.execute(sql)  # noqa: F821
    row = env.cr.fetchone()  # noqa: F821
    return row[0] if row else None


artifact_root = resolve_artifact_root()
output_json = artifact_root / "fresh_db_receipt_income_projection_write_result_v1.json"
currency_id = env.company.currency_id.id  # noqa: F821
before = int(scalar("SELECT COUNT(*) FROM sc_receipt_income") or 0)

env.cr.execute(  # noqa: F821
    """
    INSERT INTO sc_receipt_income (
      name, source_origin, source_kind, state, project_id, partner_id,
      date_receipt, document_no, income_category, amount, currency_id,
      legacy_source_model, legacy_source_table, legacy_record_id,
      legacy_document_state, note, active, create_uid, write_uid, create_date, write_date
    )
    SELECT
      COALESCE(NULLIF(f.document_no, ''), 'LEGACY-INCOME-' || f.legacy_record_id),
      'legacy',
      'receipt_income',
      CASE WHEN COALESCE(f.legacy_state, '') = '2' THEN 'legacy_confirmed' ELSE 'draft' END,
      f.project_id,
      f.partner_id,
      COALESCE(f.document_date, CURRENT_DATE),
      NULLIF(f.document_no, ''),
      NULLIF(f.income_category, ''),
      COALESCE(f.source_amount, 0),
      %s,
      'sc.legacy.receipt.income.fact',
      f.legacy_source_table,
      f.legacy_record_id,
      NULLIF(f.legacy_state, ''),
      CONCAT_WS(E'\n',
        '[migration:receipt_income] legacy_record_id=' || f.legacy_record_id,
        NULLIF(f.source_family, ''),
        NULLIF(f.direction, ''),
        NULLIF(f.note, '')
      ),
      TRUE,
      1,
      1,
      NOW(),
      NOW()
    FROM sc_legacy_receipt_income_fact f
    WHERE f.project_id IS NOT NULL
      AND COALESCE(f.source_amount, 0) > 0
    ON CONFLICT (legacy_source_model, legacy_record_id)
    DO UPDATE SET
      state = EXCLUDED.state,
      project_id = EXCLUDED.project_id,
      partner_id = EXCLUDED.partner_id,
      date_receipt = EXCLUDED.date_receipt,
      document_no = EXCLUDED.document_no,
      income_category = EXCLUDED.income_category,
      amount = EXCLUDED.amount,
      legacy_document_state = EXCLUDED.legacy_document_state,
      note = EXCLUDED.note,
      active = EXCLUDED.active,
      write_uid = 1,
      write_date = NOW()
    """,
    [currency_id],
)

env.cr.execute(  # noqa: F821
    """
    INSERT INTO sc_receipt_income (
      name, source_origin, source_kind, state, project_id, partner_id, contract_id,
      date_receipt, document_no, receipt_type, income_category, payment_method,
      receiving_account, bill_no, invoice_ref, amount, deducted_invoice_amount,
      deducted_tax_amount, settlement_amount, currency_id, legacy_source_model,
      legacy_source_table, legacy_record_id, legacy_document_state,
      legacy_residual_reason, legacy_attachment_ref, note, active,
      create_uid, write_uid, create_date, write_date
    )
    SELECT
      COALESCE(NULLIF(r.document_no, ''), 'LEGACY-RECEIPT-' || r.legacy_record_id),
      'legacy',
      'residual_receipt',
      CASE WHEN COALESCE(r.document_state, '') = '2' THEN 'legacy_confirmed' ELSE 'draft' END,
      r.project_id,
      r.partner_id,
      c.id,
      COALESCE(r.document_date, r.created_time::date, CURRENT_DATE),
      NULLIF(r.document_no, ''),
      NULLIF(r.receipt_type, ''),
      NULLIF(r.income_category, ''),
      NULLIF(r.payment_method, ''),
      NULLIF(r.receiving_account, ''),
      NULLIF(r.bill_no, ''),
      NULLIF(r.invoice_ref, ''),
      COALESCE(r.amount, 0),
      COALESCE(r.deducted_invoice_amount, 0),
      COALESCE(r.deducted_tax_amount, 0),
      COALESCE(r.settlement_amount, 0),
      %s,
      'sc.legacy.receipt.residual.fact',
      r.source_table,
      r.legacy_record_id,
      NULLIF(r.document_state, ''),
      NULLIF(r.residual_reason, ''),
      NULLIF(r.attachment_ref, ''),
      CONCAT_WS(E'\n',
        '[migration:receipt_income] legacy_record_id=' || r.legacy_record_id,
        NULLIF(r.residual_reason, ''),
        NULLIF(r.project_name, ''),
        NULLIF(r.partner_name, ''),
        NULLIF(r.note, '')
      ),
      r.active,
      1,
      1,
      NOW(),
      NOW()
    FROM sc_legacy_receipt_residual_fact r
    LEFT JOIN construction_contract c ON c.legacy_contract_id = r.contract_legacy_id
    WHERE r.active
      AND r.project_id IS NOT NULL
      AND COALESCE(r.amount, 0) > 0
    ON CONFLICT (legacy_source_model, legacy_record_id)
    DO UPDATE SET
      state = EXCLUDED.state,
      project_id = EXCLUDED.project_id,
      partner_id = EXCLUDED.partner_id,
      contract_id = EXCLUDED.contract_id,
      date_receipt = EXCLUDED.date_receipt,
      document_no = EXCLUDED.document_no,
      receipt_type = EXCLUDED.receipt_type,
      income_category = EXCLUDED.income_category,
      payment_method = EXCLUDED.payment_method,
      receiving_account = EXCLUDED.receiving_account,
      bill_no = EXCLUDED.bill_no,
      invoice_ref = EXCLUDED.invoice_ref,
      amount = EXCLUDED.amount,
      deducted_invoice_amount = EXCLUDED.deducted_invoice_amount,
      deducted_tax_amount = EXCLUDED.deducted_tax_amount,
      settlement_amount = EXCLUDED.settlement_amount,
      legacy_document_state = EXCLUDED.legacy_document_state,
      legacy_residual_reason = EXCLUDED.legacy_residual_reason,
      legacy_attachment_ref = EXCLUDED.legacy_attachment_ref,
      note = EXCLUDED.note,
      active = EXCLUDED.active,
      write_uid = 1,
      write_date = NOW()
    """,
    [currency_id],
)

env.cr.commit()  # noqa: F821

after = int(scalar("SELECT COUNT(*) FROM sc_receipt_income") or 0)
payload = {
    "status": "PASS",
    "mode": "fresh_db_receipt_income_projection_write",
    "database": env.cr.dbname,  # noqa: F821
    "before": before,
    "after": after,
    "delta": after - before,
    "legacy_rows": int(scalar("SELECT COUNT(*) FROM sc_receipt_income WHERE source_origin = 'legacy'") or 0),
    "legacy_income_rows": int(
        scalar("SELECT COUNT(*) FROM sc_receipt_income WHERE legacy_source_model = 'sc.legacy.receipt.income.fact'")
        or 0
    ),
    "legacy_residual_rows": int(
        scalar("SELECT COUNT(*) FROM sc_receipt_income WHERE legacy_source_model = 'sc.legacy.receipt.residual.fact'")
        or 0
    ),
    "legacy_confirmed": int(
        scalar("SELECT COUNT(*) FROM sc_receipt_income WHERE source_origin = 'legacy' AND state = 'legacy_confirmed'")
        or 0
    ),
    "legacy_with_project": int(
        scalar("SELECT COUNT(*) FROM sc_receipt_income WHERE source_origin = 'legacy' AND project_id IS NOT NULL")
        or 0
    ),
    "legacy_with_partner": int(
        scalar("SELECT COUNT(*) FROM sc_receipt_income WHERE source_origin = 'legacy' AND partner_id IS NOT NULL")
        or 0
    ),
    "legacy_amount_sum": float(
        scalar("SELECT COALESCE(SUM(amount), 0) FROM sc_receipt_income WHERE source_origin = 'legacy'") or 0
    ),
}
write_json(output_json, payload)
print("RECEIPT_INCOME_PROJECTION_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
