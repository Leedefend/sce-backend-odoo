# -*- coding: utf-8 -*-
"""Backfill legacy finance handling facts into source-linked treasury ledger.

Default mode is dry-run. Set APPLY=1 to insert only missing source-linked
``sc.treasury.ledger`` rows. Historical cashflow is traced through
source_model/source_res_id and never through payment_request_id.
"""

from __future__ import annotations

import json
import os
import sys
import traceback


EXPECTED_CTE = """
WITH default_company AS (
    SELECT id AS company_id, currency_id
    FROM res_company
    ORDER BY id
    LIMIT 1
),
expected AS (
    SELECT
        'payment_execution'::varchar AS lane,
        'sc.payment.execution'::varchar AS source_model,
        e.id AS source_res_id,
        e.name AS source_record_name,
        e.payment_family AS business_category,
        e.date_payment AS document_date,
        e.project_id,
        e.partner_id,
        COALESCE(e.currency_id, project_company.currency_id, default_company.currency_id) AS currency_id,
        'out'::varchar AS direction,
        'legacy_actual_outflow'::varchar AS source_kind,
        COALESCE(e.paid_amount, 0.0) AS amount,
        e.legacy_record_id,
        e.legacy_source_model
    FROM sc_payment_execution e
    JOIN project_project project ON project.id = e.project_id
    LEFT JOIN res_company project_company ON project_company.id = project.company_id
    CROSS JOIN default_company
    WHERE e.source_origin = 'legacy'
      AND e.state = 'legacy_confirmed'
      AND e.project_id IS NOT NULL
      AND COALESCE(e.paid_amount, 0.0) > 0

    UNION ALL

    SELECT
        'receipt_income'::varchar AS lane,
        'sc.receipt.income'::varchar AS source_model,
        r.id AS source_res_id,
        r.name AS source_record_name,
        COALESCE(NULLIF(r.income_category, ''), NULLIF(r.legacy_receipt_type, ''), r.source_family) AS business_category,
        r.date_receipt AS document_date,
        r.project_id,
        r.partner_id,
        COALESCE(r.currency_id, project_company.currency_id, default_company.currency_id) AS currency_id,
        'in'::varchar AS direction,
        'legacy_receipt'::varchar AS source_kind,
        COALESCE(r.amount, 0.0) AS amount,
        r.legacy_record_id,
        r.legacy_source_model
    FROM sc_receipt_income r
    JOIN project_project project ON project.id = r.project_id
    LEFT JOIN res_company project_company ON project_company.id = project.company_id
    CROSS JOIN default_company
    WHERE r.source_origin = 'legacy'
      AND r.state = 'legacy_confirmed'
      AND r.project_id IS NOT NULL
      AND COALESCE(r.amount, 0.0) > 0

    UNION ALL

    SELECT
        'expense_claim'::varchar AS lane,
        'sc.expense.claim'::varchar AS source_model,
        c.id AS source_res_id,
        c.name AS source_record_name,
        COALESCE(NULLIF(c.expense_type, ''), c.claim_type) AS business_category,
        c.date_claim AS document_date,
        c.project_id,
        c.partner_id,
        COALESCE(c.currency_id, project_company.currency_id, default_company.currency_id) AS currency_id,
        CASE WHEN c.direction = 'inflow' THEN 'in' ELSE 'out' END::varchar AS direction,
        CASE WHEN c.direction = 'inflow' THEN 'legacy_receipt' ELSE 'legacy_actual_outflow' END::varchar AS source_kind,
        COALESCE(c.approved_amount, c.amount, 0.0) AS amount,
        c.legacy_record_id,
        c.legacy_source_model
    FROM sc_expense_claim c
    JOIN project_project project ON project.id = c.project_id
    LEFT JOIN res_company project_company ON project_company.id = project.company_id
    CROSS JOIN default_company
    WHERE c.source_origin = 'legacy'
      AND c.state = 'legacy_confirmed'
      AND c.project_id IS NOT NULL
      AND COALESCE(c.approved_amount, c.amount, 0.0) > 0
),
matched AS (
    SELECT
        e.*,
        l.id AS ledger_id
    FROM expected e
    LEFT JOIN sc_treasury_ledger l
      ON l.source_model = e.source_model
     AND l.source_res_id = e.source_res_id
     AND l.project_id = e.project_id
     AND l.direction = e.direction
     AND l.source_kind = e.source_kind
     AND l.state != 'void'
)
"""


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
    if os.environ.get("FINANCE_LEGACY_CASH_LEDGER_BACKFILL_ALLOW_DB") == "1":
        return
    raise RuntimeError(
        "APPLY=1 is only allowed for sc_demo/sc_test unless "
        "FINANCE_LEGACY_CASH_LEDGER_BACKFILL_ALLOW_DB=1 is set; db=%s" % db_name
    )


def _summary():
    return _fetchone_dict(
        EXPECTED_CTE
        + """
        SELECT
            COUNT(*)::integer AS expected_source_linked_ledger_count,
            COUNT(*) FILTER (WHERE ledger_id IS NOT NULL)::integer AS existing_source_linked_ledger_count,
            COUNT(*) FILTER (WHERE ledger_id IS NULL)::integer AS missing_source_linked_ledger_count,
            COALESCE(SUM(amount), 0.0) AS expected_amount,
            COALESCE(SUM(amount) FILTER (WHERE ledger_id IS NULL), 0.0) AS missing_source_linked_amount
        FROM matched
        """
    )


