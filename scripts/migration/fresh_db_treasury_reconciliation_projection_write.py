#!/usr/bin/env python3
"""Project legacy fund daily and fund confirmation facts into runtime treasury reconciliation."""

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
output_json = artifact_root / "fresh_db_treasury_reconciliation_projection_write_result_v1.json"
currency_id = env.company.currency_id.id  # noqa: F821
before = int(scalar("SELECT COUNT(*) FROM sc_treasury_reconciliation") or 0)

env.cr.execute(  # noqa: F821
    """
    INSERT INTO sc_treasury_reconciliation (
      name, source_origin, source_kind, state, project_id, date_document,
      document_no, account_name, bank_account_no, account_balance, bank_balance,
      system_difference, daily_income, daily_expense, confirmation_amount,
      currency_id, legacy_source_model, legacy_source_table, legacy_record_id,
      legacy_document_state, note, active, create_uid, write_uid, create_date, write_date
    )
    SELECT
      COALESCE(NULLIF(l.document_no, ''), 'LEGACY-DAILY-' || l.legacy_line_id),
      'legacy',
      'daily_line',
      CASE WHEN COALESCE(l.document_state, '') = '2' THEN 'legacy_confirmed' ELSE 'draft' END,
      l.project_id,
      COALESCE(l.document_date, l.period_start::date, l.created_time::date, CURRENT_DATE),
      NULLIF(l.document_no, ''),
      NULLIF(l.account_name, ''),
      NULLIF(l.bank_account_no, ''),
      COALESCE(l.current_account_balance, l.account_balance, 0),
      COALESCE(l.current_bank_balance, 0),
      COALESCE(l.bank_system_difference, 0),
      COALESCE(l.daily_income, 0),
      COALESCE(l.daily_expense, 0),
      0,
      %s,
      'sc.legacy.fund.daily.line',
      l.source_table,
      l.legacy_line_id,
      NULLIF(l.document_state, ''),
      CONCAT_WS(E'\n',
        '[migration:treasury_reconciliation] legacy_line_id=' || l.legacy_line_id,
        NULLIF(l.title, ''),
        NULLIF(l.note, ''),
        NULLIF(l.header_note, '')
      ),
      l.active,
      1,
      1,
      NOW(),
      NOW()
    FROM sc_legacy_fund_daily_line l
    WHERE l.active
      AND l.project_id IS NOT NULL
      AND (
        COALESCE(l.daily_income, 0) <> 0
        OR COALESCE(l.daily_expense, 0) <> 0
        OR COALESCE(l.bank_system_difference, 0) <> 0
        OR COALESCE(l.current_account_balance, l.account_balance, 0) <> 0
        OR COALESCE(l.current_bank_balance, 0) <> 0
      )
    ON CONFLICT (legacy_source_model, legacy_record_id)
    DO UPDATE SET
      state = EXCLUDED.state,
      project_id = EXCLUDED.project_id,
      date_document = EXCLUDED.date_document,
      document_no = EXCLUDED.document_no,
      account_name = EXCLUDED.account_name,
      bank_account_no = EXCLUDED.bank_account_no,
      account_balance = EXCLUDED.account_balance,
      bank_balance = EXCLUDED.bank_balance,
      system_difference = EXCLUDED.system_difference,
      daily_income = EXCLUDED.daily_income,
      daily_expense = EXCLUDED.daily_expense,
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
    INSERT INTO sc_treasury_reconciliation (
      name, source_origin, source_kind, state, project_id, date_document,
      document_no, confirmation_item_name, account_balance, bank_balance,
      system_difference, daily_income, daily_expense, confirmation_amount,
      currency_id, legacy_source_model, legacy_source_table, legacy_record_id,
      legacy_document_state, note, active, create_uid, write_uid, create_date, write_date
    )
    SELECT
      COALESCE(NULLIF(l.document_no, ''), 'LEGACY-CONFIRM-' || l.legacy_line_id),
      'legacy',
      'fund_confirmation',
      CASE WHEN COALESCE(l.document_state, '') = '2' THEN 'legacy_confirmed' ELSE 'draft' END,
      l.project_id,
      COALESCE(l.receipt_time::date, l.created_time::date, CURRENT_DATE),
      NULLIF(l.document_no, ''),
      NULLIF(l.confirmation_item_name, ''),
      0,
      0,
      0,
      0,
      0,
      COALESCE(NULLIF(l.current_actual_amount, 0), l.actual_fund_amount, 0),
      %s,
      'sc.legacy.fund.confirmation.line',
      l.source_table,
      l.legacy_line_id,
      NULLIF(l.document_state, ''),
      CONCAT_WS(E'\n',
        '[migration:treasury_reconciliation] legacy_line_id=' || l.legacy_line_id,
        NULLIF(l.project_name, ''),
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
    WHERE l.active
      AND l.project_id IS NOT NULL
      AND (COALESCE(l.current_actual_amount, 0) <> 0 OR COALESCE(l.actual_fund_amount, 0) <> 0)
    ON CONFLICT (legacy_source_model, legacy_record_id)
    DO UPDATE SET
      state = EXCLUDED.state,
      project_id = EXCLUDED.project_id,
      date_document = EXCLUDED.date_document,
      document_no = EXCLUDED.document_no,
      confirmation_item_name = EXCLUDED.confirmation_item_name,
      confirmation_amount = EXCLUDED.confirmation_amount,
      legacy_document_state = EXCLUDED.legacy_document_state,
      note = EXCLUDED.note,
      active = EXCLUDED.active,
      write_uid = 1,
      write_date = NOW()
    """,
    [currency_id],
)

