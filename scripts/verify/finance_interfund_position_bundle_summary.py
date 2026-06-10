# -*- coding: utf-8 -*-
"""Summarize the finance/interfund position audit bundle."""

from __future__ import annotations

import json
import os
from collections import OrderedDict
from pathlib import Path


def artifact_root() -> Path:
    raw = os.getenv("MIGRATION_ARTIFACT_ROOT") or os.getenv("FINANCE_INTERFUND_POSITION_ARTIFACT_ROOT")
    candidates = [Path(raw)] if raw else []
    candidates.extend([Path("/mnt/artifacts/backend"), Path(f"/tmp/finance_interfund_position/{env.cr.dbname}")])  # noqa: F821
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

finance_fact_count = sql_one("SELECT COUNT(*)::integer FROM sc_finance_business_fact")
finance_project_lines = sql_one("SELECT COALESCE(SUM(source_line_count), 0)::integer FROM sc_finance_business_project_summary")
finance_capital_lines = sql_one("SELECT COALESCE(SUM(finance_source_line_count), 0)::integer FROM sc_finance_project_capital_position")
finance_project_counterparty_lines = sql_one(
    "SELECT COALESCE(SUM(finance_source_line_count), 0)::integer FROM sc_finance_project_counterparty_position"
)
finance_counterparty_summary_lines = sql_one(
    "SELECT COALESCE(SUM(finance_source_line_count), 0)::integer FROM sc_finance_counterparty_position_summary"
)
for key, actual in [
    ("finance_business_project_summary_lines", finance_project_lines),
    ("finance_project_capital_lines", finance_capital_lines),
    ("finance_project_counterparty_lines", finance_project_counterparty_lines),
    ("finance_counterparty_summary_lines", finance_counterparty_summary_lines),
]:
    assert_equal(errors, key, finance_fact_count, actual)

interfund_fact_count = sql_one("SELECT COUNT(*)::integer FROM sc_interfund_movement_fact")
interfund_project_lines = sql_one(
    "SELECT COALESCE(SUM(source_line_count), 0)::integer FROM sc_interfund_movement_project_summary"
)
interfund_capital_lines = sql_one(
    "SELECT COALESCE(SUM(interfund_source_line_count), 0)::integer FROM sc_finance_project_capital_position"
)
interfund_project_counterparty_lines = sql_one(
    "SELECT COALESCE(SUM(interfund_source_line_count), 0)::integer FROM sc_finance_project_counterparty_position"
)
interfund_counterparty_summary_lines = sql_one(
    "SELECT COALESCE(SUM(interfund_source_line_count), 0)::integer FROM sc_finance_counterparty_position_summary"
)
for key, actual in [
    ("interfund_project_capital_lines", interfund_capital_lines),
    ("interfund_project_counterparty_lines", interfund_project_counterparty_lines),
    ("interfund_counterparty_summary_lines", interfund_counterparty_summary_lines),
]:
    assert_equal(errors, key, interfund_project_lines, actual)

combined_balance_effect = sql_one(
    "SELECT COALESCE(SUM(combined_balance_effect), 0.0) FROM sc_finance_project_capital_position"
)
counterparty_combined_balance_effect = sql_one(
    "SELECT COALESCE(SUM(combined_balance_effect), 0.0) FROM sc_finance_project_counterparty_position"
)
counterparty_summary_combined_balance_effect = sql_one(
    "SELECT COALESCE(SUM(combined_balance_effect), 0.0) FROM sc_finance_counterparty_position_summary"
)
assert_amount_close(
    errors,
    "combined_balance_effect.project_vs_project_counterparty",
    combined_balance_effect,
    counterparty_combined_balance_effect,
)
assert_amount_close(
    errors,
    "combined_balance_effect.project_vs_counterparty_summary",
    combined_balance_effect,
    counterparty_summary_combined_balance_effect,
)

combined_cash_net_amount = sql_one(
    "SELECT COALESCE(SUM(combined_cash_net_amount), 0.0) FROM sc_finance_project_capital_position"
)
counterparty_combined_cash_net_amount = sql_one(
    "SELECT COALESCE(SUM(combined_cash_net_amount), 0.0) FROM sc_finance_project_counterparty_position"
)
counterparty_summary_combined_cash_net_amount = sql_one(
    "SELECT COALESCE(SUM(combined_cash_net_amount), 0.0) FROM sc_finance_counterparty_position_summary"
)
assert_amount_close(
    errors,
    "combined_cash_net_amount.project_vs_project_counterparty",
    combined_cash_net_amount,
    counterparty_combined_cash_net_amount,
)
assert_amount_close(
    errors,
    "combined_cash_net_amount.project_vs_counterparty_summary",
    combined_cash_net_amount,
    counterparty_summary_combined_cash_net_amount,
)

