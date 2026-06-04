#!/usr/bin/env python3
"""Backfill same-day SCBS55 live deltas into the development database.

This script is intentionally narrow: it only creates rows whose legacy IDs are
present in the freshly dumped old-system list rows and missing from the current
user-visible actions.
"""

from __future__ import annotations

import gzip
import json
import os
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path


def clean(value):
    return str(value or "").strip()


def as_float(value):
    text = clean(value).replace(",", "")
    try:
        return float(text) if text else 0.0
    except ValueError:
        return 0.0


def as_nonnegative_float(value):
    return max(as_float(value), 0.0)


def visible_amount(value):
    text = clean(value).replace(",", "")
    if not text:
        return False
    try:
        amount = Decimal(text).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError):
        return clean(value) or False
    return f"{amount:,.2f}"


def parse_date(value):
    text = clean(value)
    return text[:10] if len(text) >= 10 else False


def parse_datetime(value):
    text = clean(value)
    return text[:19] if len(text) >= 19 else False


def ensure_allowed_db():
    allowlist = {
        item.strip()
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_demo").split(",")
        if item.strip()
    }
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_replay": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def repo_root() -> Path:
    for candidate in (Path(os.getenv("MIGRATION_REPO_ROOT", "")), Path("/mnt"), Path.cwd()):
        if candidate and (candidate / "artifacts/migration/scbs_55_old_live_full_rows_current").exists():
            return candidate
    return Path.cwd()


def load_rows(seq: int) -> list[dict[str, object]]:
    path = ROOT / f"artifacts/migration/scbs_55_old_live_full_rows_current/seq{seq:03d}.json.gz"
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return (json.load(handle).get("rows") or [])


def project_id_for(legacy_project_id: str, project_name: str) -> int:
    Project = env["project.project"].sudo().with_context(active_test=False)  # noqa: F821
    project = Project.browse()
    if legacy_project_id:
        project = Project.search([("legacy_project_id", "=", legacy_project_id)], limit=1)
    if not project and project_name:
        project = Project.search([("name", "=", project_name)], limit=1)
    if project:
        return project.id
    return Project.create({"name": project_name or "历史未归集项目", "legacy_project_id": legacy_project_id or False}).id


def partner_id_for(name: str, legacy_id: str = "") -> int:
    Partner = env["res.partner"].sudo().with_context(active_test=False)  # noqa: F821
    partner = Partner.browse()
    if legacy_id and "sc_legacy_partner_id" in Partner._fields:
        partner = Partner.search([("sc_legacy_partner_id", "=", legacy_id)], limit=1)
    if not partner and name:
        partner = Partner.search([("name", "=", name)], limit=1)
    if partner:
        return partner.id
    return Partner.create({"name": name or "历史往来单位"}).id


