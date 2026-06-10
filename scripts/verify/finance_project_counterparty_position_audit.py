# -*- coding: utf-8 -*-
"""Audit the project counterparty capital position projection."""

from __future__ import annotations

import json
import os
from collections import OrderedDict
from pathlib import Path


def artifact_root() -> Path:
    raw = os.getenv("MIGRATION_ARTIFACT_ROOT") or os.getenv("FINANCE_PROJECT_COUNTERPARTY_ARTIFACT_ROOT")
    candidates = [Path(raw)] if raw else []
    candidates.extend([Path("/mnt/artifacts/backend"), Path(f"/tmp/finance_project_counterparty/{env.cr.dbname}")])  # noqa: F821
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


PERSPECTIVE_SQL = """
    WITH perspective AS (
        SELECT
            f.project_id,
            CASE
                WHEN f.partner_id IS NOT NULL OR NULLIF(f.partner_name, '') IS NOT NULL THEN 'partner'
                ELSE 'unknown'
            END AS counterparty_type,
            NULL::integer AS counterparty_project_id,
            f.partner_id,
            COALESCE(NULLIF(f.partner_name, ''), '未识别对象') AS counterparty_name,
            1 AS finance_source_line_count,
            0 AS interfund_source_line_count,
            f.balance_effect AS finance_balance_effect,
            f.cash_in_amount AS finance_cash_in_amount,
            f.cash_out_amount AS finance_cash_out_amount,
            0.0 AS interfund_inflow_amount,
            0.0 AS interfund_outflow_amount,
            0.0 AS interfund_net_amount,
            0.0 AS internal_transfer_amount
        FROM sc_finance_business_fact f
        UNION ALL
        SELECT
            f.target_project_id AS project_id,
            CASE
                WHEN f.source_project_id IS NOT NULL THEN 'project'
                WHEN f.partner_id IS NOT NULL OR NULLIF(f.partner_name, '') IS NOT NULL THEN 'partner'
                WHEN f.movement_type = 'contractor_to_project_repay' THEN 'partner'
                WHEN f.movement_type IN ('company_to_project_borrow', 'company_to_project_transfer') THEN 'company'
                ELSE 'unknown'
            END AS counterparty_type,
            f.source_project_id AS counterparty_project_id,
            CASE WHEN f.source_project_id IS NULL THEN f.partner_id ELSE NULL::integer END AS partner_id,
            COALESCE(
                sp.name->>'zh_CN',
                sp.name->>'en_US',
                NULLIF(f.partner_name, ''),
                CASE
                    WHEN f.movement_type = 'contractor_to_project_repay' THEN '未识别承包人'
                    ELSE '公司'
                END
            ) AS counterparty_name,
            0 AS finance_source_line_count,
            1 AS interfund_source_line_count,
            0.0 AS finance_balance_effect,
            0.0 AS finance_cash_in_amount,
            0.0 AS finance_cash_out_amount,
            f.amount AS interfund_inflow_amount,
            0.0 AS interfund_outflow_amount,
            f.amount AS interfund_net_amount,
            0.0 AS internal_transfer_amount
        FROM sc_interfund_movement_fact f
        LEFT JOIN project_project sp ON sp.id = f.source_project_id
        WHERE f.target_project_id IS NOT NULL
          AND f.movement_type IN (
                'company_to_project_borrow',
                'company_to_project_transfer',
                'project_to_project_transfer',
                'contractor_to_project_repay'
          )
        UNION ALL
        SELECT
            f.source_project_id AS project_id,
            CASE
                WHEN f.target_project_id IS NOT NULL THEN 'project'
                WHEN f.partner_id IS NOT NULL OR NULLIF(f.partner_name, '') IS NOT NULL THEN 'partner'
                WHEN f.movement_type = 'project_to_contractor_borrow' THEN 'partner'
                WHEN f.movement_type IN ('project_to_company_repay', 'project_to_company_transfer') THEN 'company'
                ELSE 'unknown'
            END AS counterparty_type,
            f.target_project_id AS counterparty_project_id,
            CASE WHEN f.target_project_id IS NULL THEN f.partner_id ELSE NULL::integer END AS partner_id,
            COALESCE(
                tp.name->>'zh_CN',
                tp.name->>'en_US',
                NULLIF(f.partner_name, ''),
                CASE
                    WHEN f.movement_type = 'project_to_contractor_borrow' THEN '未识别承包人'
                    ELSE '公司'
                END
            ) AS counterparty_name,
            0 AS finance_source_line_count,
            1 AS interfund_source_line_count,
            0.0 AS finance_balance_effect,
            0.0 AS finance_cash_in_amount,
            0.0 AS finance_cash_out_amount,
            0.0 AS interfund_inflow_amount,
            f.amount AS interfund_outflow_amount,
            -f.amount AS interfund_net_amount,
            0.0 AS internal_transfer_amount
        FROM sc_interfund_movement_fact f
        LEFT JOIN project_project tp ON tp.id = f.target_project_id
        WHERE f.source_project_id IS NOT NULL
          AND f.movement_type IN (
                'project_to_company_repay',
                'project_to_company_transfer',
                'project_to_project_transfer',
                'project_to_contractor_borrow'
          )
        UNION ALL
        SELECT
            COALESCE(f.source_project_id, f.target_project_id, f.project_id) AS project_id,
            'internal' AS counterparty_type,
            NULL::integer AS counterparty_project_id,
            NULL::integer AS partner_id,
            '项目内部账户' AS counterparty_name,
            0 AS finance_source_line_count,
            1 AS interfund_source_line_count,
            0.0 AS finance_balance_effect,
            0.0 AS finance_cash_in_amount,
            0.0 AS finance_cash_out_amount,
            0.0 AS interfund_inflow_amount,
            0.0 AS interfund_outflow_amount,
            0.0 AS interfund_net_amount,
            f.amount AS internal_transfer_amount
        FROM sc_interfund_movement_fact f
        WHERE COALESCE(f.source_project_id, f.target_project_id, f.project_id) IS NOT NULL
          AND f.movement_type IN ('same_project_account_transfer', 'unclassified_account_transfer')
    )
"""


