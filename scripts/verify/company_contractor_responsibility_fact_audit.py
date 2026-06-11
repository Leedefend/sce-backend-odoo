# -*- coding: utf-8 -*-
"""Audit company-contractor responsibility facts against canonical finance facts."""

from __future__ import annotations

import json
import os
from collections import OrderedDict
from pathlib import Path


def artifact_root() -> Path:
    raw = os.getenv("MIGRATION_ARTIFACT_ROOT") or os.getenv("COMPANY_CONTRACTOR_RESPONSIBILITY_ARTIFACT_ROOT")
    candidates = [Path(raw)] if raw else []
    candidates.extend([Path("/mnt/artifacts/backend"), Path(f"/tmp/company_contractor_responsibility/{env.cr.dbname}")])  # noqa: F821
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


SOURCE_WHERE = """
    WHERE business_domain IN ('arrival_settlement', 'self_funding')
      AND fact_type IN ('arrival_gross', 'self_funding_income', 'self_funding_refund')
      AND balance_policy = 'canonical'
"""

TYPE_MAP = OrderedDict(
    [
        ("arrival_confirmation", "arrival_gross"),
        ("self_funding_income", "self_funding_income"),
        ("self_funding_refund", "self_funding_refund"),
    ]
)


errors = []
summary = OrderedDict()

expected_total = sql_one(f"SELECT COUNT(*)::integer FROM sc_finance_business_fact {SOURCE_WHERE}")
actual_total = sql_one("SELECT COUNT(*)::integer FROM sc_company_contractor_responsibility_fact")
assert_equal(errors, "responsibility_row_count", expected_total, actual_total)

type_rows = []
for responsibility_type, fact_type in TYPE_MAP.items():
    expected = sql_rows(
        """
        SELECT
            COUNT(*)::integer,
            COALESCE(SUM(amount), 0.0),
            COALESCE(SUM(CASE WHEN fact_type = 'arrival_gross' THEN amount ELSE 0.0 END), 0.0),
            COALESCE(SUM(CASE WHEN fact_type = 'arrival_gross' THEN paid_amount ELSE 0.0 END), 0.0),
            COALESCE(SUM(CASE WHEN fact_type = 'arrival_gross' THEN deduction_amount ELSE 0.0 END), 0.0),
            COALESCE(SUM(CASE WHEN fact_type = 'self_funding_income' THEN amount ELSE 0.0 END), 0.0),
            COALESCE(SUM(CASE WHEN fact_type = 'self_funding_refund' THEN amount ELSE 0.0 END), 0.0)
          FROM sc_finance_business_fact
         WHERE fact_type = %s
           AND balance_policy = 'canonical'
        """,
        [fact_type],
    )[0]
    actual = sql_rows(
        """
        SELECT
            COUNT(*)::integer,
            COALESCE(SUM(amount), 0.0),
            COALESCE(SUM(arrival_amount), 0.0),
            COALESCE(SUM(paid_amount), 0.0),
            COALESCE(SUM(deducted_amount), 0.0),
            COALESCE(SUM(self_funding_income_amount), 0.0),
            COALESCE(SUM(self_funding_refund_amount), 0.0)
          FROM sc_company_contractor_responsibility_fact
         WHERE responsibility_type = %s
        """,
        [responsibility_type],
    )[0]
    assert_equal(errors, f"{responsibility_type}_count", expected[0], actual[0])
    for idx, metric in enumerate(
        [
            "amount",
            "arrival_amount",
            "paid_amount",
            "deducted_amount",
            "self_funding_income_amount",
            "self_funding_refund_amount",
        ],
        start=1,
    ):
        assert_amount_close(errors, f"{responsibility_type}_{metric}", expected[idx], actual[idx])
    type_rows.append(
        OrderedDict(
            [
                ("responsibility_type", responsibility_type),
                ("source_fact_type", fact_type),
                ("expected", list(expected)),
                ("actual", list(actual)),
            ]
        )
    )

