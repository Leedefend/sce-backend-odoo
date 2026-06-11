# -*- coding: utf-8 -*-
import json
import sys
import traceback


def _rows(sql, params=None):
    env.cr.execute(sql, params or [])  # noqa: F821
    return env.cr.dictfetchall()  # noqa: F821


def _scalar(sql, params=None):
    env.cr.execute(sql, params or [])  # noqa: F821
    row = env.cr.fetchone()  # noqa: F821
    return row[0] if row else 0


def _category_counts():
    return _rows(
        """
        SELECT code, target_model, COUNT(*)::integer AS category_rows
          FROM sc_business_category
         WHERE code IN (
             'invoice.output.application',
             'invoice.output.registration',
             'invoice.input.report',
             'invoice.prepaid_tax',
             'tax.deduction.registration'
         )
         GROUP BY code, target_model
         ORDER BY code
        """
    )


def _invoice_binding_rows():
    return _rows(
        """
        WITH expected AS (
            SELECT inv.id,
                   CASE
                       WHEN inv.source_kind = 'prepaid_tax' OR inv.direction = 'prepaid'
                           THEN 'invoice.prepaid_tax'
                       WHEN inv.source_kind = 'input_invoice_tax' OR inv.direction = 'input'
                           THEN 'invoice.input.report'
                       WHEN inv.source_kind = 'output_invoice_tax' AND inv.invoice_content = '销项开票申请'
                           THEN 'invoice.output.application'
                       WHEN inv.source_kind = 'output_invoice_tax' OR inv.direction = 'output'
                           THEN 'invoice.output.registration'
                       ELSE NULL
                   END AS expected_code,
                   cat.code AS actual_code
              FROM sc_invoice_registration inv
              LEFT JOIN sc_business_category cat ON cat.id = inv.business_category_id
        )
        SELECT expected_code,
               COUNT(*)::integer AS row_count,
               SUM(CASE WHEN actual_code = expected_code THEN 1 ELSE 0 END)::integer AS matched_count,
               SUM(CASE WHEN expected_code IS NOT NULL AND COALESCE(actual_code, '') != expected_code THEN 1 ELSE 0 END)::integer AS mismatch_count
          FROM expected
         WHERE expected_code IS NOT NULL
         GROUP BY expected_code
         ORDER BY expected_code
        """
    )


def _tax_binding_rows():
    return _rows(
        """
        SELECT 'tax.deduction.registration' AS expected_code,
               COUNT(*)::integer AS row_count,
               SUM(CASE WHEN cat.code = 'tax.deduction.registration' THEN 1 ELSE 0 END)::integer AS matched_count,
               SUM(CASE WHEN COALESCE(cat.code, '') != 'tax.deduction.registration' THEN 1 ELSE 0 END)::integer AS mismatch_count
          FROM sc_tax_deduction_registration ded
          LEFT JOIN sc_business_category cat ON cat.id = ded.business_category_id
         WHERE COALESCE(ded.is_transfer_out, false) = false
        """
    )


def _tax_branch_summary():
    return _rows(
        """
        SELECT COUNT(*)::integer AS total_count,
               COUNT(*) FILTER (WHERE COALESCE(is_transfer_out, false))::integer AS transfer_out_count,
               COUNT(*) FILTER (WHERE COALESCE(withholding_amount, 0.0) <> 0.0)::integer AS withholding_count,
               COUNT(*) FILTER (
                   WHERE COALESCE(is_transfer_out, false) = false
                     AND COALESCE(withholding_amount, 0.0) = 0.0
               )::integer AS ordinary_deduction_count,
               COUNT(*) FILTER (WHERE business_category_id IS NULL)::integer AS missing_category_count
          FROM sc_tax_deduction_registration
        """
    )


def _target_mismatches():
    return _rows(
        """
        SELECT model_name, code, target_model, COUNT(*)::integer AS row_count
          FROM (
                SELECT 'sc.invoice.registration' AS model_name, cat.code, cat.target_model
                  FROM sc_invoice_registration inv
                  JOIN sc_business_category cat ON cat.id = inv.business_category_id
                 WHERE cat.target_model != 'sc.invoice.registration'
                UNION ALL
                SELECT 'sc.tax.deduction.registration' AS model_name, cat.code, cat.target_model
                  FROM sc_tax_deduction_registration ded
                  JOIN sc_business_category cat ON cat.id = ded.business_category_id
                 WHERE cat.target_model != 'sc.tax.deduction.registration'
          ) t
         GROUP BY model_name, code, target_model
         ORDER BY model_name, code
        """
    )


failures = []
summary = {}

try:
    category_rows = _category_counts()
    categories = {row["code"]: row for row in category_rows}
    expected_targets = {
        "invoice.output.application": "sc.invoice.registration",
        "invoice.output.registration": "sc.invoice.registration",
        "invoice.input.report": "sc.invoice.registration",
        "invoice.prepaid_tax": "sc.invoice.registration",
        "tax.deduction.registration": "sc.tax.deduction.registration",
    }
    for code, target_model in expected_targets.items():
        row = categories.get(code)
        if not row:
            failures.append("%s: missing business category" % code)
        elif row["target_model"] != target_model:
            failures.append("%s: expected target_model=%s, got %s" % (code, target_model, row["target_model"]))

    invoice_rows = _invoice_binding_rows()
    tax_rows = _tax_binding_rows()
    tax_branch_rows = _tax_branch_summary()
    target_mismatches = _target_mismatches()
    for row in invoice_rows + tax_rows:
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
    if tax_branch_rows:
        tax_branch = tax_branch_rows[0]
        if tax_branch["missing_category_count"]:
            failures.append("tax.deduction.registration: %s rows missing business_category_id" % tax_branch["missing_category_count"])
        if tax_branch["transfer_out_count"]:
            failures.append(
                "tax.deduction.registration: %s transfer-out rows require a dedicated business category before acceptance"
                % tax_branch["transfer_out_count"]
            )
        if tax_branch["withholding_count"]:
            failures.append(
                "tax.deduction.registration: %s withholding deduction rows require a dedicated business category before acceptance"
                % tax_branch["withholding_count"]
            )

    summary = {
        "database": env.cr.dbname,  # noqa: F821
        "category_rows": category_rows,
        "invoice_bindings": invoice_rows,
        "tax_bindings": tax_rows,
        "tax_branch_summary": tax_branch_rows,
        "target_mismatches": target_mismatches,
        "invoice_total": _scalar("SELECT COUNT(*) FROM sc_invoice_registration"),
        "tax_deduction_total": _scalar("SELECT COUNT(*) FROM sc_tax_deduction_registration"),
    }
except Exception as err:
    failures.append("unexpected error: %s" % err)
    failures.append(traceback.format_exc())

result = {
    "audit": "invoice_tax_category_binding_audit",
    "status": "PASS" if not failures else "FAIL",
    "summary": summary,
    "failures": failures,
}
print("INVOICE_TAX_CATEGORY_BINDING_AUDIT: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True))
if failures:
    print("FAILURES:")
    for failure in failures:
        print("- %s" % failure)

sys.exit(0 if not failures else 1)
