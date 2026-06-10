# -*- coding: utf-8 -*-
"""Audit the project-level interfund movement summary projection.

Run inside Odoo shell:
    DB_NAME=sc_demo bash scripts/ops/odoo_shell_exec.sh < scripts/verify/interfund_movement_project_summary_audit.py
"""

from __future__ import annotations

import json
import os
from collections import OrderedDict
from pathlib import Path


def artifact_root() -> Path:
    raw = os.getenv("MIGRATION_ARTIFACT_ROOT") or os.getenv("INTERFUND_MOVEMENT_ARTIFACT_ROOT")
    candidates = [Path(raw)] if raw else []
    candidates.extend([Path("/mnt/artifacts/backend"), Path(f"/tmp/interfund_movement/{env.cr.dbname}")])  # noqa: F821
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


PROJECT_PERSPECTIVE_SQL = """
    WITH project_perspective AS (
        SELECT
            f.target_project_id AS project_id,
            f.movement_type,
            f.classification_confidence,
            f.amount,
            f.amount AS inflow_amount,
            0.0 AS outflow_amount,
            f.amount AS net_amount,
            0.0 AS internal_transfer_amount
        FROM sc_interfund_movement_fact f
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
            f.movement_type,
            f.classification_confidence,
            f.amount,
            0.0 AS inflow_amount,
            f.amount AS outflow_amount,
            -f.amount AS net_amount,
            0.0 AS internal_transfer_amount
        FROM sc_interfund_movement_fact f
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
            f.movement_type,
            f.classification_confidence,
            f.amount,
            0.0 AS inflow_amount,
            0.0 AS outflow_amount,
            0.0 AS net_amount,
            f.amount AS internal_transfer_amount
        FROM sc_interfund_movement_fact f
        WHERE COALESCE(f.source_project_id, f.target_project_id, f.project_id) IS NOT NULL
          AND f.movement_type IN ('same_project_account_transfer', 'unclassified_account_transfer')
    )
"""


errors = []
summary = OrderedDict()

expected_group_count = sql_one(
    PROJECT_PERSPECTIVE_SQL
    + """
    SELECT COUNT(*)::integer
      FROM (
            SELECT project_id, movement_type
              FROM project_perspective
             GROUP BY project_id, movement_type
           ) g
    """
)
actual_group_count = sql_one("SELECT COUNT(*)::integer FROM sc_interfund_movement_project_summary")
assert_equal(errors, "project_summary_group_count", expected_group_count, actual_group_count)

expected_totals = OrderedDict(
    (row[0], row[1:])
    for row in sql_rows(
        PROJECT_PERSPECTIVE_SQL
        + """
        SELECT
            movement_type,
            COUNT(*)::integer,
            COALESCE(SUM(inflow_amount), 0.0),
            COALESCE(SUM(outflow_amount), 0.0),
            COALESCE(SUM(net_amount), 0.0),
            COALESCE(SUM(internal_transfer_amount), 0.0),
            COUNT(*) FILTER (WHERE classification_confidence = 'low')::integer
          FROM project_perspective
         GROUP BY movement_type
         ORDER BY movement_type
        """
    )
)
actual_totals = OrderedDict(
    (row[0], row[1:])
    for row in sql_rows(
        """
        SELECT
            movement_type,
            COALESCE(SUM(source_line_count), 0)::integer,
            COALESCE(SUM(inflow_amount), 0.0),
            COALESCE(SUM(outflow_amount), 0.0),
            COALESCE(SUM(net_amount), 0.0),
            COALESCE(SUM(internal_transfer_amount), 0.0),
            COALESCE(SUM(low_confidence_count), 0)::integer
          FROM sc_interfund_movement_project_summary
         GROUP BY movement_type
         ORDER BY movement_type
        """
    )
)

metric_names = ["count", "inflow_amount", "outflow_amount", "net_amount", "internal_transfer_amount", "low_confidence_count"]
for movement_type, expected_values in expected_totals.items():
    actual_values = actual_totals.get(movement_type)
    if not actual_values:
        errors.append({"key": "missing_summary_movement_type", "movement_type": movement_type})
        continue
    assert_equal(errors, f"{movement_type}.count", expected_values[0], actual_values[0])
    for idx, metric_name in enumerate(metric_names[1:5], start=1):
        assert_amount_close(errors, f"{movement_type}.{metric_name}", expected_values[idx], actual_values[idx])
    assert_equal(errors, f"{movement_type}.low_confidence_count", expected_values[5], actual_values[5])

project_transfer_net = sql_one(
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
assert_amount_close(errors, "project_to_project_transfer_global_net_zero", 0.0, project_transfer_net)
assert_amount_close(errors, "same_project_account_transfer_net_zero", 0.0, same_project_net)

summary["expected_group_count"] = expected_group_count
summary["actual_group_count"] = actual_group_count
summary["expected_totals"] = {key: dict(zip(metric_names, value)) for key, value in expected_totals.items()}
summary["actual_totals"] = {key: dict(zip(metric_names, value)) for key, value in actual_totals.items()}
summary["business_totals"] = OrderedDict(
    [
        ("project_to_project_transfer_global_net", project_transfer_net),
        ("same_project_account_transfer_net", same_project_net),
        (
            "project_net_total",
            sql_one("SELECT COALESCE(SUM(net_amount), 0.0) FROM sc_interfund_movement_project_summary"),
        ),
    ]
)
summary["top_project_net"] = table(
    sql_rows(
        """
        SELECT project_id, movement_type, source_line_count, inflow_amount, outflow_amount, net_amount
          FROM sc_interfund_movement_project_summary
         ORDER BY ABS(net_amount) DESC, source_line_count DESC
         LIMIT 20
        """
    )
)

result = OrderedDict()
result["status"] = "PASS" if not errors else "FAIL"
result["database"] = env.cr.dbname  # noqa: F821
result["summary"] = summary
result["errors"] = errors

target = artifact_root() / f"interfund_movement_project_summary_audit_{env.cr.dbname}.json"  # noqa: F821
target.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
if errors:
    raise SystemExit(1)
