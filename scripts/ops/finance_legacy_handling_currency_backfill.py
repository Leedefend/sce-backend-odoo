# -*- coding: utf-8 -*-
"""Normalize legacy finance handling source facts to CNY.

The user's legacy finance facts are RMB facts. Default mode is dry-run; set
APPLY=1 to update only currency_id and a note marker on eligible legacy rows.
"""

from __future__ import annotations

import json
import os
import sys
import traceback


MARKER = "[currency_backfill:legacy_finance_handling_to_project_company]"


def _fetchall_dict(query, params=None):
    env.cr.execute(query, params or {})  # noqa: F821
    columns = [column.name for column in env.cr.description]  # noqa: F821
    return [dict(zip(columns, row)) for row in env.cr.fetchall()]  # noqa: F821


def _fetchone_dict(query, params=None):
    rows = _fetchall_dict(query, params)
    return rows[0] if rows else {}


def _assert_apply_allowed(apply):
    if not apply:
        return
    db_name = env.cr.dbname  # noqa: F821
    allowed = db_name in {"sc_demo", "sc_test"} or db_name.startswith(("sc_demo_", "sc_test_"))
    if allowed:
        return
    if os.environ.get("FINANCE_LEGACY_HANDLING_CURRENCY_ALLOW_DB") == "1":
        return
    raise RuntimeError(
        "APPLY=1 is only allowed for sc_demo/sc_test unless FINANCE_LEGACY_HANDLING_CURRENCY_ALLOW_DB=1 is set; db=%s"
        % db_name
    )


EXPECTED_CTE = """
WITH expected_currency AS (
    SELECT res_id AS currency_id
    FROM ir_model_data
    WHERE module = 'base'
      AND name = 'CNY'
      AND model = 'res.currency'
    LIMIT 1
),
expected AS (
    SELECT
        'payment_execution'::varchar AS lane,
        e.id AS source_res_id,
        e.name AS source_record_name,
        e.project_id,
        e.currency_id AS current_currency_id,
        expected_currency.currency_id AS expected_currency_id,
        COALESCE(e.paid_amount, 0.0) AS amount
    FROM sc_payment_execution e
    JOIN project_project project ON project.id = e.project_id
    CROSS JOIN expected_currency
    WHERE e.source_origin = 'legacy'
      AND e.state = 'legacy_confirmed'
      AND e.project_id IS NOT NULL
      AND COALESCE(e.paid_amount, 0.0) > 0

    UNION ALL

    SELECT
        'receipt_income'::varchar AS lane,
        r.id AS source_res_id,
        r.name AS source_record_name,
        r.project_id,
        r.currency_id AS current_currency_id,
        expected_currency.currency_id AS expected_currency_id,
        COALESCE(r.amount, 0.0) AS amount
    FROM sc_receipt_income r
    JOIN project_project project ON project.id = r.project_id
    CROSS JOIN expected_currency
    WHERE r.source_origin = 'legacy'
      AND r.state = 'legacy_confirmed'
      AND r.project_id IS NOT NULL
      AND COALESCE(r.amount, 0.0) > 0

    UNION ALL

    SELECT
        'expense_claim'::varchar AS lane,
        c.id AS source_res_id,
        c.name AS source_record_name,
        c.project_id,
        c.currency_id AS current_currency_id,
        expected_currency.currency_id AS expected_currency_id,
        COALESCE(c.approved_amount, c.amount, 0.0) AS amount
    FROM sc_expense_claim c
    JOIN project_project project ON project.id = c.project_id
    CROSS JOIN expected_currency
    WHERE c.source_origin = 'legacy'
      AND c.state = 'legacy_confirmed'
      AND c.project_id IS NOT NULL
      AND COALESCE(c.approved_amount, c.amount, 0.0) > 0
),
mismatched AS (
    SELECT
        e.*,
        current_currency.name AS current_currency,
        expected_currency_rec.name AS expected_currency
    FROM expected e
    LEFT JOIN res_currency current_currency ON current_currency.id = e.current_currency_id
    LEFT JOIN res_currency expected_currency_rec ON expected_currency_rec.id = e.expected_currency_id
    WHERE COALESCE(e.current_currency_id, 0) != COALESCE(e.expected_currency_id, 0)
)
"""


def _summary():
    return _fetchone_dict(
        EXPECTED_CTE
        + """
        SELECT
            (SELECT COUNT(*)::integer FROM expected) AS eligible_count,
            COUNT(*)::integer AS mismatched_count,
            COALESCE(SUM(amount), 0.0) AS mismatched_amount,
            COUNT(*) FILTER (WHERE expected_currency = 'CNY')::integer AS mismatched_to_cny_count,
            COALESCE(SUM(amount) FILTER (WHERE expected_currency = 'CNY'), 0.0) AS mismatched_to_cny_amount
        FROM mismatched
        """
    )


