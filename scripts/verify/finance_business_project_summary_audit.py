# -*- coding: utf-8 -*-
"""Audit the project-level finance business fact summary projection.

Run inside Odoo shell:
    DB_NAME=sc_demo bash scripts/ops/odoo_shell_exec.sh < scripts/verify/finance_business_project_summary_audit.py
"""

from __future__ import annotations

import json
import os
from collections import OrderedDict
from pathlib import Path


def artifact_root() -> Path:
    raw = os.getenv("MIGRATION_ARTIFACT_ROOT") or os.getenv("FINANCE_BUSINESS_FACT_ARTIFACT_ROOT")
    candidates = [Path(raw)] if raw else []
    candidates.extend([Path("/mnt/artifacts/backend"), Path(f"/tmp/finance_business_fact/{env.cr.dbname}")])  # noqa: F821
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return candidate
        except OSError:
            continue
    return Path("/tmp")


def sql_one(query, params=None):
    env.cr.execute(query, params or [])  # noqa: F821
    row = env.cr.fetchone()  # noqa: F821
    return row[0] if row else None


def sql_rows(query, params=None):
    env.cr.execute(query, params or [])  # noqa: F821
    return env.cr.fetchall()  # noqa: F821


def table(rows):
    return [list(row) for row in rows]


def assert_equal(errors, key, expected, actual):
    if int(expected or 0) != int(actual or 0):
        errors.append({"key": key, "expected": expected, "actual": actual})


def assert_amount_close(errors, key, expected, actual, tolerance=0.01):
    if abs(float(expected or 0.0) - float(actual or 0.0)) > tolerance:
        errors.append({"key": key, "expected": expected, "actual": actual})


errors = []
summary = OrderedDict()

fact_group_count = sql_one(
    """
    SELECT COUNT(*)::integer
      FROM (
            SELECT COALESCE(project_id, 0), business_domain
              FROM sc_finance_business_fact
             GROUP BY COALESCE(project_id, 0), business_domain
           ) g
    """
)
summary_count = sql_one("SELECT COUNT(*)::integer FROM sc_finance_business_project_summary")
assert_equal(errors, "summary_group_count", fact_group_count, summary_count)

fact_totals = OrderedDict(
    (row[0], row[1:])
    for row in sql_rows(
        """
        SELECT
            business_domain,
            COUNT(*)::integer,
            COALESCE(SUM(amount), 0.0),
            COALESCE(SUM(balance_effect), 0.0),
            COALESCE(SUM(cash_in_amount), 0.0),
            COALESCE(SUM(cash_out_amount), 0.0),
            COALESCE(SUM(deduction_amount), 0.0),
            COALESCE(SUM(paid_amount), 0.0),
            COALESCE(SUM(tax_amount), 0.0)
          FROM sc_finance_business_fact
         GROUP BY business_domain
         ORDER BY business_domain
        """
    )
)
summary_totals = OrderedDict(
    (row[0], row[1:])
    for row in sql_rows(
        """
        SELECT
            business_domain,
            COALESCE(SUM(source_line_count), 0)::integer,
            COALESCE(SUM(amount), 0.0),
            COALESCE(SUM(balance_effect), 0.0),
            COALESCE(SUM(cash_in_amount), 0.0),
            COALESCE(SUM(cash_out_amount), 0.0),
            COALESCE(SUM(deduction_amount), 0.0),
            COALESCE(SUM(paid_amount), 0.0),
            COALESCE(SUM(tax_amount), 0.0)
          FROM sc_finance_business_project_summary
         GROUP BY business_domain
         ORDER BY business_domain
        """
    )
)