errors = []
summary = OrderedDict()

expected_row_count = sql_one(
    PERSPECTIVE_SQL
    + """
    SELECT COUNT(*)::integer
      FROM (
            SELECT project_id, counterparty_type, counterparty_project_id, partner_id, counterparty_name
              FROM perspective
             GROUP BY project_id, counterparty_type, counterparty_project_id, partner_id, counterparty_name
           ) g
    """
)
actual_row_count = sql_one("SELECT COUNT(*)::integer FROM sc_finance_project_counterparty_position")
assert_equal(errors, "counterparty_position_row_count", expected_row_count, actual_row_count)

expected_totals = sql_rows(
    PERSPECTIVE_SQL
    + """
    SELECT
        COALESCE(SUM(finance_source_line_count), 0)::integer,
        COALESCE(SUM(interfund_source_line_count), 0)::integer,
        COALESCE(SUM(finance_balance_effect), 0.0),
        COALESCE(SUM(finance_cash_in_amount), 0.0),
        COALESCE(SUM(finance_cash_out_amount), 0.0),
        COALESCE(SUM(interfund_inflow_amount), 0.0),
        COALESCE(SUM(interfund_outflow_amount), 0.0),
        COALESCE(SUM(interfund_net_amount), 0.0),
        COALESCE(SUM(internal_transfer_amount), 0.0)
      FROM perspective
    """
)[0]
actual_totals = sql_rows(
    """
    SELECT
        COALESCE(SUM(finance_source_line_count), 0)::integer,
        COALESCE(SUM(interfund_source_line_count), 0)::integer,
        COALESCE(SUM(finance_balance_effect), 0.0),
        COALESCE(SUM(finance_cash_in_amount), 0.0),
        COALESCE(SUM(finance_cash_out_amount), 0.0),
        COALESCE(SUM(interfund_inflow_amount), 0.0),
        COALESCE(SUM(interfund_outflow_amount), 0.0),
        COALESCE(SUM(interfund_net_amount), 0.0),
        COALESCE(SUM(internal_transfer_amount), 0.0)
      FROM sc_finance_project_counterparty_position
    """
)[0]

