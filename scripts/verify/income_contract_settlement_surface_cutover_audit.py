# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import re

from odoo.osv import expression
from odoo.tools.safe_eval import safe_eval


SOURCE_MODEL = "construction.contract.income:settlement_surface"
TITLE_TERMS = ("结算", "报告", "审核")
BASE_EXECUTION_SOURCE_DOMAIN = [
    "|",
    ("legacy_income_surface_visible", "=", True),
    "&",
    ("state", "in", ["confirmed", "running"]),
    ("legacy_contract_id", "=", False),
]


def _text(value) -> str:
    cleaned = str(value or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    if cleaned in {"False", "false", "None", "none"}:
        return ""
    return cleaned


def _money(value) -> str:
    raw = _text(value).replace(",", "").replace("￥", "").replace("¥", "")
    match = re.search(r"-?\d+(?:\.\d+)?", raw)
    if not match:
        return "0"
    return ("%.2f" % float(match.group(0))).rstrip("0").rstrip(".")


def _title_domain() -> list:
    return expression.OR([[("legacy_visible_title", "ilike", term)] for term in TITLE_TERMS])


def _execution_domain_without_settlement_titles() -> list:
    action = env.ref("smart_construction_core.action_construction_contract_income_execution")  # noqa: F821
    return action.domain


def main():
    Income = env["construction.contract.income"].sudo().with_context(active_test=False)  # noqa: F821
    Settlement = env["sc.settlement.order"].sudo().with_context(active_test=False)  # noqa: F821

    source = Income.search(expression.AND([BASE_EXECUTION_SOURCE_DOMAIN, _title_domain()]), order="legacy_visible_document_no,id")
    settlement_by_income_id = {
        settlement.legacy_fact_id: settlement
        for settlement in Settlement.search([("legacy_fact_model", "=", SOURCE_MODEL), ("legacy_fact_id", "in", source.ids)])
    }
    stale_settlement_count = Settlement.search_count(
        [("legacy_fact_model", "=", SOURCE_MODEL), ("legacy_fact_id", "not in", source.ids)]
    )
    execution_action = env.ref("smart_construction_core.action_construction_contract_income_execution")  # noqa: F821
    execution_remaining = Income.search_count(expression.AND([safe_eval(execution_action.domain or "[]"), _title_domain()]))

    missing = []
    mismatches = []
    for income in source:
        settlement = settlement_by_income_id.get(income.id)
        if not settlement:
            missing.append({"income_id": income.id, "document_no": _text(income.legacy_visible_document_no)})
            continue
        expected_amount = _money(income.legacy_visible_settlement_amount) or _money(income.legacy_visible_amount)
        actual_amount = _money(settlement.approved_amount)
        checks = {
            "title": (_text(income.legacy_visible_title), _text(settlement.title)),
            "project": (income.project_id.id if income.project_id else False, settlement.project_id.id if settlement.project_id else False),
            "contract": (income.contract_id.id if income.contract_id else False, settlement.contract_id.id if settlement.contract_id else False),
            "amount": (expected_amount, actual_amount),
            "attachment": (_text(income.legacy_visible_attachment), _text(settlement.legacy_visible_attachment)),
        }
        for field, (expected, actual) in checks.items():
            if expected != actual:
                mismatches.append(
                    {
                        "income_id": income.id,
                        "settlement_id": settlement.id,
                        "field": field,
                        "expected": expected,
                        "actual": actual,
                    }
                )

    result = {
        "status": "PASS"
        if len(source) == 36
        and len(settlement_by_income_id) == len(source)
        and not missing
        and not mismatches
        and execution_remaining == 0
        and stale_settlement_count == 0
        else "FAIL",
        "db": env.cr.dbname,  # noqa: F821
        "terms": TITLE_TERMS,
        "source_count": len(source),
        "settlement_count": len(settlement_by_income_id),
        "stale_settlement_count": stale_settlement_count,
        "execution_remaining_with_settlement_title": execution_remaining,
        "execution_action_domain": _execution_domain_without_settlement_titles(),
        "missing": missing[:20],
        "mismatches": mismatches[:20],
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    if result["status"] != "PASS":
        raise AssertionError(result)


main()
