# -*- coding: utf-8 -*-
"""Project accepted direct-project material/labor/equipment settlements into formal expense settlement."""

from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path


SOURCE_SYSTEM = "online_old_scbsly"
SOURCE_MODEL = "sc.legacy.direct.acceptance.fact"
TARGET_MODEL = "sc.settlement.order"
LEGACY_FACT_TYPE_PREFIX = "direct_acceptance_expense_settlement"

CONFIGS = {
    "材料结算单": {
        "category": "材料",
        "fallback_project": "直营项目材料结算未匹配项目",
        "fallback_partner": "直营项目材料结算未匹配结算单位",
        "entry_data": "直营项目数据核对 / 材料结算单",
        "state": "01",
        "project": "02",
        "document_no": "03",
        "title": "04",
        "partner": "05",
        "date": "06",
        "amount": "07",
        "payment_state": "08",
        "paid": "09",
        "unpaid": "10",
        "request_state": "11",
        "requested": "12",
        "unrequested": "13",
        "note": "14",
        "attachment": "15",
        "creator": "16",
        "created_at": "17",
    },
    "劳务结算": {
        "category": "劳务",
        "fallback_project": "直营项目劳务结算未匹配项目",
        "fallback_partner": "直营项目劳务结算未匹配结算单位",
        "entry_data": "直营项目数据核对 / 劳务结算",
        "state": "01",
        "document_no": "02",
        "project": "03",
        "date": "04",
        "title": "05",
        "partner": "06",
        "amount": "07",
        "payment_state": "08",
        "paid": "09",
        "unpaid": "10",
        "request_state": "11",
        "requested": "12",
        "unrequested": "13",
        "note": "14",
        "attachment": "15",
        "creator": "16",
        "created_at": "17",
        "contract_no": "18",
    },
    "分包结算单": {
        "category": "分包",
        "fallback_project": "直营项目分包结算未匹配项目",
        "fallback_partner": "直营项目分包结算未匹配结算单位",
        "entry_data": "直营项目数据核对 / 分包结算单",
        "state": "01",
        "project": "02",
        "document_no": "03",
        "title": "04",
        "partner": "05",
        "amount": "06",
        "payment_state": "07",
        "paid": "08",
        "unpaid": "09",
        "request_state": "10",
        "requested": "11",
        "unrequested": "12",
        "contract_no": "13",
        "date": "16",
        "note": "17",
        "attachment": "18",
        "creator": "19",
        "created_at": "20",
    },
    "机械结算单": {
        "category": "机械",
        "fallback_project": "直营项目机械结算未匹配项目",
        "fallback_partner": "直营项目机械结算未匹配结算单位",
        "allow_missing_settlement_unit": True,
        "entry_data": "直营项目数据核对 / 机械结算单",
        "state": "01",
        "document_no": "02",
        "project": "03",
        "date": "04",
        "partner": "05",
        "write_partner": False,
        "note": "06",
        "amount": "07",
        "payment_state": "08",
        "paid": "09",
        "unpaid": "10",
        "request_state": "11",
        "requested": "12",
        "unrequested": "13",
        "attachment": "14",
        "creator": "15",
        "created_at": "16",
    },
    "租赁结算单": {
        "category": "租赁",
        "fallback_project": "直营项目租赁结算未匹配项目",
        "fallback_partner": "直营项目租赁结算未匹配结算单位",
        "allow_missing_settlement_unit": True,
        "entry_data": "直营项目数据核对 / 租赁结算单",
        "state": "01",
        "document_no": "02",
        "project": "03",
        "date": "04",
        "partner": "05",
        "write_partner": False,
        "note": "06",
        "amount": "07",
        "payment_state": "08",
        "paid": "09",
        "unpaid": "10",
        "request_state": "11",
        "requested": "12",
        "unrequested": "13",
        "attachment": "14",
        "creator": "15",
        "created_at": "16",
    },
}


def artifact_root() -> Path:
    root = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", "artifacts/migration"))
    try:
        root.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        root = Path("/tmp/sce-migration-artifacts")
        root.mkdir(parents=True, exist_ok=True)
    return root


OUTPUT_JSON = artifact_root() / "direct_acceptance_expense_settlements_write_result_v1.json"


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


def visible(fact, suffix: str | None) -> str:
    if not suffix:
        return ""
    return text(getattr(fact, "legacy_visible_%s" % suffix, ""))


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


