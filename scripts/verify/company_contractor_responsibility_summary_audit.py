# -*- coding: utf-8 -*-
"""Audit company-contractor responsibility summary against responsibility facts."""

from __future__ import annotations

import json
import os
from collections import OrderedDict
from pathlib import Path

from odoo.addons.smart_core.handlers.api_data import ApiDataHandler


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


GROUPED_SQL = """
    WITH grouped AS (
        SELECT
            project_id,
            partner_id,
            partner_name,
            COUNT(*)::integer AS source_line_count,
            COUNT(*) FILTER (WHERE responsibility_type = 'arrival_confirmation')::integer AS arrival_line_count,
            COUNT(*) FILTER (WHERE responsibility_type = 'self_funding_income')::integer AS self_funding_income_line_count,
            COUNT(*) FILTER (WHERE responsibility_type = 'self_funding_refund')::integer AS self_funding_refund_line_count,
            COALESCE(SUM(arrival_amount), 0.0) AS arrival_amount,
            COALESCE(SUM(paid_amount), 0.0) AS paid_amount,
            COALESCE(SUM(deducted_amount), 0.0) AS deducted_amount,
            COALESCE(SUM(paid_amount + deducted_amount), 0.0) AS arrival_processed_amount,
            COALESCE(SUM(arrival_amount - paid_amount - deducted_amount), 0.0) AS arrival_unprocessed_amount,
            GREATEST(-COALESCE(SUM(arrival_amount - paid_amount - deducted_amount), 0.0), 0.0) AS arrival_over_processed_amount,
            COALESCE(SUM(self_funding_income_amount), 0.0) AS self_funding_income_amount,
            COALESCE(SUM(self_funding_refund_amount), 0.0) AS self_funding_refund_amount,
            COALESCE(SUM(self_funding_balance_effect), 0.0) AS self_funding_balance,
            COALESCE(SUM(project_fund_status_effect), 0.0) AS project_fund_status_effect,
            COALESCE(SUM(contractor_responsibility_effect), 0.0) AS contractor_responsibility_effect,
            CASE
                WHEN COALESCE(SUM(arrival_amount - paid_amount - deducted_amount), 0.0) < -0.01 THEN 'over_processed'
                WHEN COALESCE(SUM(arrival_amount - paid_amount - deducted_amount), 0.0) > 0.01 THEN 'open'
                WHEN COALESCE(SUM(self_funding_balance_effect), 0.0) > 0.01 THEN 'self_funding_open'
                ELSE 'settled'
            END AS responsibility_state
        FROM sc_company_contractor_responsibility_fact
        GROUP BY project_id, partner_id, partner_name
    )
"""


errors = []
summary = OrderedDict()

expected_row_count = sql_one(GROUPED_SQL + " SELECT COUNT(*)::integer FROM grouped")
actual_row_count = sql_one("SELECT COUNT(*)::integer FROM sc_company_contractor_responsibility_summary")
assert_equal(errors, "summary_row_count", expected_row_count, actual_row_count)

metric_names = [
    "source_line_count",
    "arrival_line_count",
    "self_funding_income_line_count",
    "self_funding_refund_line_count",
    "arrival_amount",
    "paid_amount",
    "deducted_amount",
    "arrival_processed_amount",
    "arrival_unprocessed_amount",
    "arrival_over_processed_amount",
    "self_funding_income_amount",
    "self_funding_refund_amount",
    "self_funding_balance",
    "project_fund_status_effect",
    "contractor_responsibility_effect",
]

expected_totals = sql_rows(
    GROUPED_SQL
    + """
    SELECT
        COALESCE(SUM(source_line_count), 0)::integer,
        COALESCE(SUM(arrival_line_count), 0)::integer,
        COALESCE(SUM(self_funding_income_line_count), 0)::integer,
        COALESCE(SUM(self_funding_refund_line_count), 0)::integer,
        COALESCE(SUM(arrival_amount), 0.0),
        COALESCE(SUM(paid_amount), 0.0),
        COALESCE(SUM(deducted_amount), 0.0),
        COALESCE(SUM(arrival_processed_amount), 0.0),
        COALESCE(SUM(arrival_unprocessed_amount), 0.0),
        COALESCE(SUM(arrival_over_processed_amount), 0.0),
        COALESCE(SUM(self_funding_income_amount), 0.0),
        COALESCE(SUM(self_funding_refund_amount), 0.0),
        COALESCE(SUM(self_funding_balance), 0.0),
        COALESCE(SUM(project_fund_status_effect), 0.0),
        COALESCE(SUM(contractor_responsibility_effect), 0.0)
      FROM grouped
    """
)[0]
actual_totals = sql_rows(
    """
    SELECT
        COALESCE(SUM(source_line_count), 0)::integer,
        COALESCE(SUM(arrival_line_count), 0)::integer,
        COALESCE(SUM(self_funding_income_line_count), 0)::integer,
        COALESCE(SUM(self_funding_refund_line_count), 0)::integer,
        COALESCE(SUM(arrival_amount), 0.0),
        COALESCE(SUM(paid_amount), 0.0),
        COALESCE(SUM(deducted_amount), 0.0),
        COALESCE(SUM(arrival_processed_amount), 0.0),
        COALESCE(SUM(arrival_unprocessed_amount), 0.0),
        COALESCE(SUM(arrival_over_processed_amount), 0.0),
        COALESCE(SUM(self_funding_income_amount), 0.0),
        COALESCE(SUM(self_funding_refund_amount), 0.0),
        COALESCE(SUM(self_funding_balance), 0.0),
        COALESCE(SUM(project_fund_status_effect), 0.0),
        COALESCE(SUM(contractor_responsibility_effect), 0.0)
      FROM sc_company_contractor_responsibility_summary
    """
)[0]
for idx, metric in enumerate(metric_names):
    if idx < 4:
        assert_equal(errors, metric, expected_totals[idx], actual_totals[idx])
    else:
        assert_amount_close(errors, metric, expected_totals[idx], actual_totals[idx])

