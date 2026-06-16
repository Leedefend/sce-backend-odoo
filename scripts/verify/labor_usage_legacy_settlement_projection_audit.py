# -*- coding: utf-8 -*-
import json


def sql_one(query, params=None):
    env.cr.execute(query, params or ())  # noqa: F821
    row = env.cr.fetchone()  # noqa: F821
    return row[0] if row else None


def sql_rows(query, params=None):
    env.cr.execute(query, params or ())  # noqa: F821
    return env.cr.dictfetchall()  # noqa: F821


errors = []

summary = {
    "total_labor_usage": sql_one(
        """
        SELECT COUNT(*)::integer
          FROM sc_labor_usage
         WHERE legacy_fact_type IN ('direct_acceptance:方单', 'direct_acceptance:零星用工')
        """
    ),
    "ticket_usage": sql_one(
        """
        SELECT COUNT(*)::integer
          FROM sc_labor_usage
         WHERE legacy_fact_type = 'direct_acceptance:方单'
        """
    ),
    "casual_usage": sql_one(
        """
        SELECT COUNT(*)::integer
          FROM sc_labor_usage
         WHERE legacy_fact_type = 'direct_acceptance:零星用工'
        """
    ),
    "missing_currency": sql_one(
        """
        SELECT COUNT(*)::integer
          FROM sc_labor_usage
         WHERE legacy_fact_type IN ('direct_acceptance:方单', 'direct_acceptance:零星用工')
           AND currency_id IS NULL
        """
    ),
    "missing_structured_state": sql_one(
        """
        SELECT COUNT(*)::integer
          FROM sc_labor_usage
         WHERE legacy_fact_type IN ('direct_acceptance:方单', 'direct_acceptance:零星用工')
           AND legacy_settlement_state IS NULL
        """
    ),
    "state_mismatch": sql_one(
        """
        SELECT COUNT(*)::integer
          FROM sc_labor_usage
         WHERE legacy_fact_type IN ('direct_acceptance:方单', 'direct_acceptance:零星用工')
           AND legacy_settlement_state IS DISTINCT FROM CASE
                   WHEN legacy_fact_type = 'direct_acceptance:方单' AND legacy_visible_08 = '已结算' THEN 'settled'
                   WHEN legacy_fact_type = 'direct_acceptance:方单' AND legacy_visible_08 = '未结算' THEN 'unsettled'
                   WHEN legacy_fact_type = 'direct_acceptance:方单' AND COALESCE(legacy_visible_08, '') != '' THEN 'unknown'
                   WHEN legacy_fact_type = 'direct_acceptance:零星用工' AND legacy_visible_12 = '已结算' THEN 'settled'
                   WHEN legacy_fact_type = 'direct_acceptance:零星用工' AND legacy_visible_12 = '未结算' THEN 'unsettled'
                   WHEN legacy_fact_type = 'direct_acceptance:零星用工' AND COALESCE(legacy_visible_12, '') != '' THEN 'unknown'
                   ELSE NULL
               END
        """
    ),
    "amount_mismatch": sql_one(
        """
        WITH expected AS (
            SELECT id,
                   CASE
                       WHEN regexp_replace(COALESCE(legacy_visible_09, ''), '[^0-9\\.-]', '', 'g') ~ '^-?[0-9]+(\\.[0-9]+)?$'
                       THEN regexp_replace(legacy_visible_09, '[^0-9\\.-]', '', 'g')::numeric
                       ELSE 0.0
                   END AS expected_amount
              FROM sc_labor_usage
             WHERE legacy_fact_type IN ('direct_acceptance:方单', 'direct_acceptance:零星用工')
        )
        SELECT COUNT(*)::integer
          FROM sc_labor_usage usage
          JOIN expected ON expected.id = usage.id
         WHERE ABS(COALESCE(usage.legacy_settlement_amount, 0.0) - expected.expected_amount) > 0.0001
        """
    ),
}

summary["state_counts"] = sql_rows(
    """
    SELECT legacy_fact_type,
           legacy_settlement_state,
           COUNT(*)::integer AS row_count,
           SUM(COALESCE(legacy_settlement_amount, 0.0))::numeric AS amount_total
      FROM sc_labor_usage
     WHERE legacy_fact_type IN ('direct_acceptance:方单', 'direct_acceptance:零星用工')
     GROUP BY legacy_fact_type, legacy_settlement_state
     ORDER BY legacy_fact_type, legacy_settlement_state
    """
)

summary["unsettled_top"] = sql_rows(
    """
    SELECT id,
           name,
           project_id,
           contractor_id,
           legacy_fact_type,
           legacy_settlement_status,
           legacy_settlement_amount
      FROM sc_labor_usage
     WHERE legacy_fact_type IN ('direct_acceptance:方单', 'direct_acceptance:零星用工')
       AND legacy_settlement_state = 'unsettled'
     ORDER BY legacy_settlement_amount DESC, id
     LIMIT 20
    """
)

for key in ("missing_currency", "missing_structured_state", "state_mismatch", "amount_mismatch"):
    if summary[key]:
        errors.append("%s=%s" % (key, summary[key]))

result = {
    "audit": "labor_usage_legacy_settlement_projection_audit",
    "database": env.cr.dbname,  # noqa: F821
    "status": "PASS" if not errors else "FAIL",
    "summary": summary,
    "errors": errors,
}
print("LABOR_USAGE_LEGACY_SETTLEMENT_PROJECTION_AUDIT: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True, default=str))
