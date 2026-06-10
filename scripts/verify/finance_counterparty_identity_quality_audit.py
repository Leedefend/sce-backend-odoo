# -*- coding: utf-8 -*-
"""Audit counterparty identity quality for finance/interfund fact projections."""

from __future__ import annotations

import json
import os
from collections import OrderedDict
from pathlib import Path


ALLOWED_MISSING_FINANCE_FACT_TYPES = {
    "arrival_gross": "source fund confirmation has no construction unit",
    "deduction_paid": "deduction clearing may represent internal tax/fee allocation",
    "deduction_refund": "deduction refund may represent internal tax/fee allocation",
    "tax_deducted": "tax deduction may be a noncash tax fact",
    "self_funding_income": "legacy self-funding row has no stable counterparty",
    "self_funding_refund": "legacy self-funding row has no stable counterparty",
    "self_funding_visible_reference": "visible reference row is not a balance counterparty",
    "guarantee_out": "tender guarantee is tied to tender bid; some bids have no owner",
    "guarantee_return": "tender guarantee return is tied to tender bid; some bids have no owner",
}


def artifact_root() -> Path:
    raw = os.getenv("MIGRATION_ARTIFACT_ROOT") or os.getenv("FINANCE_COUNTERPARTY_IDENTITY_ARTIFACT_ROOT")
    candidates = [Path(raw)] if raw else []
    candidates.extend([Path("/mnt/artifacts/backend"), Path(f"/tmp/finance_counterparty_identity/{env.cr.dbname}")])  # noqa: F821
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


def assert_zero(errors, key, value):
    if int(value or 0) != 0:
        errors.append({"key": key, "expected": 0, "actual": value})


errors = []
summary = OrderedDict()

misleading_unknown_company = sql_one(
    """
    SELECT COUNT(*)::integer
      FROM sc_finance_project_counterparty_position
     WHERE counterparty_type = 'unknown'
       AND counterparty_name = '公司'
    """
)
assert_zero(errors, "misleading_unknown_company_count", misleading_unknown_company)
summary["misleading_unknown_company_count"] = misleading_unknown_company

unexpected_unknown_names = sql_rows(
    """
    SELECT counterparty_name, COUNT(*)::integer, COALESCE(SUM(source_line_count), 0)::integer, COALESCE(SUM(combined_balance_effect), 0.0)
      FROM sc_finance_project_counterparty_position
     WHERE counterparty_type = 'unknown'
       AND counterparty_name <> '未识别对象'
     GROUP BY counterparty_name
     ORDER BY COUNT(*) DESC
    """
)
if unexpected_unknown_names:
    errors.append(
        {
            "key": "unexpected_unknown_counterparty_names",
            "expected": [],
            "actual": [list(row) for row in unexpected_unknown_names],
        }
    )
summary["unexpected_unknown_names"] = [list(row) for row in unexpected_unknown_names]

interfund_not_perspectived = sql_one(
    """
    SELECT COUNT(*)::integer
      FROM sc_interfund_movement_fact f
     WHERE NOT (
            (target_project_id IS NOT NULL
             AND movement_type IN (
                    'company_to_project_borrow',
                    'company_to_project_transfer',
                    'project_to_project_transfer',
                    'contractor_to_project_repay'
                 ))
         OR (source_project_id IS NOT NULL
             AND movement_type IN (
                    'project_to_company_repay',
                    'project_to_company_transfer',
                    'project_to_project_transfer',
                    'project_to_contractor_borrow'
                 ))
         OR (COALESCE(source_project_id, target_project_id, project_id) IS NOT NULL
             AND movement_type IN ('same_project_account_transfer', 'unclassified_account_transfer'))
        )
    """
)
assert_zero(errors, "interfund_not_in_project_perspective_count", interfund_not_perspectived)
summary["interfund_not_in_project_perspective_count"] = interfund_not_perspectived

missing_finance_by_fact = sql_rows(
    """
    SELECT business_domain, fact_type, source_menu_hint, COUNT(*)::integer, COALESCE(SUM(balance_effect), 0.0)
      FROM sc_finance_business_fact
     WHERE partner_id IS NULL
       AND COALESCE(NULLIF(partner_name, ''), '') = ''
     GROUP BY business_domain, fact_type, source_menu_hint
     ORDER BY COUNT(*) DESC
    """
)
unexpected_missing_finance = [
    list(row)
    for row in missing_finance_by_fact
    if row[1] not in ALLOWED_MISSING_FINANCE_FACT_TYPES
]
if unexpected_missing_finance:
    errors.append(
        {
            "key": "unexpected_missing_finance_counterparty_fact_types",
            "expected_allowed_fact_types": sorted(ALLOWED_MISSING_FINANCE_FACT_TYPES),
            "actual": unexpected_missing_finance,
        }
    )
summary["missing_finance_counterparty_by_fact"] = [
    {
        "business_domain": row[0],
        "fact_type": row[1],
        "source_menu_hint": row[2],
        "count": row[3],
        "balance_effect": row[4],
        "reason": ALLOWED_MISSING_FINANCE_FACT_TYPES.get(row[1], "unexpected"),
    }
    for row in missing_finance_by_fact
]

contractor_unidentified = sql_rows(
    """
    SELECT
        COALESCE(SUM(CASE WHEN counterparty_name = '未识别承包人' THEN source_line_count ELSE 0 END), 0)::integer,
        COALESCE(SUM(CASE WHEN counterparty_name = '未识别承包人' THEN combined_balance_effect ELSE 0 END), 0.0)
      FROM sc_finance_project_counterparty_position
     WHERE counterparty_type = 'partner'
    """
)[0]
summary["unidentified_contractor"] = OrderedDict(
    [
        ("source_line_count", contractor_unidentified[0]),
        ("combined_balance_effect", contractor_unidentified[1]),
        ("classification", "partner/未识别承包人"),
    ]
)

position_type_counts = sql_rows(
    """
    SELECT counterparty_type, COUNT(*)::integer, COALESCE(SUM(source_line_count), 0)::integer, COALESCE(SUM(combined_balance_effect), 0.0)
      FROM sc_finance_project_counterparty_position
     GROUP BY counterparty_type
     ORDER BY counterparty_type
    """
)
summary["project_counterparty_type_counts"] = [list(row) for row in position_type_counts]

summary_counts = sql_rows(
    """
    SELECT counterparty_type, COUNT(*)::integer, COALESCE(SUM(source_line_count), 0)::integer, COALESCE(SUM(combined_balance_effect), 0.0)
      FROM sc_finance_counterparty_position_summary
     GROUP BY counterparty_type
     ORDER BY counterparty_type
    """
)
summary["summary_counterparty_type_counts"] = [list(row) for row in summary_counts]

result = OrderedDict()
result["status"] = "PASS" if not errors else "FAIL"
result["database"] = env.cr.dbname  # noqa: F821
result["summary"] = summary
result["errors"] = errors

target = artifact_root() / f"finance_counterparty_identity_quality_audit_{env.cr.dbname}.json"  # noqa: F821
target.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
if errors:
    raise SystemExit(1)
