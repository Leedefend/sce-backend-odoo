# -*- coding: utf-8 -*-
"""Project accepted direct-project subcontract contracts into formal expense execution."""

from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path


SOURCE_SYSTEM = "online_old_scbsly"
SOURCE_MODEL = "sc.legacy.direct.acceptance.fact"
ACCEPTANCE_LABEL = "分包合同"
TARGET_MODEL = "construction.contract"
TARGET_WRAPPER_MODEL = "construction.contract.expense"
LEGACY_ID_PREFIX = "direct_acceptance:subcontract_contract:"
MIGRATION_MARKER = "[migration:direct_acceptance_subcontract_contract_to_expense_execution]"
AMOUNT_LINE_NOTE = MIGRATION_MARKER + " amount_line"


def artifact_root() -> Path:
    root = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", "artifacts/migration"))
    try:
        root.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        root = Path("/tmp/sce-migration-artifacts")
        root.mkdir(parents=True, exist_ok=True)
    return root


OUTPUT_JSON = artifact_root() / "direct_acceptance_subcontract_contract_expense_execution_write_result_v1.json"


def ensure_allowed_db() -> None:
    allowlist = {
        item.strip()
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_demo,sc_prod_sim").split(",")
        if item.strip()
    }
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_projection": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def text(value) -> str:
    return str(value or "").replace("\r\n", "\n").replace("\r", "\n").strip()


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


def parse_amount(value) -> float:
    raw = text(value).replace(",", "").replace("￥", "").replace("¥", "")
    if not raw:
        return 0.0
    try:
        return float(raw)
    except ValueError:
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


def legacy_contract_id(fact) -> str:
    return LEGACY_ID_PREFIX + text(fact.legacy_record_id)


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
    project_name = text(fact.legacy_visible_14) or text(fact.legacy_visible_19) or text(fact.project_name)
    if not project_name:
        project_name = "直营项目分包合同未匹配项目"
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
    name = text(fact.legacy_visible_05) or first_text(payload, "f_FBDW", "FBDW", "SubcontractorName") or text(fact.partner_name)
    if not name:
        name = "直营项目分包合同未匹配分包单位"
    partner = Partner.search([("name", "=", name)], order="id", limit=1)
    if partner:
        return partner
    vals = {"name": name, "company_type": "company"}
    if "is_company" in Partner._fields:
        vals["is_company"] = True
    if "supplier_rank" in Partner._fields:
        vals["supplier_rank"] = 1
    if "legacy_partner_id" in Partner._fields:
        vals["legacy_partner_id"] = "direct_acceptance_subcontract:" + name
    if "legacy_partner_source" in Partner._fields:
        vals["legacy_partner_source"] = "direct_acceptance_subcontract_contract"
    if "legacy_source_evidence" in Partner._fields:
        vals["legacy_source_evidence"] = SOURCE_MODEL + ":" + name
    return Partner.create(vals)


def subcontract_category():
    category = env.ref("smart_construction_core.dict_expense_contract_category_subcontract", raise_if_not_found=False)  # noqa: F821
    if category:
        return category
    return env["sc.dictionary"].sudo().search(  # noqa: F821
        [("type", "=", "expense_contract_category"), ("code", "=", "subcontract")],
        limit=1,
    )


def execution_title(title: str) -> str:
    return title.replace("结算", "办理") if "结算" in title else title


def attachment_display_and_ref(fact, payload: dict) -> tuple[str, str]:
    visible_attachment = text(fact.legacy_visible_16)
    raw_ref = text(fact.attachment_ref) or first_text(payload, "f_FJ", "FJ")
    if raw_ref and not raw_ref.startswith("附件("):
        return visible_attachment, raw_ref
    return visible_attachment or raw_ref, ""