visible_reference_count = sql_one(
    """
    SELECT COUNT(*)::integer
      FROM sc_company_contractor_responsibility_fact
     WHERE source_fact_id IN (
            SELECT id FROM sc_finance_business_fact WHERE balance_policy = 'visible_reference'
          )
    """
)
assert_equal(errors, "visible_reference_rows_included", 0, visible_reference_count)

source_family_rows = OrderedDict()
source_family_specs = [
    (
        "legacy_arrival_confirmation",
        "sc.legacy.fund.confirmation.document",
        "arrival_confirmation",
        """
        SELECT COUNT(*)::integer
          FROM sc_legacy_fund_confirmation_document
         WHERE active IS TRUE
        """,
    ),
    (
        "legacy_self_funding_income",
        "sc.legacy.self.funding.fact",
        "self_funding_income",
        """
        SELECT COUNT(*)::integer
          FROM sc_legacy_self_funding_fact
         WHERE active IS TRUE
           AND line_type = 'income'
        """,
    ),
    (
        "legacy_self_funding_refund",
        "sc.legacy.self.funding.fact",
        "self_funding_refund",
        """
        SELECT COUNT(*)::integer
          FROM sc_legacy_self_funding_fact
         WHERE active IS TRUE
           AND line_type = 'refund'
        """,
    ),
    (
        "formal_self_funding_income",
        "sc.self.funding.registration",
        "self_funding_income",
        """
        SELECT COUNT(*)::integer
          FROM sc_self_funding_registration
         WHERE active IS TRUE
           AND source_origin = 'manual'
           AND state = 'done'
           AND funding_type = 'income'
        """,
    ),
    (
        "formal_self_funding_refund",
        "sc.self.funding.registration",
        "self_funding_refund",
        """
        SELECT COUNT(*)::integer
          FROM sc_self_funding_registration
         WHERE active IS TRUE
           AND source_origin = 'manual'
           AND state = 'done'
           AND funding_type = 'refund'
        """,
    ),
]
for key, source_model, responsibility_type, source_sql in source_family_specs:
    expected = sql_one(source_sql)
    actual = sql_one(
        """
        SELECT COUNT(*)::integer
          FROM sc_company_contractor_responsibility_fact
         WHERE source_model = %s
           AND responsibility_type = %s
        """,
        [source_model, responsibility_type],
    )
    assert_equal(errors, f"{key}_coverage", expected, actual)
    source_family_rows[key] = OrderedDict(
        [
            ("source_model", source_model),
            ("responsibility_type", responsibility_type),
            ("expected", expected),
            ("actual", actual),
        ]
    )

fund_daily_or_balance_leak = sql_one(
    """
    SELECT COUNT(*)::integer
      FROM sc_company_contractor_responsibility_fact r
      JOIN sc_fund_account_operation op
        ON r.source_model = 'sc.fund.account.operation'
       AND r.source_res_id = op.id
     WHERE op.operation_type IN ('fund_daily_report', 'balance_adjustment')
    """
)
assert_equal(errors, "fund_daily_or_balance_adjustment_responsibility_leak", 0, fund_daily_or_balance_leak)

duplicate_sources = sql_rows(
    """
    SELECT source_model, source_res_id, responsibility_type, COUNT(*)::integer
      FROM sc_company_contractor_responsibility_fact
     GROUP BY source_model, source_res_id, responsibility_type
    HAVING COUNT(*) > 1
     LIMIT 20
    """
)
if duplicate_sources:
    errors.append({"key": "duplicate_source_responsibility_rows", "samples": [list(row) for row in duplicate_sources]})

