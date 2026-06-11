# -*- coding: utf-8 -*-
"""Rollback-only audit for fund daily report handling.

Fund daily reports are state/ledger inputs: they must not become interfund
responsibility facts, but completed income/expense amounts must be traceable in
the unified treasury ledger for cashflow and reconciliation.
"""

import json
import sys
import traceback

from odoo import fields
from odoo.exceptions import UserError, ValidationError


def _token():
    return env["ir.sequence"].sudo().next_by_code("sc.business.fact") or str(fields.Datetime.now())  # noqa: F821


def _expect_exception(label, func, failures):
    try:
        with env.cr.savepoint():  # noqa: F821
            func()
    except (UserError, ValidationError):
        return True
    except Exception as err:
        failures.append("%s: expected business exception, got %s: %s" % (label, type(err).__name__, err))
        return False
    failures.append("%s: expected business exception, got success" % label)
    return False


def _project():
    return env["project.project"].sudo().create(  # noqa: F821
        {
            "name": "Fund Daily Audit Project %s" % _token(),
            "manager_id": env.user.id,  # noqa: F821
            "company_id": env.company.id,  # noqa: F821
        }
    )


def _account(project, name):
    return env["sc.fund.account"].sudo().create(  # noqa: F821
        {
            "name": "%s %s" % (name, _token()),
            "account_no": "FDA-%s" % _token(),
            "project_id": project.id,
            "company_id": env.company.id,  # noqa: F821
            "currency_id": env.company.currency_id.id,  # noqa: F821
            "state": "active",
        }
    )


def _ledger_rows(record, source_kind):
    rows = env["sc.treasury.ledger"].sudo().search(  # noqa: F821
        [
            ("source_model", "=", record._name),
            ("source_res_id", "=", record.id),
            ("source_kind", "=", source_kind),
            ("state", "!=", "void"),
        ],
        order="direction,id",
    )
    return rows


def _interfund_count(record):
    return env["sc.interfund.movement.fact"].sudo().search_count(  # noqa: F821
        [("source_model", "=", record._name), ("source_res_id", "=", record.id)]
    )


def _run_daily_report(failures):
    project = _project()
    account = _account(project, "Fund Daily Account")
    Operation = env["sc.fund.account.operation"].sudo()  # noqa: F821
    daily = Operation.create(
        {
            "operation_type": "fund_daily_report",
            "operation_date": fields.Date.context_today(Operation),
            "project_id": project.id,
            "fund_account_id": account.id,
            "company_id": env.company.id,  # noqa: F821
            "currency_id": env.company.currency_id.id,  # noqa: F821
            "daily_income": 120.0,
            "daily_expense": 45.0,
            "account_balance": 1000.0,
            "bank_balance": 1000.0,
            "operation_reason": "资金日报办理闭环审计",
        }
    )
    _expect_exception("fund_daily.done_before_confirm", daily.action_done, failures)
    daily.action_confirm()
    daily.action_done()
    daily.invalidate_recordset()
    ledgers = _ledger_rows(daily, "daily_line")
    by_direction = {ledger.direction: ledger for ledger in ledgers}
    if daily.state != "done":
        failures.append("fund_daily expected done, got %s" % daily.state)
    if len(ledgers) != 2:
        failures.append("fund_daily expected 2 daily_line ledgers, got %s" % len(ledgers))
    if not by_direction.get("in") or by_direction["in"].amount != 120.0:
        failures.append("fund_daily income ledger missing or amount mismatch")
    if not by_direction.get("out") or by_direction["out"].amount != 45.0:
        failures.append("fund_daily expense ledger missing or amount mismatch")
    if any(ledger.payment_request_id for ledger in ledgers):
        failures.append("fund_daily daily_line ledgers must not link payment_request")
    if _interfund_count(daily):
        failures.append("fund_daily must not create interfund movement fact")
    return {
        "operation_id": daily.id,
        "ledger_ids": ledgers.ids,
        "ledger_count": len(ledgers),
        "interfund_count": _interfund_count(daily),
    }


def _run_balance_adjustment(failures):
    project = _project()
    account = _account(project, "Balance Adjustment Account")
    Operation = env["sc.fund.account.operation"].sudo()  # noqa: F821
    adjustment = Operation.create(
        {
            "operation_type": "balance_adjustment",
            "operation_date": fields.Date.context_today(Operation),
            "project_id": project.id,
            "fund_account_id": account.id,
            "company_id": env.company.id,  # noqa: F821
            "currency_id": env.company.currency_id.id,  # noqa: F821
            "before_balance": 500.0,
            "after_balance": 520.0,
            "operation_reason": "余额调整办理闭环审计",
        }
    )
    adjustment.action_confirm()
    adjustment.action_done()
    ledgers = _ledger_rows(adjustment, "daily_line") | _ledger_rows(adjustment, "interfund")
    if ledgers:
        failures.append("balance_adjustment must not create cashflow ledger rows")
    if _interfund_count(adjustment):
        failures.append("balance_adjustment must not create interfund movement fact")
    return {
        "operation_id": adjustment.id,
        "ledger_count": len(ledgers),
        "interfund_count": _interfund_count(adjustment),
    }


failures = []
evidence = {}

try:
    evidence["daily_report"] = _run_daily_report(failures)
    evidence["balance_adjustment"] = _run_balance_adjustment(failures)
except Exception as err:
    failures.append("unexpected error: %s" % err)
    failures.append(traceback.format_exc())
finally:
    env.cr.rollback()  # noqa: F821

result = {
    "audit": "fund_daily_handling_audit",
    "status": "PASS" if not failures else "FAIL",
    "evidence": evidence,
    "failures": failures,
    "policy": {
        "fund_daily_report": "completed income/expense writes sc.treasury.ledger with source_kind=daily_line",
        "balance_adjustment": "account state adjustment only; no cashflow ledger and no interfund fact",
        "payment_request_policy": "not_applicable",
    },
}
print("FUND_DAILY_HANDLING_AUDIT: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True, default=str))
if failures:
    print("FAILURES:")
    for failure in failures:
        print("- %s" % failure)
sys.exit(0 if not failures else 1)
