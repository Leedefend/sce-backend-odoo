# -*- coding: utf-8 -*-
"""Audit handling forms can read company-contractor responsibility context."""

from __future__ import annotations

import json
import os
from collections import OrderedDict
from pathlib import Path
from types import SimpleNamespace


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


MODEL_PROBES = [
    {
        "model": "sc.payment.execution",
        "table": "sc_payment_execution",
        "match": "partner_id",
        "label": "付款执行按正式往来单位匹配责任余额",
    },
    {
        "model": "sc.expense.claim",
        "table": "sc_expense_claim",
        "name_field": "payee",
        "label": "费用/还款/保证金办理按收款人匹配责任余额",
    },
    {
        "model": "sc.tax.deduction.registration",
        "table": "sc_tax_deduction_registration",
        "name_field": "partner_name",
        "label": "扣款抵扣办理按历史往来单位匹配责任余额",
    },
    {
        "model": "sc.tax.deduction.registration",
        "table": "sc_tax_deduction_registration",
        "name_field": "deduction_unit_name",
        "label": "扣款抵扣办理按扣款单位匹配责任余额",
    },
    {
        "model": "sc.receipt.income",
        "table": "sc_receipt_income",
        "name_field": "legacy_partner_name",
        "label": "收款登记按历史往来单位匹配责任余额",
    },
]


errors = []
summary = OrderedDict()

summary["summary_without_partner_id"] = [
    list(row)
    for row in sql_rows(
        """
        SELECT responsibility_state,
               COUNT(*)::integer,
               COALESCE(SUM(arrival_unprocessed_amount), 0.0),
               COALESCE(SUM(self_funding_balance), 0.0)
          FROM sc_company_contractor_responsibility_summary
         WHERE partner_id IS NULL
         GROUP BY responsibility_state
         ORDER BY responsibility_state
        """
    )
]