def _by_lane():
    return _fetchall_dict(
        EXPECTED_CTE
        + """
        SELECT
            lane,
            COALESCE(current_currency, '<empty>') AS current_currency,
            COALESCE(expected_currency, '<empty>') AS expected_currency,
            COUNT(*)::integer AS mismatched_count,
            COALESCE(SUM(amount), 0.0) AS mismatched_amount
        FROM mismatched
        GROUP BY lane, current_currency, expected_currency
        ORDER BY lane, mismatched_count DESC
        """
    )


def _samples():
    return _fetchall_dict(
        EXPECTED_CTE
        + """
        SELECT
            lane,
            source_res_id,
            source_record_name,
            project_id,
            amount,
            current_currency,
            expected_currency
        FROM mismatched
        ORDER BY lane, source_res_id
        LIMIT 30
        """
    )


def _update_table(table, id_field="id"):
    env.cr.execute(  # noqa: F821
        """
        WITH expected_currency AS (
            SELECT res_id AS currency_id
            FROM ir_model_data
            WHERE module = 'base'
              AND name = 'CNY'
              AND model = 'res.currency'
            LIMIT 1
        ),
        expected AS (
            SELECT
                source.id AS source_id,
                expected_currency.currency_id AS expected_currency_id
            FROM {table} source
            JOIN project_project project ON project.id = source.project_id
            CROSS JOIN expected_currency
            WHERE source.source_origin = 'legacy'
              AND source.state = 'legacy_confirmed'
              AND source.project_id IS NOT NULL
              AND {amount_expr} > 0
        )
        UPDATE {table} source
           SET currency_id = expected.expected_currency_id,
               note = CASE
                   WHEN COALESCE(source.note, '') LIKE %(marker_like)s THEN source.note
                   ELSE COALESCE(source.note || ' ', '') || %(marker)s
               END,
               write_uid = %(uid)s,
               write_date = NOW()
          FROM expected
         WHERE source.{id_field} = expected.source_id
           AND expected.expected_currency_id IS NOT NULL
           AND COALESCE(source.currency_id, 0) != COALESCE(expected.expected_currency_id, 0)
        """.format(table=table, id_field=id_field, amount_expr=_amount_expr(table)),
        {"uid": env.uid, "marker": MARKER, "marker_like": "%" + MARKER + "%"},  # noqa: F821
    )
    return env.cr.rowcount  # noqa: F821


def _amount_expr(table):
    if table == "sc_payment_execution":
        return "COALESCE(source.paid_amount, 0.0)"
    if table == "sc_receipt_income":
        return "COALESCE(source.amount, 0.0)"
    if table == "sc_expense_claim":
        return "COALESCE(source.approved_amount, source.amount, 0.0)"
    raise ValueError("unsupported table: %s" % table)


def _apply():
    return {
        "payment_execution": _update_table("sc_payment_execution"),
        "receipt_income": _update_table("sc_receipt_income"),
        "expense_claim": _update_table("sc_expense_claim"),
    }


def main():
    apply = os.environ.get("APPLY") == "1"
    _assert_apply_allowed(apply)
    before = _summary()
    by_lane_before = _by_lane()
    samples_before = _samples()
    updated_by_lane = {}
    if apply:
        updated_by_lane = _apply()
        env.cr.commit()  # noqa: F821
    after = _summary()
    failures = []
    if apply and int(after.get("mismatched_count") or 0) != 0:
        failures.append("mismatched_count_after_apply=%s" % after.get("mismatched_count"))
    result = {
        "operation": "finance_legacy_handling_currency_backfill",
        "status": "PASS" if not failures else "FAIL",
        "database": env.cr.dbname,  # noqa: F821
        "apply": apply,
        "before": before,
        "after": after,
        "by_lane_before": by_lane_before,
        "samples_before": samples_before,
        "updated_by_lane": updated_by_lane,
        "failures": failures,
        "policy": {
            "scope": "legacy confirmed positive finance handling facts with a project",
            "expected_currency": "base.CNY; the user's legacy finance facts are RMB facts",
            "write_fields": "currency_id, note marker, write metadata only",
            "db_write_guard": "APPLY=1 only on sc_demo/sc_test unless explicitly allowed",
        },
    }
    print("FINANCE_LEGACY_HANDLING_CURRENCY_BACKFILL: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True, default=str))
    return 0 if not failures else 1


try:
    sys.exit(main())
except Exception as err:
    env.cr.rollback()  # noqa: F821
    result = {
        "operation": "finance_legacy_handling_currency_backfill",
        "status": "FAIL",
        "database": env.cr.dbname,  # noqa: F821
        "apply": os.environ.get("APPLY") == "1",
        "error": str(err),
        "traceback": traceback.format_exc(),
    }
    print("FINANCE_LEGACY_HANDLING_CURRENCY_BACKFILL: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True, default=str))
    sys.exit(1)
