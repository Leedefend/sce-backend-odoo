# -*- coding: utf-8 -*-
"""Audit the normalized interfund movement fact projection.

Run inside Odoo shell:
    DB_NAME=sc_demo bash scripts/ops/odoo_shell_exec.sh < scripts/verify/interfund_movement_fact_audit.py
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


def count(model_name, domain=None) -> int:
    return int(env[model_name].sudo().search_count(domain or []))  # noqa: F821


def amount_sum(model_name, domain=None, field_name="amount") -> float:
    Model = env[model_name].sudo()  # noqa: F821
    rows = Model.read_group(domain or [], [f"{field_name}:sum"], [])
    if not rows:
        return 0.0
    return float(rows[0].get(f"{field_name}_sum") or rows[0].get(field_name) or 0.0)


def sql_one(query, params=None):
    env.cr.execute(query, params or [])  # noqa: F821
    row = env.cr.fetchone()  # noqa: F821
    return row[0] if row else None


def sql_rows(query, params=None):
    env.cr.execute(query, params or [])  # noqa: F821
    return env.cr.fetchall()  # noqa: F821


def movement_count(movement_type: str) -> int:
    return count("sc.interfund.movement.fact", [("movement_type", "=", movement_type)])


def movement_amount(movement_type: str) -> float:
    return amount_sum("sc.interfund.movement.fact", [("movement_type", "=", movement_type)])


def assert_equal(errors, key, expected, actual):
    if expected != actual:
        errors.append({"key": key, "expected": expected, "actual": actual})


def assert_amount_close(errors, key, expected, actual, tolerance=0.01):
    if abs(float(expected or 0.0) - float(actual or 0.0)) > tolerance:
        errors.append({"key": key, "expected": expected, "actual": actual})


source_counts = OrderedDict()
source_amounts = OrderedDict()

source_counts["account_transfer_total"] = count(
    "sc.fund.account.operation",
    [("active", "=", True), ("operation_type", "=", "transfer_between")],
)
source_amounts["account_transfer_total"] = amount_sum(
    "sc.fund.account.operation",
    [("active", "=", True), ("operation_type", "=", "transfer_between")],
)

source_counts["financing_borrow_total"] = count(
    "sc.financing.loan",
    [("active", "=", True), ("loan_type", "=", "borrowing_request"), ("direction", "=", "borrowed_fund")],
)
source_amounts["financing_borrow_total"] = amount_sum(
    "sc.financing.loan",
    [("active", "=", True), ("loan_type", "=", "borrowing_request"), ("direction", "=", "borrowed_fund")],
)

source_counts["expense_repay_total"] = count(
    "sc.expense.claim",
    [
        ("active", "=", True),
        "|",
        ("claim_type", "=", "project_company_repay"),
        "&",
        ("expense_type", "=", "承包人还项目款"),
        ("claim_type", "in", ["expense", "deposit_receive"]),
    ],
)

env.cr.execute(  # noqa: F821
    """
    SELECT COALESCE(SUM(COALESCE(NULLIF(approved_amount, 0.0), amount, 0.0)), 0.0)
      FROM sc_expense_claim
     WHERE active IS TRUE
       AND (
            claim_type = 'project_company_repay'
         OR (expense_type = '承包人还项目款' AND claim_type IN ('expense', 'deposit_receive'))
       )
    """
)
source_amounts["expense_repay_total"] = float(env.cr.fetchone()[0] or 0.0)  # noqa: F821

source_counts["project_to_project_transfer"] = int(
    sql_one(
        """
        SELECT COUNT(*)
          FROM sc_fund_account_operation op
          JOIN sc_fund_account src ON src.id = op.source_account_id
          JOIN sc_fund_account dst ON dst.id = op.target_account_id
         WHERE op.active IS TRUE
           AND op.operation_type = 'transfer_between'
           AND src.project_id IS NOT NULL
           AND dst.project_id IS NOT NULL
           AND src.project_id <> dst.project_id
        """
    )
    or 0
)
source_amounts["project_to_project_transfer"] = float(
    sql_one(
        """
        SELECT COALESCE(SUM(op.amount), 0.0)
          FROM sc_fund_account_operation op
          JOIN sc_fund_account src ON src.id = op.source_account_id
          JOIN sc_fund_account dst ON dst.id = op.target_account_id
         WHERE op.active IS TRUE
           AND op.operation_type = 'transfer_between'
           AND src.project_id IS NOT NULL
           AND dst.project_id IS NOT NULL
           AND src.project_id <> dst.project_id
        """
    )
    or 0.0
)

source_counts["same_project_account_transfer"] = int(
    sql_one(
        """
        SELECT COUNT(*)
          FROM sc_fund_account_operation op
          JOIN sc_fund_account src ON src.id = op.source_account_id
          JOIN sc_fund_account dst ON dst.id = op.target_account_id
         WHERE op.active IS TRUE
           AND op.operation_type = 'transfer_between'
           AND src.project_id IS NOT NULL
           AND dst.project_id IS NOT NULL
           AND src.project_id = dst.project_id
        """
    )
    or 0
)

source_counts["project_company_repay_all"] = count(
    "sc.expense.claim",
    [("active", "=", True), ("claim_type", "=", "project_company_repay")],
)
source_counts["contractor_project_repay"] = count(
    "sc.expense.claim",
    [
        ("active", "=", True),
        ("expense_type", "=", "承包人还项目款"),
        ("claim_type", "in", ["expense", "deposit_receive"]),
    ],
)

projection_counts = OrderedDict()
projection_amounts = OrderedDict()
projection_counts["total"] = count("sc.interfund.movement.fact")
projection_amounts["total"] = amount_sum("sc.interfund.movement.fact")

for movement_type in [
    "company_to_project_borrow",
    "project_to_company_repay",
    "project_to_project_transfer",
    "same_project_account_transfer",
    "project_to_contractor_borrow",
    "contractor_to_project_repay",
    "project_to_company_transfer",
    "company_to_project_transfer",
    "unclassified_account_transfer",
]:
    projection_counts[movement_type] = movement_count(movement_type)
    projection_amounts[movement_type] = movement_amount(movement_type)

source_model_counts = OrderedDict(
    sql_rows(
        """
        SELECT source_model, COUNT(*)::integer
          FROM sc_interfund_movement_fact
         GROUP BY source_model
         ORDER BY source_model
        """
    )
)

confidence_counts = OrderedDict(
    sql_rows(
        """
        SELECT classification_confidence, COUNT(*)::integer
          FROM sc_interfund_movement_fact
         GROUP BY classification_confidence
         ORDER BY classification_confidence
        """
    )
)

errors = []
expected_total = (
    source_counts["account_transfer_total"]
    + source_counts["financing_borrow_total"]
    + source_counts["expense_repay_total"]
)
expected_amount_total = (
    source_amounts["account_transfer_total"]
    + source_amounts["financing_borrow_total"]
    + source_amounts["expense_repay_total"]
)

assert_equal(errors, "total_projection_count", expected_total, projection_counts["total"])
assert_amount_close(errors, "total_projection_amount", expected_amount_total, projection_amounts["total"])
assert_equal(
    errors,
    "source_model_sc_fund_account_operation_count",
    source_counts["account_transfer_total"],
    int(source_model_counts.get("sc.fund.account.operation") or 0),
)
assert_equal(
    errors,
    "source_model_sc_financing_loan_count",
    source_counts["financing_borrow_total"],
    int(source_model_counts.get("sc.financing.loan") or 0),
)
assert_equal(
    errors,
    "source_model_sc_expense_claim_count",
    source_counts["expense_repay_total"],
    int(source_model_counts.get("sc.expense.claim") or 0),
)
assert_equal(
    errors,
    "project_to_project_transfer_count",
    source_counts["project_to_project_transfer"],
    projection_counts["project_to_project_transfer"],
)
assert_amount_close(
    errors,
    "project_to_project_transfer_amount",
    source_amounts["project_to_project_transfer"],
    projection_amounts["project_to_project_transfer"],
)
assert_equal(
    errors,
    "same_project_account_transfer_count",
    source_counts["same_project_account_transfer"],
    projection_counts["same_project_account_transfer"],
)
assert_equal(
    errors,
    "project_company_repay_all_count",
    source_counts["project_company_repay_all"],
    projection_counts["project_to_company_repay"],
)
assert_equal(
    errors,
    "contractor_project_repay_count",
    source_counts["contractor_project_repay"],
    projection_counts["contractor_to_project_repay"],
)

daily_report_leak_count = int(
    sql_one(
        """
        SELECT COUNT(*)
          FROM sc_interfund_movement_fact f
          JOIN sc_fund_account_operation op
            ON f.source_model = 'sc.fund.account.operation'
           AND f.source_res_id = op.id
         WHERE op.operation_type <> 'transfer_between'
        """
    )
    or 0
)
if daily_report_leak_count:
    errors.append({"key": "daily_report_leak_count", "expected": 0, "actual": daily_report_leak_count})

duplicate_source_count = int(
    sql_one(
        """
        SELECT COUNT(*)
          FROM (
                SELECT source_model, source_res_id, COUNT(*) AS c
                  FROM sc_interfund_movement_fact
                 GROUP BY source_model, source_res_id
                HAVING COUNT(*) > 1
          ) dup
        """
    )
    or 0
)
if duplicate_source_count:
    errors.append({"key": "duplicate_source_count", "expected": 0, "actual": duplicate_source_count})

summary = OrderedDict(
    [
        ("db", env.cr.dbname),  # noqa: F821
        ("status", "FAIL" if errors else "PASS"),
        ("source_counts", source_counts),
        ("projection_counts", projection_counts),
        ("source_amounts", source_amounts),
        ("projection_amounts", projection_amounts),
        ("source_model_counts", source_model_counts),
        ("confidence_counts", confidence_counts),
        ("daily_report_leak_count", daily_report_leak_count),
        ("duplicate_source_count", duplicate_source_count),
        ("errors", errors),
    ]
)

out = artifact_root() / "interfund_movement_fact_audit_v1.json"
out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

print(json.dumps(summary, ensure_ascii=False))
print(f"INTERFUND_MOVEMENT_FACT_AUDIT_RESULT: {summary['status']} output={out}")
if errors:
    raise SystemExit(1)