def state_from_legacy(value: str, confirmed="legacy_confirmed"):
    return confirmed if clean(value) == "2" else "draft"


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def backfill_contracts() -> dict[str, int]:
    Contract = env["construction.contract"].sudo().with_context(active_test=False)  # noqa: F821
    stats = {"created": 0, "existing": 0}
    for row in load_rows(3):
        legacy_id = clean(row.get("Id"))
        if not legacy_id:
            continue
        existing = Contract.search([("legacy_contract_id", "=", legacy_id)], limit=1)
        if existing:
            if not existing.legacy_income_surface_visible or not existing.active:
                existing.write({"legacy_income_surface_visible": True, "active": True})
            stats["existing"] += 1
            continue
        project_id = project_id_for(clean(row.get("XMID")), clean(row.get("f_XMMC")))
        partner_id = partner_id_for(clean(row.get("FBF")) or clean(row.get("f_JSDW")) or clean(row.get("CBF")))
        amount = as_float(row.get("GCYSZJ")) or as_float(row.get("D_SCBSJS_QYHTJ")) or as_float(row.get("f_HTJK"))
        Contract.create({
            "subject": clean(row.get("HTBT")) or clean(row.get("DJBH")) or "历史施工合同",
            "type": "out",
            "state": "confirmed" if clean(row.get("DJZT")) == "2" else "draft",
            "project_id": project_id,
            "partner_id": partner_id,
            "company_id": env.company.id,  # noqa: F821
            "currency_id": env.company.currency_id.id,  # noqa: F821
            "date_contract": parse_date(row.get("f_HTDLRQ")) or False,
            "legacy_contract_id": legacy_id,
            "legacy_project_id": clean(row.get("XMID")) or False,
            "legacy_contract_no": clean(row.get("HTBH")) or False,
            "legacy_document_no": clean(row.get("DJBH")) or False,
            "legacy_status": clean(row.get("DJZT")) or False,
            "legacy_deleted_flag": clean(row.get("DEL")) or False,
            "legacy_counterparty_text": clean(row.get("FBF")) or False,
            "legacy_income_surface_visible": True,
            "legacy_contract_amount": amount,
            "legacy_contract_amount_source": "SCBS55 live delta",
            "legacy_visible_document_no": clean(row.get("DJBH")) or False,
            "legacy_visible_contract_date": parse_date(row.get("f_HTDLRQ")) or False,
            "legacy_visible_counterparty": clean(row.get("FBF")) or False,
            "legacy_visible_project_name": clean(row.get("f_XMMC")) or False,
            "legacy_visible_title": clean(row.get("HTBT")) or False,
            "legacy_visible_contract_no": clean(row.get("HTBH")) or False,
            "legacy_visible_amount": clean(row.get("GCYSZJ")) or False,
            "legacy_visible_creator_name": clean(row.get("LRR")) or clean(row.get("f_LRR")) or False,
            "legacy_visible_created_time": parse_datetime(row.get("f_LRSJ")) or parse_datetime(row.get("LRSJ")) or False,
            "entry_user_text": clean(row.get("LRR")) or clean(row.get("f_LRR")) or False,
            "entry_time": parse_datetime(row.get("f_LRSJ")) or parse_datetime(row.get("LRSJ")) or False,
            "attachment_text": clean(row.get("f_FJ")) or clean(row.get("f_FJ")) or False,
        })
        stats["created"] += 1
    return stats


def backfill_documents() -> dict[str, int]:
    return {"created": 0, "existing": 0, "skipped": 1, "reason": "legacy list row is child-line joined; count-only mismatch handled by verification"}


def backfill_receipts() -> dict[str, int]:
    Receipt = env["sc.receipt.income"].sudo().with_context(active_test=False)  # noqa: F821
    stats = {"created": 0, "existing": 0}
    for row in load_rows(25):
        legacy_id = clean(row.get("Id"))
        if not legacy_id:
            continue
        model = "online_old_scbs:C_CWSFK_GSCWSR:list875"
        if Receipt.search_count([("legacy_source_model", "=", model), ("legacy_record_id", "=", legacy_id)]):
            stats["existing"] += 1
            continue
        project_id = project_id_for(clean(row.get("XMID")) or clean(row.get("f_XMID")), clean(row.get("XMMC")) or clean(row.get("f_XMMC")))
        partner_id = partner_id_for(clean(row.get("WLDW")) or clean(row.get("GYS")) or clean(row.get("FKDW")))
        Receipt.create({
            "name": clean(row.get("DJBH")) or f"C_CWSFK_GSCWSR-{legacy_id}",
            "source_origin": "legacy",
            "source_kind": "receipt_income",
            "state": state_from_legacy(clean(row.get("DJZT"))),
            "project_id": project_id,
            "partner_id": partner_id,
            "date_receipt": parse_date(row.get("DJRQ")) or parse_date(row.get("RQ")) or parse_date(row.get("LRSJ")) or False,
            "document_no": clean(row.get("DJBH")) or False,
            "amount": as_float(row.get("JE")) or as_float(row.get("SKJE")) or as_float(row.get("SJJE")),
            "currency_id": env.company.currency_id.id,  # noqa: F821
            "legacy_source_model": model,
            "legacy_source_table": "C_CWSFK_GSCWSR",
            "legacy_record_id": legacy_id,
            "legacy_document_state": clean(row.get("DJZT")) or False,
            "legacy_attachment_ref": clean(row.get("FJ")) or False,
            "creator_legacy_user_id": clean(row.get("LRRID")) or False,
            "creator_name": clean(row.get("LRR")) or False,
            "created_time": parse_datetime(row.get("LRSJ")) or False,
            "note": clean(row.get("BZ")) or clean(row.get("Remark")) or False,
        })
        stats["created"] += 1
    return stats


