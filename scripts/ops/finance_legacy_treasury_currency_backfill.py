# -*- coding: utf-8 -*-
"""Normalize legacy treasury ledger currency to CNY.

Default mode is dry-run. Set APPLY=1 to update rows. The script is intentionally
limited to demo/test databases unless explicitly allowed.
"""

from __future__ import annotations

import json
import os
import sys
import traceback


LEGACY_SOURCE_KINDS = ("legacy_actual_outflow", "legacy_receipt")


EXPECTED_SQL = """
WITH expected AS (
    SELECT
        l.id AS ledger_id,
        l.name,
        l.source_kind,
        l.direction,
        l.project_id,
        l.partner_id,
        l.amount,
        l.currency_id AS current_currency_id,
        current_currency.name AS current_currency_name,
        expected_currency.currency_id AS expected_currency_id,
        expected_currency.name AS expected_currency_name
    FROM sc_treasury_ledger l
    JOIN project_project project ON project.id = l.project_id
    CROSS JOIN LATERAL (
        SELECT currency.id AS currency_id, currency.name
        FROM ir_model_data data
        JOIN res_currency currency ON currency.id = data.res_id
        WHERE data.module = 'base'
          AND data.name = 'CNY'
          AND data.model = 'res.currency'
        LIMIT 1
    ) expected_currency
    LEFT JOIN res_currency current_currency ON current_currency.id = l.currency_id
    WHERE l.source_kind IN %(source_kinds)s
      AND l.state != 'void'
),
mismatched AS (
    SELECT *
    FROM expected
    WHERE COALESCE(current_currency_id, 0) != COALESCE(expected_currency_id, 0)
)
"""


def _fetchall_dict(query, params=None):
    env.cr.execute(query, params or {})  # noqa: F821
    columns = [column.name for column in env.cr.description]  # noqa: F821
    return [dict(zip(columns, row)) for row in env.cr.fetchall()]  # noqa: F821


def _fetchone_dict(query, params=None):
    rows = _fetchall_dict(query, params)
    return rows[0] if rows else {}


def _summary():
    return _fetchone_dict(
        EXPECTED_SQL
        + """
        SELECT
            (SELECT COUNT(*)::integer FROM expected) AS legacy_ledger_count,
            COUNT(*)::integer AS mismatched_count,
            COALESCE(SUM(amount), 0.0) AS mismatched_amount,
            COUNT(*) FILTER (WHERE expected_currency_name = 'CNY')::integer AS mismatched_to_cny_count,
            COALESCE(SUM(amount) FILTER (WHERE expected_currency_name = 'CNY'), 0.0) AS mismatched_to_cny_amount
        FROM mismatched
        """,
        {"source_kinds": LEGACY_SOURCE_KINDS},
    )


def _by_currency():
    return _fetchall_dict(
        EXPECTED_SQL
        + """
        SELECT
            COALESCE(current_currency_name, '<empty>') AS current_currency,
            COALESCE(expected_currency_name, '<empty>') AS expected_currency,
            source_kind,
            direction,
            COUNT(*)::integer AS row_count,
            COALESCE(SUM(amount), 0.0) AS amount
        FROM mismatched
        GROUP BY current_currency_name, expected_currency_name, source_kind, direction
        ORDER BY row_count DESC, current_currency, expected_currency, source_kind, direction
        """,
        {"source_kinds": LEGACY_SOURCE_KINDS},
    )


def _samples():
    return _fetchall_dict(
        EXPECTED_SQL
        + """
        SELECT
            ledger_id,
            name,
            source_kind,
            direction,
            project_id,
            partner_id,
            amount,
            current_currency_name,
            expected_currency_name
        FROM mismatched
        ORDER BY ledger_id
        LIMIT 30
        """,
        {"source_kinds": LEGACY_SOURCE_KINDS},
    )


