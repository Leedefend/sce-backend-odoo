# -*- coding: utf-8 -*-
"""Audit mechanical settlement counterparty coverage."""

from __future__ import annotations

import json
import sys
import traceback


SOURCE_MODEL = "sc.legacy.direct.acceptance.fact"
ACCEPTANCE_LABEL = "机械结算单"


def _fetchall(sql, params=None):
    env.cr.execute(sql, params or [])  # noqa: F821
    names = [desc[0] for desc in env.cr.description]  # noqa: F821
    return [dict(zip(names, row)) for row in env.cr.fetchall()]  # noqa: F821


def _scalar(sql, params=None):
    env.cr.execute(sql, params or [])  # noqa: F821
    row = env.cr.fetchone()  # noqa: F821
    return row[0] if row else None


def main() -> int:
    failures = []
    summary = _fetchall(
        """
        WITH base AS (
            SELECT s.*,
                   NULLIF(COALESCE(s.legacy_visible_05, ''), '') AS counterparty_name
              FROM sc_settlement_order s
             WHERE s.legacy_fact_model = %s
               AND s.legacy_acceptance_label = %s
        ), partner_name_counts AS (
            SELECT name, COUNT(*) AS partner_count
              FROM res_partner
             WHERE COALESCE(name, '') <> ''
             GROUP BY name
        ), classified AS (
            SELECT b.*,
                   COALESCE(p.partner_count, 0) AS partner_count,
                   CASE
                     WHEN b.partner_id IS NOT NULL THEN 'covered'
                     WHEN b.counterparty_name IS NULL THEN 'missing_counterparty_name'
                     WHEN COALESCE(p.partner_count, 0) = 0 THEN 'missing_partner'
                     WHEN COALESCE(p.partner_count, 0) > 1 THEN 'duplicate_partner_name'
                     ELSE 'fillable_unique_partner'
                   END AS coverage_state
              FROM base b
              LEFT JOIN partner_name_counts p ON p.name = b.counterparty_name
        )
        SELECT coverage_state,
               COUNT(*) AS row_count,
               COALESCE(SUM(amount_total), 0.0) AS amount_total
          FROM classified
         GROUP BY coverage_state
         ORDER BY row_count DESC
        """,
        [SOURCE_MODEL, ACCEPTANCE_LABEL],
    )
    remaining_fillable = int(
        _scalar(
            """
            WITH partner_name_counts AS (
                SELECT name, COUNT(*) AS partner_count
                  FROM res_partner
                 WHERE COALESCE(name, '') <> ''
                 GROUP BY name
            )
            SELECT COUNT(*)
              FROM sc_settlement_order s
              JOIN partner_name_counts p ON p.name = s.legacy_visible_05
             WHERE s.legacy_fact_model = %s
               AND s.legacy_acceptance_label = %s
               AND s.partner_id IS NULL
               AND COALESCE(s.legacy_visible_05, '') <> ''
               AND p.partner_count = 1
            """,
            [SOURCE_MODEL, ACCEPTANCE_LABEL],
        )
        or 0
    )
    if remaining_fillable:
        failures.append(
            {
                "check": "all_unique_counterparty_names_backfilled",
                "remaining_fillable": remaining_fillable,
            }
        )

    mismatch_count = int(
        _scalar(
            """
            SELECT COUNT(*)
              FROM sc_settlement_order s
              JOIN res_partner p ON p.id = s.partner_id
             WHERE s.legacy_fact_model = %s
               AND s.legacy_acceptance_label = %s
               AND COALESCE(s.legacy_visible_05, '') <> ''
               AND p.name <> s.legacy_visible_05
            """,
            [SOURCE_MODEL, ACCEPTANCE_LABEL],
        )
        or 0
    )
    if mismatch_count:
        failures.append(
            {
                "check": "partner_matches_legacy_visible_counterparty",
                "mismatch_count": mismatch_count,
            }
        )

    result = {
        "audit": "mechanical_settlement_partner_audit",
        "status": "PASS" if not failures else "FAIL",
        "source_model": SOURCE_MODEL,
        "acceptance_label": ACCEPTANCE_LABEL,
        "summary": summary,
        "remaining_fillable": remaining_fillable,
        "mismatch_count": mismatch_count,
        "residual_policy": {
            "duplicate_partner_name": "保留待人工核对，避免把同名往来单位错绑到结算办理对象。",
            "missing_counterparty_name": "旧可见字段未提供结算单位，不能凭空补齐。",
        },
        "failures": failures,
    }
    print("MECHANICAL_SETTLEMENT_PARTNER_AUDIT: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if not failures else 1


try:
    sys.exit(main())
except Exception as err:
    result = {
        "audit": "mechanical_settlement_partner_audit",
        "status": "FAIL",
        "error": str(err),
        "traceback": traceback.format_exc(),
    }
    print("MECHANICAL_SETTLEMENT_PARTNER_AUDIT: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True))
    sys.exit(1)