source_fact_mismatch = sql_rows(
    """
    SELECT r.id, r.source_fact_id, r.responsibility_type, f.fact_type
      FROM sc_company_contractor_responsibility_fact r
      LEFT JOIN sc_finance_business_fact f ON f.id = r.source_fact_id
     WHERE f.id IS NULL
        OR (r.responsibility_type = 'arrival_confirmation' AND f.fact_type != 'arrival_gross')
        OR (r.responsibility_type = 'self_funding_income' AND f.fact_type != 'self_funding_income')
        OR (r.responsibility_type = 'self_funding_refund' AND f.fact_type != 'self_funding_refund')
     LIMIT 20
    """
)
if source_fact_mismatch:
    errors.append({"key": "source_fact_mismatch", "samples": [list(row) for row in source_fact_mismatch]})

identity_quality = OrderedDict(
    [
        ("project_linked", sql_one("SELECT COUNT(*)::integer FROM sc_company_contractor_responsibility_fact WHERE project_id IS NOT NULL")),
        ("partner_id_linked", sql_one("SELECT COUNT(*)::integer FROM sc_company_contractor_responsibility_fact WHERE partner_id IS NOT NULL")),
        (
            "partner_name_present",
            sql_one("SELECT COUNT(*)::integer FROM sc_company_contractor_responsibility_fact WHERE NULLIF(partner_name, '') IS NOT NULL"),
        ),
        (
            "arrival_project_linked",
            sql_one("SELECT COUNT(*)::integer FROM sc_company_contractor_responsibility_fact WHERE responsibility_type = 'arrival_confirmation' AND project_id IS NOT NULL"),
        ),
        (
            "self_funding_partner_linked",
            sql_one("SELECT COUNT(*)::integer FROM sc_company_contractor_responsibility_fact WHERE responsibility_type IN ('self_funding_income', 'self_funding_refund') AND partner_id IS NOT NULL"),
        ),
    ]
)

effect_totals = sql_rows(
    """
    SELECT
        COALESCE(SUM(project_fund_status_effect), 0.0),
        COALESCE(SUM(contractor_responsibility_effect), 0.0),
        COALESCE(SUM(self_funding_balance_effect), 0.0)
      FROM sc_company_contractor_responsibility_fact
    """
)[0]

expected_effect_totals = sql_rows(
    """
    SELECT
        COALESCE(SUM(CASE WHEN fact_type = 'arrival_gross' THEN amount ELSE 0.0 END), 0.0),
        COALESCE(SUM(
            CASE
                WHEN fact_type = 'arrival_gross' THEN COALESCE(paid_amount, 0.0) + COALESCE(deduction_amount, 0.0)
                WHEN fact_type = 'self_funding_income' THEN amount
                WHEN fact_type = 'self_funding_refund' THEN -amount
                ELSE 0.0
            END
        ), 0.0),
        COALESCE(SUM(
            CASE
                WHEN fact_type = 'self_funding_income' THEN amount
                WHEN fact_type = 'self_funding_refund' THEN -amount
                ELSE 0.0
            END
        ), 0.0)
      FROM sc_finance_business_fact
    """
    + SOURCE_WHERE
)[0]
for idx, metric in enumerate(["project_fund_status_effect", "contractor_responsibility_effect", "self_funding_balance_effect"]):
    assert_amount_close(errors, metric, expected_effect_totals[idx], effect_totals[idx])

summary["row_count"] = OrderedDict([("expected", expected_total), ("actual", actual_total)])
summary["type_rows"] = type_rows
summary["identity_quality"] = identity_quality
summary["effect_totals"] = OrderedDict(
    [
        ("expected", list(expected_effect_totals)),
        ("actual", list(effect_totals)),
    ]
)
summary["visible_reference_rows_included"] = visible_reference_count
summary["source_family_rows"] = source_family_rows
summary["fund_daily_or_balance_adjustment_responsibility_leak"] = fund_daily_or_balance_leak

result = OrderedDict()
result["status"] = "PASS" if not errors else "FAIL"
result["database"] = env.cr.dbname  # noqa: F821
result["summary"] = summary
result["errors"] = errors

target = artifact_root() / f"company_contractor_responsibility_fact_audit_{env.cr.dbname}.json"  # noqa: F821
target.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
if errors:
    raise SystemExit(1)