def _assert_apply_allowed(apply):
    if not apply:
        return
    db_name = env.cr.dbname  # noqa: F821
    allowed = db_name in {"sc_demo", "sc_test"} or db_name.startswith(("sc_demo_", "sc_test_"))
    if allowed:
        return
    if os.environ.get("FINANCE_LEGACY_TREASURY_CURRENCY_ALLOW_DB") == "1":
        return
    raise RuntimeError(
        "APPLY=1 is only allowed for sc_demo/sc_test unless FINANCE_LEGACY_TREASURY_CURRENCY_ALLOW_DB=1 is set; db=%s"
        % db_name
    )


def _apply():
    env.cr.execute(  # noqa: F821
        """
        WITH expected AS (
            SELECT
                l.id AS ledger_id,
                expected_currency.currency_id AS expected_currency_id
            FROM sc_treasury_ledger l
            JOIN project_project project ON project.id = l.project_id
            CROSS JOIN LATERAL (
                SELECT res_id AS currency_id
                FROM ir_model_data
                WHERE module = 'base'
                  AND name = 'CNY'
                  AND model = 'res.currency'
                LIMIT 1
            ) expected_currency
            WHERE l.source_kind IN %(source_kinds)s
              AND l.state != 'void'
        )
        UPDATE sc_treasury_ledger ledger
           SET currency_id = expected.expected_currency_id,
               note = CASE
                   WHEN COALESCE(ledger.note, '') LIKE '%%[currency_backfill:legacy_treasury_to_project_company]%%'
                       THEN ledger.note
                   ELSE COALESCE(ledger.note || ' ', '') || '[currency_backfill:legacy_treasury_to_project_company]'
               END,
               write_date = NOW()
          FROM expected
         WHERE ledger.id = expected.ledger_id
           AND expected.expected_currency_id IS NOT NULL
           AND COALESCE(ledger.currency_id, 0) != COALESCE(expected.expected_currency_id, 0)
        """,
        {"source_kinds": LEGACY_SOURCE_KINDS},
    )
    return env.cr.rowcount  # noqa: F821


def main():
    apply = os.environ.get("APPLY") == "1"
    _assert_apply_allowed(apply)

    before = _summary()
    by_currency_before = _by_currency()
    samples_before = _samples()
    updated_rows = 0
    if apply:
        updated_rows = _apply()
        env.cr.commit()  # noqa: F821
    after = _summary()
    failures = []
    if apply and int(after.get("mismatched_count") or 0) != 0:
        failures.append("mismatched_count_after_apply=%s" % after.get("mismatched_count"))
    result = {
        "operation": "finance_legacy_treasury_currency_backfill",
        "status": "PASS" if not failures else "FAIL",
        "database": env.cr.dbname,  # noqa: F821
        "apply": apply,
        "before": before,
        "after": after,
        "by_currency_before": by_currency_before,
        "samples_before": samples_before,
        "updated_rows": updated_rows,
        "failures": failures,
        "policy": {
            "scope": "sc.treasury.ledger rows with source_kind legacy_actual_outflow/legacy_receipt and state != void",
            "expected_currency": "base.CNY; the user's legacy treasury facts are RMB facts",
            "db_write_guard": "APPLY=1 only on sc_demo/sc_test unless explicitly allowed",
        },
    }
    print("FINANCE_LEGACY_TREASURY_CURRENCY_BACKFILL: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True, default=str))
    return 0 if not failures else 1


try:
    sys.exit(main())
except Exception as err:
    env.cr.rollback()  # noqa: F821
    result = {
        "operation": "finance_legacy_treasury_currency_backfill",
        "status": "FAIL",
        "database": env.cr.dbname,  # noqa: F821
        "apply": os.environ.get("APPLY") == "1",
        "error": str(err),
        "traceback": traceback.format_exc(),
    }
    print("FINANCE_LEGACY_TREASURY_CURRENCY_BACKFILL: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True, default=str))
    sys.exit(1)
