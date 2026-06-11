# -*- coding: utf-8 -*-
"""Audit user accepted finance/account data against the interfund boundary.

Run inside Odoo shell:
    DB_NAME=sc_demo bash scripts/ops/odoo_shell_exec.sh < scripts/verify/interfund_user_data_full_coverage_audit.py
"""

from __future__ import annotations

import json
import os
from collections import OrderedDict
from pathlib import Path


def artifact_root() -> Path:
    raw = os.getenv("MIGRATION_ARTIFACT_ROOT") or os.getenv("INTERFUND_USER_DATA_ARTIFACT_ROOT")
    candidates = [Path(raw)] if raw else []
    candidates.extend([Path("/mnt/artifacts/backend"), Path(f"/tmp/interfund_user_data/{env.cr.dbname}")])  # noqa: F821
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


def row_count(query, params=None) -> int:
    return int(sql_one(query, params) or 0)


def amount(query, params=None) -> float:
    return float(sql_one(query, params) or 0.0)


def assert_equal(errors, key, expected, actual, details=None):
    if int(expected or 0) != int(actual or 0):
        errors.append({"key": key, "expected": expected, "actual": actual, "details": details or {}})


def assert_amount_close(errors, key, expected, actual, tolerance=0.01, details=None):
    if abs(float(expected or 0.0) - float(actual or 0.0)) > tolerance:
        errors.append({"key": key, "expected": expected, "actual": actual, "details": details or {}})


errors = []
warnings = []
coverage = OrderedDict()

fund_operation = OrderedDict(
    sql_rows(
        """
        SELECT operation_type, COUNT(*)::integer
          FROM sc_fund_account_operation
         WHERE active IS TRUE
         GROUP BY operation_type
         ORDER BY operation_type
        """
    )
)
fund_operation_amount = OrderedDict(
    sql_rows(
        """
        SELECT operation_type, COALESCE(SUM(amount), 0.0)
          FROM sc_fund_account_operation
         WHERE active IS TRUE
         GROUP BY operation_type
         ORDER BY operation_type
        """
    )
)

interfund_source = OrderedDict(
    sql_rows(
        """
        SELECT source_model, COUNT(*)::integer
          FROM sc_interfund_movement_fact
         GROUP BY source_model
         ORDER BY source_model
        """
    )
)
interfund_type = OrderedDict(
    sql_rows(
        """
        SELECT movement_type, COUNT(*)::integer
          FROM sc_interfund_movement_fact
         GROUP BY movement_type
         ORDER BY movement_type
        """
    )
)
interfund_type_amount = OrderedDict(
    sql_rows(
        """
        SELECT movement_type, COALESCE(SUM(amount), 0.0)
          FROM sc_interfund_movement_fact
         GROUP BY movement_type
         ORDER BY movement_type
        """
    )
)

financing_borrow_count = row_count(
    """
    SELECT COUNT(*)
      FROM sc_financing_loan
     WHERE active IS TRUE
       AND loan_type = 'borrowing_request'
       AND direction = 'borrowed_fund'
    """
)
financing_borrow_amount = amount(
    """
    SELECT COALESCE(SUM(amount), 0.0)
      FROM sc_financing_loan
     WHERE active IS TRUE
       AND loan_type = 'borrowing_request'
       AND direction = 'borrowed_fund'
    """
)
financing_registration_count = row_count(
    """
    SELECT COUNT(*)
      FROM sc_financing_loan
     WHERE active IS TRUE
       AND loan_type = 'loan_registration'
       AND direction = 'financing_in'
    """
)
financing_registration_amount = amount(
    """
    SELECT COALESCE(SUM(amount), 0.0)
      FROM sc_financing_loan
     WHERE active IS TRUE
       AND loan_type = 'loan_registration'
       AND direction = 'financing_in'
    """
)

