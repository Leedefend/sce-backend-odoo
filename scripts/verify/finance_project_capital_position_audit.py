# -*- coding: utf-8 -*-
"""Audit the project capital position projection.

Run inside Odoo shell:
    DB_NAME=sc_demo bash scripts/ops/odoo_shell_exec.sh < scripts/verify/finance_project_capital_position_audit.py
"""

from __future__ import annotations

import json
import os
from collections import OrderedDict
from pathlib import Path


def artifact_root() -> Path:
    raw = os.getenv("MIGRATION_ARTIFACT_ROOT") or os.getenv("FINANCE_PROJECT_CAPITAL_ARTIFACT_ROOT")
    candidates = [Path(raw)] if raw else []
    candidates.extend([Path("/mnt/artifacts/backend"), Path(f"/tmp/finance_project_capital/{env.cr.dbname}")])  # noqa: F821
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


def assert_equal(errors, key, expected, actual):
    if int(expected or 0) != int(actual or 0):
        errors.append({"key": key, "expected": expected, "actual": actual})


def assert_amount_close(errors, key, expected, actual, tolerance=0.01):
    if abs(float(expected or 0.0) - float(actual or 0.0)) > tolerance:
        errors.append({"key": key, "expected": expected, "actual": actual})


errors = []
summary = OrderedDict()

expected_project_count = sql_one(
    """
    SELECT COUNT(*)::integer
      FROM (
            SELECT COALESCE(project_id, 0) AS project_key FROM sc_finance_business_project_summary
            UNION
            SELECT COALESCE(project_id, 0) AS project_key FROM sc_interfund_movement_project_summary
           ) s
    """
)
actual_project_count = sql_one("SELECT COUNT(*)::integer FROM sc_finance_project_capital_position")
assert_equal(errors, "project_capital_position_count", expected_project_count, actual_project_count)

missing_project_keys = sql_rows(
    """
    WITH expected AS (
        SELECT COALESCE(project_id, 0) AS project_key FROM sc_finance_business_project_summary
        UNION
        SELECT COALESCE(project_id, 0) AS project_key FROM sc_interfund_movement_project_summary
    ),
    actual AS (
        SELECT COALESCE(project_id, 0) AS project_key FROM sc_finance_project_capital_position
    )
    SELECT e.project_key
      FROM expected e
      LEFT JOIN actual a ON a.project_key = e.project_key
     WHERE a.project_key IS NULL
     ORDER BY e.project_key
    """
)
extra_project_keys = sql_rows(
    """
    WITH expected AS (
        SELECT COALESCE(project_id, 0) AS project_key FROM sc_finance_business_project_summary
        UNION
        SELECT COALESCE(project_id, 0) AS project_key FROM sc_interfund_movement_project_summary
    ),
    actual AS (
        SELECT COALESCE(project_id, 0) AS project_key FROM sc_finance_project_capital_position
    )
    SELECT a.project_key
      FROM actual a
      LEFT JOIN expected e ON e.project_key = a.project_key
     WHERE e.project_key IS NULL
     ORDER BY a.project_key
    """
)
if missing_project_keys:
    errors.append({"key": "missing_project_keys", "values": [row[0] for row in missing_project_keys]})
if extra_project_keys:
    errors.append({"key": "extra_project_keys", "values": [row[0] for row in extra_project_keys]})

finance_expected = sql_rows(
    """
    SELECT
        COUNT(*)::integer,
        COALESCE(SUM(source_line_count), 0)::integer,
        COALESCE(SUM(balance_effect), 0.0),
        COALESCE(SUM(cash_in_amount), 0.0),
        COALESCE(SUM(cash_out_amount), 0.0),
        COALESCE(SUM(arrival_amount), 0.0),
        COALESCE(SUM(deduction_net_amount), 0.0),
        COALESCE(SUM(self_funding_balance), 0.0),
        COALESCE(SUM(guarantee_outstanding_amount), 0.0),
        COALESCE(SUM(tax_deduction_amount), 0.0),
        COALESCE(SUM(tax_deduction_tax_amount), 0.0)
      FROM sc_finance_business_project_summary
    """
)[0]
finance_actual = sql_rows(
    """
    SELECT
        COALESCE(SUM(finance_group_count), 0)::integer,
        COALESCE(SUM(finance_source_line_count), 0)::integer,
        COALESCE(SUM(finance_balance_effect), 0.0),
        COALESCE(SUM(finance_cash_in_amount), 0.0),
        COALESCE(SUM(finance_cash_out_amount), 0.0),
        COALESCE(SUM(arrival_amount), 0.0),
        COALESCE(SUM(deduction_net_amount), 0.0),
        COALESCE(SUM(self_funding_balance), 0.0),
        COALESCE(SUM(guarantee_outstanding_amount), 0.0),
        COALESCE(SUM(tax_deduction_amount), 0.0),
        COALESCE(SUM(tax_deduction_tax_amount), 0.0)
      FROM sc_finance_project_capital_position
    """
)[0]