misleading_unknown_company = sql_one(
    """
    SELECT COUNT(*)::integer
      FROM sc_finance_project_counterparty_position
     WHERE counterparty_type = 'unknown'
       AND counterparty_name = '公司'
    """
)
assert_equal(errors, "misleading_unknown_company_count", 0, misleading_unknown_company)

project_to_project_net = sql_one(
    """
    SELECT COALESCE(SUM(net_amount), 0.0)
      FROM sc_interfund_movement_project_summary
     WHERE movement_type = 'project_to_project_transfer'
    """
)
same_project_net = sql_one(
    """
    SELECT COALESCE(SUM(net_amount), 0.0)
      FROM sc_interfund_movement_project_summary
     WHERE movement_type = 'same_project_account_transfer'
    """
)
assert_amount_close(errors, "project_to_project_transfer_global_net", 0.0, project_to_project_net)
assert_amount_close(errors, "same_project_account_transfer_net", 0.0, same_project_net)

summary["lineage_counts"] = OrderedDict(
    [
        ("finance_fact_count", finance_fact_count),
        ("finance_project_summary_lines", finance_project_lines),
        ("finance_project_capital_lines", finance_capital_lines),
        ("finance_project_counterparty_lines", finance_project_counterparty_lines),
        ("finance_counterparty_summary_lines", finance_counterparty_summary_lines),
        ("interfund_fact_count", interfund_fact_count),
        ("interfund_project_perspective_lines", interfund_project_lines),
        ("interfund_project_capital_lines", interfund_capital_lines),
        ("interfund_project_counterparty_lines", interfund_project_counterparty_lines),
        ("interfund_counterparty_summary_lines", interfund_counterparty_summary_lines),
    ]
)
summary["position_amounts"] = OrderedDict(
    [
        ("combined_balance_effect", combined_balance_effect),
        ("combined_cash_net_amount", combined_cash_net_amount),
        ("project_to_project_transfer_global_net", project_to_project_net),
        ("same_project_account_transfer_net", same_project_net),
    ]
)
summary["project_capital_rows"] = sql_one("SELECT COUNT(*)::integer FROM sc_finance_project_capital_position")
summary["project_counterparty_rows"] = sql_one("SELECT COUNT(*)::integer FROM sc_finance_project_counterparty_position")
summary["counterparty_summary_rows"] = sql_one("SELECT COUNT(*)::integer FROM sc_finance_counterparty_position_summary")
summary["counterparty_type_counts"] = [
    list(row)
    for row in sql_rows(
        """
        SELECT counterparty_type, COUNT(*)::integer, COALESCE(SUM(source_line_count), 0)::integer, COALESCE(SUM(combined_balance_effect), 0.0)
          FROM sc_finance_counterparty_position_summary
         GROUP BY counterparty_type
         ORDER BY counterparty_type
        """
    )
]
summary["unidentified_quality"] = OrderedDict(
    [
        ("misleading_unknown_company_count", misleading_unknown_company),
        (
            "unidentified_contractor",
            list(
                sql_rows(
                    """
                    SELECT
                        COALESCE(SUM(source_line_count), 0)::integer,
                        COALESCE(SUM(combined_balance_effect), 0.0)
                      FROM sc_finance_counterparty_position_summary
                     WHERE counterparty_type = 'partner'
                       AND counterparty_name = '未识别承包人'
                    """
                )[0]
            ),
        ),
        (
            "unidentified_object",
            list(
                sql_rows(
                    """
                    SELECT
                        COALESCE(SUM(source_line_count), 0)::integer,
                        COALESCE(SUM(combined_balance_effect), 0.0)
                      FROM sc_finance_counterparty_position_summary
                     WHERE counterparty_type = 'unknown'
                       AND counterparty_name = '未识别对象'
                    """
                )[0]
            ),
        ),
    ]
)
summary["top_project_positions"] = [
    list(row)
    for row in sql_rows(
        """
        SELECT project_id, source_line_count, combined_balance_effect, combined_cash_net_amount
          FROM sc_finance_project_capital_position
         ORDER BY ABS(combined_balance_effect) DESC, source_line_count DESC
         LIMIT 10
        """
    )
]
summary["top_counterparty_positions"] = [
    list(row)
    for row in sql_rows(
        """
        SELECT counterparty_type, counterparty_name, project_count, source_line_count, combined_balance_effect
          FROM sc_finance_counterparty_position_summary
         ORDER BY ABS(combined_balance_effect) DESC, source_line_count DESC
         LIMIT 10
        """
    )
]

result = OrderedDict()
result["status"] = "PASS" if not errors else "FAIL"
result["database"] = env.cr.dbname  # noqa: F821
result["summary"] = summary
result["errors"] = errors

target = artifact_root() / f"finance_interfund_position_bundle_summary_{env.cr.dbname}.json"  # noqa: F821
target.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
if errors:
    raise SystemExit(1)
