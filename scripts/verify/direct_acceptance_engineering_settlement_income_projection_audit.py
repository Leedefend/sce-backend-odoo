# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import re


SOURCE_MODEL = "sc.legacy.direct.acceptance.fact:direct_engineering_settlement_order"
ACCEPTANCE_LABEL = "工程结算单"


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


def main():
    Fact = env["sc.legacy.direct.acceptance.fact"].sudo().with_context(active_test=False)  # noqa: F821
    Settlement = env["sc.settlement.order"].sudo().with_context(active_test=False)  # noqa: F821

    source = Fact.search([("active", "=", True), ("acceptance_label", "=", ACCEPTANCE_LABEL)], order="document_no,id")
    settlement_by_fact_id = {
        settlement.legacy_fact_id: settlement
        for settlement in Settlement.search([("legacy_fact_model", "=", SOURCE_MODEL), ("legacy_fact_id", "in", source.ids)])
    }
    stale_count = Settlement.search_count([("legacy_fact_model", "=", SOURCE_MODEL), ("legacy_fact_id", "not in", source.ids)])
    income_action = env.ref("smart_construction_core.action_sc_settlement_order_income")  # noqa: F821

    missing = []
    mismatches = []
    for fact in source:
        settlement = settlement_by_fact_id.get(fact.id)
        if not settlement:
            missing.append({"fact_id": fact.id, "document_no": _text(fact.legacy_visible_02) or _text(fact.document_no)})
            continue
        checks = {
            "name": (_text(fact.legacy_visible_02) or _text(fact.document_no), _text(settlement.name)),
            "title": (_text(fact.legacy_visible_08) or _text(fact.document_title) or _text(fact.legacy_visible_02), _text(settlement.title)),
            "project": (True, bool(settlement.project_id)),
            "amount": (_money(fact.legacy_visible_07) or _money(fact.amount_total), _money(settlement.approved_amount)),
            "attachment": (_text(fact.legacy_visible_16) or _text(fact.attachment_ref), _text(settlement.legacy_visible_attachment)),
            "settlement_type": ("in", _text(settlement.settlement_type)),
        }
        for field, (expected, actual) in checks.items():
            if expected != actual:
                mismatches.append(
                    {
                        "fact_id": fact.id,
                        "settlement_id": settlement.id,
                        "field": field,
                        "expected": expected,
                        "actual": actual,
                    }
                )

    result = {
        "status": "PASS" if source and len(settlement_by_fact_id) == len(source) and not missing and not mismatches and stale_count == 0 else "FAIL",
        "db": env.cr.dbname,  # noqa: F821
        "acceptance_label": ACCEPTANCE_LABEL,
        "source_count": len(source),
        "settlement_count": len(settlement_by_fact_id),
        "stale_settlement_count": stale_count,
        "income_action_domain": income_action.domain,
        "missing": missing[:20],
        "mismatches": mismatches[:20],
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    if result["status"] != "PASS":
        raise AssertionError(result)


main()