interfund_expected = sql_rows(
    """
    SELECT
        COUNT(*)::integer,
        COALESCE(SUM(source_line_count), 0)::integer,
        COALESCE(SUM(inflow_amount), 0.0),
        COALESCE(SUM(outflow_amount), 0.0),
        COALESCE(SUM(net_amount), 0.0),
        COALESCE(SUM(internal_transfer_amount), 0.0),
        COALESCE(SUM(company_borrow_in_amount), 0.0),
        COALESCE(SUM(company_repay_out_amount), 0.0),
        COALESCE(SUM(project_transfer_in_amount), 0.0),
        COALESCE(SUM(project_transfer_out_amount), 0.0),
        COALESCE(SUM(contractor_borrow_out_amount), 0.0),
        COALESCE(SUM(contractor_repay_in_amount), 0.0)
      FROM sc_interfund_movement_project_summary
    """
)[0]
interfund_actual = sql_rows(
    """
    SELECT
        COALESCE(SUM(interfund_group_count), 0)::integer,
        COALESCE(SUM(interfund_source_line_count), 0)::integer,
        COALESCE(SUM(interfund_inflow_amount), 0.0),
        COALESCE(SUM(interfund_outflow_amount), 0.0),
        COALESCE(SUM(interfund_net_amount), 0.0),
        COALESCE(SUM(internal_transfer_amount), 0.0),
        COALESCE(SUM(company_borrow_in_amount), 0.0),
        COALESCE(SUM(company_repay_out_amount), 0.0),
        COALESCE(SUM(project_transfer_in_amount), 0.0),
        COALESCE(SUM(project_transfer_out_amount), 0.0),
        COALESCE(SUM(contractor_borrow_out_amount), 0.0),
        COALESCE(SUM(contractor_repay_in_amount), 0.0)
      FROM sc_finance_project_capital_position
    """
)[0]

finance_metrics = [
    "group_count",
    "source_line_count",
    "balance_effect",
    "cash_in_amount",
    "cash_out_amount",
    "arrival_amount",
    "deduction_net_amount",
    "self_funding_balance",
    "guarantee_outstanding_amount",
    "tax_deduction_amount",
    "tax_deduction_tax_amount",
]
for idx, metric in enumerate(finance_metrics):
    if idx < 2:
        assert_equal(errors, f"finance.{metric}", finance_expected[idx], finance_actual[idx])
    else:
        assert_amount_close(errors, f"finance.{metric}", finance_expected[idx], finance_actual[idx])

interfund_metrics = [
    "group_count",
    "source_line_count",
    "inflow_amount",
    "outflow_amount",
    "net_amount",
    "internal_transfer_amount",
    "company_borrow_in_amount",
    "company_repay_out_amount",
    "project_transfer_in_amount",
    "project_transfer_out_amount",
    "contractor_borrow_out_amount",
    "contractor_repay_in_amount",
]
for idx, metric in enumerate(interfund_metrics):
    if idx < 2:
        assert_equal(errors, f"interfund.{metric}", interfund_expected[idx], interfund_actual[idx])
    else:
        assert_amount_close(errors, f"interfund.{metric}", interfund_expected[idx], interfund_actual[idx])

combined_expected = float(finance_expected[2] or 0.0) + float(interfund_expected[4] or 0.0)
combined_actual = sql_one("SELECT COALESCE(SUM(combined_balance_effect), 0.0) FROM sc_finance_project_capital_position")
assert_amount_close(errors, "combined.balance_effect", combined_expected, combined_actual)

cash_net_expected = float(finance_expected[3] or 0.0) - float(finance_expected[4] or 0.0) + float(interfund_expected[4] or 0.0)
cash_net_actual = sql_one("SELECT COALESCE(SUM(combined_cash_net_amount), 0.0) FROM sc_finance_project_capital_position")
assert_amount_close(errors, "combined.cash_net_amount", cash_net_expected, cash_net_actual)

summary["expected_project_count"] = expected_project_count
summary["actual_project_count"] = actual_project_count
summary["finance_expected"] = dict(zip(finance_metrics, finance_expected))
summary["finance_actual"] = dict(zip(finance_metrics, finance_actual))
summary["interfund_expected"] = dict(zip(interfund_metrics, interfund_expected))
summary["interfund_actual"] = dict(zip(interfund_metrics, interfund_actual))
summary["combined"] = OrderedDict(
    [
        ("balance_effect_expected", combined_expected),
        ("balance_effect_actual", combined_actual),
        ("cash_net_expected", cash_net_expected),
        ("cash_net_actual", cash_net_actual),
    ]
)
summary["top_combined_balance"] = [
    list(row)
    for row in sql_rows(
        """
        SELECT project_id, source_line_count, finance_balance_effect, interfund_net_amount, combined_balance_effect
          FROM sc_finance_project_capital_position
         ORDER BY ABS(combined_balance_effect) DESC, source_line_count DESC
         LIMIT 20
        """
    )
]

result = OrderedDict()
result["status"] = "PASS" if not errors else "FAIL"
result["database"] = env.cr.dbname  # noqa: F821
result["summary"] = summary
result["errors"] = errors

target = artifact_root() / f"finance_project_capital_position_audit_{env.cr.dbname}.json"  # noqa: F821
target.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
if errors:
    raise SystemExit(1)