def contract_values(fact, category):
    payload = payload_of(fact)
    project = resolve_project(fact, payload)
    partner = resolve_partner(fact, payload)
    visible_state = text(fact.legacy_visible_01)
    visible_document_no = text(fact.legacy_visible_02)
    visible_contract_date = text(fact.legacy_visible_03)
    visible_title = text(fact.legacy_visible_04)
    visible_subcontractor = text(fact.legacy_visible_05)
    visible_content = text(fact.legacy_visible_06)
    visible_quantity = text(fact.legacy_visible_07)
    visible_amount = text(fact.legacy_visible_08)
    visible_contract_no = text(fact.legacy_visible_09)
    visible_invoice_amount = text(fact.legacy_visible_10)
    visible_paid_amount = text(fact.legacy_visible_11)
    visible_unpaid_amount = text(fact.legacy_visible_12)
    visible_uninvoiced_amount = text(fact.legacy_visible_13)
    visible_project_name = text(fact.legacy_visible_14)
    visible_note = text(fact.legacy_visible_15)
    visible_attachment, attachment_ref = attachment_display_and_ref(fact, payload)
    visible_creator = text(fact.legacy_visible_17) or text(fact.creator_name) or first_text(payload, "f_LRR", "LRR", "XGR")
    visible_created_time = text(fact.legacy_visible_18) or str(fact.created_time or "") or first_text(payload, "LRSJ", "f_LRSJ", "XGSJ")
    visible_push_project = text(fact.legacy_visible_19)
    attachment_text = visible_attachment
    if attachment_ref:
        attachment_text = (attachment_text + "\n" if attachment_text else "") + "legacy-file-id://" + attachment_ref
    amount_total = parse_amount(visible_amount or text(fact.amount_total))
    paid_amount = parse_amount(visible_paid_amount)
    unpaid_amount = parse_amount(visible_unpaid_amount)
    accepted_title = visible_title or text(fact.document_title) or visible_document_no or text(fact.legacy_record_id)
    content_text = visible_content or accepted_title
    subject = execution_title(accepted_title)
    vals = {
        "legacy_contract_id": legacy_contract_id(fact),
        "legacy_project_id": text(fact.project_legacy_id) or first_text(payload, "XMID", "SJBXXMID"),
        "legacy_contract_no": visible_contract_no,
        "legacy_document_no": visible_document_no or text(fact.document_no),
        "legacy_external_contract_no": visible_document_no or text(fact.document_no),
        "legacy_status": visible_state or first_text(payload, "DJZT", "DJZTText"),
        "legacy_counterparty_text": visible_subcontractor,
        "legacy_deleted_flag": first_text(payload, "DELFLAG", "Deleted"),
        "legacy_contract_amount_source": SOURCE_MODEL + ".legacy_visible_08",
        "legacy_contract_amount": amount_total,
        "visible_contract_amount": amount_total,
        "amount_untaxed": amount_total,
        "amount_tax": 0.0,
        "amount_total": amount_total,
        "line_amount_total": amount_total,
        "amount_change": 0.0,
        "amount_final": amount_total,
        "legacy_visible_document_state": visible_state,
        "legacy_visible_document_no": visible_document_no,
        "legacy_visible_counterparty": visible_subcontractor,
        "legacy_visible_project_name": visible_project_name,
        "legacy_visible_title": execution_title(visible_title) if visible_title else subject,
        "legacy_visible_category": "专业分包",
        "legacy_visible_contract_no": visible_contract_no,
        "legacy_visible_contract_date": parse_date(visible_contract_date),
        "legacy_visible_amount": visible_amount,
        "legacy_visible_invoice_amount": visible_invoice_amount,
        "legacy_visible_invoice_unreceived_amount": visible_uninvoiced_amount,
        "legacy_visible_received_amount": visible_paid_amount,
        "legacy_visible_unreceived_amount": visible_unpaid_amount,
        "legacy_visible_engineering_content": content_text,
        "legacy_visible_creator_name": visible_creator,
        "legacy_visible_created_time": parse_datetime(visible_created_time),
        "legacy_visible_attachment": visible_attachment,
        "visible_invoice_amount": parse_amount(visible_invoice_amount),
        "visible_received_amount": paid_amount,
        "visible_unreceived_amount": unpaid_amount,
        "visible_invoice_amount_source": SOURCE_MODEL + ".legacy_visible_10",
        "visible_received_amount_source": SOURCE_MODEL + ".legacy_visible_11",
        "visible_unreceived_amount_source": SOURCE_MODEL + ".legacy_visible_12",
        "subject": subject,
        "type": "in",
        "state": "confirmed",
        "active": True,
        "project_id": project.id,
        "partner_id": partner.id,
        "date_contract": parse_date(visible_contract_date),
        "engineering_content": content_text,
        "entry_user_text": visible_creator,
        "entry_time": parse_datetime(visible_created_time),
        "attachment_text": attachment_text,
        "note": visible_note or False,
    }
    if category:
        vals["expense_contract_category_id"] = category.id
    if visible_push_project:
        vals["legacy_visible_contractor"] = visible_push_project
    if visible_quantity:
        vals["contract_duration_text"] = "总数量：" + visible_quantity
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