metrics = [
    "finance_source_line_count",
    "interfund_source_line_count",
    "finance_balance_effect",
    "finance_cash_in_amount",
    "finance_cash_out_amount",
    "interfund_inflow_amount",
    "interfund_outflow_amount",
    "interfund_net_amount",
    "internal_transfer_amount",
]
for idx, metric in enumerate(metrics):
    if idx < 2:
        assert_equal(errors, metric, expected_totals[idx], actual_totals[idx])
    else:
        assert_amount_close(errors, metric, expected_totals[idx], actual_totals[idx])

combined_expected = float(expected_totals[2] or 0.0) + float(expected_totals[7] or 0.0)
combined_actual = sql_one("SELECT COALESCE(SUM(combined_balance_effect), 0.0) FROM sc_finance_project_counterparty_position")
cash_net_expected = float(expected_totals[3] or 0.0) - float(expected_totals[4] or 0.0) + float(expected_totals[7] or 0.0)
cash_net_actual = sql_one("SELECT COALESCE(SUM(combined_cash_net_amount), 0.0) FROM sc_finance_project_counterparty_position")
assert_amount_close(errors, "combined_balance_effect", combined_expected, combined_actual)
assert_amount_close(errors, "combined_cash_net_amount", cash_net_expected, cash_net_actual)

summary["expected_row_count"] = expected_row_count
summary["actual_row_count"] = actual_row_count
summary["expected_totals"] = dict(zip(metrics, expected_totals))
summary["actual_totals"] = dict(zip(metrics, actual_totals))
summary["combined"] = OrderedDict(
    [
        ("balance_effect_expected", combined_expected),
        ("balance_effect_actual", combined_actual),
        ("cash_net_expected", cash_net_expected),
        ("cash_net_actual", cash_net_actual),
    ]
)
summary["counterparty_type_counts"] = [
    list(row)
    for row in sql_rows(
        """
        SELECT counterparty_type, COUNT(*)::integer, COALESCE(SUM(source_line_count), 0)::integer, COALESCE(SUM(combined_balance_effect), 0.0)
          FROM sc_finance_project_counterparty_position
         GROUP BY counterparty_type
         ORDER BY counterparty_type
        """
    )
]
summary["top_counterparty_balance"] = [
    list(row)
    for row in sql_rows(
        """
        SELECT project_id, counterparty_type, counterparty_name, source_line_count, combined_balance_effect
          FROM sc_finance_project_counterparty_position
         ORDER BY ABS(combined_balance_effect) DESC, source_line_count DESC
         LIMIT 20
        """
    )
]

misleading_unknown_company = sql_one(
    """
    SELECT COUNT(*)::integer
      FROM sc_finance_project_counterparty_position
     WHERE counterparty_type = 'unknown'
       AND counterparty_name = '公司'
    """
)
assert_equal(errors, "misleading_unknown_company_count", 0, misleading_unknown_company)
summary["misleading_unknown_company_count"] = misleading_unknown_company

result = OrderedDict()
result["status"] = "PASS" if not errors else "FAIL"
result["database"] = env.cr.dbname  # noqa: F821
result["summary"] = summary
result["errors"] = errors

target = artifact_root() / f"finance_project_counterparty_position_audit_{env.cr.dbname}.json"  # noqa: F821
target.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
if errors:
    raise SystemExit(1)
