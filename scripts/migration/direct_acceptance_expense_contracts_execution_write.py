# -*- coding: utf-8 -*-
"""Project accepted direct-project expense contracts into formal expense execution."""

from __future__ import annotations

import json
import os
import re
import zlib
from datetime import datetime
from pathlib import Path


SOURCE_SYSTEM = "online_old_scbsly"
SOURCE_MODEL = "sc.legacy.direct.acceptance.fact"
TARGET_MODEL = "construction.contract"
WRAPPER_MODEL = "construction.contract.expense"
LEGACY_ID_PREFIX = "direct_acceptance:expense_contract:"
MIGRATION_MARKER = "[migration:direct_acceptance_expense_contracts_execution]"
AMOUNT_LINE_NOTE = MIGRATION_MARKER + " amount_line"

CONFIGS = {
    "分包合同": {
        "category": "分包",
        "state": "01",
        "document_no": "02",
        "date": "03",
        "title": "04",
        "partner": "05",
        "content": "06",
        "amount": "08",
        "contract_no": "09",
        "invoice_amount": "10",
        "paid_amount": "11",
        "unpaid_amount": "12",
        "uninvoiced_amount": "13",
        "project": "14",
        "note": "15",
        "attachment": "16",
        "creator": "17",
        "created_at": "18",
    },
    "租赁合同": {
        "category": "租赁",
        "state": "01",
        "document_no": "02",
        "contract_no": "03",
        "project": "04",
        "title": "05",
        "partner": "06",
        "content": "07",
        "invoice_amount": "09",
        "paid_amount": "10",
        "unpaid_amount": "11",
        "uninvoiced_amount": "12",
        "amount": "13",
        "date": "14",
        "handler": "15",
        "tax_rate": "16",
        "tax_type": "17",
        "note": "18",
        "attachment": "19",
        "creator": "20",
        "created_at": "21",
    },
    "供货合同": {
        "category": "材料",
        "state": "01",
        "contract_no": "02",
        "document_no": "02",
        "title": "03",
        "partner": "04",
        "project": "05",
        "amount": "06",
        "invoice_amount": "07",
        "paid_amount": "08",
        "unpaid_amount": "09",
        "uninvoiced_amount": "10",
        "created_at": "12",
        "tax_rate": "13",
        "creator": "14",
        "attachment": "15",
    },
    "劳务合同": {
        "category": "劳务",
        "state": "01",
        "document_no": "02",
        "project": "03",
        "date": "04",
        "title": "05",
        "partner": "06",
        "amount": "08",
        "invoice_amount": "10",
        "paid_amount": "11",
        "unpaid_amount": "12",
        "uninvoiced_amount": "13",
        "pricing_method": "14",
        "work_part": "15",
        "contract_no": "16",
        "attachment": "17",
        "creator": "18",
        "payment_terms": "19",
        "push_project": "20",
    },
    "机械合同（合同）": {
        "category": "机械",
        "state": "01",
        "project": "02",
        "partner": "03",
        "contract_no": "04",
        "content": "05",
        "pricing_method": "06",
        "duration": "07",
        "payment_terms": "08",
        "amount": "09",
        "handler": "14",
        "date": "11",
        "note": "13",
        "document_no": "18",
        "title": "29",
        "tax_rate": "39",
        "attachment": "51",
        "creator": "52",
        "created_at": "53",
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


OUTPUT_JSON = artifact_root() / "direct_acceptance_expense_contracts_execution_write_result_v1.json"


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
    return "" if cleaned.lower() in {"false", "none", "null"} else cleaned


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
            return datetime.strptime(raw[:size], fmt).strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue
    return None


def legacy_contract_id(label: str, fact) -> str:
    token = text(fact.legacy_record_id) or str(fact.id)
    return LEGACY_ID_PREFIX + label + ":" + token


def ensure_direct_project(project):
    if project and "operation_strategy" in project._fields and project.operation_strategy != "direct":
        project.sudo().write({"operation_strategy": "direct"})
    return project


def resolve_project(fact, payload: dict, cfg: dict):
    Project = env["project.project"].sudo().with_context(active_test=False)  # noqa: F821
    if fact.project_id:
        return ensure_direct_project(fact.project_id)
    legacy_project_id = text(fact.project_legacy_id) or first_text(payload, "XMID", "SJBXXMID", "f_XMID")
    if legacy_project_id and "legacy_project_id" in Project._fields:
        project = Project.search([("legacy_project_id", "=", legacy_project_id)], limit=1)
        if project:
            return ensure_direct_project(project)
    project_name = visible(fact, cfg.get("project")) or text(fact.project_name) or first_text(payload, "XMMC", "ProjectName", "TSXMMC", "f_GCMC")
    if not project_name:
        project_name = "直营项目支出合同未匹配项目"
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
    name = visible(fact, cfg.get("partner")) or text(fact.partner_name) or first_text(payload, "GYDW", "JSDW", "FBDW", "f_GYSName", "f_BZZ", "SGDWMC")
    if not name:
        name = "直营项目支出合同未匹配相对方"
    partner = Partner.search([("name", "=", name)], order="id", limit=1)
    if partner:
        return partner
    vals = {"name": name, "company_type": "company"}
    if "is_company" in Partner._fields:
        vals["is_company"] = True
    if "supplier_rank" in Partner._fields:
        vals["supplier_rank"] = 1
    if "legacy_partner_id" in Partner._fields:
        vals["legacy_partner_id"] = "direct_acceptance_expense_contract:" + name
    if "legacy_partner_source" in Partner._fields:
        vals["legacy_partner_source"] = "direct_acceptance_expense_contract"
    return Partner.create(vals)


def category_for(name: str):
    Dictionary = env["sc.dictionary"].sudo()  # noqa: F821
    category = Dictionary.search([("type", "=", "expense_contract_category"), ("name", "=", name)], limit=1)
    if category:
        return category
    aliases = {
        "材料": ["材料", "材料采购", "供货"],
        "分包": ["分包", "专业分包"],
        "租赁": ["租赁", "机械租赁", "周转材料租赁"],
        "劳务": ["劳务"],
        "机械": ["机械"],
    }
    return Dictionary.search([("type", "=", "expense_contract_category"), ("name", "in", aliases.get(name, [name]))], limit=1)


def execution_title(title: str) -> str:
    return title.replace("结算", "办理") if "结算" in title else title


def contract_values(label: str, fact, cfg: dict, category):
    payload = payload_of(fact)
    project = resolve_project(fact, payload, cfg)
    partner = resolve_partner(fact, payload, cfg)
    doc_no = visible(fact, cfg.get("document_no")) or text(fact.document_no) or text(fact.legacy_record_id) or "%s-%s" % (label, fact.id)
    contract_no = visible(fact, cfg.get("contract_no")) or first_text(payload, "HTBH", "f_HTBH", "ContractNo")
    title = visible(fact, cfg.get("title")) or text(fact.document_title) or doc_no
    content = visible(fact, cfg.get("content")) or visible(fact, cfg.get("payment_terms")) or visible(fact, cfg.get("work_part")) or visible(fact, cfg.get("note"))
    amount_total = money(visible(fact, cfg.get("amount")) or fact.amount_total)
    invoice_amount = money(visible(fact, cfg.get("invoice_amount")))
    paid_amount = money(visible(fact, cfg.get("paid_amount")))
    unpaid_amount = money(visible(fact, cfg.get("unpaid_amount")))
    uninvoiced_amount = money(visible(fact, cfg.get("uninvoiced_amount")))
    created_at = parse_datetime(visible(fact, cfg.get("created_at"))) or parse_datetime(fact.created_time)
    attachment = visible(fact, cfg.get("attachment")) or text(fact.attachment_ref)
    raw_ref = text(fact.attachment_ref) or first_text(payload, "f_FJ", "FJ")
    attachment_text = attachment
    if raw_ref and raw_ref not in attachment_text:
        attachment_text = (attachment_text + "\n" if attachment_text else "") + "legacy-file-id://" + raw_ref
    state_text = visible(fact, cfg.get("state")) or text(fact.document_state)
    subject = execution_title(title)
    vals = {
        "legacy_acceptance_label": label,
        "legacy_contract_id": legacy_contract_id(label, fact),
        "legacy_project_id": text(fact.project_legacy_id) or first_text(payload, "XMID", "SJBXXMID", "f_XMID"),
        "legacy_contract_no": contract_no,
        "legacy_document_no": doc_no,
        "legacy_external_contract_no": doc_no,
        "legacy_status": state_text,
        "legacy_counterparty_text": partner.display_name,
        "legacy_contract_amount_source": SOURCE_MODEL + "." + label,
        "legacy_contract_amount": amount_total,
        "visible_contract_amount": amount_total,
        "amount_untaxed": amount_total,
        "amount_tax": 0.0,
        "amount_total": amount_total,
        "line_amount_total": amount_total,
        "amount_change": 0.0,
        "amount_final": amount_total,
        "visible_invoice_amount": invoice_amount,
        "visible_received_amount": paid_amount,
        "visible_unreceived_amount": unpaid_amount,
        "visible_invoice_amount_source": SOURCE_MODEL + "." + label,
        "visible_received_amount_source": SOURCE_MODEL + "." + label,
        "visible_unreceived_amount_source": SOURCE_MODEL + "." + label,
        "legacy_visible_document_state": state_text,
        "legacy_visible_document_no": doc_no,
        "legacy_visible_contract_date": parse_date(visible(fact, cfg.get("date"))),
        "legacy_visible_counterparty": partner.display_name,
        "legacy_visible_project_name": visible(fact, cfg.get("project")) or text(fact.project_name),
        "legacy_visible_title": subject,
        "legacy_visible_category": cfg["category"],
        "legacy_visible_contract_no": contract_no,
        "legacy_visible_amount": visible(fact, cfg.get("amount")),
        "legacy_visible_settlement_amount": False,
        "legacy_visible_invoice_amount": visible(fact, cfg.get("invoice_amount")),
        "legacy_visible_received_amount": visible(fact, cfg.get("paid_amount")),
        "legacy_visible_unreceived_amount": visible(fact, cfg.get("unpaid_amount")),
        "legacy_visible_invoice_unreceived_amount": visible(fact, cfg.get("uninvoiced_amount")),
        "legacy_visible_engineering_content": content,
        "legacy_visible_creator_name": visible(fact, cfg.get("creator")) or text(fact.creator_name),
        "legacy_visible_created_time": created_at,
        "legacy_visible_attachment": attachment,
        "subject": subject,
        "type": "in",
        "state": "confirmed",
        "active": True,
        "project_id": project.id,
        "partner_id": partner.id,
        "date_contract": parse_date(visible(fact, cfg.get("date"))),
        "engineering_content": content,
        "contract_payment_method_text": visible(fact, cfg.get("payment_terms")) or visible(fact, cfg.get("pricing_method")),
        "contract_duration_text": visible(fact, cfg.get("duration")),
        "entry_user_text": visible(fact, cfg.get("creator")) or text(fact.creator_name),
        "entry_time": created_at,
        "attachment_text": attachment_text,
        "note": "\n".join(
            item
            for item in [
                MIGRATION_MARKER,
                "acceptance_label=%s" % label,
                "source_fact_id=%s" % fact.id,
                "legacy_record_id=%s" % text(fact.legacy_record_id),
                "source_title=%s" % title,
                "tax_rate=%s" % visible(fact, cfg.get("tax_rate")),
                "uninvoiced_amount=%s" % uninvoiced_amount,
            ]
            if item.split("=", 1)[-1]
        ),
    }
    for index in range(1, 61):
        visible_value = text(getattr(fact, "legacy_visible_%02d" % index, ""))
        if visible_value:
            vals["legacy_visible_%02d" % index] = visible_value
    if category:
        vals["expense_contract_category_id"] = category.id
    return {key: value for key, value in vals.items() if value not in ("", None)}


def sync_amount_line(contract, amount_total: float) -> str:
    Line = env["construction.contract.line"].sudo()  # noqa: F821
    existing = contract.line_ids.filtered(lambda line: (line.note or "") == AMOUNT_LINE_NOTE)
    vals = {
        "contract_id": contract.id,
        "project_id": contract.project_id.id,
        "currency_id": contract.currency_id.id,
        "sequence": 10,
        "qty_contract": 0.0 if not amount_total else 1.0,
        "price_contract": amount_total,
        "amount_contract": amount_total,
        "amount_contract_leaf": amount_total,
        "boq_amount_leaf": 0.0,
        "delta_amount": amount_total,
        "boq_amount_source": "none",
        "note": AMOUNT_LINE_NOTE,
        "active": True,
    }
    if existing:
        existing[:1].write(vals)
        return "line_updated"
    Line.create(vals)
    return "line_created"


def ensure_wrapper(contract) -> tuple[object, bool]:
    Wrapper = env[WRAPPER_MODEL].sudo()  # noqa: F821
    wrapper = Wrapper.search([("contract_id", "=", contract.id)], limit=1)
    if wrapper:
        return wrapper, False
    return Wrapper.create({"contract_id": contract.id}), True


def main() -> None:
    ensure_allowed_db()
    Fact = env[SOURCE_MODEL].sudo().with_context(active_test=False)  # noqa: F821
    Contract = env[TARGET_MODEL].sudo().with_context(skip_validation_check=True, active_test=False)  # noqa: F821
    tax = Contract._get_default_tax("in")
    results = []
    total_created = total_updated = total_wrappers = total_line_created = total_line_updated = 0
    for label, cfg in CONFIGS.items():
        facts = Fact.search(
            [("source_system", "=", SOURCE_SYSTEM), ("acceptance_label", "=", label), ("active", "=", True)],
            order="legacy_record_id,id",
        )
        category = category_for(cfg["category"])
        if not category:
            raise RuntimeError({"missing_expense_contract_category": cfg["category"], "label": label})
        created = updated = wrappers = line_created = line_updated = 0
        seen = set()
        samples = []
        for fact in facts:
            identity = legacy_contract_id(label, fact)
            if identity in seen:
                continue
            seen.add(identity)
            vals = contract_values(label, fact, cfg, category)
            if tax:
                vals["tax_id"] = tax.id
            contract = Contract.search([("legacy_contract_id", "=", identity)], limit=1)
            if contract:
                contract.write(vals)
                updated += 1
                action = "updated"
            else:
                contract = Contract.create(vals)
                created += 1
                action = "created"
            line_action = sync_amount_line(contract, vals.get("legacy_contract_amount") or 0.0)
            if line_action == "line_created":
                line_created += 1
            else:
                line_updated += 1
            wrapper, wrapper_created = ensure_wrapper(contract)
            wrapper_vals = {"legacy_acceptance_label": label}
            for index in range(1, 61):
                value = text(getattr(contract, "legacy_visible_%02d" % index, ""))
                if value:
                    wrapper_vals["legacy_visible_%02d" % index] = value
            wrapper.write(wrapper_vals)
            wrappers += 1 if wrapper_created else 0
            if len(samples) < 5:
                samples.append(
                    {
                        "action": action,
                        "fact_id": fact.id,
                        "contract_id": contract.id,
                        "expense_id": wrapper.id,
                        "document_no": contract.legacy_visible_document_no,
                        "title": contract.legacy_visible_title,
                        "project": contract.project_id.display_name,
                        "partner": contract.partner_id.display_name,
                    }
                )
        total_created += created
        total_updated += updated
        total_wrappers += wrappers
        total_line_created += line_created
        total_line_updated += line_updated
        prefix = LEGACY_ID_PREFIX + label + ":%"
        projected = Contract.search_count([("legacy_contract_id", "ilike", prefix)])
        visible = env[WRAPPER_MODEL].sudo().search_count(  # noqa: F821
            [
                ("legacy_contract_id", "ilike", prefix),
                ("state", "in", ["confirmed", "running"]),
                ("legacy_visible_title", "not ilike", "结算"),
                ("subject", "not ilike", "结算"),
            ]
        )
        results.append(
            {
                "label": label,
                "source_count": len(facts),
                "unique_count": len(seen),
                "projected_count": projected,
                "expense_execution_visible_count": visible,
                "created_contracts": created,
                "updated_contracts": updated,
                "line_created": line_created,
                "line_updated": line_updated,
                "expense_wrappers_created": wrappers,
                "sample": samples,
                "status": "PASS" if projected == len(seen) and visible == len(seen) else "FAIL",
            }
        )
    env.cr.commit()  # noqa: F821
    result = {
        "status": "PASS" if all(item["status"] == "PASS" for item in results) else "FAIL",
        "mode": "direct_acceptance_expense_contracts_execution_write",
        "db": env.cr.dbname,  # noqa: F821
        "source_system": SOURCE_SYSTEM,
        "target_model": TARGET_MODEL,
        "wrapper_model": WRAPPER_MODEL,
        "created_contracts": total_created,
        "updated_contracts": total_updated,
        "line_created": total_line_created,
        "line_updated": total_line_updated,
        "expense_wrappers_created": total_wrappers,
        "results": results,
    }
    OUTPUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("DIRECT_ACCEPTANCE_EXPENSE_CONTRACTS_EXECUTION_WRITE=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
    if result["status"] != "PASS":
        raise RuntimeError(result)


main()
