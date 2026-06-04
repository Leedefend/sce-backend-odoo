# -*- coding: utf-8 -*-
"""Move settlement-like expense contracts into the expense settlement formal surface."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

from odoo import fields
from odoo.osv import expression


SOURCE_MODEL = "construction.contract.expense:settlement_surface"
TITLE_TERM = "结算"
BASE_EXECUTION_DOMAIN = [("state", "in", ["confirmed", "running"])]
EXECUTION_DOMAIN = [
    "&",
    "&",
    ("state", "in", ["confirmed", "running"]),
    ("legacy_visible_title", "not ilike", TITLE_TERM),
    ("subject", "not ilike", TITLE_TERM),
]


def artifact_root() -> Path:
    root = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", "artifacts/migration"))
    try:
        root.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        root = Path("/tmp/sce-migration-artifacts")
        root.mkdir(parents=True, exist_ok=True)
    return root


OUTPUT_JSON = artifact_root() / "expense_contract_settlement_surface_write_result_v1.json"


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


def settlement_amount_from_title(title: str) -> float:
    match = re.search(r"结算金额\s*[:：]?\s*(-?\d+(?:,\d{3})*(?:\.\d+)?|-?\d+(?:\.\d+)?)", title or "")
    if not match:
        return 0.0
    return money(match.group(1))


def title_domain() -> list:
    return expression.OR([[("legacy_visible_title", "ilike", TITLE_TERM)], [("subject", "ilike", TITLE_TERM)]])


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
    if state in {"已审核", "审核通过", "已批准", "已生效"}:
        return "approve"
    if state in {"审核中", "审批中"}:
        return "submit"
    return "draft"


def source_records(Expense):
    return Expense.search(
        expression.AND([BASE_EXECUTION_DOMAIN, title_domain()]),
        order="legacy_visible_document_no,id",
    )


def source_title(expense) -> str:
    return text(expense.legacy_visible_title) or text(expense.subject) or text(expense.name) or "支出合同结算"


def source_document_date(expense):
    value = expense.legacy_visible_contract_date or expense.date_contract or expense.legacy_visible_created_time or False
    if not value:
        return False
    return fields.Date.to_date(value)


def source_amount(expense, title: str) -> float:
    parsed = settlement_amount_from_title(title)
    if parsed:
        return parsed
    raw = (
        money(expense.legacy_visible_settlement_amount)
        or money(expense.legacy_visible_amount)
        or float(expense.visible_contract_amount or expense.amount_total or expense.amount_final or 0.0)
    )
    return abs(raw)


def line_values(expense, amount: float) -> dict:
    return {
        "name": source_title(expense),
        "contract_id": expense.contract_id.id if expense.contract_id else False,
        "qty": 1.0,
        "price_unit": amount,
    }


def source_attachment_ids(expense) -> list[int]:
    Attachment = env["ir.attachment"].sudo()  # noqa: F821
    attachments = Attachment.search(
        [("res_model", "=", "construction.contract.expense"), ("res_id", "=", expense.id)],
        order="id",
    )
    if not attachments and expense.contract_id:
        attachments = Attachment.search(
            [("res_model", "=", "construction.contract"), ("res_id", "=", expense.contract_id.id)],
            order="id",
        )
    return attachments.ids


def settlement_values(expense, amount: float) -> dict:
    contract = expense.contract_id
    project = expense.project_id or (contract.project_id if contract else False)
    partner = expense.partner_id or (contract.partner_id if contract else False)
    title = source_title(expense)
    document_date = source_document_date(expense)
    state = state_from_document_state(expense.legacy_visible_document_state)
    vals = {
        "name": text(expense.legacy_visible_document_no) or text(expense.legacy_document_no) or "支出合同结算-%s" % expense.id,
        "project_id": project.id,
        "contract_id": contract.id if contract else False,
        "partner_id": partner.id if partner else False,
        "settlement_unit_id": partner.id if partner else False,
        "legacy_counterparty_name": text(expense.legacy_visible_counterparty) or False,
        "title": title,
        "document_date": document_date,
        "settlement_type": "out",
        "settlement_stage": settlement_stage(title),
        "date_settlement": document_date,
        "approved_date": document_date if state == "approve" else False,
        "final_approved_date": document_date if state == "approve" else False,
        "submitted_amount": abs(money(expense.legacy_visible_amount) or float(expense.visible_contract_amount or expense.amount_total or 0.0)),
        "approved_amount": amount,
        "requested_fund_amount": amount,
        "state": state,
        "entry_user_id": expense.create_uid.id or env.user.id,  # noqa: F821
        "source_created_by": text(expense.legacy_visible_creator_name) or False,
        "source_created_at": expense.legacy_visible_created_time or False,
        "entry_data": "formal_projection:%s:%s" % (SOURCE_MODEL, expense.id),
        "legacy_fact_model": SOURCE_MODEL,
        "legacy_fact_id": expense.id,
        "legacy_fact_type": "expense_contract_settlement_title_cutover",
        "settlement_description": "\n".join(
            item
            for item in [
                "由正式支出合同执行面按合同标题含“结算”迁入支出合同结算。",
                "合同标题：%s" % title,
                "原单据编号：%s" % text(expense.legacy_visible_document_no),
                "合同编号：%s" % text(expense.legacy_visible_contract_no),
                "源可见金额：%s" % text(expense.legacy_visible_amount),
                "附件：%s" % text(expense.legacy_visible_attachment),
            ]
            if item.split("：", 1)[-1]
        ),
        "legacy_visible_attachment": text(expense.legacy_visible_attachment) or False,
        "attachment_ids": [(6, 0, source_attachment_ids(expense))],
        "note": "\n".join(
            [
                "[migration:expense_contract_settlement_surface]",
                "source_model=construction.contract.expense",
                "source_expense_id=%s" % expense.id,
                "source_contract_id=%s" % (contract.id if contract else ""),
            ]
        ),
    }
    if not vals["partner_id"] and not vals["legacy_counterparty_name"]:
        vals["legacy_counterparty_name"] = "旧系统未填往来单位"
    return vals


def ensure_execution_action_domain() -> str:
    action = env.ref("smart_construction_core.action_construction_contract_expense_execution")  # noqa: F821
    action.write({"domain": repr(EXECUTION_DOMAIN)})
    return action.domain


def main() -> None:
    ensure_allowed_db()
    Expense = env["construction.contract.expense"].sudo().with_context(active_test=False)  # noqa: F821
    Settlement = env["sc.settlement.order"].sudo().with_context(  # noqa: F821
        active_test=False,
        legacy_migration_allow_missing_contract=True,
    )
    Line = env["sc.settlement.order.line"].sudo().with_context(legacy_migration_allow_missing_contract=True)  # noqa: F821
    source = source_records(Expense)
    if not source:
        raise RuntimeError({"error": "missing_expense_contract_settlement_source", "term": TITLE_TERM})

    action_domain = ensure_execution_action_domain()
    created = 0
    updated = 0
    line_created = 0
    line_updated = 0
    linked_attachment_count = 0
    blocked = []
    stale_removed = 0
    samples = []

    stale = Settlement.search([("legacy_fact_model", "=", SOURCE_MODEL), ("legacy_fact_id", "not in", source.ids)])
    if stale:
        stale_removed = len(stale)
        stale.unlink()

    for expense in source:
        if not expense.project_id:
            blocked.append({"expense_id": expense.id, "document_no": text(expense.legacy_visible_document_no), "reason": "missing_project"})
            continue
        title = source_title(expense)
        amount = source_amount(expense, title)
        vals = settlement_values(expense, amount)
        settlement = Settlement.search([("legacy_fact_model", "=", SOURCE_MODEL), ("legacy_fact_id", "=", expense.id)], limit=1)
        if settlement:
            settlement.write(vals)
            updated += 1
            action = "updated"
        else:
            settlement = Settlement.create(vals)
            created += 1
            action = "created"
        line_vals = line_values(expense, amount)
        line = settlement.line_ids[:1]
        if line:
            line.with_context(allow_contract_change=True).write(line_vals)
            line_updated += 1
        else:
            line_vals["settlement_id"] = settlement.id
            Line.create(line_vals)
            line_created += 1
        attachment_ids = source_attachment_ids(expense)
        linked_attachment_count += len(attachment_ids)
        if len(samples) < 20:
            samples.append(
                {
                    "action": action,
                    "expense_id": expense.id,
                    "contract_id": expense.contract_id.id if expense.contract_id else False,
                    "settlement_id": settlement.id,
                    "document_no": text(expense.legacy_visible_document_no),
                    "title": title,
                    "approved_amount": amount,
                    "attachment": text(expense.legacy_visible_attachment),
                    "attachment_ids": attachment_ids,
                    "source_created_by": text(expense.legacy_visible_creator_name),
                    "source_created_at": text(expense.legacy_visible_created_time),
                }
            )

    env.cr.commit()  # noqa: F821
    settlement_count = Settlement.search_count([("legacy_fact_model", "=", SOURCE_MODEL), ("legacy_fact_id", "in", source.ids)])
    execution_remaining = Expense.search_count(expression.AND([EXECUTION_DOMAIN, title_domain()]))
    result = {
        "status": "PASS" if settlement_count == len(source) and execution_remaining == 0 and not blocked else "FAIL",
        "mode": "expense_contract_settlement_surface_write",
        "db": env.cr.dbname,  # noqa: F821
        "source_model": "construction.contract.expense",
        "target_model": "sc.settlement.order",
        "source_count": len(source),
        "settlement_count": settlement_count,
        "created_settlements": created,
        "updated_settlements": updated,
        "created_lines": line_created,
        "updated_lines": line_updated,
        "linked_attachment_count": linked_attachment_count,
        "removed_stale_settlements": stale_removed,
        "execution_remaining_with_settlement_title": execution_remaining,
        "execution_action_domain": action_domain,
        "blocked": blocked[:20],
        "sample": samples,
    }
    OUTPUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("EXPENSE_CONTRACT_SETTLEMENT_SURFACE_WRITE=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
    if result["status"] != "PASS":
        raise RuntimeError(result)


main()
