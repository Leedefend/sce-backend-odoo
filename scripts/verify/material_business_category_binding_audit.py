# -*- coding: utf-8 -*-
import json
import sys
import traceback


def _rows(sql, params=None):
    env.cr.execute(sql, params or [])  # noqa: F821
    return env.cr.dictfetchall()  # noqa: F821


failures = []
summary = {}

try:
    expected_targets = {
        "material.plan": "project.material.plan",
        "material.purchase.request": "sc.material.purchase.request",
        "material.acceptance": "sc.material.acceptance",
        "material.rfq": "sc.material.rfq",
        "material.inbound": "sc.material.inbound",
        "material.outbound": "sc.material.outbound",
        "material.return": "sc.material.outbound",
        "material.transfer": "sc.material.outbound",
        "material.loss": "sc.material.outbound",
        "material.settlement": "sc.material.settlement",
    }
    category_rows = _rows(
        """
        SELECT code, target_model, COUNT(*)::integer AS category_rows
          FROM sc_business_category
         WHERE code = ANY(%s)
         GROUP BY code, target_model
         ORDER BY code
        """,
        [list(expected_targets.keys())],
    )
    categories = {row["code"]: row for row in category_rows}
    for code, target_model in expected_targets.items():
        row = categories.get(code)
        if not row:
            failures.append("%s: missing business category" % code)
        elif row["target_model"] != target_model:
            failures.append("%s: expected target_model=%s, got %s" % (code, target_model, row["target_model"]))

    singleton_rows = _rows(
        """
        SELECT expected_code,
               COUNT(*)::integer AS row_count,
               SUM(CASE WHEN actual_code = expected_code THEN 1 ELSE 0 END)::integer AS matched_count,
               SUM(CASE WHEN COALESCE(actual_code, '') != expected_code THEN 1 ELSE 0 END)::integer AS mismatch_count
          FROM (
                SELECT 'material.plan' AS expected_code, cat.code AS actual_code
                  FROM project_material_plan rec
                  LEFT JOIN sc_business_category cat ON cat.id = rec.business_category_id
                UNION ALL
                SELECT 'material.purchase.request' AS expected_code, cat.code AS actual_code
                  FROM sc_material_purchase_request rec
                  LEFT JOIN sc_business_category cat ON cat.id = rec.business_category_id
                UNION ALL
                SELECT 'material.acceptance' AS expected_code, cat.code AS actual_code
                  FROM sc_material_acceptance rec
                  LEFT JOIN sc_business_category cat ON cat.id = rec.business_category_id
                UNION ALL
                SELECT 'material.inbound' AS expected_code, cat.code AS actual_code
                  FROM sc_material_inbound rec
                  LEFT JOIN sc_business_category cat ON cat.id = rec.business_category_id
                UNION ALL
                SELECT 'material.rfq' AS expected_code, cat.code AS actual_code
                  FROM sc_material_rfq rec
                  LEFT JOIN sc_business_category cat ON cat.id = rec.business_category_id
                UNION ALL
                SELECT 'material.settlement' AS expected_code, cat.code AS actual_code
                  FROM sc_material_settlement rec
                  LEFT JOIN sc_business_category cat ON cat.id = rec.business_category_id
          ) expected
         GROUP BY expected_code
         ORDER BY expected_code
        """
    )
    outbound_rows = _rows(
        """
        WITH expected AS (
            SELECT CASE COALESCE(rec.outbound_type, 'issue')
                       WHEN 'return' THEN 'material.return'
                       WHEN 'transfer' THEN 'material.transfer'
                       WHEN 'loss' THEN 'material.loss'
                       ELSE 'material.outbound'
                   END AS expected_code,
                   cat.code AS actual_code
              FROM sc_material_outbound rec
              LEFT JOIN sc_business_category cat ON cat.id = rec.business_category_id
        )
        SELECT expected_code,
               COUNT(*)::integer AS row_count,
               SUM(CASE WHEN actual_code = expected_code THEN 1 ELSE 0 END)::integer AS matched_count,
               SUM(CASE WHEN COALESCE(actual_code, '') != expected_code THEN 1 ELSE 0 END)::integer AS mismatch_count
          FROM expected
         GROUP BY expected_code
         ORDER BY expected_code
        """
    )
    target_mismatches = _rows(
        """
        SELECT model_name, code, target_model, COUNT(*)::integer AS row_count
          FROM (
                SELECT 'project.material.plan' AS model_name, cat.code, cat.target_model
                  FROM project_material_plan rec
                  JOIN sc_business_category cat ON cat.id = rec.business_category_id
                 WHERE cat.target_model != 'project.material.plan'
                UNION ALL
                SELECT 'sc.material.purchase.request' AS model_name, cat.code, cat.target_model
                  FROM sc_material_purchase_request rec
                  JOIN sc_business_category cat ON cat.id = rec.business_category_id
                 WHERE cat.target_model != 'sc.material.purchase.request'
                UNION ALL
                SELECT 'sc.material.acceptance' AS model_name, cat.code, cat.target_model
                  FROM sc_material_acceptance rec
                  JOIN sc_business_category cat ON cat.id = rec.business_category_id
                 WHERE cat.target_model != 'sc.material.acceptance'
                UNION ALL
                SELECT 'sc.material.inbound' AS model_name, cat.code, cat.target_model
                  FROM sc_material_inbound rec
                  JOIN sc_business_category cat ON cat.id = rec.business_category_id
                 WHERE cat.target_model != 'sc.material.inbound'
                UNION ALL
                SELECT 'sc.material.outbound' AS model_name, cat.code, cat.target_model
                  FROM sc_material_outbound rec
                  JOIN sc_business_category cat ON cat.id = rec.business_category_id
                 WHERE cat.target_model != 'sc.material.outbound'
                UNION ALL
                SELECT 'sc.material.rfq' AS model_name, cat.code, cat.target_model
                  FROM sc_material_rfq rec
                  JOIN sc_business_category cat ON cat.id = rec.business_category_id
                 WHERE cat.target_model != 'sc.material.rfq'
                UNION ALL
                SELECT 'sc.material.settlement' AS model_name, cat.code, cat.target_model
                  FROM sc_material_settlement rec
                  JOIN sc_business_category cat ON cat.id = rec.business_category_id
                 WHERE cat.target_model != 'sc.material.settlement'
          ) t
         GROUP BY model_name, code, target_model
         ORDER BY model_name, code
        """
    )
    for row in singleton_rows + outbound_rows:
        if row["mismatch_count"]:
            failures.append(
                "%s: %s mismatched of %s rows"
                % (row["expected_code"], row["mismatch_count"], row["row_count"])
            )
    for row in target_mismatches:
        failures.append(
            "%s/%s: bound category target_model=%s for %s rows"
            % (row["model_name"], row["code"], row["target_model"], row["row_count"])
        )

    summary = {
        "database": env.cr.dbname,  # noqa: F821
        "category_rows": category_rows,
        "singleton_bindings": singleton_rows,
        "outbound_bindings": outbound_rows,
        "target_mismatches": target_mismatches,
    }
except Exception as err:
    failures.append("unexpected error: %s" % err)
    failures.append(traceback.format_exc())

result = {
    "audit": "material_business_category_binding_audit",
    "status": "PASS" if not failures else "FAIL",
    "summary": summary,
    "failures": failures,
}
print("MATERIAL_BUSINESS_CATEGORY_BINDING_AUDIT: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True))
if failures:
    print("FAILURES:")
    for failure in failures:
        print("- %s" % failure)

sys.exit(0 if not failures else 1)
