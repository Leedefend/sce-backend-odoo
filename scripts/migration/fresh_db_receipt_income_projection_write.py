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
currency_id = env.ref("base.CNY", raise_if_not_found=False).id  # noqa: F821
before = int(scalar("SELECT COUNT(*) FROM sc_receipt_income") or 0)

env.cr.execute(  # noqa: F821
    """
    INSERT INTO sc_receipt_income (
      name, source_origin, source_kind, state, project_id, partner_id,
      date_receipt, document_no, receipt_type, legacy_receipt_type, legacy_receipt_subtype,
      income_category, amount, currency_id,
      legacy_source_model, legacy_source_table, legacy_record_id,
      legacy_document_state, creator_legacy_user_id, creator_name, created_time,
      note, active, create_uid, write_uid, create_date, write_date
    )
    SELECT
      COALESCE(NULLIF(f.document_no, ''), 'LEGACY-INCOME-' || f.legacy_record_id),
      'legacy',
      'receipt_income',
      CASE WHEN COALESCE(f.legacy_state, '') = '2' THEN 'legacy_confirmed' ELSE 'draft' END,
      f.project_id,
      COALESCE(f.partner_id, partner_match.id),
      COALESCE(f.document_date, f.created_time::date),
      NULLIF(f.document_no, ''),
      CASE
        WHEN f.source_family = 'company_financial_income' THEN '公司财务收入'
        WHEN f.source_family = 'receipt_confirmation' THEN '到款确认'
        WHEN f.source_family = 'customer_receipt' THEN '客户收款'
        ELSE NULLIF(f.source_family, '')
      END,
      NULLIF(f.receipt_type, ''),
      NULLIF(f.receipt_subtype, ''),
      NULLIF(f.income_category, ''),
      COALESCE(f.source_amount, 0),
      %s,
      'sc.legacy.receipt.income.fact',
      f.legacy_source_table,
      f.legacy_record_id,
      NULLIF(f.legacy_state, ''),
      NULLIF(f.creator_legacy_user_id, ''),
      NULLIF(f.creator_name, ''),
      f.created_time,
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
    LEFT JOIN LATERAL (
      SELECT rp.id
      FROM res_partner rp
      WHERE rp.active
        AND NULLIF(f.legacy_partner_name, '') IS NOT NULL
        AND rp.name = f.legacy_partner_name
      ORDER BY rp.id
      LIMIT 1
    ) partner_match ON TRUE
    WHERE f.project_id IS NOT NULL
      AND COALESCE(f.source_amount, 0) > 0
    ON CONFLICT (legacy_source_model, legacy_record_id)
    DO UPDATE SET
      state = EXCLUDED.state,
      project_id = EXCLUDED.project_id,
      partner_id = EXCLUDED.partner_id,
      date_receipt = EXCLUDED.date_receipt,
      document_no = EXCLUDED.document_no,
      receipt_type = EXCLUDED.receipt_type,
      legacy_receipt_type = EXCLUDED.legacy_receipt_type,
      legacy_receipt_subtype = EXCLUDED.legacy_receipt_subtype,
      income_category = EXCLUDED.income_category,
      amount = EXCLUDED.amount,
      legacy_document_state = EXCLUDED.legacy_document_state,
      creator_legacy_user_id = EXCLUDED.creator_legacy_user_id,
      creator_name = EXCLUDED.creator_name,
      created_time = EXCLUDED.created_time,
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
      date_receipt, document_no, receipt_type, legacy_receipt_type, legacy_receipt_subtype,
      income_category, payment_method,
      receiving_account, bill_no, invoice_ref, amount, deducted_invoice_amount,
      deducted_tax_amount, settlement_amount, currency_id, legacy_source_model,
      legacy_source_table, legacy_record_id, legacy_document_state,
      legacy_residual_reason, legacy_attachment_ref, creator_legacy_user_id,
      creator_name, created_time, note, active,
      create_uid, write_uid, create_date, write_date
    )
    SELECT
      COALESCE(NULLIF(r.document_no, ''), 'LEGACY-RECEIPT-' || r.legacy_record_id),
      'legacy',
      'residual_receipt',
      CASE WHEN COALESCE(r.document_state, '') = '2' THEN 'legacy_confirmed' ELSE 'draft' END,
      COALESCE(r.project_id, project_match.id),
      r.partner_id,
      c.id,
      COALESCE(r.document_date, r.created_time::date, CURRENT_DATE),
      NULLIF(r.document_no, ''),
      NULLIF(r.receipt_type, ''),
      NULLIF(r.legacy_receipt_type, ''),
      NULLIF(r.legacy_receipt_subtype, ''),
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
      NULLIF(r.creator_legacy_user_id, ''),
      NULLIF(r.creator_name, ''),
      r.created_time,
      CONCAT_WS(E'\n',
        '[migration:receipt_income] legacy_record_id=' || r.legacy_record_id,
        CASE
          WHEN NULLIF(r.contract_legacy_id, '') IS NOT NULL AND LOWER(r.contract_legacy_id) <> 'null'
          THEN 'legacy_contract_id=' || r.contract_legacy_id
          ELSE NULL
        END,
        CASE WHEN NULLIF(r.invoice_ref, '') IS NOT NULL THEN 'invoice_ref=' || r.invoice_ref ELSE NULL END,
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
    LEFT JOIN (
      SELECT DISTINCT ON (legacy_project_id) legacy_project_id, id
      FROM project_project
      WHERE legacy_project_id IS NOT NULL
      ORDER BY legacy_project_id, id
    ) project_match ON project_match.legacy_project_id = r.project_legacy_id
    LEFT JOIN construction_contract c ON c.legacy_contract_id = r.contract_legacy_id
    WHERE r.active
      AND COALESCE(r.project_id, project_match.id) IS NOT NULL
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
      legacy_receipt_type = EXCLUDED.legacy_receipt_type,
      legacy_receipt_subtype = EXCLUDED.legacy_receipt_subtype,
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
      creator_legacy_user_id = EXCLUDED.creator_legacy_user_id,
      creator_name = EXCLUDED.creator_name,
      created_time = EXCLUDED.created_time,
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
