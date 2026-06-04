# -*- coding: utf-8 -*-
"""Project accepted direct-project construction contracts into formal income execution."""

from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path


SOURCE_SYSTEM = "online_old_scbsly"
ACCEPTANCE_LABEL = "施工合同"
LEGACY_ID_PREFIX = "direct_acceptance:construction_contract:"
AMOUNT_LINE_NOTE = "legacy_contract_amount:sc.legacy.direct.acceptance.fact"


def artifact_root() -> Path:
    root = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", "artifacts/migration"))
    try:
        root.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        root = Path("/tmp/sce-migration-artifacts")
        root.mkdir(parents=True, exist_ok=True)
    return root


OUTPUT_JSON = artifact_root() / "direct_acceptance_construction_contract_income_execution_write_result_v1.json"


def ensure_allowed_db() -> None:
    allowlist = {
        item.strip()
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_demo,sc_prod_sim").split(",")
        if item.strip()
    }
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_replay": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def text(value) -> str:
    return str(value or "").replace("\r\n", "\n").replace("\r", "\n").strip()


def clean_rich_text(value) -> str:
    raw = text(value)
    if not raw:
        return ""
    raw = re.sub(r"(?i)<br\s*/?>", "\n", raw)
    raw = re.sub(r"(?i)</p\s*>", "\n", raw)
    raw = re.sub(r"<[^>]+>", "", raw)
    lines = [line.strip() for line in raw.splitlines()]
    return "\n".join(line for line in lines if line).strip()


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


def amount(payload: dict, *fields: str) -> float:
    for field in fields:
        raw = text(payload.get(field)).replace(",", "").replace("￥", "").replace("¥", "")
        if not raw:
            continue
        try:
            value = float(raw)
        except ValueError:
            match = re.search(r"-?\d+(?:\.\d+)?", raw)
            value = float(match.group(0)) if match else 0.0
        if value:
            return value
    return 0.0


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
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(raw[: len("YYYY-MM-DD") if fmt == "%Y-%m-%d" else 19], fmt).date().isoformat()
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


def resolve_project(fact, payload: dict):
    Project = env["project.project"].sudo().with_context(active_test=False)  # noqa: F821
    if fact.project_id:
        return fact.project_id
    legacy_project_id = text(fact.project_legacy_id) or first_text(payload, "XMID", "SJBXXMID")
    if legacy_project_id and "legacy_project_id" in Project._fields:
        project = Project.search([("legacy_project_id", "=", legacy_project_id)], limit=1)
        if project:
            return project
    project_name = (
        text(getattr(fact, "legacy_visible_05", ""))
        or text(fact.project_name)
        or first_text(payload, "f_XMMC", "XMMC", "ProjectName")
        or "直营项目施工合同项目"
    )
    project = Project.search([("name", "=", project_name)], limit=1)
    if project:
        return project
    vals = {"name": project_name}
    if legacy_project_id and "legacy_project_id" in Project._fields:
        vals["legacy_project_id"] = legacy_project_id
    if "company_id" in Project._fields:
        vals["company_id"] = env.company.id  # noqa: F821
    return Project.create(vals)


def resolve_partner(fact, payload: dict):
    Partner = env["res.partner"].sudo().with_context(active_test=False)  # noqa: F821
    name = (
        text(getattr(fact, "legacy_visible_03", ""))
        or first_text(payload, "FBF", "f_FBF", "WLDWMC")
        or text(fact.partner_name)
        or "直营项目施工合同发包人"
    )
    partner = Partner.search([("name", "=", name)], order="id", limit=1)
    if partner:
        return partner
    vals = {
        "name": name,
        "company_type": "company",
    }
    if "is_company" in Partner._fields:
        vals["is_company"] = True
    if "customer_rank" in Partner._fields:
        vals["customer_rank"] = 1
    if "legacy_partner_id" in Partner._fields:
        vals["legacy_partner_id"] = "direct_acceptance_counterparty:" + name
    if "legacy_partner_source" in Partner._fields:
        vals["legacy_partner_source"] = "direct_acceptance_construction_contract"
    if "legacy_source_evidence" in Partner._fields:
        vals["legacy_source_evidence"] = "sc.legacy.direct.acceptance.fact:" + name
    return Partner.create(vals)


def document_state(payload: dict, fact) -> str:
    return first_text(payload, "DJZT", "DJZTText") or text(fact.document_state)


def formal_state(payload: dict, fact) -> str:
    state = document_state(payload, fact)
    if state in {"2", "审核通过"}:
        return "confirmed"
    if state in {"-1", "否决"}:
        return "cancel"
    return "draft"


