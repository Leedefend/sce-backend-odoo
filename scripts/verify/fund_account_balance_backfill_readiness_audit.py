# -*- coding: utf-8 -*-
"""Read-only audit for formal fund account balance initialization.

This proves whether legacy account balances can be safely initialized from the
latest fund daily line, falling back to the account opening balance. It does not
write historical balances into the current database.
"""

import json
import sys
import traceback


def _fetchone(query, params=None):
    env.cr.execute(query, params or {})  # noqa: F821
    columns = [column.name for column in env.cr.description]  # noqa: F821
    row = env.cr.fetchone()  # noqa: F821
    return dict(zip(columns, row)) if row else {}


def _fetchall(query, params=None):
    env.cr.execute(query, params or {})  # noqa: F821
    columns = [column.name for column in env.cr.description]  # noqa: F821
    return [dict(zip(columns, row)) for row in env.cr.fetchall()]  # noqa: F821


MATCH_CTE = """
WITH formal_account AS (
    SELECT
        f.id,
        f.name,
        f.account_no,
        f.legacy_account_id,
        f.opening_balance,
        f.current_account_balance,
        f.current_bank_balance,
        f.current_balance_source,
        f.balance_as_of_date
    FROM sc_fund_account f
    WHERE f.active IS TRUE
      AND f.source_origin = 'legacy'
),
latest_daily AS (
    SELECT DISTINCT ON (f.id)
        f.id AS fund_account_id,
        l.id AS daily_line_id,
        l.legacy_line_id,
        l.document_date,
        l.current_account_balance AS daily_account_balance,
        l.current_bank_balance AS daily_bank_balance,
        CASE
            WHEN NULLIF(l.account_legacy_id, '') = NULLIF(f.legacy_account_id, '') THEN 'legacy_account_id'
            WHEN NULLIF(l.bank_account_no, '') = NULLIF(f.account_no, '') THEN 'account_no'
            WHEN lower(trim(NULLIF(l.account_name, ''))) = lower(trim(NULLIF(f.name, ''))) THEN 'account_name'
            ELSE 'none'
        END AS match_key
    FROM formal_account f
    JOIN sc_legacy_fund_daily_line l
      ON l.active IS TRUE
     AND (
            NULLIF(l.account_legacy_id, '') = NULLIF(f.legacy_account_id, '')
         OR NULLIF(l.bank_account_no, '') = NULLIF(f.account_no, '')
         OR lower(trim(NULLIF(l.account_name, ''))) = lower(trim(NULLIF(f.name, '')))
     )
    ORDER BY f.id, l.document_date DESC NULLS LAST, l.id DESC
),
expected AS (
    SELECT
        f.*,
        d.daily_line_id,
        d.legacy_line_id,
        d.document_date,
        d.daily_account_balance,
        d.daily_bank_balance,
        d.match_key,
        COALESCE(d.daily_account_balance, f.opening_balance, 0.0) AS expected_account_balance,
        COALESCE(d.daily_bank_balance, 0.0) AS expected_bank_balance,
        CASE WHEN d.daily_line_id IS NOT NULL THEN 'fund_daily_report' ELSE 'opening' END AS expected_balance_source
    FROM formal_account f
    LEFT JOIN latest_daily d ON d.fund_account_id = f.id
)
"""


failures = []

try:
    table_presence = _fetchone(
        """
        SELECT
            to_regclass('sc_fund_account') IS NOT NULL AS has_fund_account,
            to_regclass('sc_legacy_account_master') IS NOT NULL AS has_legacy_account_master,
            to_regclass('sc_legacy_fund_daily_line') IS NOT NULL AS has_legacy_fund_daily_line
        """
    )
    missing_tables = [key for key, value in table_presence.items() if not value]
    if missing_tables:
        failures.append("missing required tables: %s" % ", ".join(missing_tables))

    summary = _fetchone(
        MATCH_CTE
        + """
        SELECT
            COUNT(*)::integer AS formal_legacy_account_count,
            COUNT(*) FILTER (WHERE daily_line_id IS NOT NULL)::integer AS latest_daily_matched_count,
            COUNT(*) FILTER (WHERE daily_line_id IS NULL)::integer AS latest_daily_missing_count,
            COUNT(*) FILTER (
                WHERE daily_line_id IS NULL
                  AND COALESCE(opening_balance, 0.0) = 0.0
            )::integer AS no_daily_no_opening_count,
            COUNT(*) FILTER (
                WHERE current_account_balance IS DISTINCT FROM expected_account_balance
                   OR current_balance_source IS DISTINCT FROM expected_balance_source
                   OR COALESCE(current_bank_balance, 0.0) IS DISTINCT FROM COALESCE(expected_bank_balance, 0.0)
                   OR balance_as_of_date IS DISTINCT FROM document_date
            )::integer AS current_state_mismatch_count,
            COALESCE(SUM(expected_account_balance), 0.0) AS expected_account_balance_total,
            COALESCE(SUM(expected_bank_balance), 0.0) AS expected_bank_balance_total
        FROM expected
        """
    )
    by_match_key = _fetchall(
        MATCH_CTE
        + """
        SELECT COALESCE(match_key, 'no_daily_match') AS match_key,
               COUNT(*)::integer AS account_count
          FROM expected
         GROUP BY COALESCE(match_key, 'no_daily_match')
         ORDER BY match_key
        """
    )
    mismatch_samples = _fetchall(
        MATCH_CTE
        + """
        SELECT
            id,
            name,
            legacy_account_id,
            account_no,
            current_account_balance,
            expected_account_balance,
            current_bank_balance,
            expected_bank_balance,
            current_balance_source,
            expected_balance_source,
            balance_as_of_date,
            legacy_line_id,
            document_date,
            match_key
        FROM expected
        WHERE current_account_balance IS DISTINCT FROM expected_account_balance
           OR current_balance_source IS DISTINCT FROM expected_balance_source
           OR COALESCE(current_bank_balance, 0.0) IS DISTINCT FROM COALESCE(expected_bank_balance, 0.0)
           OR balance_as_of_date IS DISTINCT FROM document_date
        ORDER BY id
        LIMIT 20
        """
    )
    no_basis_samples = _fetchall(
        MATCH_CTE
        + """
        SELECT id, name, legacy_account_id, account_no, opening_balance
          FROM expected
         WHERE daily_line_id IS NULL
           AND COALESCE(opening_balance, 0.0) = 0.0
         ORDER BY id
         LIMIT 20
        """
    )
    if summary.get("formal_legacy_account_count", 0) <= 0:
        failures.append("expected formal legacy fund accounts, got 0")
except Exception as err:
    failures.append("unexpected error: %s" % err)
    failures.append(traceback.format_exc())
    summary = {}
    by_match_key = []
    mismatch_samples = []
    no_basis_samples = []

result = {
    "audit": "fund_account_balance_backfill_readiness_audit",
    "status": "PASS" if not failures else "FAIL",
    "summary": summary,
    "by_match_key": by_match_key,
    "mismatch_samples": mismatch_samples,
    "no_basis_samples": no_basis_samples,
    "failures": failures,
    "policy": {
        "write_mode": "read_only",
        "initialization_order": "latest fund daily line, then opening balance",
        "transfer_balance_policy": "do not enable transfer debit/credit until opening balance and historical account lines are confirmed",
    },
}
print("FUND_ACCOUNT_BALANCE_BACKFILL_READINESS_AUDIT: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True, default=str))
if failures:
    print("FAILURES:")
    for failure in failures:
        print("- %s" % failure)
sys.exit(0 if not failures else 1)
