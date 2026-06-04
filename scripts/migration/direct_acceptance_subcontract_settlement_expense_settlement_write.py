# -*- coding: utf-8 -*-
"""Project accepted direct-project subcontract settlements into formal expense settlement."""

from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path


SOURCE_SYSTEM = "online_old_scbsly"
SOURCE_MODEL = "sc.legacy.direct.acceptance.fact"
ACCEPTANCE_LABEL = "分包结算单"
TARGET_MODEL = "sc.settlement.order"
LEGACY_FACT_TYPE = "direct_acceptance_subcontract_settlement_expense_settlement"
SETTLEMENT_CATEGORY = "专业分包"


def artifact_root() -> Path:
    root = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", "artifacts/migration"))
    try:
        root.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        root = Path("/tmp/sce-migration-artifacts")
        root.mkdir(parents=True, exist_ok=True)
    return root


OUTPUT_JSON = artifact_root() / "direct_acceptance_subcontract_settlement_expense_settlement_write_result_v1.json"


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
    if cleaned.lower() in {"false", "none", "null"}:
        return ""
    return cleaned


def payload_of(fact) -> dict:
    try:
        payload = json.loads(fact.raw_payload or "{}")
    except (TypeError, ValueError):
        return {}
    return payload if isinstance(payload, dict) else {}


def first_text(payload: dict, *fields: str) -> str:
    for field in fields:
        value = text(payload.get(field))
        if value:
            return value
    return ""


def money(value) -> float:
    raw = text(value).replace(",", "").replace("￥", "").replace("¥", "")
    if not raw:
        return 0.0
    match = re.search(r"-?\d+(?:\.\d+)?", raw)
    return float(match.group(0)) if match else 0.0


def parse_date(value) -> str | None:
    raw = text(value).replace("/", "-")
    if not raw:
        return None
    for fmt, size in (("%Y-%m-%d %H:%M:%S", 19), ("%Y-%m-%d %H:%M", 16), ("%Y-%m-%d", 10)):
        try:
            return datetime.strptime(raw[:size], fmt).date().isoformat()
        except ValueError:
            continue
    return None


def parse_datetime(value) -> str | None:
    raw = text(value).replace("T", " ").replace("/", "-")
    if not raw:
        return None
    raw = re.sub(r"\.\d+$", "", raw)
    for fmt, size in (("%Y-%m-%d %H:%M:%S", 19), ("%Y-%m-%d %H:%M", 16), ("%Y-%m-%d", 10)):
        try:
            parsed = datetime.strptime(raw[:size], fmt)
            return parsed.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue
    return None


def ensure_direct_project(project):
    if project and "operation_strategy" in project._fields and project.operation_strategy != "direct":
        project.sudo().write({"operation_strategy": "direct"})
    return project


def resolve_project(fact, payload: dict):
    Project = env["project.project"].sudo().with_context(active_test=False)  # noqa: F821
    if fact.project_id:
        return ensure_direct_project(fact.project_id)
    legacy_project_id = text(fact.project_legacy_id) or first_text(payload, "XMID", "SJBXXMID")
    if legacy_project_id and "legacy_project_id" in Project._fields:
        project = Project.search([("legacy_project_id", "=", legacy_project_id)], limit=1)
        if project:
            return ensure_direct_project(project)
    project_name = text(fact.legacy_visible_02) or text(fact.project_name) or first_text(payload, "XMMC")
    if not project_name:
        project_name = "直营项目分包结算未匹配项目"
    project = Project.search([("name", "=", project_name)], limit=1)
    if project:
        return ensure_direct_project(project)
    vals = {"name": project_name}
    if legacy_project_id and "legacy_project_id" in Project._fields:
        vals["legacy_project_id"] = legacy_project_id
    if "company_id" in Project._fields:
        vals["company_id"] = env.company.id  # noqa: F821
    if "operation_strategy" in Project._fields:
        vals["operation_strategy"] = "direct"
    return Project.create(vals)


def resolve_partner(fact, payload: dict):
    Partner = env["res.partner"].sudo().with_context(active_test=False)  # noqa: F821
    name = text(fact.legacy_visible_05) or first_text(payload, "GYDW", "JSDW", "FBDW") or text(fact.partner_name)
    if not name:
        name = "直营项目分包结算未匹配结算单位"
    partner = Partner.search([("name", "=", name)], order="id", limit=1)
    if partner:
        return partner
    vals = {"name": name, "company_type": "company"}
    if "is_company" in Partner._fields:
        vals["is_company"] = True
    if "supplier_rank" in Partner._fields:
        vals["supplier_rank"] = 1
    if "legacy_partner_id" in Partner._fields:
        vals["legacy_partner_id"] = "direct_acceptance_subcontract_settlement:" + name
    if "legacy_partner_source" in Partner._fields:
        vals["legacy_partner_source"] = "direct_acceptance_subcontract_settlement"
    if "legacy_source_evidence" in Partner._fields:
        vals["legacy_source_evidence"] = SOURCE_MODEL + ":" + name
    return Partner.create(vals)