expected_states = dict(sql_rows(GROUPED_SQL + " SELECT responsibility_state, COUNT(*)::integer FROM grouped GROUP BY responsibility_state"))
actual_states = dict(sql_rows("SELECT responsibility_state, COUNT(*)::integer FROM sc_company_contractor_responsibility_summary GROUP BY responsibility_state"))
if expected_states != actual_states:
    errors.append({"key": "state_counts", "expected": expected_states, "actual": actual_states})

view_columns = {
    row[0]
    for row in sql_rows(
        """
        SELECT column_name
          FROM information_schema.columns
         WHERE table_name = 'sc_company_contractor_responsibility_summary'
        """
    )
}
required_view_columns = {
    "id",
    "display_name",
    "company_id",
    "currency_id",
    "project_id",
    "partner_id",
    "partner_name",
    "responsibility_state",
    "arrival_unprocessed_amount",
    "arrival_over_processed_amount",
    "self_funding_balance",
}
missing_view_columns = sorted(required_view_columns - view_columns)
if missing_view_columns:
    errors.append({"key": "view_columns", "missing": missing_view_columns})

action = env.ref("smart_construction_core.action_sc_company_contractor_responsibility_summary", raise_if_not_found=False)  # noqa: F821
if not action or action.res_model != "sc.company.contractor.responsibility.summary":
    errors.append(
        {
            "key": "menu_action",
            "expected": "sc.company.contractor.responsibility.summary",
            "actual": action.res_model if action else None,
        }
    )

api_fields = [
    "id",
    "responsibility_state",
    "project_id",
    "partner_name",
    "currency_id",
    "source_line_count",
    "arrival_amount",
    "paid_amount",
    "deducted_amount",
    "arrival_processed_amount",
    "arrival_unprocessed_amount",
    "arrival_over_processed_amount",
    "self_funding_income_amount",
    "self_funding_refund_amount",
    "self_funding_balance",
]
api_result = ApiDataHandler(env).handle(  # noqa: F821
    params={
        "op": "list",
        "model": "sc.company.contractor.responsibility.summary",
        "fields": api_fields,
        "limit": 20,
        "offset": 0,
        "order": "project_id, partner_name",
        "group_by": "responsibility_state",
        "need_total": True,
        "need_aggregates": True,
        "need_group_total": True,
    }
)
api_data = api_result[0] if isinstance(api_result, tuple) else api_result
api_meta = api_result[1] if isinstance(api_result, tuple) and len(api_result) > 1 else {}
if not isinstance(api_data, dict) or "records" not in api_data:
    errors.append({"key": "api_data_list", "result": api_result})
else:
    if int(api_data.get("total") or 0) != int(actual_row_count or 0):
        errors.append({"key": "api_data_total", "expected": actual_row_count, "actual": api_data.get("total")})
    if not isinstance(api_data.get("group_summary"), list):
        errors.append({"key": "api_data_group_summary", "actual": type(api_data.get("group_summary")).__name__})
    if not isinstance(api_data.get("aggregates"), dict):
        errors.append({"key": "api_data_aggregates", "actual": type(api_data.get("aggregates")).__name__})

state_amounts = [
    list(row)
    for row in sql_rows(
        """
        SELECT responsibility_state,
               COUNT(*)::integer,
               COALESCE(SUM(arrival_unprocessed_amount), 0.0),
               COALESCE(SUM(arrival_over_processed_amount), 0.0),
               COALESCE(SUM(self_funding_balance), 0.0)
          FROM sc_company_contractor_responsibility_summary
         GROUP BY responsibility_state
         ORDER BY responsibility_state
        """
    )
]

top_open_rows = [
    list(row)
    for row in sql_rows(
        """
        SELECT project_id, partner_name, responsibility_state, source_line_count,
               arrival_unprocessed_amount, arrival_over_processed_amount, self_funding_balance
          FROM sc_company_contractor_responsibility_summary
         ORDER BY ABS(arrival_unprocessed_amount) DESC, ABS(self_funding_balance) DESC
         LIMIT 20
        """
    )
]

summary["row_count"] = OrderedDict([("expected", expected_row_count), ("actual", actual_row_count)])
summary["expected_totals"] = dict(zip(metric_names, expected_totals))
summary["actual_totals"] = dict(zip(metric_names, actual_totals))
summary["state_counts"] = actual_states
summary["state_amounts"] = state_amounts
summary["top_open_rows"] = top_open_rows
summary["view_columns_checked"] = sorted(required_view_columns)
summary["api_data_entry"] = OrderedDict(
    [
        ("records", len(api_data.get("records") or []) if isinstance(api_data, dict) else None),
        ("total", api_data.get("total") if isinstance(api_data, dict) else None),
        ("group_summary", len(api_data.get("group_summary") or []) if isinstance(api_data, dict) else None),
        ("aggregates", sorted((api_data.get("aggregates") or {}).keys()) if isinstance(api_data, dict) else []),
        ("meta_model", api_meta.get("model") if isinstance(api_meta, dict) else None),
    ]
)

result = OrderedDict()
result["status"] = "PASS" if not errors else "FAIL"
result["database"] = env.cr.dbname  # noqa: F821
result["summary"] = summary
result["errors"] = errors

target = artifact_root() / f"company_contractor_responsibility_summary_audit_{env.cr.dbname}.json"  # noqa: F821
target.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
if errors:
    raise SystemExit(1)