def resolve_project(fact, payload: dict, cfg: dict):
    Project = env["project.project"].sudo().with_context(active_test=False)  # noqa: F821
    if fact.project_id:
        return ensure_direct_project(fact.project_id)
    legacy_project_id = text(fact.project_legacy_id) or first_text(payload, "XMID", "SJBXXMID")
    if legacy_project_id and "legacy_project_id" in Project._fields:
        project = Project.search([("legacy_project_id", "=", legacy_project_id)], limit=1)
        if project:
            return ensure_direct_project(project)
    project_name = visible(fact, cfg.get("project")) or text(fact.project_name) or first_text(payload, "XMMC")
    if not project_name:
        project_name = cfg["fallback_project"]
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


def resolve_partner(fact, payload: dict, cfg: dict):
    Partner = env["res.partner"].sudo().with_context(active_test=False)  # noqa: F821
    name = visible(fact, cfg.get("partner")) or first_text(payload, "GYDW", "JSDW", "FBDW") or text(fact.partner_name)
    if not name and cfg.get("allow_missing_settlement_unit"):
        return Partner.browse()
    if not name:
        name = cfg["fallback_partner"]
    partner = Partner.search([("name", "=", name)], order="id", limit=1)
    if partner:
        return partner
    vals = {"name": name, "company_type": "company"}
    if "is_company" in Partner._fields:
        vals["is_company"] = True
    if "supplier_rank" in Partner._fields:
        vals["supplier_rank"] = 1
    if "legacy_partner_id" in Partner._fields:
        vals["legacy_partner_id"] = "direct_acceptance_expense_settlement:" + name
    if "legacy_partner_source" in Partner._fields:
        vals["legacy_partner_source"] = "direct_acceptance_expense_settlement"
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


def attachment_display(fact, payload: dict, cfg: dict) -> str:
    display = visible(fact, cfg.get("attachment"))
    raw_ref = text(fact.attachment_ref) or first_text(payload, "f_FJ", "FJ")
    if raw_ref and raw_ref not in display:
        if display:
            return display + "\nlegacy-file-id://" + raw_ref
        return "附件(1)\nlegacy-file-id://" + raw_ref
    return display


def state_from_document_state(value: str) -> str:
    state = text(value)
    if state in {"已审核", "审核通过", "已批准", "已生效"}:
        return "approve"
    if state in {"审核中", "审批中", "提交审批"}:
        return "submit"
    return "draft"


def description_text(detail: dict) -> str:
    parts = []
    if detail["settlement_note"]:
        parts.append((False, detail["settlement_note"]))
    parts += [
        ("付款状态", detail["payment_state"]),
        ("已付款金额", detail["paid_amount_text"]),
        ("未付款金额", detail["unpaid_amount_text"]),
        ("支付申请状态", detail["request_state"]),
        ("已申请金额", detail["requested_amount_text"]),
        ("未申请金额", detail["unrequested_amount_text"]),
        ("合同编号", detail["contract_no"]),
    ]
    return "\n".join(("%s：%s" % (label, value)) if label else value for label, value in parts if value)


def legacy_fact_type(label: str) -> str:
    if label == "分包结算单":
        return "direct_acceptance_subcontract_settlement_expense_settlement"
    return LEGACY_FACT_TYPE_PREFIX + ":" + label


def expense_category(name: str):
    category = env["sc.dictionary"].sudo().search(  # noqa: F821
        [("type", "=", "expense_contract_category"), ("name", "=", name)],
        limit=1,
    )
    if category:
        return category
    aliases = {
        "分包": ["专业分包", "分包"],
        "材料": ["材料"],
        "劳务": ["劳务"],
        "机械": ["机械"],
        "租赁": ["租赁"],
    }
    category = env["sc.dictionary"].sudo().search(  # noqa: F821
        [("type", "=", "expense_contract_category"), ("name", "in", aliases.get(name, [name]))],
        limit=1,
    )
    if not category:
        raise RuntimeError({"missing_expense_contract_category": name})
    return category


