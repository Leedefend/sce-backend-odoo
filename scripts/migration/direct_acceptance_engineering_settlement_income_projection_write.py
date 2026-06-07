# -*- coding: utf-8 -*-
"""Project direct-acceptance engineering settlement orders into income settlements."""

from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path


SOURCE_MODEL = "sc.legacy.direct.acceptance.fact:direct_engineering_settlement_order"
ACCEPTANCE_LABEL = "工程结算单"


def artifact_root() -> Path:
    root = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", "artifacts/migration"))
    try:
        root.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        root = Path("/tmp/sce-migration-artifacts")
        root.mkdir(parents=True, exist_ok=True)
    return root


OUTPUT_JSON = artifact_root() / "direct_acceptance_engineering_settlement_income_projection_result_v1.json"


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
    if not raw:
        return 0.0
    try:
        return float(raw)
    except ValueError:
        match = re.search(r"-?\d+(?:\.\d+)?", raw)
        return float(match.group(0)) if match else 0.0


def date_value(value):
    raw = text(value).replace("T", " ").replace("/", "-")
    if not raw:
        return False
    raw = re.sub(r"\.\d+$", "", raw)
    for fmt, size in (("%Y-%m-%d %H:%M:%S", 19), ("%Y-%m-%d %H:%M", 16), ("%Y-%m-%d", 10)):
        try:
            return datetime.strptime(raw[:size], fmt).date().isoformat()
        except ValueError:
            continue
    return False


def state_from_visible(value: str) -> str:
    state = text(value)
    if state in {"2", "审核通过", "已审核", "已批准"}:
        return "approve"
    if state in {"1", "审批中", "审核中"}:
        return "submit"
    if state in {"-1", "否决"}:
        return "cancel"
    return "draft"


def source_records(Fact):
    return Fact.search([("active", "=", True), ("acceptance_label", "=", ACCEPTANCE_LABEL)], order="document_no,id")


def project_for_fact(fact, cache):
    if fact.project_id:
        return fact.project_id
    project_name = text(fact.legacy_visible_04) or text(fact.project_name) or "旧系统未填项目（直营工程结算）"
    key = text(fact.project_legacy_id) or "__name__:" + project_name
    if key in cache:
        return cache[key]
    Project = env["project.project"].sudo().with_context(active_test=False)  # noqa: F821
    project = False
    if text(fact.project_legacy_id) and "legacy_project_id" in Project._fields:
        project = Project.search([("legacy_project_id", "=", text(fact.project_legacy_id))], limit=1)
    if not project:
        project = Project.search([("name", "=", project_name)], limit=1)
    if not project:
        vals = {"name": project_name}
        if "legacy_project_id" in Project._fields and text(fact.project_legacy_id):
            vals["legacy_project_id"] = text(fact.project_legacy_id)
        if "operation_strategy" in Project._fields:
            vals["operation_strategy"] = "direct"
        project = Project.create(vals)
    cache[key] = project
    return project


def partner_by_name(name, cache):
    partner_name = text(name)
    if not partner_name:
        return False
    if partner_name in cache:
        return cache[partner_name]
    Partner = env["res.partner"].sudo().with_context(active_test=False)  # noqa: F821
    partner = Partner.search([("name", "=", partner_name)], limit=1)
    if not partner:
        partner = Partner.create({"name": partner_name, "customer_rank": 1})
    elif partner.customer_rank <= 0:
        partner.write({"customer_rank": 1})
    cache[partner_name] = partner
    return partner