def _by_lane():
    return _fetchall_dict(
        EXPECTED_CTE
        + """
        SELECT
            lane,
            direction,
            source_kind,
            COUNT(*)::integer AS expected_count,
            COUNT(*) FILTER (WHERE ledger_id IS NOT NULL)::integer AS existing_count,
            COUNT(*) FILTER (WHERE ledger_id IS NULL)::integer AS missing_count,
            COALESCE(SUM(amount), 0.0) AS expected_amount,
            COALESCE(SUM(amount) FILTER (WHERE ledger_id IS NULL), 0.0) AS missing_amount
        FROM matched
        GROUP BY lane, direction, source_kind
        ORDER BY lane, direction, source_kind
        """
    )


def _missing_samples():
    return _fetchall_dict(
        EXPECTED_CTE
        + """
        SELECT
            lane,
            source_model,
            source_res_id,
            source_record_name,
            business_category,
            project_id,
            partner_id,
            direction,
            source_kind,
            amount,
            currency_id,
            document_date,
            legacy_source_model,
            legacy_record_id
        FROM matched
        WHERE ledger_id IS NULL
        ORDER BY lane, source_res_id
        LIMIT 30
        """
    )


def _insert_missing_ledgers():
    env.cr.execute(  # noqa: F821
        EXPECTED_CTE
        + """
        INSERT INTO sc_treasury_ledger (
            name,
            date,
            project_id,
            partner_id,
            payment_request_id,
            source_model,
            source_res_id,
            direction,
            amount,
            currency_id,
            state,
            note,
            source_kind,
            legacy_record_id,
            legacy_source_ref,
            create_uid,
            create_date,
            write_uid,
            write_date
        )
        SELECT
            'LEGACY-CF-' || source_model || '-' || source_res_id::varchar || '-' || project_id::varchar || '-' || direction || '-' || source_kind,
            COALESCE(document_date, CURRENT_DATE),
            project_id,
            partner_id,
            NULL,
            source_model,
            source_res_id,
            direction,
            amount,
            currency_id,
            'posted',
            'backfill:finance_legacy_cash_ledger:' || lane || ':' || COALESCE(NULLIF(business_category, ''), '<empty>'),
            source_kind,
            legacy_record_id,
            legacy_source_model,
            %(uid)s,
            NOW(),
            %(uid)s,
            NOW()
        FROM matched
        WHERE ledger_id IS NULL
          AND currency_id IS NOT NULL
          AND NOT EXISTS (
              SELECT 1
              FROM sc_treasury_ledger existing
              WHERE existing.source_model = matched.source_model
                AND existing.source_res_id = matched.source_res_id
                AND existing.project_id = matched.project_id
                AND existing.direction = matched.direction
                AND existing.source_kind = matched.source_kind
                AND existing.state != 'void'
          )
        """,
        {"uid": env.uid},  # noqa: F821
    )
    return env.cr.rowcount  # noqa: F821


def main():
    apply = os.environ.get("APPLY") == "1"
    _assert_apply_allowed(apply)
    before = _summary()
    before_by_lane = _by_lane()
    samples = _missing_samples()
    inserted = 0
    if apply:
        inserted = _insert_missing_ledgers()
        env.cr.commit()  # noqa: F821
    after = _summary()
    failures = []
    if apply and int(after.get("missing_source_linked_ledger_count") or 0) != 0:
        failures.append("missing_source_linked_ledger_count_after_apply=%s" % after.get("missing_source_linked_ledger_count"))
    result = {
        "operation": "finance_legacy_cash_ledger_backfill",
        "status": "PASS" if not failures else "FAIL",
        "database": env.cr.dbname,  # noqa: F821
        "apply": apply,
        "before": before,
        "after": after,
        "by_lane_before": before_by_lane,
        "missing_samples_before": samples,
        "inserted_rows": inserted,
        "failures": failures,
        "policy": {
            "scope": "legacy confirmed finance handling facts with project and positive amount",
            "cashflow_ledger": "sc.treasury.ledger",
            "idempotent_key": "source_model/source_res_id/project_id/direction/source_kind",
            "payment_request_boundary": "payment_request_id is always NULL for these source-linked legacy cashflow rows",
            "write_mode": "insert missing ledgers only; source facts are not modified",
        },
    }
    print("FINANCE_LEGACY_CASH_LEDGER_BACKFILL: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True, default=str))
    return 0 if not failures else 1


try:
    sys.exit(main())
except Exception as err:
    env.cr.rollback()  # noqa: F821
    result = {
        "operation": "finance_legacy_cash_ledger_backfill",
        "status": "FAIL",
        "database": env.cr.dbname,  # noqa: F821
        "apply": os.environ.get("APPLY") == "1",
        "error": str(err),
        "traceback": traceback.format_exc(),
    }
    print("FINANCE_LEGACY_CASH_LEDGER_BACKFILL: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True, default=str))
    sys.exit(1)
