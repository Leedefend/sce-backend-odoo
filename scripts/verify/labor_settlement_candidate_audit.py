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
    "source_usage_count": sql_one(
        """
        SELECT COUNT(*)::integer
          FROM sc_labor_usage
         WHERE legacy_fact_type IN ('direct_acceptance:方单', 'direct_acceptance:零星用工')
           AND legacy_settlement_state IN ('unsettled', 'unknown')
           AND project_id IS NOT NULL
           AND contractor_id IS NOT NULL
        """
    ),
    "candidate_usage_count": sql_one(
        """
        SELECT COALESCE(SUM(usage_count), 0)::integer
          FROM sc_labor_settlement_candidate
        """
    ),
    "source_amount": sql_one(
        """
        SELECT COALESCE(SUM(legacy_settlement_amount), 0.0)::numeric
          FROM sc_labor_usage
         WHERE legacy_fact_type IN ('direct_acceptance:方单', 'direct_acceptance:零星用工')
           AND legacy_settlement_state IN ('unsettled', 'unknown')
           AND project_id IS NOT NULL
           AND contractor_id IS NOT NULL
        """
    ),
    "candidate_amount": sql_one(
        """
        SELECT COALESCE(SUM(legacy_settlement_amount), 0.0)::numeric
          FROM sc_labor_settlement_candidate
        """
    ),
    "candidate_group_count": sql_one(
        """
        SELECT COUNT(*)::integer
          FROM sc_labor_settlement_candidate
        """
    ),
    "ready_group_count": sql_one(
        """
        SELECT COUNT(*)::integer
          FROM sc_labor_settlement_candidate
         WHERE candidate_state = 'ready'
        """
    ),
    "review_group_count": sql_one(
        """
        SELECT COUNT(*)::integer
          FROM sc_labor_settlement_candidate
         WHERE candidate_state = 'needs_review'
        """
    ),
    "missing_business_anchor": sql_one(
        """
        SELECT COUNT(*)::integer
          FROM sc_labor_settlement_candidate
         WHERE project_id IS NULL
            OR contractor_id IS NULL
            OR currency_id IS NULL
        """
    ),
}

summary["by_type_state"] = sql_rows(
    """
    SELECT legacy_fact_type,
           legacy_settlement_state,
           candidate_state,
           COUNT(*)::integer AS group_count,
           SUM(usage_count)::integer AS usage_count,
           SUM(legacy_settlement_amount)::numeric AS amount_total
      FROM sc_labor_settlement_candidate
     GROUP BY legacy_fact_type, legacy_settlement_state, candidate_state
     ORDER BY legacy_fact_type, legacy_settlement_state, candidate_state
    """
)

summary["top_candidates"] = sql_rows(
    """
    SELECT id,
           display_name,
           project_id,
           contractor_id,
           legacy_fact_type,
           candidate_state,
           usage_count,
           legacy_settlement_amount
      FROM sc_labor_settlement_candidate
     ORDER BY legacy_settlement_amount DESC, id
     LIMIT 20
    """
)

if summary["source_usage_count"] != summary["candidate_usage_count"]:
    errors.append(
        "candidate usage_count mismatch: source=%s candidate=%s"
        % (summary["source_usage_count"], summary["candidate_usage_count"])
    )

if abs(float(summary["source_amount"] or 0.0) - float(summary["candidate_amount"] or 0.0)) > 0.0001:
    errors.append(
        "candidate amount mismatch: source=%s candidate=%s"
        % (summary["source_amount"], summary["candidate_amount"])
    )

if summary["missing_business_anchor"]:
    errors.append("missing business anchor=%s" % summary["missing_business_anchor"])

if not summary["ready_group_count"]:
    errors.append("no ready labor settlement candidates")

result = {
    "audit": "labor_settlement_candidate_audit",
    "database": env.cr.dbname,  # noqa: F821
    "status": "PASS" if not errors else "FAIL",
    "summary": summary,
    "errors": errors,
}
print("LABOR_SETTLEMENT_CANDIDATE_AUDIT: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True, default=str))