def contract_values(fact) -> dict:
    payload = payload_of(fact)
    project = resolve_project(fact, payload)
    partner = resolve_partner(fact, payload)
    visible_state = text(fact.legacy_visible_01)
    visible_document_no = text(fact.legacy_visible_02)
    visible_counterparty = text(fact.legacy_visible_03)
    visible_contractor = text(fact.legacy_visible_04)
    visible_project_name = text(fact.legacy_visible_05)
    visible_title = text(fact.legacy_visible_06)
    visible_contract_amount = text(fact.legacy_visible_07)
    visible_invoice_amount = text(fact.legacy_visible_08)
    visible_received_amount = text(fact.legacy_visible_09)
    visible_invoice_unreceived_amount = text(fact.legacy_visible_10)
    visible_unreceived_amount = text(fact.legacy_visible_11)
    visible_unreceived_rate = text(fact.legacy_visible_12)
    visible_contract_no = text(fact.legacy_visible_13)
    visible_contract_date = text(fact.legacy_visible_14)
    visible_engineering_address = text(fact.legacy_visible_15)
    visible_engineering_content = clean_rich_text(text(fact.legacy_visible_16))
    visible_duration = clean_rich_text(text(fact.legacy_visible_17))
    visible_creator = text(fact.legacy_visible_18)
    visible_created_time = text(fact.legacy_visible_19)
    visible_attachment = text(fact.legacy_visible_20)
    contract_amount = parse_amount(visible_contract_amount)
    invoice_amount = parse_amount(visible_invoice_amount)
    received_amount = parse_amount(visible_received_amount)
    unreceived_amount = parse_amount(visible_unreceived_amount)
    vals = {
        "legacy_contract_id": legacy_contract_id(fact),
        "legacy_project_id": text(fact.project_legacy_id) or first_text(payload, "XMID", "SJBXXMID"),
        "legacy_contract_no": visible_contract_no or first_text(payload, "HTBH", "f_HTBH"),
        "legacy_document_no": visible_document_no or text(fact.document_no) or first_text(payload, "DJBH", "HTBH"),
        "legacy_external_contract_no": first_text(payload, "WBHTBH"),
        "legacy_status": visible_state or document_state(payload, fact),
        "legacy_counterparty_text": visible_counterparty,
        "legacy_income_surface_visible": True,
        "legacy_visible_document_state": visible_state,
        "legacy_visible_document_no": visible_document_no,
        "legacy_visible_counterparty": visible_counterparty,
        "legacy_visible_contractor": visible_contractor,
        "legacy_visible_project_name": visible_project_name,
        "legacy_visible_title": visible_title,
        "legacy_visible_amount": visible_contract_amount,
        "legacy_visible_invoice_amount": visible_invoice_amount,
        "legacy_visible_received_amount": visible_received_amount,
        "legacy_visible_invoice_unreceived_amount": visible_invoice_unreceived_amount,
        "legacy_visible_unreceived_amount": visible_unreceived_amount,
        "legacy_visible_unreceived_rate": visible_unreceived_rate,
        "legacy_visible_contract_no": visible_contract_no,
        "legacy_visible_contract_date": parse_date(visible_contract_date),
        "legacy_visible_engineering_address": visible_engineering_address,
        "legacy_visible_engineering_content": visible_engineering_content,
        "legacy_visible_contract_duration_days": visible_duration,
        "legacy_visible_creator_name": visible_creator,
        "legacy_visible_created_time": parse_datetime(visible_created_time),
        "legacy_visible_attachment": visible_attachment,
        "subject": visible_title or text(fact.document_title) or first_text(payload, "HTBT", "f_XMMC", "DJBH", "HTBH") or visible_document_no,
        "type": "out",
        "state": formal_state(payload, fact),
        "project_id": project.id,
        "partner_id": partner.id,
        "date_contract": parse_date(visible_contract_date),
        "engineering_address": visible_engineering_address,
        "engineering_category_text": first_text(payload, "HTLX", "GCLB"),
        "engineering_content": visible_engineering_content,
        "affiliated_person": first_text(payload, "GKR"),
        "contract_duration_text": visible_duration,
        "contract_payment_method_text": clean_rich_text(first_text(payload, "HTYDFKFS", "f_FKFS")),
        "entry_user_text": visible_creator,
        "entry_time": parse_datetime(visible_created_time),
        "attachment_text": visible_attachment,
        "legacy_contract_amount": contract_amount,
        "legacy_contract_amount_source": "sc.legacy.direct.acceptance.fact.legacy_visible_07",
        "visible_invoice_amount": invoice_amount,
        "visible_received_amount": received_amount,
        "visible_unreceived_amount": unreceived_amount,
        "visible_invoice_amount_source": "sc.legacy.direct.acceptance.fact.legacy_visible_08",
        "visible_received_amount_source": "sc.legacy.direct.acceptance.fact.legacy_visible_09",
        "visible_unreceived_amount_source": "sc.legacy.direct.acceptance.fact.legacy_visible_11",
    }
    vals["visible_unreceived_rate"] = visible_unreceived_rate
    clearable_keys = {
        "legacy_visible_document_state",
        "legacy_visible_document_no",
        "legacy_visible_counterparty",
        "legacy_visible_contractor",
        "legacy_visible_project_name",
        "legacy_visible_title",
        "legacy_visible_amount",
        "legacy_visible_invoice_amount",
        "legacy_visible_received_amount",
        "legacy_visible_invoice_unreceived_amount",
        "legacy_visible_unreceived_amount",
        "legacy_visible_unreceived_rate",
        "legacy_visible_contract_no",
        "legacy_visible_contract_date",
        "legacy_visible_engineering_address",
        "legacy_visible_engineering_content",
        "legacy_visible_contract_duration_days",
        "legacy_visible_creator_name",
        "legacy_visible_created_time",
        "legacy_visible_attachment",
        "engineering_address",
        "engineering_content",
        "contract_duration_text",
        "entry_user_text",
        "entry_time",
        "attachment_text",
        "visible_unreceived_rate",
    }
    cleaned = {}
    for key, value in vals.items():
        if value in ("", None):
            if key in clearable_keys:
                cleaned[key] = False
            continue
        cleaned[key] = value
    return cleaned