metric_names = [
    "count",
    "amount",
    "balance_effect",
    "cash_in_amount",
    "cash_out_amount",
    "deduction_amount",
    "paid_amount",
    "tax_amount",
]
for domain, fact_values in fact_totals.items():
    summary_values = summary_totals.get(domain)
    if not summary_values:
        errors.append({"key": "missing_summary_domain", "domain": domain})
        continue
    assert_equal(errors, f"{domain}.count", fact_values[0], summary_values[0])
    for idx, metric_name in enumerate(metric_names[1:], start=1):
        assert_amount_close(errors, f"{domain}.{metric_name}", fact_values[idx], summary_values[idx])

business_totals = OrderedDict()
business_totals["fact_self_funding_canonical_balance"] = sql_one(
    """
    SELECT COALESCE(SUM(balance_effect), 0.0)
      FROM sc_finance_business_fact
     WHERE business_domain = 'self_funding'
       AND balance_policy = 'canonical'
    """
)
business_totals["summary_self_funding_balance"] = sql_one(
    "SELECT COALESCE(SUM(self_funding_balance), 0.0) FROM sc_finance_business_project_summary"
)
business_totals["summary_self_funding_visible_reference_amount"] = sql_one(
    "SELECT COALESCE(SUM(self_funding_visible_reference_amount), 0.0) FROM sc_finance_business_project_summary"
)
business_totals["fact_guarantee_balance"] = sql_one(
    "SELECT COALESCE(SUM(balance_effect), 0.0) FROM sc_finance_business_fact WHERE business_domain = 'guarantee_deposit'"
)
business_totals["summary_guarantee_outstanding"] = sql_one(
    "SELECT COALESCE(SUM(guarantee_outstanding_amount), 0.0) FROM sc_finance_business_project_summary"
)
business_totals["fact_tax_balance_effect"] = sql_one(
    "SELECT COALESCE(SUM(balance_effect), 0.0) FROM sc_finance_business_fact WHERE business_domain = 'tax_deduction'"
)
business_totals["summary_tax_balance_effect"] = sql_one(
    "SELECT COALESCE(SUM(balance_effect), 0.0) FROM sc_finance_business_project_summary WHERE business_domain = 'tax_deduction'"
)

assert_amount_close(
    errors,
    "self_funding_canonical_balance",
    business_totals["fact_self_funding_canonical_balance"],
    business_totals["summary_self_funding_balance"],
)
assert_amount_close(
    errors,
    "guarantee_outstanding",
    business_totals["fact_guarantee_balance"],
    business_totals["summary_guarantee_outstanding"],
)
assert_amount_close(errors, "fact_tax_balance_effect_zero", 0.0, business_totals["fact_tax_balance_effect"])
assert_amount_close(errors, "summary_tax_balance_effect_zero", 0.0, business_totals["summary_tax_balance_effect"])

missing_project_rows = table(
    sql_rows(
        """
        SELECT business_domain, COUNT(*)::integer, COALESCE(SUM(amount), 0.0), COALESCE(SUM(balance_effect), 0.0)
          FROM sc_finance_business_project_summary
         WHERE project_id IS NULL
         GROUP BY business_domain
         ORDER BY business_domain
        """
    )
)

summary["fact_group_count"] = fact_group_count
summary["summary_count"] = summary_count
summary["fact_totals"] = {key: dict(zip(metric_names, value)) for key, value in fact_totals.items()}
summary["summary_totals"] = {key: dict(zip(metric_names, value)) for key, value in summary_totals.items()}
summary["business_totals"] = business_totals
summary["missing_project_rows"] = missing_project_rows
summary["top_project_balances"] = table(
    sql_rows(
        """
        SELECT project_id, business_domain, source_line_count, balance_effect
          FROM sc_finance_business_project_summary
         ORDER BY ABS(balance_effect) DESC, source_line_count DESC
         LIMIT 20
        """
    )
)

result = OrderedDict()
result["status"] = "PASS" if not errors else "FAIL"
result["database"] = env.cr.dbname  # noqa: F821
result["summary"] = summary
result["errors"] = errors

target = artifact_root() / f"finance_business_project_summary_audit_{env.cr.dbname}.json"  # noqa: F821
target.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
if errors:
    raise SystemExit(1)
