#!/usr/bin/env python3
"""Project accepted partner payments into the formal payment execution model."""

from __future__ import annotations

import gzip
import json
import os
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path


JOINT_SOURCE_MODEL = "online_old_scbs:T_FK_SUPPLIER:list881"
DIRECT_SOURCE_MODEL = "online_old_scbsly:T_FK_SUPPLIER:list881"
SOURCE_TABLE = "T_FK_SUPPLIER"


def clean(value):
    if value is None or value is False:
        return ""
    text = re.sub(r"\s+", " ", str(value).replace("\u3000", " ").strip())
    return "" if text in {"False", "false", "None", "NULL"} else text


def money(value) -> Decimal:
    text = clean(value).replace(",", "")
    if not text:
        return Decimal("0")
    try:
        return Decimal(text)
    except (InvalidOperation, ValueError):
        return Decimal("0")


def money_float_abs(value) -> float:
    return float(abs(money(value)))


def money_text(value) -> str:
    amount = money(value).quantize(Decimal("0.01"))
    if amount == amount.to_integral():
        return str(amount.to_integral())
    return format(amount.normalize(), "f")


def parse_date(value):
    text = clean(value)
    if not text:
        return False
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(text[:10], fmt).date()
        except ValueError:
            continue
    return False


def parse_dt(value):
    text = clean(value)
    if not text:
        return False
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%m/%d/%Y %H:%M:%S", "%m/%d/%Y"):
        try:
            return datetime.strptime(text[:19] if "%H" in fmt else text[:10], fmt)
        except ValueError:
            continue
    return False


def entry_date_text(value, fact=None):
    text = clean(value)
    if text:
        return text[:10]
    fact_created_time = getattr(fact, "created_time", None) if fact else None
    return str(fact_created_time)[:10] if fact_created_time else ""


