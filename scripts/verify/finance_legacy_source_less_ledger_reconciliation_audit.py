# -*- coding: utf-8 -*-
"""Read-only reconciliation for source-less legacy treasury ledger rows.

This audit decides which existing historical cash ledger rows are safe to
source-attach before any source-linked migration is allowed to create new rows.
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


MATCH_CTE = """
WITH source_less AS (
    SELECT
        l.id AS ledger_id,
        l.name AS ledger_name,
        l.date AS ledger_date,
        l.project_id,
        l.partner_id,
        l.direction,
        l.source_kind,
        l.amount,
        l.currency_id,
        l.legacy_record_id,
        l.legacy_source_ref,
        l.note
    FROM sc_treasury_ledger l
    WHERE l.source_kind IN ('legacy_actual_outflow', 'legacy_receipt')
      AND COALESCE(l.source_model, '') = ''
      AND l.source_res_id IS NULL
      AND l.state != 'void'
),
candidates AS (
    SELECT
        'sc.payment.execution'::varchar AS source_model,
        e.id AS source_res_id,
        e.name AS source_record_name,
        e.legacy_record_id,
        e.project_id,
        e.partner_id,
        e.date_payment AS document_date,
        'out'::varchar AS direction,
        'legacy_actual_outflow'::varchar AS source_kind,
        COALESCE(e.paid_amount, 0.0) AS amount,
        e.currency_id,
        e.payment_family AS business_category
    FROM sc_payment_execution e
    WHERE e.source_origin = 'legacy'
      AND e.state = 'legacy_confirmed'
      AND COALESCE(e.legacy_record_id, '') != ''

    UNION ALL

    SELECT
        'sc.receipt.income'::varchar AS source_model,
        r.id AS source_res_id,
        r.name AS source_record_name,
        r.legacy_record_id,
        r.project_id,
        r.partner_id,
        r.date_receipt AS document_date,
        'in'::varchar AS direction,
        'legacy_receipt'::varchar AS source_kind,
        COALESCE(r.amount, 0.0) AS amount,
        r.currency_id,
        COALESCE(NULLIF(r.income_category, ''), NULLIF(r.legacy_receipt_type, ''), r.source_family) AS business_category
    FROM sc_receipt_income r
    WHERE r.source_origin = 'legacy'
      AND r.state = 'legacy_confirmed'
      AND COALESCE(r.legacy_record_id, '') != ''

    UNION ALL

    SELECT
        'sc.expense.claim'::varchar AS source_model,
        c.id AS source_res_id,
        c.name AS source_record_name,
        c.legacy_record_id,
        c.project_id,
        c.partner_id,
        c.date_claim AS document_date,
        CASE WHEN c.direction = 'inflow' THEN 'in' ELSE 'out' END::varchar AS direction,
        CASE WHEN c.direction = 'inflow' THEN 'legacy_receipt' ELSE 'legacy_actual_outflow' END::varchar AS source_kind,
        COALESCE(c.approved_amount, c.amount, 0.0) AS amount,
        c.currency_id,
        COALESCE(NULLIF(c.expense_type, ''), c.claim_type) AS business_category
    FROM sc_expense_claim c
    WHERE c.source_origin = 'legacy'
      AND c.state = 'legacy_confirmed'
      AND COALESCE(c.legacy_record_id, '') != ''
),
matched AS (
    SELECT
        l.*,
        c.source_model,
        c.source_res_id,
        c.source_record_name,
        c.document_date,
        c.business_category,
        c.project_id AS candidate_project_id,
        c.partner_id AS candidate_partner_id,
        c.direction AS candidate_direction,
        c.source_kind AS candidate_source_kind,
        c.amount AS candidate_amount,
        c.currency_id AS candidate_currency_id,
        CASE WHEN c.project_id = l.project_id THEN 1 ELSE 0 END AS project_match,
        CASE WHEN COALESCE(c.partner_id, 0) = COALESCE(l.partner_id, 0) THEN 1 ELSE 0 END AS partner_match,
        CASE WHEN c.direction = l.direction THEN 1 ELSE 0 END AS direction_match,
        CASE WHEN c.source_kind = l.source_kind THEN 1 ELSE 0 END AS source_kind_match,
        CASE WHEN ABS(COALESCE(c.amount, 0.0) - COALESCE(l.amount, 0.0)) <= 0.01 THEN 1 ELSE 0 END AS amount_match,
        CASE
            WHEN COALESCE(c.currency_id, 0) = COALESCE(l.currency_id, 0) THEN 1
            WHEN c.currency_id IS NULL AND l.currency_id IS NOT NULL THEN 1
            ELSE 0
        END AS currency_match,
        CASE WHEN c.currency_id IS NULL AND l.currency_id IS NOT NULL THEN 1 ELSE 0 END AS candidate_currency_missing,
        CASE WHEN c.document_date = l.ledger_date THEN 1 ELSE 0 END AS date_match
    FROM source_less l
    LEFT JOIN candidates c ON c.legacy_record_id = l.legacy_record_id
),
exact AS (
    SELECT *
    FROM matched
    WHERE source_model IS NOT NULL
      AND project_match = 1
      AND direction_match = 1
      AND source_kind_match = 1
      AND amount_match = 1
      AND currency_match = 1
),
exact_counts AS (
    SELECT ledger_id, COUNT(*)::integer AS exact_count
    FROM exact
    GROUP BY ledger_id
),
all_counts AS (
    SELECT ledger_id, COUNT(source_model)::integer AS candidate_count
    FROM matched
    GROUP BY ledger_id
)
"""


summary = _fetchone_dict(
    MATCH_CTE
    + """
    SELECT
        COUNT(*)::integer AS source_less_legacy_ledger_count,
        COUNT(*) FILTER (WHERE l.source_kind = 'legacy_actual_outflow')::integer AS source_less_outflow_count,
        COUNT(*) FILTER (WHERE l.source_kind = 'legacy_receipt')::integer AS source_less_receipt_count,
        COALESCE(SUM(l.amount), 0.0) AS source_less_amount,
        COUNT(ec.ledger_id)::integer AS exact_attachable_ledger_count,
        COALESCE(SUM(l.amount) FILTER (WHERE ec.ledger_id IS NOT NULL), 0.0) AS exact_attachable_amount,
        COUNT(*) FILTER (WHERE ac.candidate_count > 0 AND ec.ledger_id IS NULL)::integer AS candidate_but_not_exact_count,
        COUNT(*) FILTER (WHERE COALESCE(ac.candidate_count, 0) = 0)::integer AS no_candidate_count,
        COUNT(*) FILTER (WHERE ec.exact_count > 1)::integer AS ambiguous_exact_count
    FROM source_less l
    LEFT JOIN exact_counts ec ON ec.ledger_id = l.ledger_id
    LEFT JOIN all_counts ac ON ac.ledger_id = l.ledger_id
    """
)

by_kind = _fetchall_dict(
    MATCH_CTE
    + """
    SELECT
        l.source_kind,
        l.direction,
        COUNT(*)::integer AS source_less_count,
        COUNT(ec.ledger_id)::integer AS exact_attachable_count,
        COUNT(*) FILTER (WHERE ac.candidate_count > 0 AND ec.ledger_id IS NULL)::integer AS candidate_but_not_exact_count,
        COUNT(*) FILTER (WHERE COALESCE(ac.candidate_count, 0) = 0)::integer AS no_candidate_count,
        COALESCE(SUM(l.amount), 0.0) AS amount,
        COALESCE(SUM(l.amount) FILTER (WHERE ec.ledger_id IS NOT NULL), 0.0) AS exact_attachable_amount
    FROM source_less l
    LEFT JOIN exact_counts ec ON ec.ledger_id = l.ledger_id
    LEFT JOIN all_counts ac ON ac.ledger_id = l.ledger_id
    GROUP BY l.source_kind, l.direction
    ORDER BY l.source_kind, l.direction
    """
)

exact_by_source = _fetchall_dict(
    MATCH_CTE
    + """
    SELECT
        e.source_kind,
        e.legacy_source_ref,
        e.source_model,
        COUNT(*)::integer AS exact_rows,
        COUNT(DISTINCT e.ledger_id)::integer AS exact_ledgers,
        COALESCE(SUM(e.amount), 0.0) AS amount
    FROM exact e
    GROUP BY e.source_kind, e.legacy_source_ref, e.source_model
    ORDER BY exact_ledgers DESC, e.source_kind, e.source_model
    """
)

not_exact_reasons = _fetchall_dict(
    MATCH_CTE
    + """
    SELECT
        reason,
        COUNT(*)::integer AS ledger_count
    FROM (
        SELECT
            l.ledger_id,
            CASE
                WHEN COALESCE(ac.candidate_count, 0) = 0 THEN 'no_candidate_by_legacy_record_id'
                WHEN ec.ledger_id IS NOT NULL THEN 'exact_attachable'
                WHEN EXISTS (
                    SELECT 1 FROM matched m
                    WHERE m.ledger_id = l.ledger_id
                      AND m.source_model IS NOT NULL
                      AND m.project_match = 0
                ) THEN 'candidate_project_mismatch'
                WHEN EXISTS (
                    SELECT 1 FROM matched m
                    WHERE m.ledger_id = l.ledger_id
                      AND m.source_model IS NOT NULL
                      AND m.direction_match = 0
                ) THEN 'candidate_direction_mismatch'
                WHEN EXISTS (
                    SELECT 1 FROM matched m
                    WHERE m.ledger_id = l.ledger_id
                      AND m.source_model IS NOT NULL
                      AND m.source_kind_match = 0
                ) THEN 'candidate_source_kind_mismatch'
                WHEN EXISTS (
                    SELECT 1 FROM matched m
                    WHERE m.ledger_id = l.ledger_id
                      AND m.source_model IS NOT NULL
                      AND m.amount_match = 0
                ) THEN 'candidate_amount_mismatch'
                WHEN EXISTS (
                    SELECT 1 FROM matched m
                    WHERE m.ledger_id = l.ledger_id
                      AND m.source_model IS NOT NULL
                      AND m.currency_match = 0
                ) THEN 'candidate_currency_mismatch'
                ELSE 'candidate_not_exact_other'
            END AS reason
        FROM source_less l
        LEFT JOIN exact_counts ec ON ec.ledger_id = l.ledger_id
        LEFT JOIN all_counts ac ON ac.ledger_id = l.ledger_id
    ) reasons
    GROUP BY reason
    ORDER BY ledger_count DESC, reason
    """
)

attachable_samples = _fetchall_dict(
    MATCH_CTE
    + """
    SELECT
        ledger_id,
        ledger_name,
        ledger_date,
        source_kind,
        direction,
        amount,
        legacy_record_id,
        legacy_source_ref,
        source_model,
        source_res_id,
        source_record_name,
        business_category,
        project_id,
        partner_id
    FROM exact
    ORDER BY ledger_id
    LIMIT 20
    """
)

unmatched_samples = _fetchall_dict(
    MATCH_CTE
    + """
    SELECT
        l.ledger_id,
        l.ledger_name,
        l.ledger_date,
        l.source_kind,
        l.direction,
        l.amount,
        l.legacy_record_id,
        l.legacy_source_ref,
        l.project_id,
        l.partner_id,
        LEFT(l.note, 240) AS note_preview,
        COALESCE(ac.candidate_count, 0) AS candidate_count
    FROM source_less l
    LEFT JOIN exact_counts ec ON ec.ledger_id = l.ledger_id
    LEFT JOIN all_counts ac ON ac.ledger_id = l.ledger_id
    WHERE ec.ledger_id IS NULL
    ORDER BY l.ledger_id
    LIMIT 30
    """
)

ambiguous_exact = _fetchall_dict(
    MATCH_CTE
    + """
    SELECT
        ledger_id,
        COUNT(*)::integer AS exact_count,
        json_agg(
            json_build_object(
                'source_model', source_model,
                'source_res_id', source_res_id,
                'source_record_name', source_record_name
            )
            ORDER BY source_model, source_res_id
        ) AS candidates
    FROM exact
    GROUP BY ledger_id
    HAVING COUNT(*) > 1
    ORDER BY ledger_id
    LIMIT 20
    """
)

already_source_linked = _fetchone_dict(
    """
    SELECT
        COUNT(*)::integer AS source_linked_count
    FROM sc_treasury_ledger
    WHERE source_model IN ('sc.payment.execution', 'sc.receipt.income', 'sc.expense.claim')
      AND source_res_id IS NOT NULL
      AND source_kind IN ('legacy_actual_outflow', 'legacy_receipt')
      AND state != 'void'
    """
)

failures = []
if ambiguous_exact:
    failures.append({"key": "ambiguous_exact_legacy_ledger_attachment", "rows": ambiguous_exact})

result = {
    "audit": "finance_legacy_source_less_ledger_reconciliation_audit",
    "status": "PASS" if not failures else "FAIL",
    "database": env.cr.dbname,  # noqa: F821
    "summary": summary,
    "by_kind": by_kind,
    "exact_by_source": exact_by_source,
    "not_exact_reasons": not_exact_reasons,
    "already_source_linked": already_source_linked,
    "attachable_samples": attachable_samples,
    "unmatched_samples": unmatched_samples,
    "failures": failures,
    "policy": {
        "write_mode": "read_only",
        "safe_attach_rule": "legacy_record_id + project_id + direction + source_kind + amount must match exactly and one-to-one; currency must match or be missing on the candidate while present on the ledger",
        "safe_attach_count_field": "summary.exact_attachable_ledger_count",
        "unmatched_policy": [
            "do not source-attach rows without an exact one-to-one match",
            "keep unmatched rows as legacy daily/general cash ledger evidence until their source facts are found",
            "source-linked migration may create new rows only for expected source facts not already covered by exact source-less attachments",
        ],
    },
}

print("FINANCE_LEGACY_SOURCE_LESS_LEDGER_RECONCILIATION_AUDIT: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True, default=str))
if failures:
    raise SystemExit(1)