probe_results = []
for probe in MODEL_PROBES:
    table = probe["table"]
    model = probe["model"]
    match_mode = probe.get("match") or "name"
    name_field = probe.get("name_field") or ""
    if match_mode == "partner_id":
        match_count = sql_one(
            f"""
            SELECT COUNT(*)::integer
              FROM {table} r
             WHERE r.project_id IS NOT NULL
               AND r.partner_id IS NOT NULL
               AND EXISTS (
                    SELECT 1
                      FROM sc_company_contractor_responsibility_summary s
                     WHERE s.project_id = r.project_id
                       AND s.partner_id = r.partner_id
               )
            """
        )
        sample_rows = sql_rows(
            f"""
            SELECT r.id,
                   s.id AS summary_id,
                   s.responsibility_state,
                   s.arrival_unprocessed_amount,
                   s.arrival_over_processed_amount,
                   s.self_funding_balance
              FROM {table} r
              JOIN sc_company_contractor_responsibility_summary s
                ON s.project_id = r.project_id
               AND s.partner_id = r.partner_id
             WHERE r.project_id IS NOT NULL
               AND r.partner_id IS NOT NULL
             ORDER BY r.id
             LIMIT 5
            """
        )
    else:
        match_count = sql_one(
            f"""
            SELECT COUNT(*)::integer
              FROM {table} r
             WHERE r.project_id IS NOT NULL
               AND r.partner_id IS NULL
               AND COALESCE(r.{name_field}, '') <> ''
               AND EXISTS (
                    SELECT 1
                      FROM sc_company_contractor_responsibility_summary s
                     WHERE s.project_id = r.project_id
                       AND s.partner_id IS NULL
                       AND s.partner_name = r.{name_field}
               )
            """
        )
        sample_rows = sql_rows(
            f"""
            SELECT r.id,
                   s.id AS summary_id,
                   s.responsibility_state,
                   s.arrival_unprocessed_amount,
                   s.arrival_over_processed_amount,
                   s.self_funding_balance
              FROM {table} r
              JOIN sc_company_contractor_responsibility_summary s
                ON s.project_id = r.project_id
               AND s.partner_id IS NULL
               AND s.partner_name = r.{name_field}
             WHERE r.project_id IS NOT NULL
               AND r.partner_id IS NULL
               AND COALESCE(r.{name_field}, '') <> ''
             ORDER BY r.id
             LIMIT 5
            """
        )
    checked = []
    for row in sample_rows:
        rec_id, summary_id, state, arrival_unprocessed, arrival_over_processed, self_funding = row
        rec = env[model].browse(rec_id)  # noqa: F821
        actual_summary = rec.company_contractor_responsibility_summary_id
        checked_row = OrderedDict(
            [
                ("record_id", rec_id),
                ("expected_summary_id", summary_id),
                ("actual_summary_id", actual_summary.id if actual_summary else False),
                ("expected_state", state),
                ("actual_state", rec.company_contractor_responsibility_state),
            ]
        )
        checked.append(checked_row)
        if not actual_summary or actual_summary.id != summary_id:
            errors.append({"key": f"{model}.{name_field}.summary", **checked_row})
        if rec.company_contractor_responsibility_state != state:
            errors.append({"key": f"{model}.{name_field}.state", **checked_row})
        if abs(float(rec.company_contractor_arrival_unprocessed_amount or 0.0) - float(arrival_unprocessed or 0.0)) > 0.01:
            errors.append({"key": f"{model}.{name_field}.arrival_unprocessed", **checked_row})
        if abs(float(rec.company_contractor_arrival_over_processed_amount or 0.0) - float(arrival_over_processed or 0.0)) > 0.01:
            errors.append({"key": f"{model}.{name_field}.arrival_over_processed", **checked_row})
        if abs(float(rec.company_contractor_self_funding_balance or 0.0) - float(self_funding or 0.0)) > 0.01:
            errors.append({"key": f"{model}.{name_field}.self_funding", **checked_row})
    probe_results.append(
        OrderedDict(
            [
                ("label", probe["label"]),
                ("model", model),
                ("match", match_mode),
                ("name_field", name_field),
                ("matched_rows", match_count),
                ("sample_checked", checked),
            ]
        )
    )

if not any(int(item["matched_rows"] or 0) > 0 for item in probe_results):
    errors.append({"key": "real_user_context_samples", "message": "no handling records matched name-only responsibility rows"})

summary["handling_context_probes"] = probe_results

PaymentExecution = env["sc.payment.execution"]  # noqa: F821
currency = env.company.currency_id  # noqa: F821
constraint_rows = []
payment_execution_sample = PaymentExecution.search(
    [
        ("company_contractor_responsibility_summary_id", "!=", False),
        ("company_contractor_responsibility_state", "=", "self_funding_open"),
    ],
    limit=1,
)
if payment_execution_sample:
    failures = payment_execution_sample._company_contractor_payment_responsibility_failures(
        payment_execution_sample.company_contractor_responsibility_summary_id,
        payment_execution_sample.paid_amount or 0.0,
    )
    constraint_rows.append(
        {
            "case": "self_funding_open_does_not_block_payment_execution",
            "record_id": payment_execution_sample.id,
            "failure_count": len(failures),
        }
    )
    if failures:
        errors.append({"key": "payment_execution.self_funding_open_should_not_block", "failures": [str(item) for item in failures]})
else:
    errors.append({"key": "payment_execution.self_funding_open_sample_missing"})

fake_over_processed = SimpleNamespace(
    currency_id=currency,
    arrival_over_processed_amount=100.0,
    arrival_unprocessed_amount=0.0,
)
over_processed_failures = PaymentExecution._company_contractor_payment_responsibility_failures(fake_over_processed, 1.0)
constraint_rows.append({"case": "over_processed_blocks_payment_execution", "failure_count": len(over_processed_failures)})
if not over_processed_failures:
    errors.append({"key": "payment_execution.over_processed_not_blocked"})