def ensure_expense_wrapper(contract) -> tuple[object, str]:
    Expense = env[TARGET_WRAPPER_MODEL].sudo()  # noqa: F821
    wrapper = Expense.search([("contract_id", "=", contract.id)], limit=1)
    if wrapper:
        return wrapper, ""
    return Expense.create({"contract_id": contract.id}), "expense_wrapper_created"


def copy_source_attachments(fact, contract, wrapper) -> tuple[int, int]:
    Attachment = env["ir.attachment"].sudo()  # noqa: F821
    source = Attachment.search([("res_model", "=", SOURCE_MODEL), ("res_id", "=", fact.id)])
    contract_created = wrapper_created = 0
    for attachment in source:
        description = f"{MIGRATION_MARKER} source_model={SOURCE_MODEL}; source_id={fact.id}; source_attachment_id={attachment.id}"
        if not Attachment.search([("res_model", "=", TARGET_MODEL), ("description", "ilike", f"%source_attachment_id={attachment.id}%")], limit=1):
            attachment.copy({"res_model": TARGET_MODEL, "res_id": contract.id, "description": description})
            contract_created += 1
        if not Attachment.search([("res_model", "=", TARGET_WRAPPER_MODEL), ("description", "ilike", f"%source_attachment_id={attachment.id}%")], limit=1):
            attachment.copy({"res_model": TARGET_WRAPPER_MODEL, "res_id": wrapper.id, "description": description})
            wrapper_created += 1
    return contract_created, wrapper_created


