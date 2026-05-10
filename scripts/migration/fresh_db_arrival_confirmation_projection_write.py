#!/usr/bin/env python3
"""Project legacy fund confirmation lines into the arrival confirmation user entry."""

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
currency_id = env.company.currency_id.id  # noqa: F821
target_domain_sql = """
    source_kind = 'receipt_income'
    AND receipt_type = '到款确认表'
    AND legacy_source_model = 'sc.legacy.fund.confirmation.line'
"""

before = int(scalar(f"SELECT COUNT(*) FROM sc_receipt_income WHERE {target_domain_sql}") or 0)
candidate_count = int(
    scalar(
        """
        SELECT COUNT(*)
        FROM sc_legacy_fund_confirmation_line l
        WHERE l.active
          AND l.project_id IS NOT NULL
          AND COALESCE(NULLIF(l.current_actual_amount, 0), l.actual_fund_amount, 0) > 0
        """
    )
    or 0
)

env.cr.execute(  # noqa: F821
    """
    INSERT INTO sc_receipt_income (
      name, source_origin, source_kind, state, project_id, partner_id, contract_id,
      date_receipt, document_no, receipt_type, income_category, payment_method,
      receiving_account, receiving_account_name, receiving_account_no,
      receiving_bank_name, bill_no, invoice_ref, amount, deducted_invoice_amount,
      deducted_tax_amount, settlement_amount, currency_id, legacy_source_model,
      legacy_source_table, legacy_record_id, legacy_document_state,
      legacy_attachment_ref, note, active, create_uid, write_uid, create_date, write_date
    )
    SELECT
      COALESCE(NULLIF(l.document_no, '') || '-' || LEFT(l.legacy_line_id, 8), 'DKQR-' || LEFT(l.legacy_line_id, 12)),
      'legacy',
      'receipt_income',
      CASE WHEN COALESCE(l.document_state, '') = '2' THEN 'legacy_confirmed' ELSE 'draft' END,
      l.project_id,
      COALESCE(c.partner_id, p.id),
      c.id,
      COALESCE(l.receipt_time::date, l.created_time::date, CURRENT_DATE),
      NULLIF(l.document_no, ''),
      '到款确认表',
      COALESCE(NULLIF(l.confirmation_item_name, ''), '到款确认'),
      NULL,
      NULL,
      NULL,
      NULL,
      NULL,
      NULL,
      NULL,
      COALESCE(NULLIF(l.current_actual_amount, 0), l.actual_fund_amount, 0),
      0,
      0,
      COALESCE(NULLIF(l.accumulated_actual_amount, 0), l.actual_fund_amount, 0),
      %s,
      'sc.legacy.fund.confirmation.line',
      l.source_table,
      l.legacy_line_id,
      NULLIF(l.document_state, ''),
      NULLIF(l.attachment_ref, ''),
      CONCAT_WS(E'\n',
        '[migration:arrival_confirmation] legacy_line_id=' || l.legacy_line_id,
        NULLIF(l.project_name, ''),
        NULLIF(l.contract_name, ''),
        NULLIF(l.confirmation_item_name, ''),
        NULLIF(l.filler_name, ''),
        NULLIF(l.application_balance_note, ''),
        NULLIF(l.invoice_receipt_note, ''),
        NULLIF(l.quality_return_note, ''),
        NULLIF(l.available_balance_note, ''),
        NULLIF(l.construction_deduction_note, ''),
        NULLIF(l.payable_construction_deduction_note, ''),
        NULLIF(l.note, '')
      ),
      l.active,
      1,
      1,
      NOW(),
      NOW()
    FROM sc_legacy_fund_confirmation_line l
    LEFT JOIN construction_contract c ON c.legacy_contract_id = l.contract_legacy_id
    LEFT JOIN LATERAL (
      SELECT rp.id
      FROM res_partner rp
      WHERE rp.active
        AND rp.name = l.contract_name
      ORDER BY rp.id
      LIMIT 1
    ) p ON TRUE
    WHERE l.active
      AND l.project_id IS NOT NULL
      AND COALESCE(NULLIF(l.current_actual_amount, 0), l.actual_fund_amount, 0) > 0
    ON CONFLICT (legacy_source_model, legacy_record_id)
    DO UPDATE SET
      source_kind = EXCLUDED.source_kind,
      state = EXCLUDED.state,
      project_id = EXCLUDED.project_id,
      partner_id = EXCLUDED.partner_id,
      contract_id = EXCLUDED.contract_id,
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
      note = EXCLUDED.note,
      active = EXCLUDED.active,
      write_uid = 1,
      write_date = NOW()
    """,
    [currency_id],
)

env.cr.commit()  # noqa: F821

after = int(scalar(f"SELECT COUNT(*) FROM sc_receipt_income WHERE {target_domain_sql}") or 0)
visible_rows = int(
    scalar(
        """
        SELECT COUNT(*)
        FROM sc_receipt_income
        WHERE source_kind = 'receipt_income'
          AND receipt_type = '到款确认表'
          AND active
        """
    )
    or 0
)
payload = {
    "mode": "fresh_db_arrival_confirmation_projection_write",
    "database": env.cr.dbname,  # noqa: F821
    "source_model": "sc.legacy.fund.confirmation.line",
    "source_table": "ZJGL_SZQR_DKQRB_CB",
    "target_model": "sc.receipt.income",
    "target_receipt_type": "到款确认表",
    "candidate_count": candidate_count,
    "before_arrival_confirmation": before,
    "after_arrival_confirmation": after,
    "visible_rows": visible_rows,
    "delta": after - before,
    "legacy_confirmed": int(
        scalar(
            f"SELECT COUNT(*) FROM sc_receipt_income WHERE {target_domain_sql} AND state = 'legacy_confirmed'"
        )
        or 0
    ),
    "draft": int(scalar(f"SELECT COUNT(*) FROM sc_receipt_income WHERE {target_domain_sql} AND state = 'draft'") or 0),
    "amount_sum": float(scalar(f"SELECT COALESCE(SUM(amount), 0) FROM sc_receipt_income WHERE {target_domain_sql}") or 0),
    "skipped_no_project_or_amount": int(
        scalar(
            """
            SELECT COUNT(*)
            FROM sc_legacy_fund_confirmation_line l
            WHERE l.active
              AND (
                l.project_id IS NULL
                OR COALESCE(NULLIF(l.current_actual_amount, 0), l.actual_fund_amount, 0) <= 0
              )
            """
        )
        or 0
    ),
    "status": "PASS" if after == candidate_count and visible_rows >= candidate_count else "FAIL",
}
write_json(output_json, payload)
print(json.dumps(payload, ensure_ascii=False, indent=2))
if payload["status"] != "PASS":
    raise SystemExit(1)
