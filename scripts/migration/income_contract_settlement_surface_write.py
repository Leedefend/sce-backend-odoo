# -*- coding: utf-8 -*-
"""Move settlement-like income contracts into the income settlement formal surface."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

from odoo.osv import expression


SOURCE_MODEL = "construction.contract.income:settlement_surface"
TITLE_TERMS = ("结算", "报告", "审核")
BASE_EXECUTION_DOMAIN = [
    "|",
    ("legacy_income_surface_visible", "=", True),
    "&",
    ("state", "in", ["confirmed", "running"]),
    ("legacy_contract_id", "=", False),
]
EXECUTION_DOMAIN = [
    "&",
    "&",
    "&",
    "|",
    ("legacy_income_surface_visible", "=", True),
    "&",
    ("state", "in", ["confirmed", "running"]),
    ("legacy_contract_id", "=", False),
    ("legacy_visible_title", "not ilike", TITLE_TERMS[0]),
    ("legacy_visible_title", "not ilike", TITLE_TERMS[1]),
    ("legacy_visible_title", "not ilike", TITLE_TERMS[2]),
]


def artifact_root() -> Path:
    root = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", "artifacts/migration"))
    try:
        root.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        root = Path("/tmp/sce-migration-artifacts")
        root.mkdir(parents=True, exist_ok=True)
    return root


OUTPUT_JSON = artifact_root() / "income_contract_settlement_surface_write_result_v1.json"


def ensure_allowed_db() -> None:
    allowlist = {
        item.strip()
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_demo,sc_prod_sim").split(",")
        if item.strip()
    }
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_projection": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def text(value) -> str:
    cleaned = str(value or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    if cleaned in {"False", "false", "None", "none"}:
        return ""
    return cleaned


def money(value) -> float:
    raw = text(value).replace(",", "").replace("￥", "").replace("¥", "")
    match = re.search(r"-?\d+(?:\.\d+)?", raw)
    if not match:
        return 0.0
    return float(match.group(0))


def title_domain() -> list:
    return expression.OR([[("legacy_visible_title", "ilike", term)] for term in TITLE_TERMS])


def settlement_stage(title: str) -> str:
    if "定案" in title:
        return "final"
    if "二审" in title:
        return "second_review"
    if "一审" in title or "初审" in title:
        return "first_review"
    if "审核" in title or "审计" in title or "报告" in title:
        return "final"
    return "declared"


def state_from_document_state(value: str) -> str:
    state = text(value)
    if state in {"已审核", "审核通过", "已批准"}:
        return "approve"
    if state in {"审核中", "审批中"}:
        return "submit"
    return "draft"


def source_records(Income):
    return Income.search(expression.AND([BASE_EXECUTION_DOMAIN, title_domain()]), order="legacy_visible_document_no,id")


def line_values(income, amount: float) -> dict:
    return {
        "name": text(income.legacy_visible_title) or text(income.subject) or text(income.name) or "收入合同结算",
        "contract_id": income.contract_id.id if income.contract_id else False,
        "qty": 1.0,
        "price_unit": amount,
    }


def settlement_values(income, amount: float) -> dict:
    contract = income.contract_id
    project = income.project_id or (contract.project_id if contract else False)
    partner = income.partner_id or (contract.partner_id if contract else False)
    document_date = income.legacy_visible_contract_date or income.date_contract or False
    title = text(income.legacy_visible_title) or text(income.subject) or text(income.name) or "收入合同结算"
    state = state_from_document_state(income.legacy_visible_document_state)
    vals = {
        "name": text(income.legacy_visible_document_no) or text(income.legacy_document_no) or "收入合同结算-%s" % income.id,
        "project_id": project.id,
        "contract_id": contract.id if contract else False,
        "partner_id": partner.id if partner else False,
        "settlement_unit_id": partner.id if partner else False,
        "legacy_counterparty_name": text(income.legacy_visible_counterparty) or False,
        "title": title,
        "document_date": document_date,
        "settlement_type": "in",
        "settlement_stage": settlement_stage(title),
        "date_settlement": document_date,
        "approved_date": document_date if state == "approve" else False,
        "final_approved_date": document_date if state == "approve" else False,
        "submitted_amount": money(income.legacy_visible_amount),
        "approved_amount": amount,
        "requested_fund_amount": amount,
        "state": state,
        "entry_user_id": income.create_uid.id or env.user.id,  # noqa: F821
        "entry_data": "formal_projection:%s:%s" % (SOURCE_MODEL, income.id),
        "legacy_fact_model": SOURCE_MODEL,
        "legacy_fact_id": income.id,
        "legacy_fact_type": "income_contract_settlement_title_cutover",
        "settlement_description": "\n".join(
            item
            for item in [
                "由正式收入合同执行面按标题关键词迁入收入合同结算。",
                "合同标题：%s" % title,
                "原单据编号：%s" % text(income.legacy_visible_document_no),
                "合同编号：%s" % text(income.legacy_visible_contract_no),
                "附件：%s" % text(income.legacy_visible_attachment),
            ]
            if item.split("：", 1)[-1]
        ),
        "legacy_visible_attachment": text(income.legacy_visible_attachment) or False,
        "note": "\n".join(
            [
                "[migration:income_contract_settlement_surface]",
                "source_model=construction.contract.income",
                "source_income_id=%s" % income.id,
                "source_contract_id=%s" % (contract.id if contract else ""),
                "legacy_contract_id=%s" % text(income.legacy_contract_id),
            ]
        ),
    }
    if not vals["partner_id"] and not vals["legacy_counterparty_name"]:
        vals["legacy_counterparty_name"] = "旧系统未填往来单位"
    return vals


def ensure_execution_action_domain() -> str:
    action = env.ref("smart_construction_core.action_construction_contract_income_execution")  # noqa: F821
    action.write({"domain": repr(EXECUTION_DOMAIN)})
    return action.domain


def main() -> None:
    ensure_allowed_db()
    Income = env["construction.contract.income"].sudo().with_context(active_test=False)  # noqa: F821
    Settlement = env["sc.settlement.order"].sudo().with_context(  # noqa: F821
        active_test=False,
        legacy_migration_allow_missing_contract=True,
    )
    Line = env["sc.settlement.order.line"].sudo().with_context(legacy_migration_allow_missing_contract=True)  # noqa: F821
    source = source_records(Income)
    if not source:
        raise RuntimeError({"error": "missing_income_contract_settlement_source", "terms": TITLE_TERMS})

    action_domain = ensure_execution_action_domain()
    created = 0
    updated = 0
    line_created = 0
    line_updated = 0
    blocked = []
    stale_removed = 0
    samples = []

    stale = Settlement.search([("legacy_fact_model", "=", SOURCE_MODEL), ("legacy_fact_id", "not in", source.ids)])
    if stale:
        stale_removed = len(stale)
        stale.unlink()

    for income in source:
        if not income.project_id:
            blocked.append({"income_id": income.id, "document_no": text(income.legacy_visible_document_no), "reason": "missing_project"})
            continue
        amount = money(income.legacy_visible_settlement_amount) or money(income.legacy_visible_amount)
        vals = settlement_values(income, amount)
        settlement = Settlement.search([("legacy_fact_model", "=", SOURCE_MODEL), ("legacy_fact_id", "=", income.id)], limit=1)
        if settlement:
            settlement.write(vals)
            updated += 1
            action = "updated"
        else:
            settlement = Settlement.create(vals)
            created += 1
            action = "created"
        line_vals = line_values(income, amount)
        line = settlement.line_ids[:1]
        if line:
            line.with_context(allow_contract_change=True).write(line_vals)
            line_updated += 1
        else:
            line_vals["settlement_id"] = settlement.id
            Line.create(line_vals)
            line_created += 1
        if len(samples) < 20:
            samples.append(
                {
                    "action": action,
                    "income_id": income.id,
                    "settlement_id": settlement.id,
                    "document_no": text(income.legacy_visible_document_no),
                    "title": text(income.legacy_visible_title),
                    "approved_amount": amount,
                    "attachment": text(income.legacy_visible_attachment),
                }
            )

    env.cr.commit()  # noqa: F821
    settlement_count = Settlement.search_count([("legacy_fact_model", "=", SOURCE_MODEL), ("legacy_fact_id", "in", source.ids)])
    execution_remaining = Income.search_count(expression.AND([EXECUTION_DOMAIN, title_domain()]))
    result = {
        "status": "PASS" if settlement_count == len(source) and execution_remaining == 0 and not blocked else "FAIL",
        "mode": "income_contract_settlement_surface_write",
        "db": env.cr.dbname,  # noqa: F821
        "source_model": "construction.contract.income",
        "target_model": "sc.settlement.order",
        "source_count": len(source),
        "settlement_count": settlement_count,
        "created_settlements": created,
        "updated_settlements": updated,
        "created_lines": line_created,
        "updated_lines": line_updated,
        "removed_stale_settlements": stale_removed,
        "execution_remaining_with_settlement_title": execution_remaining,
        "execution_action_domain": action_domain,
        "blocked": blocked[:20],
        "sample": samples,
    }
    OUTPUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    if result["status"] != "PASS":
        raise RuntimeError(result)


main()