expense_repay_count = row_count(
    """
    SELECT COUNT(*)
      FROM sc_expense_claim
     WHERE active IS TRUE
       AND (
            claim_type = 'project_company_repay'
         OR (expense_type = '承包人还项目款' AND claim_type IN ('expense', 'deposit_receive'))
       )
    """
)
expense_repay_amount = amount(
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

finance_fact_source = OrderedDict(
    sql_rows(
        """
        SELECT source_model || ':' || fact_type, COUNT(*)::integer
          FROM sc_finance_business_fact
         GROUP BY source_model, fact_type
         ORDER BY source_model, fact_type
        """
    )
)

self_funding_source = OrderedDict(
    sql_rows(
        """
        SELECT line_type, COUNT(*)::integer
          FROM sc_legacy_self_funding_fact
         WHERE active IS TRUE
         GROUP BY line_type
         ORDER BY line_type
        """
    )
)

account_transaction = OrderedDict(
    sql_rows(
        """
        SELECT metric_bucket || ':' || direction, COUNT(*)::integer
          FROM sc_legacy_account_transaction_line
         WHERE active IS TRUE
         GROUP BY metric_bucket, direction
         ORDER BY metric_bucket, direction
        """
    )
)

account_transaction_amount = OrderedDict(
    sql_rows(
        """
        SELECT metric_bucket || ':' || direction, COALESCE(SUM(amount), 0.0)
          FROM sc_legacy_account_transaction_line
         WHERE active IS TRUE
         GROUP BY metric_bucket, direction
         ORDER BY metric_bucket, direction
        """
    )
)

fund_daily_source_count = int(fund_operation.get("fund_daily_report") or 0)
fund_daily_summary_source = row_count(
    """
    SELECT COUNT(*)
      FROM sc_legacy_fund_daily_snapshot_fact
     WHERE document_scope = 'enterprise'
       AND business_entity_id IS NOT NULL
    """
)
fund_daily_line_count = row_count("SELECT COUNT(*) FROM sc_legacy_fund_daily_line WHERE active IS TRUE")
fund_daily_summary_line_count = row_count("SELECT COALESCE(SUM(line_count), 0)::integer FROM sc_fund_daily_summary")

arrival_source_count = row_count("SELECT COUNT(*) FROM sc_legacy_fund_confirmation_document WHERE active IS TRUE")
arrival_fact_count = int(finance_fact_source.get("sc.legacy.fund.confirmation.document:arrival_gross") or 0)

coverage["interfund_movement_facts"] = OrderedDict(
    [
        (
            "account_transfer",
            {
                "source": "sc.fund.account.operation / operation_type=transfer_between",
                "source_count": int(fund_operation.get("transfer_between") or 0),
                "source_amount": float(fund_operation_amount.get("transfer_between") or 0.0),
                "projection_count": int(interfund_source.get("sc.fund.account.operation") or 0),
                "boundary": "纳入往来款：账户/项目之间发生资金调拨事实",
            },
        ),
        (
            "financing_borrow",
            {
                "source": "sc.financing.loan / borrowing_request + borrowed_fund",
                "source_count": financing_borrow_count,
                "source_amount": financing_borrow_amount,
                "projection_count": int(interfund_source.get("sc.financing.loan") or 0),
                "boundary": "纳入往来款：项目借公司款、承包人借项目款均形成应收应还关系",
            },
        ),
        (
            "expense_repayment",
            {
                "source": "sc.expense.claim / project_company_repay or 承包人还项目款",
                "source_count": expense_repay_count,
                "source_amount": expense_repay_amount,
                "projection_count": int(interfund_source.get("sc.expense.claim") or 0),
                "boundary": "纳入往来款：项目还公司款、承包人还项目款均为往来清偿事实",
            },
        ),
    ]
)

coverage["not_interfund_by_design"] = OrderedDict(
    [
        (
            "fund_daily_report",
            {
                "source": "sc.fund.account.operation / operation_type=fund_daily_report",
                "source_count": fund_daily_source_count,
                "summary_source_count": fund_daily_summary_source,
                "summary_line_count": fund_daily_summary_line_count,
                "boundary": "不纳入往来款：资金日报是用户日报型台账/余额快照，后续资金台账口径以此承接",
            },
        ),
        (
            "balance_adjustment",
            {
                "source": "sc.fund.account.operation / operation_type=balance_adjustment",
                "source_count": int(fund_operation.get("balance_adjustment") or 0),
                "source_amount": float(fund_operation_amount.get("balance_adjustment") or 0.0),
                "boundary": "不纳入往来款：余额校准不直接产生对方应收应还关系",
            },
        ),
        (
            "arrival_confirmation",
            {
                "source": "sc.legacy.fund.confirmation.document",
                "source_count": arrival_source_count,
                "finance_fact_count": arrival_fact_count,
                "boundary": "不直接纳入往来款：到款确认属于工程款到账清算事实",
            },
        ),
        (
            "self_funding_visible",
            {
                "source": "sc.legacy.self.funding.fact / visible families",
                "income_visible_count": int(self_funding_source.get("income_visible") or 0),
                "refund_visible_count": int(self_funding_source.get("refund_visible") or 0),
                "finance_visible_count": int(
                    finance_fact_source.get("sc.legacy.self.funding.fact:self_funding_visible_reference") or 0
                ),
                "boundary": "不直接纳入往来款：自筹垫资/退回先作为财务事实和余额权益口径治理",
            },
        ),
        (
            "financing_registration",
            {
                "source": "sc.financing.loan / loan_registration + financing_in",
                "source_count": financing_registration_count,
                "source_amount": financing_registration_amount,
                "boundary": "不纳入当前往来款：融资贷款登记属于融资债务能力域，应独立闭环",
            },
        ),
        (
            "account_transaction_lines",
            {
                "source": "sc.legacy.account.transaction.line",
                "line_counts": account_transaction,
                "line_amounts": account_transaction_amount,
                "fund_daily_line_count": fund_daily_line_count,
                "boundary": "不直接纳入往来款：账户明细承接账户收支/日报台账，避免和正式调拨单重复计算",
            },
        ),
    ]
)

classification_evidence = OrderedDict(
    [
        ("movement_type_counts", interfund_type),
        ("movement_type_amounts", interfund_type_amount),
        (
            "loan_text_classifier",
            OrderedDict(
                [
                    (
                        "project_to_contractor_borrow",
                        int(interfund_type.get("project_to_contractor_borrow") or 0),
                    ),
                    (
                        "company_to_project_borrow",
                        int(interfund_type.get("company_to_project_borrow") or 0),
                    ),
                    (
                        "legacy_user_confirmed_contractor_borrow_menu_count",
                        227,
                    ),
                    (
                        "note",
                        "旧系统未统一往来款概念；当前按借...项目...款顺序文本识别承包人借项目款，差异必须沉淀为可维护分类字典后再作为新验收基线。",
                    ),
                ]
            ),
        ),
    ]
)

assert_equal(
    errors,
    "account_transfer_interfund_coverage",
    fund_operation.get("transfer_between") or 0,
    interfund_source.get("sc.fund.account.operation") or 0,
)
assert_equal(
    errors,
    "financing_borrow_interfund_coverage",
    financing_borrow_count,
    interfund_source.get("sc.financing.loan") or 0,
)
assert_equal(
    errors,
    "expense_repay_interfund_coverage",
    expense_repay_count,
    interfund_source.get("sc.expense.claim") or 0,
)
assert_amount_close(
    errors,
    "account_transfer_interfund_amount",
    fund_operation_amount.get("transfer_between") or 0.0,
    sql_one("SELECT COALESCE(SUM(amount), 0.0) FROM sc_interfund_movement_fact WHERE source_model='sc.fund.account.operation'"),
)
assert_amount_close(
    errors,
    "financing_borrow_interfund_amount",
    financing_borrow_amount,
    sql_one("SELECT COALESCE(SUM(amount), 0.0) FROM sc_interfund_movement_fact WHERE source_model='sc.financing.loan'"),
)
assert_amount_close(
    errors,
    "expense_repay_interfund_amount",
    expense_repay_amount,
    sql_one("SELECT COALESCE(SUM(amount), 0.0) FROM sc_interfund_movement_fact WHERE source_model='sc.expense.claim'"),
)

daily_or_balance_leak = row_count(
    """
    SELECT COUNT(*)
      FROM sc_interfund_movement_fact f
      JOIN sc_fund_account_operation op
        ON f.source_model = 'sc.fund.account.operation'
       AND f.source_res_id = op.id
     WHERE op.operation_type IN ('fund_daily_report', 'balance_adjustment')
    """
)
assert_equal(errors, "fund_daily_or_balance_adjustment_leak", 0, daily_or_balance_leak)

assert_equal(errors, "arrival_confirmation_finance_fact_coverage", arrival_source_count, arrival_fact_count)
assert_equal(
    errors,
    "self_funding_visible_reference_coverage",
    (self_funding_source.get("income_visible") or 0) + (self_funding_source.get("refund_visible") or 0),
    finance_fact_source.get("sc.legacy.self.funding.fact:self_funding_visible_reference") or 0,
)
assert_equal(errors, "fund_daily_user_report_baseline", 7453, fund_daily_source_count)
assert_equal(errors, "account_transfer_user_report_baseline", 395, fund_operation.get("transfer_between") or 0)
assert_equal(errors, "arrival_user_report_baseline", 5205, arrival_source_count)
assert_equal(errors, "self_funding_income_visible_user_report_baseline", 2144, self_funding_source.get("income_visible") or 0)
assert_equal(errors, "self_funding_refund_visible_user_report_baseline", 827, self_funding_source.get("refund_visible") or 0)

if int(interfund_type.get("project_to_contractor_borrow") or 0) != 227:
    warnings.append(
        {
            "key": "contractor_borrow_menu_baseline_requires_new_dictionary_confirmation",
            "legacy_user_confirmed_count": 227,
            "current_fact_classifier_count": int(interfund_type.get("project_to_contractor_borrow") or 0),
            "policy": "不能按旧菜单名直接收口；需基于用户数据文本和可维护业务分类字典确认新验收口径。",
        }
    )

summary = OrderedDict(
    [
        ("db", env.cr.dbname),  # noqa: F821
        ("status", "FAIL" if errors else "PASS"),
        ("policy", "旧系统没有统一往来款概念；往来款按业务事实识别，用户入口名称只作为认知保留和追溯证据。"),
        ("coverage", coverage),
        ("classification_evidence", classification_evidence),
        ("warnings", warnings),
        ("errors", errors),
    ]
)

out = artifact_root() / f"interfund_user_data_full_coverage_audit_{env.cr.dbname}.json"
out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

print(json.dumps(summary, ensure_ascii=False))
print(f"INTERFUND_USER_DATA_FULL_COVERAGE_AUDIT_RESULT: {summary['status']} output={out}")
if errors:
    raise SystemExit(1)