def resolve_contract(project, partner, contract_no: str):
    if not contract_no:
        return False
    Contract = env["construction.contract"].sudo().with_context(active_test=False, skip_validation_check=True)  # noqa: F821
    base = [
        ("project_id", "=", project.id),
        "|",
        ("legacy_contract_no", "=", contract_no),
        ("legacy_visible_contract_no", "=", contract_no),
    ]
    if partner:
        contract = Contract.search(base + [("partner_id", "=", partner.id)], order="id desc", limit=1)
        if contract:
            return contract
    return Contract.search(base, order="id desc", limit=1)


def expense_category(name: str):
    category = env["sc.dictionary"].sudo().search(  # noqa: F821
        [("type", "=", "expense_contract_category"), ("name", "=", name)],
        limit=1,
    )
    if not category:
        raise RuntimeError({"missing_expense_contract_category": name})
    return category


def attachment_display(fact, payload: dict) -> str:
    visible = text(fact.legacy_visible_18)
    raw_ref = text(fact.attachment_ref) or first_text(payload, "f_FJ", "FJ")
    if raw_ref and raw_ref not in visible:
        if visible:
            return visible + "\nlegacy-file-id://" + raw_ref
        return "附件(1)\nlegacy-file-id://" + raw_ref
    return visible


def state_from_document_state(value: str) -> str:
    state = text(value)
    if state in {"已审核", "审核通过", "已批准", "已生效"}:
        return "approve"
    if state in {"审核中", "审批中", "提交审批"}:
        return "submit"
    return "draft"


def description_text(values: dict) -> str:
    parts = []
    if values["settlement_note"]:
        parts.append((False, values["settlement_note"]))
    parts += [
        ("付款状态", values["payment_state"]),
        ("已付款金额", values["paid_amount_text"]),
        ("未付款金额", values["unpaid_amount_text"]),
        ("支付申请状态", values["request_state"]),
        ("已申请金额", values["requested_amount_text"]),
        ("未申请金额", values["unrequested_amount_text"]),
        ("合同编号", values["contract_no"]),
        ("起始结算日期", values["period_start"]),
        ("终止结算日期", values["period_end"]),
    ]
    return "\n".join(("%s：%s" % (label, value)) if label else value for label, value in parts if value)


def settlement_values(fact) -> tuple[dict, dict, float]:
    payload = payload_of(fact)
    project = resolve_project(fact, payload)
    partner = resolve_partner(fact, payload)
    state_text = text(fact.legacy_visible_01) or first_text(payload, "DJZTText", "DJZT")
    document_no = text(fact.legacy_visible_03) or text(fact.document_no) or text(fact.legacy_record_id)
    title = text(fact.legacy_visible_04) or text(fact.document_title) or document_no or "分包结算单"
    amount = money(fact.legacy_visible_06 or fact.amount_total)
    contract_no = text(fact.legacy_visible_13) or first_text(payload, "HTBH", "ContractNo")
    settlement_date = parse_date(fact.legacy_visible_16) or parse_date(fact.created_time)
    created_at = parse_datetime(fact.legacy_visible_20) or parse_datetime(fact.created_time)
    creator = text(fact.legacy_visible_19) or text(fact.creator_name) or first_text(payload, "LRR", "f_LRR")
    contract = resolve_contract(project, partner, contract_no)
    category = expense_category(SETTLEMENT_CATEGORY)
    detail = {
        "payment_state": text(fact.legacy_visible_07),
        "paid_amount_text": text(fact.legacy_visible_08),
        "unpaid_amount_text": text(fact.legacy_visible_09),
        "request_state": text(fact.legacy_visible_10),
        "requested_amount_text": text(fact.legacy_visible_11),
        "unrequested_amount_text": text(fact.legacy_visible_12),
        "contract_no": contract_no,
        "period_start": text(fact.legacy_visible_14),
        "period_end": text(fact.legacy_visible_15),
        "settlement_note": text(fact.legacy_visible_17),
    }
    vals = {
        "name": document_no or "分包结算单-%s" % fact.id,
        "project_id": project.id,
        "contract_id": contract.id if contract else False,
        "partner_id": partner.id,
        "settlement_unit_id": partner.id,
        "legacy_counterparty_name": text(fact.legacy_visible_05) or False,
        "title": title,
        "document_date": settlement_date,
        "settlement_type": "out",
        "settlement_category_id": category.id,
        "legacy_settlement_category": SETTLEMENT_CATEGORY,
        "settlement_stage": "final" if "定案" in title or "审核" in title else "declared",
        "date_settlement": settlement_date,
        "approved_date": settlement_date if state_from_document_state(state_text) == "approve" else False,
        "final_approved_date": settlement_date if state_from_document_state(state_text) == "approve" else False,
        "settlement_amount": amount,
        "submitted_amount": amount,
        "approved_amount": amount,
        "requested_fund_amount": money(fact.legacy_visible_11) or amount,
        "legacy_document_state": state_text,
        "legacy_contract_no": contract_no,
        "settlement_period_start": parse_date(fact.legacy_visible_14),
        "settlement_period_end": parse_date(fact.legacy_visible_15),
        "legacy_payment_state": detail["payment_state"],
        "legacy_paid_amount": money(fact.legacy_visible_08),
        "legacy_unpaid_amount": money(fact.legacy_visible_09),
        "legacy_payment_request_state": detail["request_state"],
        "legacy_unrequested_amount": money(fact.legacy_visible_12),
        "state": state_from_document_state(state_text),
        "source_created_by": creator or False,
        "source_created_at": created_at,
        "entry_data": "直营项目数据核对 / 分包结算单",
        "settlement_description": description_text(detail),
        "legacy_visible_attachment": attachment_display(fact, payload) or False,
        "note": False,
        "legacy_fact_model": SOURCE_MODEL,
        "legacy_fact_id": fact.id,
        "legacy_fact_type": LEGACY_FACT_TYPE,
    }
    return {key: value for key, value in vals.items() if value not in ("", None)}, detail, amount