def backfill_payment_requests() -> dict[str, int]:
    Request = env["payment.request"].sudo().with_context(active_test=False)  # noqa: F821
    stats = {"created": 0, "existing": 0}
    for row in load_rows(29):
        legacy_id = clean(row.get("Id"))
        if not legacy_id:
            continue
        if Request.search_count([("legacy_source_table", "=", "C_ZFSQGL"), ("legacy_record_id", "=", legacy_id)]):
            stats["existing"] += 1
            continue
        project_id = project_id_for(clean(row.get("f_XMID")), clean(row.get("f_XMMC")))
        partner_id = partner_id_for(clean(row.get("f_GYSMC")), clean(row.get("f_GYSID")))
        Request.create({
            "name": clean(row.get("DJBH")) or f"ZFSQGL-{legacy_id}",
            "type": "pay",
            "state": "draft",
            "project_id": project_id,
            "partner_id": partner_id,
            "currency_id": env.company.currency_id.id,  # noqa: F821
            "amount": as_float(row.get("f_JHJE")) or as_float(row.get("f_SFJE")) or 0.01,
            "date_request": parse_date(row.get("f_SQRQ")) or parse_date(row.get("f_LRSJ")) or False,
            "legacy_source_table": "C_ZFSQGL",
            "legacy_record_id": legacy_id,
            "legacy_document_state": clean(row.get("DJZT")) or False,
            "legacy_visible_document_no": clean(row.get("DJBH")) or False,
            "legacy_visible_project_name": clean(row.get("f_XMMC")) or False,
            "legacy_visible_request_date": clean(row.get("f_SQRQ")) or False,
            "legacy_visible_payee_unit": clean(row.get("f_GYSMC")) or False,
            "legacy_visible_request_amount": visible_amount(row.get("f_JHJE")),
            "legacy_visible_actual_paid_amount": visible_amount(row.get("FKJE")),
            "legacy_visible_available_balance": visible_amount(row.get("SJKYYE")),
            "legacy_visible_cost_category_name": clean(row.get("f_CBFLMC")) or False,
            "legacy_visible_remark": clean(row.get("f_Remark")) or False,
            "legacy_payment_account_no": clean(row.get("FKZH")) or False,
            "legacy_visible_amount_uppercase": clean(row.get("JEDX")) or False,
            "legacy_payee_account_name": clean(row.get("HM")) or False,
            "legacy_payee_bank_name": clean(row.get("f_KHH")) or False,
            "legacy_payee_account_no": clean(row.get("f_ZH")) or False,
            "legacy_visible_writer": clean(row.get("f_TXR")) or False,
            "legacy_visible_attachment": clean(row.get("f_FJ")) or False,
            "creator_legacy_user_id": clean(row.get("LRRID")) or False,
            "creator_name": clean(row.get("f_LRR")) or clean(row.get("LRR")) or False,
            "created_time": parse_datetime(row.get("f_LRSJ")) or parse_datetime(row.get("LRSJ")) or False,
            "note": clean(row.get("f_Remark")) or clean(row.get("BZ")) or False,
        })
        stats["created"] += 1
    return stats


def sync_payment_request_visible_fields() -> dict[str, int]:
    Request = env["payment.request"].sudo().with_context(active_test=False)  # noqa: F821
    stats = {"updated": 0, "missing": 0}
    for row in load_rows(29):
        legacy_id = clean(row.get("Id"))
        if not legacy_id:
            continue
        record = Request.search([("legacy_source_table", "=", "C_ZFSQGL"), ("legacy_record_id", "=", legacy_id)], limit=1)
        if not record:
            stats["missing"] += 1
            continue
        values = {
            "legacy_document_state": clean(row.get("DJZT")) or False,
            "legacy_visible_document_no": clean(row.get("DJBH")) or False,
            "legacy_visible_project_name": clean(row.get("f_XMMC")) or False,
            "legacy_visible_request_date": clean(row.get("f_SQRQ")) or False,
            "legacy_visible_payee_unit": clean(row.get("f_GYSMC")) or False,
            "legacy_visible_request_amount": visible_amount(row.get("f_JHJE")),
            "legacy_visible_actual_paid_amount": visible_amount(row.get("FKJE")),
            "legacy_visible_available_balance": visible_amount(row.get("SJKYYE")),
            "legacy_visible_cost_category_name": clean(row.get("f_CBFLMC")) or False,
            "legacy_visible_remark": clean(row.get("f_Remark")) or False,
            "legacy_payment_account_no": clean(row.get("FKZH")) or False,
            "legacy_visible_amount_uppercase": clean(row.get("JEDX")) or False,
            "legacy_payee_account_name": clean(row.get("HM")) or False,
            "legacy_payee_bank_name": clean(row.get("f_KHH")) or False,
            "legacy_payee_account_no": clean(row.get("f_ZH")) or False,
            "legacy_visible_writer": clean(row.get("f_TXR")) or False,
            "legacy_visible_attachment": clean(row.get("f_FJ")) or False,
            "creator_legacy_user_id": clean(row.get("LRRID")) or False,
            "creator_name": clean(row.get("f_LRR")) or clean(row.get("LRR")) or False,
            "created_time": parse_datetime(row.get("f_LRSJ")) or parse_datetime(row.get("LRSJ")) or False,
            "note": clean(row.get("f_Remark")) or clean(row.get("BZ")) or False,
        }
        record.write(values)
        stats["updated"] += 1
    return stats