def settlement_values(fact, project, partner):
    visible_state = text(fact.legacy_visible_01)
    document_no = text(fact.legacy_visible_02) or text(fact.document_no) or "直营工程结算-%s" % fact.id
    document_date = date_value(fact.legacy_visible_03) or date_value(fact.document_date)
    submitted_amount = money(fact.legacy_visible_05)
    contract_total = money(fact.legacy_visible_06)
    approved_amount = money(fact.legacy_visible_07) or money(fact.amount_total)
    title = text(fact.legacy_visible_08) or text(fact.document_title) or document_no
    employer = text(fact.legacy_visible_09)
    contractor = text(fact.legacy_visible_10)
    delta_amount = money(fact.legacy_visible_11)
    audit_unit = text(fact.legacy_visible_12)
    contract_name = text(fact.legacy_visible_13)
    approved_date = date_value(fact.legacy_visible_14)
    engineering_address = text(fact.legacy_visible_15)
    attachment = text(fact.legacy_visible_16) or text(fact.attachment_ref)
    creator = text(fact.legacy_visible_17) or text(fact.creator_name)
    created_time = text(fact.legacy_visible_18) or text(fact.created_time)
    state = state_from_visible(visible_state)
    vals = {
        "name": document_no,
        "project_id": project.id,
        "partner_id": partner.id if partner else False,
        "settlement_unit_id": partner.id if partner else False,
        "legacy_counterparty_name": employer or contractor or False,
        "title": title,
        "document_date": document_date,
        "settlement_type": "in",
        "settlement_stage": "final",
        "date_settlement": approved_date or document_date,
        "declared_date": document_date,
        "approved_date": approved_date or (document_date if state == "approve" else False),
        "final_approved_date": approved_date or (document_date if state == "approve" else False),
        "settlement_amount": approved_amount,
        "submitted_amount": submitted_amount,
        "approved_amount": approved_amount,
        "requested_fund_amount": approved_amount,
        "state": state,
        "entry_user_id": fact.create_uid.id or env.user.id,  # noqa: F821
        "entry_data": "formal_projection:%s:%s" % (SOURCE_MODEL, fact.id),
        "legacy_acceptance_label": ACCEPTANCE_LABEL,
        "legacy_fact_model": SOURCE_MODEL,
        "legacy_fact_id": fact.id,
        "legacy_fact_type": "direct_acceptance_engineering_settlement_order",
        "legacy_visible_attachment": attachment or False,
        "settlement_description": "\n".join(
            item
            for item in [
                "由直营项目数据核对-工程结算单整体合并进入收入合同结算。",
                "单据状态：%s" % visible_state,
                "单据编号：%s" % document_no,
                "项目名称：%s" % (text(fact.legacy_visible_04) or text(fact.project_name)),
                "送审金额：%s" % text(fact.legacy_visible_05),
                "合同总额：%s" % text(fact.legacy_visible_06),
                "审定金额：%s" % text(fact.legacy_visible_07),
                "发包人：%s" % employer,
                "承包人：%s" % contractor,
                "审增减金额：%s" % text(fact.legacy_visible_11),
                "审计单位：%s" % audit_unit,
                "合同名称：%s" % contract_name,
                "工程地址：%s" % engineering_address,
                "附件：%s" % attachment,
                "录入人：%s" % creator,
                "录入时间：%s" % created_time,
            ]
            if item.split("：", 1)[-1]
        ),
        "note": "\n".join(
            [
                "[migration:direct_acceptance_engineering_settlement_income_projection]",
                "source_model=sc.legacy.direct.acceptance.fact",
                "source_fact_id=%s" % fact.id,
                "legacy_record_id=%s" % text(fact.legacy_record_id),
                "legacy_project_id=%s" % text(fact.project_legacy_id),
                "contract_total=%s" % contract_total,
                "delta_amount=%s" % delta_amount,
            ]
        ),
    }
    for index in range(1, 61):
        field = "legacy_visible_%02d" % index
        if field in env["sc.settlement.order"]._fields:  # noqa: F821
            vals[field] = text(getattr(fact, field, "")) or False
    return vals


def line_values(fact, amount):
    return {
        "name": text(fact.legacy_visible_13) or text(fact.legacy_visible_08) or text(fact.legacy_visible_02) or "工程结算单",
        "qty": 1.0,
        "price_unit": amount,
    }


def main():
    ensure_allowed_db()
    Fact = env["sc.legacy.direct.acceptance.fact"].sudo().with_context(active_test=False)  # noqa: F821
    Settlement = env["sc.settlement.order"].sudo().with_context(active_test=False, legacy_migration_allow_missing_contract=True)  # noqa: F821
    Line = env["sc.settlement.order.line"].sudo().with_context(legacy_migration_allow_missing_contract=True)  # noqa: F821
    source = source_records(Fact)
    if not source:
        raise RuntimeError({"error": "missing_direct_acceptance_engineering_settlement_source", "acceptance_label": ACCEPTANCE_LABEL})

    project_cache = {}
    partner_cache = {}
    created = 0
    updated = 0
    line_created = 0
    line_updated = 0
    samples = []

    stale = Settlement.search([("legacy_fact_model", "=", SOURCE_MODEL), ("legacy_fact_id", "not in", source.ids)])
    stale_count = len(stale)
    if stale:
        stale.unlink()

    for fact in source:
        project = project_for_fact(fact, project_cache)
        partner = partner_by_name(text(fact.legacy_visible_09) or text(fact.partner_name), partner_cache)
        amount = money(fact.legacy_visible_07) or money(fact.amount_total)
        vals = settlement_values(fact, project, partner)
        settlement = Settlement.search([("legacy_fact_model", "=", SOURCE_MODEL), ("legacy_fact_id", "=", fact.id)], limit=1)
        if settlement:
            settlement.write(vals)
            updated += 1
            action = "updated"
        else:
            settlement = Settlement.create(vals)
            created += 1
            action = "created"
        line_vals = line_values(fact, amount)
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
                    "fact_id": fact.id,
                    "settlement_id": settlement.id,
                    "document_no": vals["name"],
                    "project": project.display_name,
                    "title": vals["title"],
                    "approved_amount": amount,
                    "attachment": vals["legacy_visible_attachment"],
                }
            )

    env.cr.commit()  # noqa: F821
    settlement_count = Settlement.search_count([("legacy_fact_model", "=", SOURCE_MODEL), ("legacy_fact_id", "in", source.ids)])
    result = {
        "status": "PASS" if settlement_count == len(source) else "FAIL",
        "mode": "direct_acceptance_engineering_settlement_income_projection_write",
        "db": env.cr.dbname,  # noqa: F821
        "acceptance_label": ACCEPTANCE_LABEL,
        "source_model": "sc.legacy.direct.acceptance.fact",
        "target_model": "sc.settlement.order",
        "source_count": len(source),
        "settlement_count": settlement_count,
        "created_settlements": created,
        "updated_settlements": updated,
        "created_lines": line_created,
        "updated_lines": line_updated,
        "removed_stale_settlements": stale_count,
        "sample": samples,
    }
    OUTPUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    if result["status"] != "PASS":
        raise RuntimeError(result)


main()
