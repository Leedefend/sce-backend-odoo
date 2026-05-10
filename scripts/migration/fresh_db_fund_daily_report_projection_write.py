#!/usr/bin/env python3
"""Project legacy fund daily lines into the editable fund daily report entry."""

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
output_json = artifact_root / "fresh_db_fund_daily_report_projection_write_result_v1.json"
currency_id = env.company.currency_id.id  # noqa: F821
target_domain_sql = """
    operation_type = 'fund_daily_report'
    AND legacy_source_model = 'sc.legacy.fund.daily.line'
"""

before = int(scalar(f"SELECT COUNT(*) FROM sc_fund_account_operation WHERE {target_domain_sql}") or 0)

env.cr.execute(  # noqa: F821
    """
    UPDATE sc_fund_account
    SET display_name = CONCAT_WS(' / ', NULLIF(name, ''), NULLIF(account_no, ''), NULLIF(bank_name, '')),
        write_uid = 1,
        write_date = NOW()
    WHERE active
      AND COALESCE(display_name, '') = ''
      AND COALESCE(name, '') <> ''
    """
)

candidate_count = int(
    scalar(
        """
        SELECT COUNT(*)
        FROM sc_legacy_fund_daily_line l
        WHERE l.active
          AND l.project_id IS NOT NULL
          AND EXISTS (
            SELECT 1
            FROM sc_fund_account a
            WHERE a.active
              AND (
                a.legacy_account_id = l.account_legacy_id
                OR a.account_no = l.bank_account_no
                OR a.name = l.account_name
              )
          )
        """
    )
    or 0
)

env.cr.execute(  # noqa: F821
    """
    INSERT INTO sc_fund_account_operation (
      name, operation_type, operation_date, fund_account_id, project_id,
      company_id, currency_id, amount, daily_income, daily_expense,
      account_balance, bank_balance, before_balance, after_balance,
      operation_reason, state, note, legacy_source_model, legacy_record_id,
      legacy_document_state, active, create_uid, write_uid, create_date, write_date
    )
    SELECT
      COALESCE(NULLIF(l.document_no, '') || '-' || LEFT(l.legacy_line_id, 8), 'ZJRB-' || LEFT(l.legacy_line_id, 12)),
      'fund_daily_report',
      COALESCE(l.document_date, l.period_start::date, l.created_time::date, CURRENT_DATE),
      a.id,
      l.project_id,
      %s,
      %s,
      0,
      COALESCE(l.daily_income, 0),
      COALESCE(l.daily_expense, 0),
      COALESCE(l.current_account_balance, l.account_balance, 0),
      COALESCE(l.current_bank_balance, 0),
      0,
      0,
      COALESCE(NULLIF(l.title, ''), NULLIF(l.account_name, ''), '资金日报表'),
      CASE WHEN COALESCE(l.document_state, '') = '2' THEN 'done' ELSE 'draft' END,
      CONCAT_WS(E'\n',
        '[migration:fund_daily_report] legacy_line_id=' || l.legacy_line_id,
        NULLIF(l.document_no, ''),
        NULLIF(l.project_name, ''),
        NULLIF(l.account_name, ''),
        NULLIF(l.bank_account_no, ''),
        NULLIF(l.creator_name, ''),
        NULLIF(l.note, ''),
        NULLIF(l.header_note, '')
      ),
      'sc.legacy.fund.daily.line',
      l.legacy_line_id,
      NULLIF(l.document_state, ''),
      l.active,
      1,
      1,
      NOW(),
      NOW()
    FROM sc_legacy_fund_daily_line l
    JOIN LATERAL (
      SELECT fa.id
      FROM sc_fund_account fa
      WHERE fa.active
        AND (
          fa.legacy_account_id = l.account_legacy_id
          OR fa.account_no = l.bank_account_no
          OR fa.name = l.account_name
        )
      ORDER BY
        CASE
          WHEN fa.legacy_account_id = l.account_legacy_id THEN 0
          WHEN fa.account_no = l.bank_account_no THEN 1
          ELSE 2
        END,
        fa.id
      LIMIT 1
    ) a ON TRUE
    WHERE l.active
      AND l.project_id IS NOT NULL
    ON CONFLICT (legacy_source_model, legacy_record_id)
    DO UPDATE SET
      operation_type = EXCLUDED.operation_type,
      operation_date = EXCLUDED.operation_date,
      fund_account_id = EXCLUDED.fund_account_id,
      project_id = EXCLUDED.project_id,
      company_id = EXCLUDED.company_id,
      currency_id = EXCLUDED.currency_id,
      daily_income = EXCLUDED.daily_income,
      daily_expense = EXCLUDED.daily_expense,
      account_balance = EXCLUDED.account_balance,
      bank_balance = EXCLUDED.bank_balance,
      operation_reason = EXCLUDED.operation_reason,
      state = EXCLUDED.state,
      note = EXCLUDED.note,
      legacy_document_state = EXCLUDED.legacy_document_state,
      active = EXCLUDED.active,
      write_uid = 1,
      write_date = NOW()
    """,
    [env.company.id, currency_id],  # noqa: F821
)

env.cr.commit()  # noqa: F821

after = int(scalar(f"SELECT COUNT(*) FROM sc_fund_account_operation WHERE {target_domain_sql}") or 0)
visible_rows = int(
    scalar(
        """
        SELECT COUNT(*)
        FROM sc_fund_account_operation
        WHERE operation_type = 'fund_daily_report'
          AND active
        """
    )
    or 0
)
payload = {
    "mode": "fresh_db_fund_daily_report_projection_write",
    "database": env.cr.dbname,  # noqa: F821
    "source_model": "sc.legacy.fund.daily.line",
    "target_model": "sc.fund.account.operation",
    "target_operation_type": "fund_daily_report",
    "candidate_count": candidate_count,
    "before_fund_daily_report": before,
    "after_fund_daily_report": after,
    "visible_rows": visible_rows,
    "delta": after - before,
    "done": int(scalar(f"SELECT COUNT(*) FROM sc_fund_account_operation WHERE {target_domain_sql} AND state = 'done'") or 0),
    "draft": int(
        scalar(f"SELECT COUNT(*) FROM sc_fund_account_operation WHERE {target_domain_sql} AND state = 'draft'") or 0
    ),
    "daily_income_sum": float(
        scalar(f"SELECT COALESCE(SUM(daily_income), 0) FROM sc_fund_account_operation WHERE {target_domain_sql}") or 0
    ),
    "daily_expense_sum": float(
        scalar(f"SELECT COALESCE(SUM(daily_expense), 0) FROM sc_fund_account_operation WHERE {target_domain_sql}") or 0
    ),
    "skipped_no_project_or_account": int(
        scalar(
            """
            SELECT COUNT(*)
            FROM sc_legacy_fund_daily_line l
            WHERE l.active
              AND (
                l.project_id IS NULL
                OR NOT EXISTS (
                  SELECT 1
                  FROM sc_fund_account a
                  WHERE a.active
                    AND (
                      a.legacy_account_id = l.account_legacy_id
                      OR a.account_no = l.bank_account_no
                      OR a.name = l.account_name
                    )
                )
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