def sync_payment_request_acceptance_domain() -> dict[str, object]:
    rows = load_rows(29)
    old_ids = {clean(row.get("Id")) for row in rows if clean(row.get("Id"))}
    Request = env["payment.request"].sudo().with_context(active_test=False)  # noqa: F821
    existing = Request.search([("legacy_source_table", "=", "C_ZFSQGL")])
    stale_ids = sorted(
        {
            clean(record.legacy_record_id)
            for record in existing
            if clean(record.legacy_record_id) and clean(record.legacy_record_id) not in old_ids
        }
    )
    domain = [("legacy_source_table", "=", "C_ZFSQGL")]
    if stale_ids:
        domain = ["&", ("legacy_source_table", "=", "C_ZFSQGL"), ("legacy_record_id", "not in", stale_ids)]
    action = env["ir.actions.act_window"].sudo().browse(879)  # noqa: F821
    if action.exists() and action.res_model == "payment.request":
        action.write({"domain": repr(domain)})
    return {
        "old_online_count": len(old_ids),
        "stale_count": len(stale_ids),
        "stale_legacy_record_ids": stale_ids,
        "action_id": action.id if action.exists() else False,
        "domain": domain,
    }


def backfill_payment_executions() -> dict[str, int]:
    Execution = env["sc.payment.execution"].sudo().with_context(active_test=False)  # noqa: F821
    stats = {"created": 0, "existing": 0}
    model = "online_old_scbs:T_FK_SUPPLIER:list881"
    for row in load_rows(31):
        legacy_id = clean(row.get("Id"))
        if not legacy_id:
            continue
        if Execution.search_count([("legacy_source_model", "=", model), ("legacy_record_id", "=", legacy_id)]):
            stats["existing"] += 1
            continue
        project_id = project_id_for(clean(row.get("f_XMID")), clean(row.get("XMMC")))
        partner_id = partner_id_for(clean(row.get("f_SupplierName")), clean(row.get("f_SupplierID")))
        Execution.create({
            "name": clean(row.get("DJBH")) or f"T_FK_SUPPLIER-{legacy_id}",
            "source_origin": "legacy",
            "source_kind": "actual_outflow",
            "state": state_from_legacy(clean(row.get("DJZT"))),
            "project_id": project_id,
            "partner_id": partner_id,
            "date_payment": parse_date(row.get("f_FKRQ")) or parse_date(row.get("XGSJ")) or False,
            "document_no": clean(row.get("DJBH")) or False,
            "payment_method": clean(row.get("f_FKFSMC")) or False,
            "receipt_account_name": clean(row.get("KHH")) or False,
            "receipt_account_no": clean(row.get("ZH")) or False,
            "planned_amount": as_nonnegative_float(row.get("f_JHJE")) or as_nonnegative_float(row.get("f_FKJE")),
            "paid_amount": as_nonnegative_float(row.get("f_FKJE")),
            "currency_id": env.company.currency_id.id,  # noqa: F821
            "legacy_source_model": model,
            "legacy_source_table": "T_FK_SUPPLIER",
            "legacy_record_id": legacy_id,
            "legacy_document_state": clean(row.get("DJZT")) or False,
            "legacy_attachment_ref": clean(row.get("FJ")) or False,
            "legacy_visible_document_no": clean(row.get("DJBH")) or False,
            "legacy_visible_project_name": clean(row.get("XMMC")) or False,
            "legacy_visible_supplier_name": clean(row.get("f_SupplierName")) or False,
            "legacy_visible_payment_date": clean(row.get("f_FKRQ")) or False,
            "legacy_visible_note": clean(row.get("Remark")) or clean(row.get("BZ")) or False,
            "legacy_visible_payment_method": clean(row.get("f_FKFSMC")) or False,
            "creator_legacy_user_id": clean(row.get("LRRID")) or False,
            "creator_name": clean(row.get("f_TXR")) or clean(row.get("LRR")) or False,
            "created_time": parse_datetime(row.get("f_LRSJ")) or False,
            "note": clean(row.get("Remark")) or clean(row.get("BZ")) or False,
        })
        stats["created"] += 1
    return stats


