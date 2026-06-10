# -*- coding: utf-8 -*-
"""Audit the cross-project counterparty capital position summary projection."""

from __future__ import annotations

import json
import os
from collections import OrderedDict
from pathlib import Path


def artifact_root() -> Path:
    raw = os.getenv("MIGRATION_ARTIFACT_ROOT") or os.getenv("FINANCE_COUNTERPARTY_SUMMARY_ARTIFACT_ROOT")
    candidates = [Path(raw)] if raw else []
    candidates.extend([Path("/mnt/artifacts/backend"), Path(f"/tmp/finance_counterparty_summary/{env.cr.dbname}")])  # noqa: F821
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


GROUP_SQL = """
    FROM sc_finance_project_counterparty_position
   GROUP BY counterparty_type, counterparty_project_id, partner_id, counterparty_name
"""


errors = []
summary = OrderedDict()

expected_row_count = sql_one("SELECT COUNT(*)::integer FROM (SELECT 1 " + GROUP_SQL + ") g")
actual_row_count = sql_one("SELECT COUNT(*)::integer FROM sc_finance_counterparty_position_summary")
assert_equal(errors, "counterparty_summary_row_count", expected_row_count, actual_row_count)

expected_totals = sql_rows(
    """
    SELECT
        COALESCE(SUM(finance_source_line_count), 0)::integer,
        COALESCE(SUM(interfund_source_line_count), 0)::integer,
        COALESCE(SUM(source_line_count), 0)::integer,
        COALESCE(SUM(finance_balance_effect), 0.0),
        COALESCE(SUM(finance_cash_in_amount), 0.0),
        COALESCE(SUM(finance_cash_out_amount), 0.0),
        COALESCE(SUM(finance_cash_net_amount), 0.0),
        COALESCE(SUM(interfund_inflow_amount), 0.0),
        COALESCE(SUM(interfund_outflow_amount), 0.0),
        COALESCE(SUM(interfund_net_amount), 0.0),
        COALESCE(SUM(internal_transfer_amount), 0.0),
        COALESCE(SUM(combined_balance_effect), 0.0),
        COALESCE(SUM(combined_cash_net_amount), 0.0)
      FROM sc_finance_project_counterparty_position
    """
)[0]
actual_totals = sql_rows(
    """
    SELECT
        COALESCE(SUM(finance_source_line_count), 0)::integer,
        COALESCE(SUM(interfund_source_line_count), 0)::integer,
        COALESCE(SUM(source_line_count), 0)::integer,
        COALESCE(SUM(finance_balance_effect), 0.0),
        COALESCE(SUM(finance_cash_in_amount), 0.0),
        COALESCE(SUM(finance_cash_out_amount), 0.0),
        COALESCE(SUM(finance_cash_net_amount), 0.0),
        COALESCE(SUM(interfund_inflow_amount), 0.0),
        COALESCE(SUM(interfund_outflow_amount), 0.0),
        COALESCE(SUM(interfund_net_amount), 0.0),
        COALESCE(SUM(internal_transfer_amount), 0.0),
        COALESCE(SUM(combined_balance_effect), 0.0),
        COALESCE(SUM(combined_cash_net_amount), 0.0)
      FROM sc_finance_counterparty_position_summary
    """
)[0]

metrics = [
    "finance_source_line_count",
    "interfund_source_line_count",
    "source_line_count",
    "finance_balance_effect",
    "finance_cash_in_amount",
    "finance_cash_out_amount",
    "finance_cash_net_amount",
    "interfund_inflow_amount",
    "interfund_outflow_amount",
    "interfund_net_amount",
    "internal_transfer_amount",
    "combined_balance_effect",
    "combined_cash_net_amount",
]
for idx, metric in enumerate(metrics):
    if idx < 3:
        assert_equal(errors, metric, expected_totals[idx], actual_totals[idx])
    else:
        assert_amount_close(errors, metric, expected_totals[idx], actual_totals[idx])

direction_counts = sql_rows(
    """
    SELECT position_direction, COUNT(*)::integer, COALESCE(SUM(source_line_count), 0)::integer, COALESCE(SUM(combined_balance_effect), 0.0)
      FROM sc_finance_counterparty_position_summary
     GROUP BY position_direction
     ORDER BY position_direction
    """
)
type_counts = sql_rows(
    """
    SELECT counterparty_type, COUNT(*)::integer, COALESCE(SUM(source_line_count), 0)::integer, COALESCE(SUM(combined_balance_effect), 0.0)
      FROM sc_finance_counterparty_position_summary
     GROUP BY counterparty_type
     ORDER BY counterparty_type
    """
)
top_balances = sql_rows(
    """
    SELECT counterparty_type, counterparty_name, project_count, source_line_count, combined_balance_effect
      FROM sc_finance_counterparty_position_summary
     ORDER BY ABS(combined_balance_effect) DESC, source_line_count DESC
     LIMIT 20
    """
)

summary["expected_row_count"] = expected_row_count
summary["actual_row_count"] = actual_row_count
summary["expected_totals"] = dict(zip(metrics, expected_totals))
summary["actual_totals"] = dict(zip(metrics, actual_totals))
summary["direction_counts"] = [list(row) for row in direction_counts]
summary["counterparty_type_counts"] = [list(row) for row in type_counts]
summary["top_counterparty_balances"] = [list(row) for row in top_balances]

result = OrderedDict()
result["status"] = "PASS" if not errors else "FAIL"
result["database"] = env.cr.dbname  # noqa: F821
result["summary"] = summary
result["errors"] = errors

target = artifact_root() / f"finance_counterparty_position_summary_audit_{env.cr.dbname}.json"  # noqa: F821
target.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
if errors:
    raise SystemExit(1)