def sync_amount_line(contract, contract_amount: float) -> str:
    if not contract_amount:
        return ""
    Line = env["construction.contract.line"].sudo()  # noqa: F821
    existing = contract.line_ids.filtered(lambda line: (line.note or "") == AMOUNT_LINE_NOTE)
    vals = {
        "contract_id": contract.id,
        "sequence": 1,
        "qty_contract": 1.0,
        "price_contract": contract_amount,
        "note": AMOUNT_LINE_NOTE,
    }
    if existing:
        existing[:1].write(vals)
        return "line_updated"
    if not contract.line_ids:
        Line.create(vals)
        return "line_created"
    return ""


def ensure_income_wrapper(contract) -> str:
    Income = env["construction.contract.income"].sudo()  # noqa: F821
    if Income.search([("contract_id", "=", contract.id)], limit=1):
        return ""
    Income.create({"contract_id": contract.id})
    return "income_wrapper_created"


def main() -> None:
    ensure_allowed_db()
    Fact = env["sc.legacy.direct.acceptance.fact"].sudo().with_context(active_test=False)  # noqa: F821
    Contract = env["construction.contract"].sudo().with_context(skip_validation_check=True)  # noqa: F821
    facts = Fact.search(
        [
            ("source_system", "=", SOURCE_SYSTEM),
            ("acceptance_label", "=", ACCEPTANCE_LABEL),
            ("active", "=", True),
        ],
        order="legacy_record_id,id",
    )
    created = updated = line_created = line_updated = wrappers = 0
    seen = set()
    skipped_duplicates = []
    detail = []
    tax = Contract._get_default_tax("out")
    for fact in facts:
        identity = legacy_contract_id(fact)
        if identity in seen:
            skipped_duplicates.append(identity)
            continue
        seen.add(identity)
        vals = contract_values(fact)
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
        wrapper_action = ensure_income_wrapper(contract)
        if wrapper_action:
            wrappers += 1
        detail.append(
            {
                "action": "+".join(item for item in (action, amount_action, wrapper_action) if item),
                "fact_id": fact.id,
                "legacy_record_id": fact.legacy_record_id,
                "contract_id": contract.id,
                "legacy_document_no": contract.legacy_document_no,
                "state": contract.state,
                "amount": contract.legacy_contract_amount,
            }
        )
    env.cr.commit()  # noqa: F821

    projected_count = Contract.search_count([("legacy_contract_id", "ilike", LEGACY_ID_PREFIX + "%")])
    income_execution_count = env["construction.contract.income"].sudo().search_count(  # noqa: F821
        [
            ("legacy_contract_id", "ilike", LEGACY_ID_PREFIX + "%"),
            ("legacy_income_surface_visible", "=", True),
        ]
    )
    result = {
        "status": "PASS" if projected_count == len(seen) and income_execution_count == len(seen) else "FAIL",
        "mode": "direct_acceptance_construction_contract_income_execution_write",
        "db": env.cr.dbname,  # noqa: F821
        "source_system": SOURCE_SYSTEM,
        "acceptance_label": ACCEPTANCE_LABEL,
        "accepted_fact_count": len(facts),
        "unique_fact_count": len(seen),
        "created_contracts": created,
        "updated_contracts": updated,
        "line_created": line_created,
        "line_updated": line_updated,
        "income_wrappers_created": wrappers,
        "projected_contract_count": projected_count,
        "income_execution_projected_count": income_execution_count,
        "skipped_duplicate_count": len(skipped_duplicates),
        "skipped_duplicates": skipped_duplicates[:20],
        "detail_sample": detail[:20],
    }
    OUTPUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    if result["status"] != "PASS":
        raise RuntimeError(result)


main()