fake_available = SimpleNamespace(
    currency_id=currency,
    arrival_over_processed_amount=0.0,
    arrival_unprocessed_amount=50.0,
)
exceed_failures = PaymentExecution._company_contractor_payment_responsibility_failures(fake_available, 51.0)
within_failures = PaymentExecution._company_contractor_payment_responsibility_failures(fake_available, 50.0)
constraint_rows.append({"case": "amount_exceeding_arrival_balance_blocks", "failure_count": len(exceed_failures)})
constraint_rows.append({"case": "amount_within_arrival_balance_allows", "failure_count": len(within_failures)})
if not exceed_failures:
    errors.append({"key": "payment_execution.exceeding_arrival_balance_not_blocked"})
if within_failures:
    errors.append({"key": "payment_execution.within_arrival_balance_should_not_block", "failures": [str(item) for item in within_failures]})

summary["payment_execution_responsibility_constraints"] = constraint_rows

ExpenseClaim = env["sc.expense.claim"]  # noqa: F821
expense_constraint_rows = []
expense_self_funding_sample = ExpenseClaim.search(
    [
        ("business_category_id.code", "=", "finance.repayment.contractor_project"),
        ("company_contractor_responsibility_summary_id", "!=", False),
        ("company_contractor_responsibility_state", "=", "self_funding_open"),
    ],
    limit=1,
)
if expense_self_funding_sample:
    failures = expense_self_funding_sample._company_contractor_responsibility_balance_failures(
        expense_self_funding_sample.company_contractor_responsibility_summary_id,
        expense_self_funding_sample.approved_amount or expense_self_funding_sample.amount or 0.0,
        "本次扣款金额",
    )
    expense_constraint_rows.append(
        {
            "case": "self_funding_open_does_not_block_deduction_bill_balance_helper",
            "record_id": expense_self_funding_sample.id,
            "failure_count": len(failures),
        }
    )
    if failures:
        errors.append({"key": "expense_claim.self_funding_open_should_not_block", "failures": [str(item) for item in failures]})
else:
    errors.append({"key": "expense_claim.self_funding_open_sample_missing"})

expense_over_processed_failures = ExpenseClaim._company_contractor_responsibility_balance_failures(fake_over_processed, 1.0, "本次扣款金额")
expense_exceed_failures = ExpenseClaim._company_contractor_responsibility_balance_failures(fake_available, 51.0, "本次扣款金额")
expense_within_failures = ExpenseClaim._company_contractor_responsibility_balance_failures(fake_available, 50.0, "本次扣款金额")
expense_constraint_rows.append({"case": "over_processed_blocks_deduction_bill", "failure_count": len(expense_over_processed_failures)})
expense_constraint_rows.append({"case": "deduction_amount_exceeding_arrival_balance_blocks", "failure_count": len(expense_exceed_failures)})
expense_constraint_rows.append({"case": "deduction_amount_within_arrival_balance_allows", "failure_count": len(expense_within_failures)})
if not expense_over_processed_failures:
    errors.append({"key": "expense_claim.over_processed_not_blocked"})
if not expense_exceed_failures:
    errors.append({"key": "expense_claim.exceeding_arrival_balance_not_blocked"})
if expense_within_failures:
    errors.append({"key": "expense_claim.within_arrival_balance_should_not_block", "failures": [str(item) for item in expense_within_failures]})

summary["expense_claim_deduction_responsibility_constraints"] = expense_constraint_rows

result = OrderedDict()
result["status"] = "PASS" if not errors else "FAIL"
result["database"] = env.cr.dbname  # noqa: F821
result["summary"] = summary
result["errors"] = errors

target = artifact_root() / f"company_contractor_responsibility_context_audit_{env.cr.dbname}.json"  # noqa: F821
target.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
if errors:
    raise SystemExit(1)
