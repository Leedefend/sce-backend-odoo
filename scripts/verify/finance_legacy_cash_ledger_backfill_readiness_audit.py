# -*- coding: utf-8 -*-
"""Read-only audit for legacy finance handling facts missing source-linked cash ledgers.

The existing legacy cash ledger can already contain source-less historical rows.
This audit therefore does not write records and does not treat missing
source-linked rows as a failure. It proves the candidate set and the duplicate
risk that a later migration must handle explicitly.
"""

from __future__ import annotations

import json


def _fetchall_dict(query, params=None):
    env.cr.execute(query, params or {})  # noqa: F821
    columns = [column.name for column in env.cr.description]  # noqa: F821
    return [dict(zip(columns, row)) for row in env.cr.fetchall()]  # noqa: F821


def _fetchone_dict(query, params=None):
    rows = _fetchall_dict(query, params)
    return rows[0] if rows else {}


EXPECTED_CTE = """
WITH expected AS (
    SELECT
        'payment_execution'::varchar AS lane,
        'sc.payment.execution'::varchar AS source_model,
        e.id AS source_res_id,
        e.name AS source_record_name,
        e.payment_family AS business_category,
        e.date_payment AS document_date,
        e.project_id,
        e.partner_id,
        e.currency_id,
        'out'::varchar AS direction,
        'legacy_actual_outflow'::varchar AS source_kind,
        COALESCE(e.paid_amount, 0.0) AS amount,
        e.legacy_record_id,
        e.legacy_source_model
    FROM sc_payment_execution e
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
        r.currency_id,
        'in'::varchar AS direction,
        'legacy_receipt'::varchar AS source_kind,
        COALESCE(r.amount, 0.0) AS amount,
        r.legacy_record_id,
        r.legacy_source_model
    FROM sc_receipt_income r
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
        c.currency_id,
        CASE WHEN c.direction = 'inflow' THEN 'in' ELSE 'out' END::varchar AS direction,
        CASE WHEN c.direction = 'inflow' THEN 'legacy_receipt' ELSE 'legacy_actual_outflow' END::varchar AS source_kind,
        COALESCE(c.approved_amount, c.amount, 0.0) AS amount,
        c.legacy_record_id,
        c.legacy_source_model
    FROM sc_expense_claim c
    WHERE c.source_origin = 'legacy'
      AND c.state = 'legacy_confirmed'
      AND c.project_id IS NOT NULL
      AND COALESCE(c.approved_amount, c.amount, 0.0) > 0
),
matched AS (
    SELECT
        e.*,
        l.id AS ledger_id,
        l.amount AS ledger_amount,
        l.direction AS ledger_direction,
        l.currency_id AS ledger_currency_id,
        l.state AS ledger_state,
        l.payment_request_id AS ledger_payment_request_id
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


summary = _fetchone_dict(
    EXPECTED_CTE
    + """
    SELECT
        COUNT(*)::integer AS expected_source_linked_ledger_count,
        COUNT(*) FILTER (WHERE ledger_id IS NOT NULL)::integer AS existing_source_linked_ledger_count,
        COUNT(*) FILTER (WHERE ledger_id IS NULL)::integer AS missing_source_linked_ledger_count,
        COALESCE(SUM(amount), 0.0) AS expected_amount,
        COALESCE(SUM(amount) FILTER (WHERE direction = 'in'), 0.0) AS expected_inflow_amount,
        COALESCE(SUM(amount) FILTER (WHERE direction = 'out'), 0.0) AS expected_outflow_amount,
        COALESCE(SUM(amount) FILTER (WHERE ledger_id IS NULL), 0.0) AS missing_source_linked_amount
    FROM matched
    """
)

by_lane = _fetchall_dict(
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

by_category = _fetchall_dict(
    EXPECTED_CTE
    + """
    SELECT
        lane,
        direction,
        source_kind,
        COALESCE(NULLIF(business_category, ''), '<empty>') AS business_category,
        COUNT(*)::integer AS expected_count,
        COUNT(*) FILTER (WHERE ledger_id IS NULL)::integer AS missing_count,
        COALESCE(SUM(amount), 0.0) AS expected_amount
    FROM matched
    GROUP BY lane, direction, source_kind, COALESCE(NULLIF(business_category, ''), '<empty>')
    ORDER BY expected_count DESC, lane, business_category
    LIMIT 40
    """
)

blocked = _fetchall_dict(
    """
    SELECT 'payment_execution'::varchar AS lane,
           COUNT(*) FILTER (WHERE project_id IS NULL)::integer AS missing_project_count,
           COUNT(*) FILTER (WHERE COALESCE(paid_amount, 0.0) <= 0)::integer AS non_positive_amount_count
      FROM sc_payment_execution
     WHERE source_origin = 'legacy'
       AND state = 'legacy_confirmed'
    UNION ALL
    SELECT 'receipt_income',
           COUNT(*) FILTER (WHERE project_id IS NULL)::integer,
           COUNT(*) FILTER (WHERE COALESCE(amount, 0.0) <= 0)::integer
      FROM sc_receipt_income
     WHERE source_origin = 'legacy'
       AND state = 'legacy_confirmed'
    UNION ALL
    SELECT 'expense_claim',
           COUNT(*) FILTER (WHERE project_id IS NULL)::integer,
           COUNT(*) FILTER (WHERE COALESCE(approved_amount, amount, 0.0) <= 0)::integer
      FROM sc_expense_claim
     WHERE source_origin = 'legacy'
       AND state = 'legacy_confirmed'
    """
)

source_less_legacy = _fetchall_dict(
    """
    SELECT
        source_kind,
        direction,
        COUNT(*)::integer AS ledger_count,
        COALESCE(SUM(amount), 0.0) AS amount
    FROM sc_treasury_ledger
    WHERE source_kind IN ('legacy_actual_outflow', 'legacy_receipt')
      AND COALESCE(source_model, '') = ''
      AND source_res_id IS NULL
      AND state != 'void'
    GROUP BY source_kind, direction
    ORDER BY source_kind, direction
    """
)

mismatches = _fetchall_dict(
    EXPECTED_CTE
    + """
    SELECT
        lane,
        source_model,
        source_res_id,
        source_record_name,
        project_id,
        direction,
        source_kind,
        amount,
        ledger_id,
        ledger_amount,
        ledger_direction,
        currency_id,
        ledger_currency_id,
        ledger_payment_request_id
    FROM matched
    WHERE ledger_id IS NOT NULL
      AND (
            ABS(COALESCE(ledger_amount, 0.0) - COALESCE(amount, 0.0)) > 0.01
         OR COALESCE(ledger_currency_id, 0) != COALESCE(currency_id, 0)
         OR ledger_direction != direction
         OR ledger_payment_request_id IS NOT NULL
      )
    ORDER BY lane, source_res_id
    LIMIT 50
    """
)

duplicate_source_ledgers = _fetchall_dict(
    """
    SELECT
        source_model,
        source_res_id,
        project_id,
        direction,
        source_kind,
        COUNT(*)::integer AS ledger_count
    FROM sc_treasury_ledger
    WHERE source_model IN ('sc.payment.execution', 'sc.receipt.income', 'sc.expense.claim')
      AND source_res_id IS NOT NULL
      AND source_kind IN ('legacy_actual_outflow', 'legacy_receipt')
      AND state != 'void'
    GROUP BY source_model, source_res_id, project_id, direction, source_kind
    HAVING COUNT(*) > 1
    ORDER BY source_model, source_res_id
    LIMIT 50
    """
)

missing_samples = _fetchall_dict(
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

failures = []
if mismatches:
    failures.append({"key": "source_linked_legacy_ledger_mismatch", "rows": mismatches})
if duplicate_source_ledgers:
    failures.append({"key": "duplicate_source_linked_legacy_ledger", "rows": duplicate_source_ledgers})

result = {
    "audit": "finance_legacy_cash_ledger_backfill_readiness_audit",
    "status": "PASS" if not failures else "FAIL",
    "database": env.cr.dbname,  # noqa: F821
    "summary": summary,
    "by_lane": by_lane,
    "top_categories": by_category,
    "blocked_or_non_backfillable": blocked,
    "existing_source_less_legacy_ledgers": source_less_legacy,
    "missing_samples": missing_samples,
    "failures": failures,
    "policy": {
        "write_mode": "read_only",
        "cashflow_ledger": "sc.treasury.ledger",
        "payment_ledger_boundary": "payment.ledger remains payment_request-only and is not used for all legacy handling facts",
        "eligible": [
            "legacy sc.payment.execution with project and positive paid_amount -> legacy_actual_outflow/out",
            "legacy sc.receipt.income with project and positive amount -> legacy_receipt/in",
            "legacy sc.expense.claim with project and positive approved_amount/amount -> direction-derived legacy cashflow",
        ],
        "migration_guard": [
            "do not duplicate source-less legacy treasury rows without reconciliation",
            "source-linked migration must use source_model/source_res_id/project/direction/source_kind as idempotent key",
            "payment_request_id must stay empty for source-linked legacy cashflow rows unless the source fact is a real payment.request completion",
        ],
    },
}

print("FINANCE_LEGACY_CASH_LEDGER_BACKFILL_READINESS_AUDIT: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True, default=str))
if failures:
    raise SystemExit(1)