def line_values(settlement, amount: float) -> dict:
    return {
        "settlement_id": settlement.id,
        "contract_id": settlement.contract_id.id if settlement.contract_id else False,
        "name": settlement.title or settlement.name,
        "qty": 1.0 if amount else 0.0,
        "price_unit": amount,
    }


def main() -> None:
    ensure_allowed_db()
    Fact = env[SOURCE_MODEL].sudo().with_context(active_test=False)  # noqa: F821
    Settlement = env[TARGET_MODEL].sudo().with_context(active_test=False, legacy_migration_allow_missing_contract=True)  # noqa: F821
    Line = env["sc.settlement.order.line"].sudo().with_context(legacy_migration_allow_missing_contract=True)  # noqa: F821
    facts = Fact.search(
        [
            ("source_system", "=", SOURCE_SYSTEM),
            ("acceptance_label", "=", ACCEPTANCE_LABEL),
            ("active", "=", True),
        ],
        order="legacy_record_id,id",
    )
    if not facts:
        raise RuntimeError({"error": "missing_direct_acceptance_subcontract_settlement_source"})

    stale = Settlement.search(
        [
            ("legacy_fact_model", "=", SOURCE_MODEL),
            ("legacy_fact_type", "=", LEGACY_FACT_TYPE),
            ("legacy_fact_id", "not in", facts.ids),
        ]
    )
    stale_removed = len(stale)
    if stale:
        stale.unlink()

    created = updated = line_created = line_updated = 0
    sample = []
    for fact in facts:
        vals, detail, amount = settlement_values(fact)
        settlement = Settlement.search([("legacy_fact_model", "=", SOURCE_MODEL), ("legacy_fact_id", "=", fact.id)], limit=1)
        if settlement:
            settlement.write(vals)
            updated += 1
            action = "updated"
        else:
            settlement = Settlement.create(vals)
            created += 1
            action = "created"
        line_vals = line_values(settlement, amount)
        line = settlement.line_ids[:1]
        if line:
            line.with_context(allow_contract_change=True, legacy_migration_allow_missing_contract=True).write(line_vals)
            line_updated += 1
        else:
            Line.create(line_vals)
            line_created += 1
        if len(sample) < 20:
            sample.append(
                {
                    "action": action,
                    "fact_id": fact.id,
                    "legacy_record_id": fact.legacy_record_id,
                    "settlement_id": settlement.id,
                    "name": settlement.name,
                    "title": settlement.title,
                    "project": settlement.project_id.display_name,
                    "operation_strategy": settlement.operation_strategy,
                    "partner": settlement.partner_id.display_name,
                    "contract_id": settlement.contract_id.id,
                    "category": settlement.settlement_category_display,
                    "amount": settlement.amount_total,
                    "legacy_document_state": settlement.legacy_document_state,
                    "legacy_contract_no": settlement.legacy_contract_no,
                    "settlement_period_start": str(settlement.settlement_period_start or ""),
                    "settlement_period_end": str(settlement.settlement_period_end or ""),
                    "legacy_payment_state": settlement.legacy_payment_state,
                    "legacy_paid_amount": settlement.legacy_paid_amount,
                    "legacy_unpaid_amount": settlement.legacy_unpaid_amount,
                    "legacy_payment_request_state": settlement.legacy_payment_request_state,
                    "legacy_unrequested_amount": settlement.legacy_unrequested_amount,
                    "source_created_by": settlement.source_created_by,
                    "source_created_at": str(settlement.source_created_at or ""),
                    "attachment": settlement.legacy_visible_attachment,
                    "detail": detail,
                }
            )

    env.cr.commit()  # noqa: F821
    projected_domain = [("legacy_fact_model", "=", SOURCE_MODEL), ("legacy_fact_type", "=", LEGACY_FACT_TYPE)]
    projected_count = Settlement.search_count(projected_domain)
    direct_count = Settlement.search_count(projected_domain + [("operation_strategy", "=", "direct")])
    category_count = Settlement.search_count(projected_domain + [("settlement_category_display", "=", SETTLEMENT_CATEGORY)])
    attachment_count = Settlement.search_count(projected_domain + [("legacy_visible_attachment", "!=", False)])
    creator_count = Settlement.search_count(projected_domain + [("source_created_by", "!=", False)])
    document_state_count = Settlement.search_count(projected_domain + [("legacy_document_state", "!=", False)])
    payment_state_count = Settlement.search_count(projected_domain + [("legacy_payment_state", "!=", False)])
    paid_amount_count = Settlement.search_count(projected_domain + [("legacy_paid_amount", "!=", 0)])
    unpaid_amount_count = Settlement.search_count(projected_domain + [("legacy_unpaid_amount", "!=", 0)])
    payment_request_state_count = Settlement.search_count(projected_domain + [("legacy_payment_request_state", "!=", False)])
    unrequested_amount_count = Settlement.search_count(projected_domain + [("legacy_unrequested_amount", "!=", 0)])
    contract_no_source_count = sum(1 for fact in facts if text(fact.legacy_visible_13))
    contract_no_count = Settlement.search_count(projected_domain + [("legacy_contract_no", "!=", False)])
    period_start_source_count = sum(1 for fact in facts if text(fact.legacy_visible_14))
    period_start_count = Settlement.search_count(projected_domain + [("settlement_period_start", "!=", False)])
    period_end_source_count = sum(1 for fact in facts if text(fact.legacy_visible_15))
    period_end_count = Settlement.search_count(projected_domain + [("settlement_period_end", "!=", False)])
    amount_count = Settlement.search_count(projected_domain + [("amount_total", "!=", 0)])
    action = env.ref("smart_construction_core.action_sc_settlement_order_expense")  # noqa: F821
    visible_count = Settlement.search_count([("settlement_type", "=", "out")] + projected_domain)
    result = {
        "status": "PASS"
        if projected_count == len(facts)
        and visible_count == len(facts)
        and direct_count == len(facts)
        and category_count == len(facts)
        and document_state_count == len(facts)
        and payment_state_count == len(facts)
        and payment_request_state_count == len(facts)
        and contract_no_count == contract_no_source_count
        and period_start_count == period_start_source_count
        and period_end_count == period_end_source_count
        else "FAIL",
        "mode": "direct_acceptance_subcontract_settlement_expense_settlement_write",
        "db": env.cr.dbname,  # noqa: F821
        "source_system": SOURCE_SYSTEM,
        "acceptance_label": ACCEPTANCE_LABEL,
        "target_model": TARGET_MODEL,
        "source_count": len(facts),
        "projected_count": projected_count,
        "visible_in_expense_settlement_count": visible_count,
        "direct_operation_count": direct_count,
        "category_count": category_count,
        "attachment_display_count": attachment_count,
        "creator_count": creator_count,
        "document_state_count": document_state_count,
        "payment_state_count": payment_state_count,
        "paid_amount_nonzero_count": paid_amount_count,
        "unpaid_amount_nonzero_count": unpaid_amount_count,
        "payment_request_state_count": payment_request_state_count,
        "unrequested_amount_nonzero_count": unrequested_amount_count,
        "contract_no_source_count": contract_no_source_count,
        "contract_no_count": contract_no_count,
        "period_start_source_count": period_start_source_count,
        "period_start_count": period_start_count,
        "period_end_source_count": period_end_source_count,
        "period_end_count": period_end_count,
        "amount_nonzero_count": amount_count,
        "created_settlements": created,
        "updated_settlements": updated,
        "created_lines": line_created,
        "updated_lines": line_updated,
        "removed_stale_settlements": stale_removed,
        "expense_settlement_action_domain": action.domain,
        "sample": sample,
    }
    OUTPUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("DIRECT_ACCEPTANCE_SUBCONTRACT_SETTLEMENT_EXPENSE_SETTLEMENT_WRITE=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
    if result["status"] != "PASS":
        raise RuntimeError(result)


main()
