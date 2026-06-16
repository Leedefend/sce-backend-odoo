# -*- coding: utf-8 -*-
"""Audit the normalized finance business fact projection.

Run inside Odoo shell:
    DB_NAME=sc_demo bash scripts/ops/odoo_shell_exec.sh < scripts/verify/finance_business_fact_projection_audit.py
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


def named(keys, query, params=None):
    env.cr.execute(query, params or [])  # noqa: F821
    row = env.cr.fetchone() or []  # noqa: F821
    return OrderedDict(zip(keys, row))


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

source_counts = OrderedDict()
source_counts["arrival_settlement"] = sql_one(
    "SELECT COUNT(*)::integer FROM sc_legacy_fund_confirmation_document WHERE active IS TRUE"
)
source_counts["deduction_paid"] = sql_one(
    """
    SELECT COUNT(*)::integer
      FROM sc_expense_claim
     WHERE active IS TRUE
       AND legacy_source_model = 'online_old_scbs:T_KK_SJDJB:list897'
    """
)
source_counts["deduction_refund"] = sql_one(
    """
    SELECT COUNT(*)::integer
      FROM sc_expense_claim
     WHERE active IS TRUE
       AND legacy_source_model = 'online_old_scbs:T_KK_SJTHB:list898'
    """
)
source_counts["tax_deduction"] = sql_one(
    "SELECT COUNT(*)::integer FROM sc_tax_deduction_registration WHERE active IS TRUE"
)
source_counts["legacy_self_funding"] = sql_one(
    """
    SELECT COUNT(*)::integer
      FROM sc_legacy_self_funding_fact
     WHERE active IS TRUE
       AND COALESCE(deleted_flag, '0') IN ('0', '')
    """
)
source_counts["formal_self_funding"] = sql_one(
    """
    SELECT COUNT(*)::integer
      FROM sc_self_funding_registration
     WHERE active IS TRUE
       AND state = 'done'
    """
)
source_counts["self_funding"] = source_counts["legacy_self_funding"] + source_counts["formal_self_funding"]
source_counts["guarantee_deposit"] = sql_one("SELECT COUNT(*)::integer FROM tender_guarantee")
source_counts["total"] = sum(
    int(source_counts[key] or 0)
    for key in [
        "arrival_settlement",
        "deduction_paid",
        "deduction_refund",
        "tax_deduction",
        "self_funding",
        "guarantee_deposit",
    ]
)

projection_counts = OrderedDict(
    sql_rows(
        """
        SELECT business_domain, COUNT(*)::integer
          FROM sc_finance_business_fact
         GROUP BY business_domain
         ORDER BY business_domain
        """
    )
)
projection_counts["total"] = sql_one("SELECT COUNT(*)::integer FROM sc_finance_business_fact")

assert_equal(errors, "arrival_settlement_count", source_counts["arrival_settlement"], projection_counts.get("arrival_settlement"))
assert_equal(errors, "deduction_clearing_count", source_counts["deduction_paid"] + source_counts["deduction_refund"], projection_counts.get("deduction_clearing"))
assert_equal(errors, "tax_deduction_count", source_counts["tax_deduction"], projection_counts.get("tax_deduction"))
assert_equal(errors, "self_funding_count", source_counts["self_funding"], projection_counts.get("self_funding"))
assert_equal(errors, "guarantee_deposit_count", source_counts["guarantee_deposit"], projection_counts.get("guarantee_deposit"))
assert_equal(errors, "total_count", source_counts["total"], projection_counts.get("total"))

source_amounts = OrderedDict()
source_amounts["arrival_amount"] = sql_one(
    "SELECT COALESCE(SUM(actual_fund_amount), 0.0) FROM sc_legacy_fund_confirmation_document WHERE active IS TRUE"
)
source_amounts["arrival_deduction"] = sql_one(
    "SELECT COALESCE(SUM(deducted_amount_total), 0.0) FROM sc_legacy_fund_confirmation_document WHERE active IS TRUE"
)
source_amounts["arrival_paid"] = sql_one(
    "SELECT COALESCE(SUM(paid_amount_total), 0.0) FROM sc_legacy_fund_confirmation_document WHERE active IS TRUE"
)
source_amounts["deduction_paid"] = sql_one(
    """
    SELECT COALESCE(SUM(COALESCE(NULLIF(approved_amount, 0.0), amount, 0.0)), 0.0)
      FROM sc_expense_claim
     WHERE active IS TRUE
       AND legacy_source_model = 'online_old_scbs:T_KK_SJDJB:list897'
    """
)
source_amounts["deduction_refund"] = sql_one(
    """
    SELECT COALESCE(SUM(COALESCE(NULLIF(approved_amount, 0.0), amount, 0.0)), 0.0)
      FROM sc_expense_claim
     WHERE active IS TRUE
       AND legacy_source_model = 'online_old_scbs:T_KK_SJTHB:list898'
    """
)
source_amounts["tax_deduction_amount"] = sql_one(
    "SELECT COALESCE(SUM(deduction_amount), 0.0) FROM sc_tax_deduction_registration WHERE active IS TRUE"
)
source_amounts["tax_amount"] = sql_one(
    "SELECT COALESCE(SUM(deduction_tax_amount), 0.0) FROM sc_tax_deduction_registration WHERE active IS TRUE"
)
source_amounts["legacy_self_funding_canonical_balance"] = sql_one(
    """
    SELECT COALESCE(SUM(
        CASE
            WHEN line_type = 'income' THEN self_funding_amount
            WHEN line_type = 'refund' THEN -refund_amount
            ELSE 0.0
        END
    ), 0.0)
      FROM sc_legacy_self_funding_fact
     WHERE active IS TRUE
       AND COALESCE(deleted_flag, '0') IN ('0', '')
    """
)
source_amounts["formal_self_funding_canonical_balance"] = sql_one(
    """
    SELECT COALESCE(SUM(
        CASE
            WHEN funding_type = 'refund' THEN -amount
            ELSE amount
        END
    ), 0.0)
      FROM sc_self_funding_registration
     WHERE active IS TRUE
       AND state = 'done'
    """
)
source_amounts["self_funding_canonical_balance"] = (
    source_amounts["legacy_self_funding_canonical_balance"]
    + source_amounts["formal_self_funding_canonical_balance"]
)
source_amounts["guarantee_balance"] = sql_one(
    "SELECT COALESCE(SUM(CASE WHEN type = 'return' THEN -amount ELSE amount END), 0.0) FROM tender_guarantee"
)

projection_amounts = OrderedDict()
projection_amounts["arrival_amount"] = sql_one(
    """
    SELECT COALESCE(SUM(amount), 0.0)
      FROM sc_finance_business_fact
     WHERE fact_type = 'arrival_gross'
    """
)
projection_amounts["arrival_deduction"] = sql_one(
    """
    SELECT COALESCE(SUM(deduction_amount), 0.0)
      FROM sc_finance_business_fact
     WHERE fact_type = 'arrival_gross'
    """
)
projection_amounts["arrival_paid"] = sql_one(
    """
    SELECT COALESCE(SUM(paid_amount), 0.0)
      FROM sc_finance_business_fact
     WHERE fact_type = 'arrival_gross'
    """
)
projection_amounts["deduction_paid"] = sql_one(
    """
    SELECT COALESCE(SUM(amount), 0.0)
      FROM sc_finance_business_fact
     WHERE fact_type = 'deduction_paid'
    """
)
projection_amounts["deduction_refund"] = sql_one(
    """
    SELECT COALESCE(SUM(amount), 0.0)
      FROM sc_finance_business_fact
     WHERE fact_type = 'deduction_refund'
    """
)
projection_amounts["tax_deduction_amount"] = sql_one(
    """
    SELECT COALESCE(SUM(amount), 0.0)
      FROM sc_finance_business_fact
     WHERE fact_type = 'tax_deducted'
    """
)
projection_amounts["tax_amount"] = sql_one(
    """
    SELECT COALESCE(SUM(tax_amount), 0.0)
      FROM sc_finance_business_fact
     WHERE fact_type = 'tax_deducted'
    """
)
projection_amounts["tax_balance_effect"] = sql_one(
    """
    SELECT COALESCE(SUM(balance_effect), 0.0)
      FROM sc_finance_business_fact
     WHERE fact_type = 'tax_deducted'
    """
)
projection_amounts["self_funding_canonical_balance"] = sql_one(
    """
    SELECT COALESCE(SUM(balance_effect), 0.0)
      FROM sc_finance_business_fact
     WHERE business_domain = 'self_funding'
       AND balance_policy = 'canonical'
    """
)
projection_amounts["self_funding_visible_balance"] = sql_one(
    """
    SELECT COALESCE(SUM(balance_effect), 0.0)
      FROM sc_finance_business_fact
     WHERE business_domain = 'self_funding'
       AND balance_policy = 'visible_reference'
    """
)
projection_amounts["guarantee_balance"] = sql_one(
    """
    SELECT COALESCE(SUM(balance_effect), 0.0)
      FROM sc_finance_business_fact
     WHERE business_domain = 'guarantee_deposit'
    """
)

for key in [
    "arrival_amount",
    "arrival_deduction",
    "arrival_paid",
    "deduction_paid",
    "deduction_refund",
    "tax_deduction_amount",
    "tax_amount",
    "self_funding_canonical_balance",
    "guarantee_balance",
]:
    assert_amount_close(errors, key, source_amounts[key], projection_amounts[key])

assert_amount_close(errors, "tax_balance_effect_zero", 0.0, projection_amounts["tax_balance_effect"])
assert_amount_close(errors, "self_funding_visible_balance_zero", 0.0, projection_amounts["self_funding_visible_balance"])

duplicate_sources = table(
    sql_rows(
        """
        SELECT source_model, source_res_id, fact_type, COUNT(*)::integer
          FROM sc_finance_business_fact
         GROUP BY source_model, source_res_id, fact_type
        HAVING COUNT(*) > 1
         ORDER BY COUNT(*) DESC, source_model, source_res_id
         LIMIT 20
        """
    )
)
if duplicate_sources:
    errors.append({"key": "duplicate_source_fact_type", "samples": duplicate_sources})

summary["source_counts"] = source_counts
summary["projection_counts"] = projection_counts
summary["source_amounts"] = source_amounts
summary["projection_amounts"] = projection_amounts
summary["fact_type_counts"] = table(
    sql_rows(
        """
        SELECT fact_type, balance_policy, COUNT(*)::integer, COALESCE(SUM(amount), 0.0), COALESCE(SUM(balance_effect), 0.0)
          FROM sc_finance_business_fact
         GROUP BY fact_type, balance_policy
         ORDER BY fact_type, balance_policy
        """
    )
)
summary["source_model_counts"] = table(
    sql_rows(
        """
        SELECT source_model, COUNT(*)::integer
          FROM sc_finance_business_fact
         GROUP BY source_model
         ORDER BY source_model
        """
    )
)

result = OrderedDict()
result["status"] = "PASS" if not errors else "FAIL"
result["database"] = env.cr.dbname  # noqa: F821
result["summary"] = summary
result["errors"] = errors

target = artifact_root() / f"finance_business_fact_projection_audit_{env.cr.dbname}.json"  # noqa: F821
target.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
if errors:
    raise SystemExit(1)