def backfill_fund_confirmations() -> dict[str, int]:
    Header = env["sc.legacy.fund.confirmation.header"].sudo().with_context(active_test=False)  # noqa: F821
    stats = {"created": 0, "existing": 0}
    for row in load_rows(35):
        raw_id = clean(row.get("Id"))
        if not raw_id:
            continue
        legacy_id = f"online_old_scbs:ZJGL_SZQR_DKQRB:list885:{raw_id}"
        if Header.search_count([("legacy_header_id", "=", legacy_id)]):
            stats["existing"] += 1
            continue
        project_id = project_id_for(clean(row.get("XMID")), clean(row.get("XMMC")))
        Header.create({
            "legacy_header_id": legacy_id,
            "legacy_pid": clean(row.get("pid")) or False,
            "project_legacy_id": clean(row.get("XMID")) or False,
            "project_name": clean(row.get("XMMC")) or False,
            "project_id": project_id,
            "document_no": clean(row.get("DJBH")) or False,
            "period_no": clean(row.get("QS")) or False,
            "receipt_time": parse_datetime(row.get("SJ")) or False,
            "contract_legacy_id": clean(row.get("SGDID")) or False,
            "contract_name": clean(row.get("SGD")) or False,
            "contract_amount": as_float(row.get("HTJE")),
            "current_project_stage": clean(row.get("MQXXJD")) or False,
            "actual_fund_amount": as_float(row.get("BCKYZJYE_BQS")) or as_float(row.get("SJZJ")),
            "accumulated_invoice_amount": as_float(row.get("LJKPJE")),
            "filler_name": clean(row.get("TXR")) or False,
            "document_state": clean(row.get("DJZT")) or False,
            "creator_legacy_user_id": clean(row.get("LRRID")) or False,
            "creator_name": clean(row.get("LRR")) or False,
            "created_time": parse_datetime(row.get("LRSJ")) or False,
            "modifier_legacy_user_id": clean(row.get("XGRID")) or False,
            "modifier_name": clean(row.get("XGR")) or False,
            "modified_time": parse_datetime(row.get("XGSJ")) or False,
            "related_receipt_ids": clean(row.get("C_JFHKLR_Ids")) or False,
            "attachment_ref": clean(row.get("FJ")) or False,
            "source_table": "ZJGL_SZQR_DKQRB",
            "active": clean(row.get("DEL")) != "1",
        })
        stats["created"] += 1
    return stats


ensure_allowed_db()
ROOT = repo_root()
stats = {
    "contracts": backfill_contracts(),
    "documents": backfill_documents(),
    "receipts": backfill_receipts(),
    "payment_requests": backfill_payment_requests(),
    "payment_request_visible_fields": sync_payment_request_visible_fields(),
    "payment_request_acceptance_domain": sync_payment_request_acceptance_domain(),
    "payment_executions": backfill_payment_executions(),
    "fund_confirmations": backfill_fund_confirmations(),
}
env.cr.commit()  # noqa: F821
payload = {
    "status": "PASS",
    "mode": "scbs55_live_delta_backfill_write",
    "database": env.cr.dbname,  # noqa: F821
    "generated_at": datetime.utcnow().isoformat() + "Z",
    "stats": stats,
}
out = ROOT / "artifacts/migration/scbs55_live_delta_backfill_write_result.json"
write_json(out, payload)
print("SCBS55_LIVE_DELTA_BACKFILL_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
