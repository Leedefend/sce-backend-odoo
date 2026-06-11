#!/usr/bin/env python3
"""Project legacy arrival confirmations into receipt income at document grain."""

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


def scalar(sql: str, params: list[object] | None = None) -> object:
    env.cr.execute(sql, params or [])  # noqa: F821
    row = env.cr.fetchone()  # noqa: F821
    return row[0] if row else None


artifact_root = resolve_artifact_root()
output_json = artifact_root / "fresh_db_arrival_confirmation_projection_write_result_v1.json"
currency_id = env.ref("base.CNY", raise_if_not_found=False).id  # noqa: F821
uid = env.uid  # noqa: F821

document_domain_sql = """
    source_kind = 'receipt_income'
    AND receipt_type = '到款确认表'
    AND active
"""
line_projection_sql = """
    source_kind = 'receipt_income'
    AND receipt_type = '到款确认表'
    AND legacy_source_model = 'sc.legacy.fund.confirmation.line'
"""

before_visible = int(scalar(f"SELECT COUNT(*) FROM sc_receipt_income WHERE {document_domain_sql}") or 0)
before_line_active = int(scalar(f"SELECT COUNT(*) FROM sc_receipt_income WHERE {line_projection_sql} AND active") or 0)
candidate_count = int(
    scalar(
        """
        SELECT COUNT(*)
        FROM sc_legacy_fund_confirmation_document d
        WHERE d.active
          AND d.project_id IS NOT NULL
          AND COALESCE(d.actual_fund_amount, 0) > 0
        """
    )
    or 0
)

env.cr.execute(  # noqa: F821
    """
    WITH document_source AS (
      SELECT
        d.*,
        COALESCE(d.receipt_time::date, d.created_time::date, CURRENT_DATE) AS receipt_date,
        COALESCE(NULLIF(d.actual_fund_amount, 0), 0) AS receipt_amount,
        COALESCE(NULLIF(d.paid_amount_total, 0), NULLIF(d.actual_fund_amount, 0), 0) AS settlement_value
      FROM sc_legacy_fund_confirmation_document d
      WHERE d.active
        AND d.project_id IS NOT NULL
        AND COALESCE(d.actual_fund_amount, 0) > 0
    )
    UPDATE sc_receipt_income r
    SET
      project_id = s.project_id,
      date_receipt = s.receipt_date,
      receipt_type = '到款确认表',
      amount = s.receipt_amount,
      settlement_amount = s.settlement_value,
      legacy_document_state = s.document_state,
      legacy_attachment_ref = s.attachment_ref,
      creator_name = s.creator_name,
      created_time = s.created_time,
      note = CONCAT_WS(E'\n',
        '[migration:arrival_confirmation_document] legacy_header_id=' || s.legacy_header_id,
        NULLIF(s.project_name, ''),
        NULLIF(s.construction_unit_name, ''),
        NULLIF(s.current_project_stage, '')
      ),
      active = TRUE,
      write_uid = %s,
      write_date = NOW()
    FROM document_source s
    WHERE r.source_kind = 'receipt_income'
      AND r.legacy_source_model = 'sc.legacy.receipt.income.fact'
      AND r.legacy_source_table = 'ZJGL_SZQR_DKQRB'
      AND r.document_no = s.document_no
    """,
    [uid],
)
updated_existing = env.cr.rowcount  # noqa: F821