env.cr.commit()  # noqa: F821

after = int(scalar("SELECT COUNT(*) FROM sc_treasury_reconciliation") or 0)
payload = {
    "status": "PASS",
    "mode": "fresh_db_treasury_reconciliation_projection_write",
    "database": env.cr.dbname,  # noqa: F821
    "before": before,
    "after": after,
    "inserted_or_existing_delta": after - before,
    "legacy_rows": int(scalar("SELECT COUNT(*) FROM sc_treasury_reconciliation WHERE source_origin = 'legacy'") or 0),
    "legacy_daily_rows": int(
        scalar(
            "SELECT COUNT(*) FROM sc_treasury_reconciliation "
            "WHERE legacy_source_model = 'sc.legacy.fund.daily.line'"
        )
        or 0
    ),
    "legacy_confirmation_rows": int(
        scalar(
            "SELECT COUNT(*) FROM sc_treasury_reconciliation "
            "WHERE legacy_source_model = 'sc.legacy.fund.confirmation.line'"
        )
        or 0
    ),
    "legacy_confirmed": int(
        scalar(
            "SELECT COUNT(*) FROM sc_treasury_reconciliation "
            "WHERE source_origin = 'legacy' AND state = 'legacy_confirmed'"
        )
        or 0
    ),
    "legacy_with_project": int(
        scalar(
            "SELECT COUNT(*) FROM sc_treasury_reconciliation "
            "WHERE source_origin = 'legacy' AND project_id IS NOT NULL"
        )
        or 0
    ),
    "daily_income_sum": float(
        scalar("SELECT COALESCE(SUM(daily_income), 0) FROM sc_treasury_reconciliation WHERE source_origin = 'legacy'")
        or 0
    ),
    "daily_expense_sum": float(
        scalar("SELECT COALESCE(SUM(daily_expense), 0) FROM sc_treasury_reconciliation WHERE source_origin = 'legacy'")
        or 0
    ),
    "confirmation_amount_sum": float(
        scalar(
            "SELECT COALESCE(SUM(confirmation_amount), 0) "
            "FROM sc_treasury_reconciliation WHERE source_origin = 'legacy'"
        )
        or 0
    ),
}
write_json(output_json, payload)
print("TREASURY_RECONCILIATION_PROJECTION_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