def ensure_allowed_db():
    allowlist = {
        item.strip()
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_demo").split(",")
        if item.strip()
    }
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_projection": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def joint_source_path() -> Path:
    candidates = [
        os.getenv("PAYMENT_EXECUTION_JOINT_ROWS_JSON"),
        "/mnt/artifacts/migration/scbs_55_old_live_full_rows_current/seq031.json.gz",
        "artifacts/migration/scbs_55_old_live_full_rows_current/seq031.json.gz",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return Path(candidate)
    raise RuntimeError({"payment_execution_joint_rows_missing": [item for item in candidates if item]})


def payload_dict(value):
    if isinstance(value, dict):
        return value
    if isinstance(value, str) and value.strip():
        try:
            payload = json.loads(value)
        except json.JSONDecodeError:
            return {}
        return payload if isinstance(payload, dict) else {}
    return {}


def project_for(row, fact=None):
    Project = env["project.project"].sudo().with_context(active_test=False)  # noqa: F821
    if fact is not None and "project_id" in fact._fields and fact.project_id:
        return fact.project_id
    legacy_project_id = clean(row.get("f_XMID") or row.get("XMID"))
    if legacy_project_id and "legacy_project_id" in Project._fields:
        project = Project.search([("legacy_project_id", "=", legacy_project_id)], limit=1)
        if project:
            return project
    name = clean(row.get("XMMC") or row.get("D_BQJT_XMMC") or row.get("TSXMMC") or row.get("f_LYXM") or row.get("f_BM"))
    if name:
        project = Project.search([("name", "=", name)], limit=1)
        if project:
            return project
        return Project.create({"name": name, "legacy_project_id": legacy_project_id or False})
    return Project.search([], limit=1)


def partner_for(row):
    Partner = env["res.partner"].sudo().with_context(active_test=False)  # noqa: F821
    legacy_id = clean(row.get("f_SupplierID"))
    if legacy_id:
        for field_name in ("sc_legacy_partner_id", "legacy_partner_id"):
            if field_name in Partner._fields:
                partner = Partner.search([(field_name, "=", legacy_id)], limit=1)
                if partner:
                    return partner
    name = clean(row.get("f_SupplierName") or row.get("HM") or row.get("f_GYSMC"))
    if name:
        partner = Partner.search([("name", "=", name)], limit=1)
        if partner:
            return partner
        return Partner.create({"name": name, "supplier_rank": 1})
    return Partner.browse()


def payment_request_for(row):
    Request = env["payment.request"].sudo().with_context(active_test=False)  # noqa: F821
    request_no = clean(row.get("ZFSQDH"))
    request_id = clean(row.get("f_ZFSQGLId"))
    if request_id:
        request = Request.search([("legacy_record_id", "=", request_id)], limit=1)
        if request:
            return request
    if request_no:
        return Request.search([("name", "=", request_no)], limit=1)
    return Request.browse()


def attachment_label(row):
    return clean(row.get("f_FJ")) or ("附件(1)" if clean(row.get("FJ")) else "")


def link_attachment(record, row):
    ref = clean(row.get("FJ") or row.get("f_FJ"))
    if not ref:
        return False
    Attachment = env["ir.attachment"].sudo()  # noqa: F821
    url = f"legacy-file-id://{ref}"
    attachment = Attachment.search([("res_model", "=", record._name), ("res_id", "=", record.id), ("url", "=", url)], limit=1)
    if not attachment:
        attachment = Attachment.create(
            {
                "name": attachment_label(row) or f"历史附件-{record.name or record.id}",
                "type": "url",
                "url": url,
                "res_model": record._name,
                "res_id": record.id,
            }
        )
    if "attachment_ids" in record._fields:
        env.cr.execute(  # noqa: F821
            """
            INSERT INTO sc_payment_execution_attachment_rel (execution_id, attachment_id)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING
            """,
            [record.id, attachment.id],
        )
    return True


def values_for(row, source_model, fact=None):
    project = project_for(row, fact=fact)
    partner = partner_for(row)
    request = payment_request_for(row)
    amount_value = row.get("f_FKJE") if clean(row.get("f_FKJE")) else row.get("FKJE")
    document_state = clean(row.get("DJZT")) or clean(row.get("DJZTText"))
    document_no = clean(row.get("DJBH"))
    project_name = clean(row.get("XMMC") or row.get("D_BQJT_XMMC") or row.get("TSXMMC") or row.get("f_LYXM") or row.get("f_BM"))
    supplier_name = clean(row.get("f_SupplierName") or row.get("HM") or row.get("f_GYSMC"))
    note = clean(row.get("Remark")) or clean(row.get("f_BZ") or row.get("BZ"))
    entry_source = row.get("f_LRSJ") or row.get("LRSJ")
    created_time = parse_dt(entry_source) or (fact.created_time if fact and fact.created_time else False)
    return {
        "name": document_no or clean(row.get("Id")) or clean(row.get("ID")),
        "source_origin": "legacy",
        "source_kind": "actual_outflow",
        "state": "legacy_confirmed" if document_state in ("2", "审核通过", "已审核") else "draft",
        "project_id": project.id if project else False,
        "partner_id": partner.id if partner else False,
        "payment_request_id": request.id if request else False,
        "date_payment": parse_date(row.get("f_FKRQ")),
        "document_no": document_no or False,
        "payment_family": "往来单位付款",
        "payment_method": clean(row.get("f_FKFSMC")) or False,
        "bank_account": clean(row.get("FKZH")) or False,
        "payment_account_name": clean(row.get("FKZHMC")) or False,
        "payment_account_no": clean(row.get("FKZH")) or False,
        "receipt_account_name": clean(row.get("HM") or row.get("f_SupplierName")) or False,
        "receipt_account_no": clean(row.get("ZH")) or False,
        "receipt_bank_name": clean(row.get("KHH")) or False,
        "planned_amount": money_float_abs(amount_value),
        "paid_amount": money_float_abs(amount_value),
        "invoice_amount": money_float_abs(row.get("f_FPJE")),
        "currency_id": env.company.currency_id.id,  # noqa: F821
        "legacy_source_model": source_model,
        "legacy_source_table": SOURCE_TABLE,
        "legacy_record_id": clean(row.get("Id") or row.get("ID") or (fact.legacy_record_id if fact else "")),
        "legacy_document_state": document_state or False,
        "legacy_attachment_ref": clean(row.get("FJ") or row.get("f_FJ")) or False,
        "legacy_visible_document_no": document_no or False,
        "legacy_visible_project_name": project_name or False,
        "legacy_visible_supplier_name": supplier_name or False,
        "legacy_visible_payment_date": clean(row.get("f_FKRQ")) or False,
        "legacy_visible_payment_amount": money_text(amount_value),
        "legacy_visible_note": clean(row.get("f_BZ")) or False,
        "legacy_visible_other_note": clean(row.get("Remark") or row.get("BZ")) or False,
        "legacy_visible_payment_method": clean(row.get("f_FKFSMC")) or False,
        "legacy_visible_receipt_bank_name": clean(row.get("KHH")) or False,
        "legacy_visible_receipt_account_no": clean(row.get("ZH")) or False,
        "legacy_visible_payment_account_no": clean(row.get("FKZH")) or False,
        "legacy_visible_payment_account_name": clean(row.get("FKZHMC")) or False,
        "legacy_visible_request_no": clean(row.get("ZFSQDH")) or False,
        "creator_legacy_user_id": clean(row.get("LRRID")) or False,
        "creator_name": clean(row.get("f_LRR") or row.get("LRR") or row.get("f_TXR")) or False,
        "legacy_visible_entry_date": entry_date_text(entry_source, fact=fact) or False,
        "created_time": created_time,
        "note": note or False,
        "active": True,
    }


def safe_values(model, values):
    return {key: value for key, value in values.items() if key in model._fields}


def sql_update_execution(record, values):
    values = safe_values(record, values)
    allowed = [
        "name",
        "source_origin",
        "source_kind",
        "state",
        "project_id",
        "partner_id",
        "payment_request_id",
        "date_payment",
        "document_no",
        "payment_family",
        "payment_method",
        "bank_account",
        "payment_account_name",
        "payment_account_no",
        "receipt_account_name",
        "receipt_account_no",
        "receipt_bank_name",
        "planned_amount",
        "paid_amount",
        "invoice_amount",
        "currency_id",
        "legacy_source_model",
        "legacy_source_table",
        "legacy_record_id",
        "legacy_document_state",
        "legacy_attachment_ref",
        "legacy_visible_document_no",
        "legacy_visible_project_name",
        "legacy_visible_supplier_name",
        "legacy_visible_payment_date",
        "legacy_visible_payment_amount",
        "legacy_visible_note",
        "legacy_visible_other_note",
        "legacy_visible_payment_method",
        "legacy_visible_receipt_bank_name",
        "legacy_visible_receipt_account_no",
        "legacy_visible_payment_account_no",
        "legacy_visible_payment_account_name",
        "legacy_visible_request_no",
        "legacy_visible_entry_date",
        "creator_legacy_user_id",
        "creator_name",
        "created_time",
        "note",
        "active",
    ]
    update_values = {key: (None if values[key] is False else values[key]) for key in allowed if key in values}
    if not update_values:
        return
    update_values["write_uid"] = env.uid  # noqa: F821
    set_clause = ", ".join(f"{key} = %s" for key in update_values)
    params = list(update_values.values()) + [record.id]
    env.cr.execute(f"UPDATE sc_payment_execution SET {set_clause}, write_date = NOW() WHERE id = %s", params)  # noqa: F821


ensure_allowed_db()
Execution = env["sc.payment.execution"].sudo().with_context(active_test=False)  # noqa: F821
DirectFact = env["sc.legacy.direct.acceptance.fact"].sudo().with_context(active_test=False)  # noqa: F821

stats = {
    "joint_rows": 0,
    "joint_created": 0,
    "joint_updated": 0,
    "direct_rows": 0,
    "direct_created": 0,
    "direct_updated": 0,
    "direct_negative_visible_amount": 0,
    "attachments_linked": 0,
}

with gzip.open(joint_source_path(), "rt", encoding="utf-8") as handle:
    joint_rows = json.load(handle).get("rows") or []
stats["joint_rows"] = len(joint_rows)
for row in joint_rows:
    key = clean(row.get("Id") or row.get("ID"))
    if not key:
        continue
    record = Execution.search([("legacy_source_model", "=", JOINT_SOURCE_MODEL), ("legacy_record_id", "=", key)], limit=1)
    values = safe_values(Execution, values_for(row, JOINT_SOURCE_MODEL))
    if record:
        sql_update_execution(record, values)
        stats["joint_updated"] += 1
    else:
        record = Execution.create(values)
        stats["joint_created"] += 1
    if link_attachment(record, row):
        stats["attachments_linked"] += 1

direct_facts = DirectFact.search(
    [("source_system", "=", "online_old_scbsly"), ("acceptance_label", "=", "往来单位付款"), ("active", "=", True)]
)
stats["direct_rows"] = len(direct_facts)
for fact in direct_facts:
    row = payload_dict(fact.raw_payload)
    key = clean(row.get("Id") or row.get("ID") or fact.legacy_record_id)
    if not key:
        continue
    if money(row.get("f_FKJE") or row.get("FKJE")) < 0:
        stats["direct_negative_visible_amount"] += 1
    record = Execution.search([("legacy_source_model", "=", DIRECT_SOURCE_MODEL), ("legacy_record_id", "=", key)], limit=1)
    values = safe_values(Execution, values_for(row, DIRECT_SOURCE_MODEL, fact=fact))
    if record:
        sql_update_execution(record, values)
        stats["direct_updated"] += 1
    else:
        record = Execution.create(values)
        stats["direct_created"] += 1
    if link_attachment(record, row):
        stats["attachments_linked"] += 1

env.cr.commit()  # noqa: F821
print(
    "PAYMENT_EXECUTION_PARTNER_PAYMENT_FORMAL_PROJECTION="
    + json.dumps(
        {
            "database": env.cr.dbname,  # noqa: F821
            "mode": "payment_execution_partner_payment_formal_projection_write",
            "status": "PASS",
            **stats,
            "decision": "accepted_direct_and_joint_partner_payments_projected_to_sc_payment_execution",
        },
        ensure_ascii=False,
        sort_keys=True,
    )
)
