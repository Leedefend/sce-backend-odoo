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
    category_rows = _rows(
        """
        SELECT code, target_model, COUNT(*)::integer AS category_rows
          FROM sc_business_category
         WHERE code IN ('contract.income', 'contract.expense', 'settlement.income', 'settlement.expense')
         GROUP BY code, target_model
         ORDER BY code
        """
    )
    categories = {row["code"]: row for row in category_rows}
    expected_targets = {
        "contract.income": "construction.contract.income",
        "contract.expense": "construction.contract.expense",
        "settlement.income": "sc.settlement.order",
        "settlement.expense": "sc.settlement.order",
    }
    for code, target_model in expected_targets.items():
        row = categories.get(code)
        if not row:
            failures.append("%s: missing business category" % code)
        elif row["target_model"] != target_model:
            failures.append("%s: expected target_model=%s, got %s" % (code, target_model, row["target_model"]))

    contract_rows = _rows(
        """
        WITH expected AS (
            SELECT c.id,
                   CASE WHEN c.type = 'in' THEN 'contract.expense' ELSE 'contract.income' END AS expected_code,
                   cat.code AS actual_code
              FROM construction_contract c
              LEFT JOIN sc_business_category cat ON cat.id = c.business_category_id
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
    settlement_rows = _rows(
        """
        WITH expected AS (
            SELECT s.id,
                   CASE WHEN s.settlement_type = 'in' THEN 'settlement.income' ELSE 'settlement.expense' END AS expected_code,
                   cat.code AS actual_code
              FROM sc_settlement_order s
              LEFT JOIN sc_business_category cat ON cat.id = s.business_category_id
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
                SELECT 'construction.contract' AS model_name, cat.code, cat.target_model
                  FROM construction_contract c
                  JOIN sc_business_category cat ON cat.id = c.business_category_id
                 WHERE (c.type = 'in' AND cat.target_model != 'construction.contract.expense')
                    OR (c.type != 'in' AND cat.target_model != 'construction.contract.income')
                UNION ALL
                SELECT 'sc.settlement.order' AS model_name, cat.code, cat.target_model
                  FROM sc_settlement_order s
                  JOIN sc_business_category cat ON cat.id = s.business_category_id
                 WHERE cat.target_model != 'sc.settlement.order'
          ) t
         GROUP BY model_name, code, target_model
         ORDER BY model_name, code
        """
    )
    for row in contract_rows + settlement_rows:
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
        "contract_bindings": contract_rows,
        "settlement_bindings": settlement_rows,
        "target_mismatches": target_mismatches,
    }
except Exception as err:
    failures.append("unexpected error: %s" % err)
    failures.append(traceback.format_exc())

result = {
    "audit": "contract_business_category_binding_audit",
    "status": "PASS" if not failures else "FAIL",
    "summary": summary,
    "failures": failures,
}
print("CONTRACT_BUSINESS_CATEGORY_BINDING_AUDIT: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True))
if failures:
    print("FAILURES:")
    for failure in failures:
        print("- %s" % failure)

sys.exit(0 if not failures else 1)