def settlement_values(fact, cfg: dict):
    payload = payload_of(fact)
    project = resolve_project(fact, payload, cfg)
    partner = resolve_partner(fact, payload, cfg)
    state_text = visible(fact, cfg.get("state")) or first_text(payload, "DJZTText", "DJZT")
    document_no = visible(fact, cfg.get("document_no")) or text(fact.document_no) or text(fact.legacy_record_id)
    note = visible(fact, cfg.get("note"))
    title = visible(fact, cfg.get("title")) or text(fact.document_title) or note or document_no or cfg["category"]
    amount = money(visible(fact, cfg.get("amount")) or fact.amount_total)
    contract_no = visible(fact, cfg.get("contract_no")) or first_text(payload, "HTBH", "ContractNo")
    settlement_date = parse_date(visible(fact, cfg.get("date"))) or parse_date(fact.created_time)
    created_at = parse_datetime(visible(fact, cfg.get("created_at"))) or parse_datetime(fact.created_time)
    creator = visible(fact, cfg.get("creator")) or text(fact.creator_name) or first_text(payload, "LRR", "f_LRR")
    write_partner = cfg.get("write_partner", True)
    contract_partner = partner if write_partner else False
    contract = resolve_contract(project, contract_partner, contract_no)
    category = expense_category(cfg["category"])
    detail = {
        "payment_state": visible(fact, cfg.get("payment_state")),
        "paid_amount_text": visible(fact, cfg.get("paid")),
        "unpaid_amount_text": visible(fact, cfg.get("unpaid")),
        "request_state": visible(fact, cfg.get("request_state")),
        "requested_amount_text": visible(fact, cfg.get("requested")),
        "unrequested_amount_text": visible(fact, cfg.get("unrequested")),
        "contract_no": contract_no,
        "settlement_note": note,
    }
    state = state_from_document_state(state_text)
    vals = {
        "name": document_no or "%s-%s" % (cfg["category"], fact.id),
        "project_id": project.id,
        "contract_id": contract.id if contract else False,
        "partner_id": partner.id if write_partner else False,
        "settlement_unit_id": partner.id,
        "legacy_counterparty_name": visible(fact, cfg.get("partner")) if write_partner else False,
        "title": title,
        "document_date": settlement_date,
        "settlement_type": "out",
        "settlement_category_id": category.id,
        "legacy_settlement_category": cfg["category"],
        "settlement_stage": "declared",
        "date_settlement": settlement_date,
        "approved_date": settlement_date if state == "approve" else False,
        "final_approved_date": settlement_date if state == "approve" else False,
        "settlement_amount": amount,
        "submitted_amount": amount,
        "approved_amount": amount,
        "requested_fund_amount": money(detail["requested_amount_text"]),
        "legacy_document_state": state_text,
        "legacy_contract_no": contract_no or False,
        "legacy_payment_state": detail["payment_state"],
        "legacy_paid_amount": money(detail["paid_amount_text"]),
        "legacy_unpaid_amount": money(detail["unpaid_amount_text"]),
        "legacy_payment_request_state": detail["request_state"],
        "legacy_unrequested_amount": money(detail["unrequested_amount_text"]),
        "state": state,
        "source_created_by": creator or False,
        "source_created_at": created_at,
        "entry_data": cfg["entry_data"],
        "legacy_acceptance_label": fact.acceptance_label,
        "settlement_description": description_text(detail),
        "legacy_visible_attachment": attachment_display(fact, payload, cfg) or False,
        "note": False,
        "legacy_fact_model": SOURCE_MODEL,
        "legacy_fact_id": fact.id,
        "legacy_fact_type": legacy_fact_type(fact.acceptance_label),
    }
    for index in range(1, 61):
        field = "legacy_visible_%02d" % index
        if field in env[TARGET_MODEL]._fields:  # noqa: F821
            vals[field] = visible(fact, "%02d" % index) or False
    return {key: value for key, value in vals.items() if value not in ("", None)}, detail, amount


def line_values(settlement, amount: float) -> dict:
    return {
        "settlement_id": settlement.id,
        "contract_id": settlement.contract_id.id if settlement.contract_id else False,
        "name": settlement.title or settlement.name,
        "qty": 1.0 if amount else 0.0,
        "price_unit": amount,
    }


