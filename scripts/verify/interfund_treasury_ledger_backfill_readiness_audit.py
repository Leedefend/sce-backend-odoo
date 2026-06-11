# -*- coding: utf-8 -*-
"""Audit historical interfund facts that are eligible for treasury ledger backfill.

This script is intentionally read-only. It proves the cash-flow boundary before
any migration writes historical rows into sc.treasury.ledger.
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


def _failures_from_rows(rows, prefix):
    return [
        {
            "key": "%s_%s_%s_%s_%s" % (
                prefix,
                row.get("source_model"),
                row.get("source_res_id"),
                row.get("project_id"),
                row.get("direction"),
            ),
            "details": row,
        }
        for row in rows
    ]


EXPECTED_CTE = """
WITH expected AS (
    SELECT
        f.source_model,
        f.source_res_id,
        f.source_record_name,
        f.movement_type,
        f.source_menu_hint,
        f.document_date,
        f.company_id,
        f.currency_id,
        f.amount,
        f.source_project_id AS project_id,
        'out'::varchar AS direction,
        'source_project_outflow'::varchar AS backfill_role,
        f.classification_confidence
    FROM sc_interfund_movement_fact f
    WHERE f.amount > 0
      AND f.source_project_id IS NOT NULL
      AND f.movement_type IN (
            'project_to_project_transfer',
            'project_to_company_transfer',
            'project_to_contractor_borrow',
            'project_to_company_repay'
      )
    UNION ALL
    SELECT
        f.source_model,
        f.source_res_id,
        f.source_record_name,
        f.movement_type,
        f.source_menu_hint,
        f.document_date,
        f.company_id,
        f.currency_id,
        f.amount,
        f.target_project_id AS project_id,
        'in'::varchar AS direction,
        'target_project_inflow'::varchar AS backfill_role,
        f.classification_confidence
    FROM sc_interfund_movement_fact f
    WHERE f.amount > 0
      AND f.target_project_id IS NOT NULL
      AND f.movement_type IN (
            'project_to_project_transfer',
            'company_to_project_transfer',
            'company_to_project_borrow',
            'contractor_to_project_repay'
      )
),
matched AS (
    SELECT
        e.*,
        l.id AS ledger_id,
        l.amount AS ledger_amount,
        l.currency_id AS ledger_currency_id,
        l.state AS ledger_state,
        l.payment_request_id AS ledger_payment_request_id
    FROM expected e
    LEFT JOIN sc_treasury_ledger l
      ON l.source_model = e.source_model
     AND l.source_res_id = e.source_res_id
     AND l.project_id = e.project_id
     AND l.direction = e.direction
     AND l.source_kind = 'interfund'
     AND l.state != 'void'
)
"""


summary = _fetchone_dict(
    EXPECTED_CTE
    + """
    SELECT
        COUNT(*)::integer AS expected_ledger_entry_count,
        COUNT(*) FILTER (WHERE ledger_id IS NOT NULL)::integer AS existing_ledger_entry_count,
        COUNT(*) FILTER (WHERE ledger_id IS NULL)::integer AS missing_ledger_entry_count,
        COALESCE(SUM(amount), 0.0) AS expected_ledger_amount,
        COALESCE(SUM(amount) FILTER (WHERE direction = 'in'), 0.0) AS expected_inflow_amount,
        COALESCE(SUM(amount) FILTER (WHERE direction = 'out'), 0.0) AS expected_outflow_amount,
        COALESCE(SUM(amount) FILTER (WHERE ledger_id IS NULL), 0.0) AS missing_ledger_amount
    FROM matched
    """
)

by_type = _fetchall_dict(
    EXPECTED_CTE
    + """
    SELECT
        movement_type,
        direction,
        COUNT(*)::integer AS expected_count,
        COUNT(*) FILTER (WHERE ledger_id IS NOT NULL)::integer AS existing_count,
        COUNT(*) FILTER (WHERE ledger_id IS NULL)::integer AS missing_count,
        COALESCE(SUM(amount), 0.0) AS expected_amount,
        COALESCE(SUM(amount) FILTER (WHERE ledger_id IS NULL), 0.0) AS missing_amount
    FROM matched
    GROUP BY movement_type, direction
    ORDER BY movement_type, direction
    """
)

unsafe = _fetchone_dict(
    """
    SELECT
        COUNT(*) FILTER (WHERE movement_type = 'same_project_account_transfer')::integer AS same_project_fact_count,
        COALESCE(SUM(amount) FILTER (WHERE movement_type = 'same_project_account_transfer'), 0.0) AS same_project_amount,
        COUNT(*) FILTER (WHERE movement_type = 'unclassified_account_transfer')::integer AS unclassified_fact_count,
        COALESCE(SUM(amount) FILTER (WHERE movement_type = 'unclassified_account_transfer'), 0.0) AS unclassified_amount,
        COUNT(*) FILTER (WHERE amount <= 0)::integer AS non_positive_fact_count,
        COALESCE(SUM(amount) FILTER (WHERE amount <= 0), 0.0) AS non_positive_amount
    FROM sc_interfund_movement_fact
    """
)

mismatches = _fetchall_dict(
    EXPECTED_CTE
    + """
    SELECT
        source_model,
        source_res_id,
        source_record_name,
        movement_type,
        project_id,
        direction,
        amount,
        ledger_amount,
        currency_id,
        ledger_currency_id,
        ledger_payment_request_id,
        ledger_id
    FROM matched
    WHERE ledger_id IS NOT NULL
      AND (
            ABS(COALESCE(ledger_amount, 0.0) - COALESCE(amount, 0.0)) > 0.01
         OR COALESCE(ledger_currency_id, 0) != COALESCE(currency_id, 0)
         OR ledger_payment_request_id IS NOT NULL
      )
    ORDER BY source_model, source_res_id, project_id, direction
    LIMIT 20
    """
)

unexpected_ledgers = _fetchall_dict(
    EXPECTED_CTE
    + """
    SELECT
        l.id AS ledger_id,
        l.source_model,
        l.source_res_id,
        l.project_id,
        l.direction,
        l.amount,
        l.currency_id
    FROM sc_treasury_ledger l
    LEFT JOIN expected e
      ON e.source_model = l.source_model
     AND e.source_res_id = l.source_res_id
     AND e.project_id = l.project_id
     AND e.direction = l.direction
    WHERE l.source_kind = 'interfund'
      AND l.state != 'void'
      AND l.source_model IS NOT NULL
      AND l.source_res_id IS NOT NULL
      AND e.source_model IS NULL
    ORDER BY l.id
    LIMIT 20
    """
)

missing_samples = _fetchall_dict(
    EXPECTED_CTE
    + """
    SELECT
        source_model,
        source_res_id,
        source_record_name,
        movement_type,
        source_menu_hint,
        project_id,
        direction,
        amount,
        currency_id,
        document_date,
        backfill_role
    FROM matched
    WHERE ledger_id IS NULL
    ORDER BY movement_type, source_model, source_res_id, project_id, direction
    LIMIT 20
    """
)

failures = []
failures.extend(_failures_from_rows(mismatches, "interfund_ledger_mismatch"))
failures.extend(_failures_from_rows(unexpected_ledgers, "unexpected_interfund_ledger"))

result = {
    "audit": "interfund_treasury_ledger_backfill_readiness_audit",
    "status": "PASS" if not failures else "FAIL",
    "database": env.cr.dbname,  # noqa: F821
    "summary": summary,
    "by_type": by_type,
    "unsafe_or_non_backfillable": unsafe,
    "missing_samples": missing_samples,
    "failures": failures,
    "policy": {
        "write_mode": "read_only",
        "eligible": [
            "company_to_project_borrow:target_project/in",
            "project_to_company_repay:source_project/out",
            "project_to_project_transfer:source_project/out,target_project/in",
            "project_to_company_transfer:source_project/out",
            "company_to_project_transfer:target_project/in",
            "project_to_contractor_borrow:source_project/out",
            "contractor_to_project_repay:target_project/in",
        ],
        "excluded": [
            "same_project_account_transfer:net cashflow zero",
            "unclassified_account_transfer:missing project anchors",
            "non_positive_amount",
        ],
    },
}

print("INTERFUND_TREASURY_LEDGER_BACKFILL_READINESS_AUDIT: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True, default=str))
if failures:
    raise SystemExit(1)
