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
    "total_direct_acceptance_requests": sql_one(
        """
        SELECT COUNT(*)::integer
          FROM sc_subcontract_request
         WHERE legacy_fact_type = 'direct_acceptance:分包方单'
        """
    ),
    "linked_requests": sql_one(
        """
        SELECT COUNT(*)::integer
          FROM sc_subcontract_request
         WHERE legacy_fact_type = 'direct_acceptance:分包方单'
           AND contract_id IS NOT NULL
        """
    ),
    "missing_contract_requests": sql_one(
        """
        SELECT COUNT(*)::integer
          FROM sc_subcontract_request
         WHERE legacy_fact_type = 'direct_acceptance:分包方单'
           AND contract_id IS NULL
        """
    ),
    "linked_project_partner_mismatch": sql_one(
        """
        SELECT COUNT(*)::integer
          FROM sc_subcontract_request r
          JOIN construction_contract c ON c.id = r.contract_id
         WHERE r.legacy_fact_type = 'direct_acceptance:分包方单'
           AND (
                c.project_id IS DISTINCT FROM r.project_id
                OR c.partner_id IS DISTINCT FROM r.suggested_subcontractor_id
           )
        """
    ),
}

residual_rows = sql_rows(
    """
    WITH candidates AS (
        SELECT r.id AS request_id,
               COUNT(c.id)::integer AS candidate_count
          FROM sc_subcontract_request r
          LEFT JOIN construction_contract c
            ON c.type = 'in'
           AND c.project_id = r.project_id
           AND c.partner_id = r.suggested_subcontractor_id
         WHERE r.contract_id IS NULL
           AND r.legacy_fact_type = 'direct_acceptance:分包方单'
         GROUP BY r.id
    )
    SELECT CASE
               WHEN candidate_count = 0 THEN 'no_candidate'
               WHEN candidate_count = 1 THEN 'unique_candidate_unlinked'
               ELSE 'multiple_candidates'
           END AS residual_type,
           COUNT(*)::integer AS row_count
      FROM candidates
     GROUP BY 1
     ORDER BY 1
    """
)
summary["residuals"] = residual_rows

sample_rows = sql_rows(
    """
    WITH candidates AS (
        SELECT r.id AS request_id,
               r.name,
               r.project_id,
               r.suggested_subcontractor_id,
               r.legacy_visible_05 AS subcontractor_name,
               r.legacy_visible_07 AS scope_name,
               COUNT(c.id)::integer AS candidate_count
          FROM sc_subcontract_request r
          LEFT JOIN construction_contract c
            ON c.type = 'in'
           AND c.project_id = r.project_id
           AND c.partner_id = r.suggested_subcontractor_id
         WHERE r.contract_id IS NULL
           AND r.legacy_fact_type = 'direct_acceptance:分包方单'
         GROUP BY r.id
    )
    SELECT CASE
               WHEN candidate_count = 0 THEN 'no_candidate'
               WHEN candidate_count = 1 THEN 'unique_candidate_unlinked'
               ELSE 'multiple_candidates'
           END AS residual_type,
           request_id,
           name,
           project_id,
           suggested_subcontractor_id,
           subcontractor_name,
           scope_name,
           candidate_count
      FROM candidates
     ORDER BY residual_type, request_id
     LIMIT 20
    """
)
summary["residual_sample"] = sample_rows

unique_residual = next(
    (row["row_count"] for row in residual_rows if row["residual_type"] == "unique_candidate_unlinked"),
    0,
)
if unique_residual:
    errors.append("%s subcontract requests still have a unique contract candidate but no contract_id" % unique_residual)
if summary["linked_project_partner_mismatch"]:
    errors.append("%s linked subcontract requests mismatch project or subcontractor" % summary["linked_project_partner_mismatch"])

result = {
    "audit": "subcontract_request_contract_anchor_audit",
    "database": env.cr.dbname,  # noqa: F821
    "status": "PASS" if not errors else "FAIL",
    "summary": summary,
    "errors": errors,
}
print("SUBCONTRACT_REQUEST_CONTRACT_ANCHOR_AUDIT: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True))