def write_label(label: str, cfg: dict) -> dict:
    Fact = env[SOURCE_MODEL].sudo().with_context(active_test=False)  # noqa: F821
    Settlement = env[TARGET_MODEL].sudo().with_context(active_test=False, legacy_migration_allow_missing_contract=True)  # noqa: F821
    Line = env["sc.settlement.order.line"].sudo().with_context(legacy_migration_allow_missing_contract=True)  # noqa: F821
    category = expense_category(cfg["category"])
    facts = Fact.search(
        [("source_system", "=", SOURCE_SYSTEM), ("acceptance_label", "=", label), ("active", "=", True)],
        order="legacy_record_id,id",
    )
    type_value = legacy_fact_type(label)
    stale = Settlement.search(
        [("legacy_fact_model", "=", SOURCE_MODEL), ("legacy_fact_type", "=", type_value), ("legacy_fact_id", "not in", facts.ids or [-1])]
    )
    stale_removed = len(stale)
    if stale:
        stale.unlink()

    created = updated = line_created = line_updated = 0
    sample = []
    for fact in facts:
        vals, detail, amount = settlement_values(fact, cfg)
        settlement = Settlement.search([("legacy_fact_model", "=", SOURCE_MODEL), ("legacy_fact_id", "=", fact.id)], limit=1)
        if settlement:
            settlement.write(vals)
            updated += 1
            action = "updated"
        else:
            settlement = Settlement.create(vals)
            created += 1
            action = "created"
        line = settlement.line_ids[:1]
        vals_line = line_values(settlement, amount)
        if line:
            line.with_context(allow_contract_change=True, legacy_migration_allow_missing_contract=True).write(vals_line)
            line_updated += 1
        else:
            Line.create(vals_line)
            line_created += 1
        if len(sample) < 10:
            sample.append(
                {
                    "action": action,
                    "fact_id": fact.id,
                    "legacy_record_id": fact.legacy_record_id,
                    "settlement_id": settlement.id,
                    "name": settlement.name,
                    "title": settlement.title,
                    "project": settlement.project_id.display_name,
                    "partner": settlement.partner_id.display_name,
                    "category": settlement.settlement_category_display,
                    "amount": settlement.amount_total,
                    "payment_state": settlement.legacy_payment_state,
                    "payment_request_state": settlement.legacy_payment_request_state,
                    "attachment": settlement.legacy_visible_attachment,
                    "source_created_by": settlement.source_created_by,
                    "source_created_at": str(settlement.source_created_at or ""),
                    "detail": detail,
                }
            )
    env.cr.commit()  # noqa: F821

    domain = [("legacy_fact_model", "=", SOURCE_MODEL), ("legacy_fact_type", "=", type_value)]
    source_contract_no_count = sum(1 for fact in facts if visible(fact, cfg.get("contract_no")))
    if not cfg.get("contract_no"):
        Settlement.search(domain + [("legacy_contract_no", "!=", False)]).write({"legacy_contract_no": False})
        env.cr.commit()  # noqa: F821
    result = {
        "label": label,
        "category": cfg["category"],
        "source_count": len(facts),
        "projected_count": Settlement.search_count(domain),
        "visible_in_expense_settlement_count": Settlement.search_count([("settlement_type", "=", "out")] + domain),
        "direct_operation_count": Settlement.search_count(domain + [("operation_strategy", "=", "direct")]),
        "category_count": Settlement.search_count(domain + [("settlement_category_id", "=", category.id)]),
        "document_state_count": Settlement.search_count(domain + [("legacy_document_state", "!=", False)]),
        "payment_state_count": Settlement.search_count(domain + [("legacy_payment_state", "!=", False)]),
        "payment_request_state_count": Settlement.search_count(domain + [("legacy_payment_request_state", "!=", False)]),
        "contract_no_source_count": source_contract_no_count,
        "contract_no_count": Settlement.search_count(domain + [("legacy_contract_no", "!=", False)]),
        "amount_nonzero_count": Settlement.search_count(domain + [("amount_total", "!=", 0)]),
        "paid_amount_nonzero_count": Settlement.search_count(domain + [("legacy_paid_amount", "!=", 0)]),
        "unpaid_amount_nonzero_count": Settlement.search_count(domain + [("legacy_unpaid_amount", "!=", 0)]),
        "unrequested_amount_nonzero_count": Settlement.search_count(domain + [("legacy_unrequested_amount", "!=", 0)]),
        "attachment_display_count": Settlement.search_count(domain + [("legacy_visible_attachment", "!=", False)]),
        "creator_count": Settlement.search_count(domain + [("source_created_by", "!=", False)]),
        "created_settlements": created,
        "updated_settlements": updated,
        "created_lines": line_created,
        "updated_lines": line_updated,
        "removed_stale_settlements": stale_removed,
        "sample": sample,
    }
    result["status"] = (
        "PASS"
        if result["projected_count"] == len(facts)
        and result["visible_in_expense_settlement_count"] == len(facts)
        and result["direct_operation_count"] == len(facts)
        and result["category_count"] == len(facts)
        and result["document_state_count"] == len(facts)
        and result["payment_state_count"] == len(facts)
        and result["payment_request_state_count"] == len(facts)
        and result["contract_no_count"] == source_contract_no_count
        else "FAIL"
    )
    return result


def main() -> None:
    ensure_allowed_db()
    results = [write_label(label, cfg) for label, cfg in CONFIGS.items()]
    final = {
        "status": "PASS" if all(item["status"] == "PASS" for item in results) else "FAIL",
        "mode": "direct_acceptance_expense_settlements_write",
        "db": env.cr.dbname,  # noqa: F821
        "source_system": SOURCE_SYSTEM,
        "target_model": TARGET_MODEL,
        "results": results,
    }
    OUTPUT_JSON.write_text(json.dumps(final, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("DIRECT_ACCEPTANCE_EXPENSE_SETTLEMENTS_WRITE=" + json.dumps(final, ensure_ascii=False, sort_keys=True))
    if final["status"] != "PASS":
        raise RuntimeError(final)


main()