env.cr.execute(  # noqa: F821
    """
    WITH document_source AS (
      SELECT
        d.*,
        COALESCE(d.receipt_time::date, d.created_time::date, CURRENT_DATE) AS receipt_date,
        COALESCE(NULLIF(d.actual_fund_amount, 0), 0) AS receipt_amount,
        COALESCE(NULLIF(d.paid_amount_total, 0), NULLIF(d.actual_fund_amount, 0), 0) AS settlement_value
      FROM sc_legacy_fund_confirmation_document d
      WHERE d.active
        AND d.project_id IS NOT NULL
        AND COALESCE(d.actual_fund_amount, 0) > 0
        AND NOT EXISTS (
          SELECT 1
          FROM sc_receipt_income existing
          WHERE existing.source_kind = 'receipt_income'
            AND existing.receipt_type = '到款确认表'
            AND existing.document_no = d.document_no
            AND existing.active
            AND existing.legacy_source_model <> 'sc.legacy.fund.confirmation.line'
        )
    )
    INSERT INTO sc_receipt_income (
      name, source_origin, source_kind, state, project_id, partner_id, contract_id,
      date_receipt, document_no, receipt_type, income_category, payment_method,
      receiving_account, receiving_account_name, receiving_account_no,
      receiving_bank_name, bill_no, invoice_ref, amount, deducted_invoice_amount,
      deducted_tax_amount, settlement_amount, currency_id, legacy_source_model,
      legacy_source_table, legacy_record_id, legacy_document_state,
      legacy_attachment_ref, creator_legacy_user_id, creator_name, created_time,
      note, active, create_uid, write_uid, create_date, write_date
    )
    SELECT
      COALESCE(NULLIF(s.document_no, ''), 'DKQR-' || LEFT(s.legacy_header_id, 12)),
      'legacy',
      'receipt_income',
      CASE WHEN COALESCE(s.document_state, '') = '审核通过' THEN 'legacy_confirmed' ELSE 'draft' END,
      s.project_id,
      p.id,
      NULL,
      s.receipt_date,
      NULLIF(s.document_no, ''),
      '到款确认表',
      '到款确认',
      NULL,
      NULL,
      NULL,
      NULL,
      NULL,
      NULL,
      NULL,
      s.receipt_amount,
      COALESCE(s.deducted_amount_total, 0),
      0,
      s.settlement_value,
      %s,
      'sc.legacy.fund.confirmation.document',
      'ZJGL_SZQR_DKQRB',
      s.legacy_header_id,
      NULLIF(s.document_state, ''),
      NULLIF(s.attachment_ref, ''),
      NULL,
      NULLIF(s.creator_name, ''),
      s.created_time,
      CONCAT_WS(E'\n',
        '[migration:arrival_confirmation_document] legacy_header_id=' || s.legacy_header_id,
        NULLIF(s.project_name, ''),
        NULLIF(s.construction_unit_name, ''),
        NULLIF(s.current_project_stage, '')
      ),
      TRUE,
      %s,
      %s,
      NOW(),
      NOW()
    FROM document_source s
    LEFT JOIN LATERAL (
      SELECT rp.id
      FROM res_partner rp
      WHERE rp.active
        AND rp.name = s.construction_unit_name
      ORDER BY rp.id
      LIMIT 1
    ) p ON TRUE
    ON CONFLICT (legacy_source_model, legacy_record_id)
    DO UPDATE SET
      state = EXCLUDED.state,
      project_id = EXCLUDED.project_id,
      partner_id = EXCLUDED.partner_id,
      date_receipt = EXCLUDED.date_receipt,
      document_no = EXCLUDED.document_no,
      receipt_type = EXCLUDED.receipt_type,
      income_category = EXCLUDED.income_category,
      amount = EXCLUDED.amount,
      deducted_invoice_amount = EXCLUDED.deducted_invoice_amount,
      deducted_tax_amount = EXCLUDED.deducted_tax_amount,
      settlement_amount = EXCLUDED.settlement_amount,
      legacy_document_state = EXCLUDED.legacy_document_state,
      legacy_attachment_ref = EXCLUDED.legacy_attachment_ref,
      creator_name = EXCLUDED.creator_name,
      created_time = EXCLUDED.created_time,
      note = EXCLUDED.note,
      active = TRUE,
      write_uid = EXCLUDED.write_uid,
      write_date = NOW()
    """,
    [currency_id, uid, uid],
)
inserted_or_updated_document = env.cr.rowcount  # noqa: F821

env.cr.execute(  # noqa: F821
    f"""
    UPDATE sc_receipt_income
    SET active = FALSE,
        note = CONCAT_WS(E'\n', note, '[migration:arrival_confirmation_document] superseded_by_document_grain_projection'),
        write_uid = %s,
        write_date = NOW()
    WHERE {line_projection_sql}
      AND active
    """,
    [uid],
)
deactivated_line_rows = env.cr.rowcount  # noqa: F821

env.cr.commit()  # noqa: F821

after_visible = int(scalar(f"SELECT COUNT(*) FROM sc_receipt_income WHERE {document_domain_sql}") or 0)
after_line_active = int(scalar(f"SELECT COUNT(*) FROM sc_receipt_income WHERE {line_projection_sql} AND active") or 0)
duplicate_active_documents = int(
    scalar(
        f"""
        SELECT COUNT(*)
        FROM (
          SELECT document_no
          FROM sc_receipt_income
          WHERE {document_domain_sql}
            AND COALESCE(document_no, '') LIKE 'DKQRB-%'
          GROUP BY document_no
          HAVING COUNT(*) > 1
        ) dup
        """
    )
    or 0
)

payload = {
    "mode": "fresh_db_arrival_confirmation_projection_write",
    "database": env.cr.dbname,  # noqa: F821
    "source_model": "sc.legacy.fund.confirmation.document",
    "source_table": "ZJGL_SZQR_DKQRB",
    "target_model": "sc.receipt.income",
    "target_receipt_type": "到款确认表",
    "candidate_count": candidate_count,
    "before_visible": before_visible,
    "after_visible": after_visible,
    "before_line_active": before_line_active,
    "after_line_active": after_line_active,
    "updated_existing": updated_existing,
    "inserted_or_updated_document": inserted_or_updated_document,
    "deactivated_line_rows": deactivated_line_rows,
    "duplicate_active_documents": duplicate_active_documents,
    "amount_sum": float(scalar(f"SELECT COALESCE(SUM(amount), 0) FROM sc_receipt_income WHERE {document_domain_sql}") or 0),
    "settlement_sum": float(
        scalar(f"SELECT COALESCE(SUM(settlement_amount), 0) FROM sc_receipt_income WHERE {document_domain_sql}") or 0
    ),
    "skipped_no_project_or_amount": int(
        scalar(
            """
            SELECT COUNT(*)
            FROM sc_legacy_fund_confirmation_document d
            WHERE d.active
              AND (
                d.project_id IS NULL
                OR COALESCE(d.actual_fund_amount, 0) <= 0
              )
            """
        )
        or 0
    ),
    "status": "PASS" if after_visible == candidate_count and after_line_active == 0 and duplicate_active_documents == 0 else "FAIL",
}
write_json(output_json, payload)
print("FRESH_DB_ARRIVAL_CONFIRMATION_PROJECTION_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
if payload["status"] != "PASS":
    raise SystemExit(1)
