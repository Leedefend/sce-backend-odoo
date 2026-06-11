# -*- coding: utf-8 -*-
"""Verify formal self-funding handling closes responsibility and ledger boundaries."""

from __future__ import annotations

import json
import sys
import traceback
from collections import OrderedDict

from odoo.exceptions import UserError  # noqa: F401


def fail(message, **payload):
    raise AssertionError(json.dumps({"message": message, **payload}, ensure_ascii=False, sort_keys=True, default=str))


def main():
    Registration = env["sc.self.funding.registration"].sudo()  # noqa: F821
    Ledger = env["sc.treasury.ledger"].sudo()  # noqa: F821
    Fact = env["sc.finance.business.fact"].sudo()  # noqa: F821
    Summary = env["sc.company.contractor.responsibility.summary"].sudo()  # noqa: F821
    Category = env["sc.business.category"].sudo()  # noqa: F821

    project = env["project.project"].sudo().search([("active", "=", True), ("company_id", "!=", False)], limit=1)  # noqa: F821
    partner = env["res.partner"].sudo().search([("name", "!=", False)], limit=1)  # noqa: F821
    if not project or not partner:
        fail("missing project or partner sample", project=project.id, partner=partner.id)

    old = Registration.search([("summary", "ilike", "[self-funding-audit]")])
    if old:
        old.with_context(allow_done_self_funding_write=True).write({"active": False})
        Ledger.search([("source_model", "=", "sc.self.funding.registration"), ("source_res_id", "in", old.ids)]).write(
            {"state": "void"}
        )

    income_category = Category.search(
        [("code", "=", "finance.self_funding.income"), ("target_model", "=", "sc.self.funding.registration")],
        limit=1,
    )
    refund_category = Category.search(
        [("code", "=", "finance.self_funding.refund"), ("target_model", "=", "sc.self.funding.registration")],
        limit=1,
    )
    if not income_category or not refund_category:
        fail("self funding business categories missing")

    income_action = env.ref("smart_construction_core.action_sc_self_funding_registration_income", raise_if_not_found=False)  # noqa: F821
    refund_action = env.ref("smart_construction_core.action_sc_self_funding_registration_refund", raise_if_not_found=False)  # noqa: F821
    if not income_action or not refund_action:
        fail("self funding actions missing")

    income = Registration.create(
        {
            "funding_type": "income",
            "project_id": project.id,
            "partner_id": partner.id,
            "document_date": "2026-06-12",
            "amount": 1234.56,
            "summary": "[self-funding-audit] income",
        }
    )
    income.action_confirm()
    income.action_done()
    env.flush_all()  # noqa: F821

    income_fact = Fact.search(
        [("source_model", "=", income._name), ("source_res_id", "=", income.id), ("fact_type", "=", "self_funding_income")],
        limit=1,
    )
    if not income_fact or income_fact.balance_policy != "canonical":
        fail("income fact missing", income_id=income.id)
    income_ledger = Ledger.search(
        [("source_model", "=", income._name), ("source_res_id", "=", income.id), ("source_kind", "=", "self_funding")],
        limit=1,
    )
    if not income_ledger or income_ledger.direction != "in" or income_ledger.payment_request_id:
        fail("income ledger invalid", income_id=income.id, ledger_id=income_ledger.id if income_ledger else False)

    income_summary = Summary.search([("project_id", "=", project.id), ("partner_id", "=", partner.id)], limit=1)
    if not income_summary or income_summary.self_funding_balance < 1234.55:
        fail("summary did not include income", summary_id=income_summary.id if income_summary else False)

    refund = Registration.create(
        {
            "funding_type": "refund",
            "project_id": project.id,
            "partner_id": partner.id,
            "document_date": "2026-06-12",
            "amount": 234.56,
            "summary": "[self-funding-audit] refund",
        }
    )
    refund.action_confirm()
    refund.action_done()
    env.flush_all()  # noqa: F821

    refund_fact = Fact.search(
        [("source_model", "=", refund._name), ("source_res_id", "=", refund.id), ("fact_type", "=", "self_funding_refund")],
        limit=1,
    )
    if not refund_fact or refund_fact.balance_effect >= 0:
        fail("refund fact missing", refund_id=refund.id)
    refund_ledger = Ledger.search(
        [("source_model", "=", refund._name), ("source_res_id", "=", refund.id), ("source_kind", "=", "self_funding")],
        limit=1,
    )
    if not refund_ledger or refund_ledger.direction != "out" or refund_ledger.payment_request_id:
        fail("refund ledger invalid", refund_id=refund.id, ledger_id=refund_ledger.id if refund_ledger else False)

    summary_after = Summary.search([("project_id", "=", project.id), ("partner_id", "=", partner.id)], limit=1)
    if not summary_after or summary_after.self_funding_balance < 999.99:
        fail("summary did not subtract refund", summary_id=summary_after.id if summary_after else False)

    blocked = Registration.create(
        {
            "funding_type": "refund",
            "project_id": project.id,
            "partner_id": partner.id,
            "document_date": "2026-06-12",
            "amount": summary_after.self_funding_balance + 1000000.0,
            "summary": "[self-funding-audit] over refund blocked",
        }
    )
    try:
        blocked.action_done()
    except UserError as exc:
        blocked_ok = "超过自筹未退余额" in str(exc)
    else:
        blocked_ok = False
    if not blocked_ok:
        fail("over refund was not blocked", blocked_id=blocked.id)
    blocked.write({"active": False})

    env.cr.commit()  # noqa: F821
    result = OrderedDict(
        [
            ("status", "PASS"),
            ("project_id", project.id),
            ("partner_id", partner.id),
            ("income_id", income.id),
            ("refund_id", refund.id),
            ("income_fact_id", income_fact.id),
            ("refund_fact_id", refund_fact.id),
            ("income_ledger_id", income_ledger.id),
            ("refund_ledger_id", refund_ledger.id),
            ("payment_request_links", 0),
            ("self_funding_balance_after", summary_after.self_funding_balance),
        ]
    )
    print("SELF_FUNDING_HANDLING_AUDIT: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True, default=str))
    return 0


try:
    sys.exit(main())
except Exception as err:
    env.cr.rollback()  # noqa: F821
    print(
        "SELF_FUNDING_HANDLING_AUDIT: %s"
        % json.dumps(
            {
                "status": "FAIL",
                "error": str(err),
                "traceback": traceback.format_exc(),
            },
            ensure_ascii=False,
            sort_keys=True,
            default=str,
        )
    )
    sys.exit(1)