def main() -> None:
    ensure_allowed_db()
    Fact = env[SOURCE_MODEL].sudo().with_context(active_test=False)  # noqa: F821
    Contract = env[TARGET_MODEL].sudo().with_context(skip_validation_check=True, active_test=False)  # noqa: F821
    facts = Fact.search(
        [
            ("source_system", "=", SOURCE_SYSTEM),
            ("acceptance_label", "=", ACCEPTANCE_LABEL),
            ("active", "=", True),
        ],
        order="legacy_record_id,id",
    )
    tax = Contract._get_default_tax("in")
    category = subcontract_category()
    if not category:
        raise RuntimeError({"missing_expense_contract_subcontract_category": True})
    created = updated = line_created = line_updated = wrappers = 0
    copied_contract_attachments = copied_wrapper_attachments = 0
    seen = set()
    skipped_duplicates = []
    detail = []
    for fact in facts:
        identity = legacy_contract_id(fact)
        if identity in seen:
            skipped_duplicates.append(identity)
            continue
        seen.add(identity)
        vals = contract_values(fact, category)
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
        amount_action = sync_amount_line(contract, vals.get("legacy_contract_amount") or 0.0)
        if amount_action == "line_created":
            line_created += 1
        elif amount_action == "line_updated":
            line_updated += 1
        wrapper, wrapper_action = ensure_expense_wrapper(contract)
        if wrapper_action:
            wrappers += 1
        c_att, w_att = copy_source_attachments(fact, contract, wrapper)
        copied_contract_attachments += c_att
        copied_wrapper_attachments += w_att
        detail.append(
            {
                "action": "+".join(item for item in (action, amount_action, wrapper_action) if item),
                "fact_id": fact.id,
                "legacy_record_id": fact.legacy_record_id,
                "contract_id": contract.id,
                "expense_id": wrapper.id,
                "contract_no": contract.legacy_contract_no,
                "subject": contract.subject,
                "operation_strategy": contract.operation_strategy,
                "category": contract.expense_contract_category_id.name,
                "amount": contract.legacy_contract_amount,
                "content": contract.legacy_visible_engineering_content,
                "note": contract.note,
                "attachment": contract.legacy_visible_attachment,
            }
        )
    env.cr.commit()  # noqa: F821

    projected_domain = [("legacy_contract_id", "ilike", LEGACY_ID_PREFIX + "%")]
    projected_count = Contract.search_count(projected_domain)
    expense_execution_count = env[TARGET_WRAPPER_MODEL].sudo().search_count(  # noqa: F821
        projected_domain
        + [
            ("state", "in", ["confirmed", "running"]),
            ("subject", "not ilike", "结算"),
            ("legacy_visible_title", "not ilike", "结算"),
        ]
    )
    category_count = Contract.search_count(projected_domain + [("expense_contract_category_id", "=", category.id)])
    direct_count = Contract.search_count(projected_domain + [("operation_strategy", "=", "direct")])
    content_count = Contract.search_count(projected_domain + [("legacy_visible_engineering_content", "!=", False)])
    amount_count = Contract.search_count(projected_domain + [("legacy_contract_amount", "!=", 0)])
    creator_count = Contract.search_count(projected_domain + [("legacy_visible_creator_name", "!=", False)])
    note_count = Contract.search_count(projected_domain + [("note", "!=", False)])
    display_attachment_count = Contract.search_count(projected_domain + [("legacy_visible_attachment", "!=", False)])
    ref_attachment_count = Contract.search_count(projected_domain + [("attachment_text", "!=", False)])
    source_attachment_count = env["ir.attachment"].sudo().search_count([("res_model", "=", SOURCE_MODEL), ("res_id", "in", facts.ids or [-1])])  # noqa: F821
    wrapper_attachment_count = env["ir.attachment"].sudo().search_count(  # noqa: F821
        [("res_model", "=", TARGET_WRAPPER_MODEL), ("description", "ilike", MIGRATION_MARKER)]
    )
    result = {
        "status": "PASS"
        if projected_count == len(seen)
        and expense_execution_count == len(seen)
        and category_count == len(seen)
        and direct_count == len(seen)
        and content_count == len(seen)
        and wrapper_attachment_count >= source_attachment_count
        else "FAIL",
        "mode": "direct_acceptance_subcontract_contract_expense_execution_write",
        "db": env.cr.dbname,  # noqa: F821
        "source_system": SOURCE_SYSTEM,
        "acceptance_label": ACCEPTANCE_LABEL,
        "accepted_fact_count": len(facts),
        "unique_fact_count": len(seen),
        "created_contracts": created,
        "updated_contracts": updated,
        "line_created": line_created,
        "line_updated": line_updated,
        "expense_wrappers_created": wrappers,
        "projected_contract_count": projected_count,
        "expense_execution_projected_count": expense_execution_count,
        "subcontract_category_count": category_count,
        "direct_operation_count": direct_count,
        "content_count": content_count,
        "amount_nonzero_count": amount_count,
        "creator_count": creator_count,
        "note_count": note_count,
        "source_attachment_count": source_attachment_count,
        "copied_contract_attachments": copied_contract_attachments,
        "copied_wrapper_attachments": copied_wrapper_attachments,
        "wrapper_attachment_count": wrapper_attachment_count,
        "display_attachment_count": display_attachment_count,
        "ref_attachment_count": ref_attachment_count,
        "skipped_duplicate_count": len(skipped_duplicates),
        "skipped_duplicates": skipped_duplicates[:20],
        "detail_sample": detail[:20],
    }
    OUTPUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("DIRECT_ACCEPTANCE_SUBCONTRACT_CONTRACT_EXPENSE_EXECUTION_WRITE=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
    if result["status"] != "PASS":
        raise RuntimeError(result)


main()
