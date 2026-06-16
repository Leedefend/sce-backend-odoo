#!/usr/bin/env python3
"""Mirror SCBSLY current-user supplier payment rows into payment execution."""

from __future__ import annotations

import gzip
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


INPUT = Path("/tmp/scbs_55_old_live_full_rows_seq031_supplier_payment.json.gz")
SURFACE = "online_old_scbly:T_FK_SUPPLIER:list881"
TABLE = "T_FK_SUPPLIER"


def clean(value: object) -> str:
    if value in (None, False):
        return ""
    text = re.sub(r"\s+", " ", str(value).replace("\u3000", " ").strip())
    return "" if text in {"False", "false", "None", "NULL"} else text


def parse_date(value: object):
    text = clean(value)
    if not text:
        return False
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(text[:10], fmt).date()
        except ValueError:
            continue
    return False


def parse_dt(value: object):
    text = clean(value)
    if not text:
        return False
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%m/%d/%Y %H:%M:%S", "%m/%d/%Y"):
        try:
            return datetime.strptime(text[:19] if "%H" in fmt else text[:10], fmt)
        except ValueError:
            continue
    return False


def amount(value: object) -> float:
    text = clean(value)
    if not text:
        return 0.0
    try:
        return abs(float(text))
    except ValueError:
        return 0.0


def safe_vals(model, vals: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in vals.items() if key in model._fields}


def project_for(row: dict[str, Any]):
    Project = env["project.project"].sudo().with_context(active_test=False)  # noqa: F821
    legacy_project_id = clean(row.get("f_XMID") or row.get("XMID"))
    if legacy_project_id and "legacy_project_id" in Project._fields:
        project = Project.search([("legacy_project_id", "=", legacy_project_id)], limit=1)
        if project:
            return project
    name = clean(row.get("D_BQJT_XMMC") or row.get("TSXMMC") or row.get("f_LYXM") or row.get("f_BM"))
    if name:
        project = Project.search([("name", "ilike", name[:60])], limit=1)
        if project:
            return project
    return Project.search([], limit=1)


def partner_for(row: dict[str, Any]):
    Partner = env["res.partner"].sudo().with_context(active_test=False)  # noqa: F821
    legacy_id = clean(row.get("f_SupplierID"))
    if legacy_id and "legacy_partner_id" in Partner._fields:
        partner = Partner.search([("legacy_partner_id", "=", legacy_id)], limit=1)
        if partner:
            return partner
    name = clean(row.get("f_SupplierName") or row.get("HM"))
    if name:
        partner = Partner.search([("name", "=", name)], limit=1)
        if partner:
            return partner
        return Partner.create({"name": name, "supplier_rank": 1})
    return Partner.browse()


def ensure_payload_table() -> None:
    env.cr.execute(  # noqa: F821
        """
        CREATE TABLE IF NOT EXISTS sc_p1_legacy_visible_alias_payload (
            model varchar NOT NULL,
            res_id integer NOT NULL,
            payload jsonb NOT NULL DEFAULT '{}'::jsonb,
            write_date timestamp without time zone NOT NULL DEFAULT now(),
            PRIMARY KEY (model, res_id)
        )
        """
    )


def write_payload(record, row: dict[str, Any]) -> None:
    payload = {
        "单据状态": clean(row.get("DJZT")),
        "推送结果": clean(row.get("TSJG") or row.get("D_SCBSJS_IsPush")),
        "金蝶单据编号": clean(row.get("OTHER_SYSTEM_CODE")),
        "单据编号": clean(row.get("DJBH")),
        "項目名称": clean(row.get("D_BQJT_XMMC") or row.get("TSXMMC") or row.get("f_LYXM") or row.get("f_BM")),
        "供应商名称": clean(row.get("f_SupplierName")),
        "付款日期": clean(row.get("f_FKRQ"))[:10],
        "付款金额": str(amount(row.get("f_FKJE"))),
        "备注": clean(row.get("f_BZ") or row.get("BZ")),
        "其他备注": clean(row.get("Remark")),
        "付款方式名称": clean(row.get("f_FKFSMC")),
        "填写人": clean(row.get("f_TXR")),
        "开户行": clean(row.get("KHH")),
        "账户": clean(row.get("ZH")),
        "付款账户": clean(row.get("FKZH")),
        "付款账户名称": clean(row.get("FKZHMC")),
        "支付申请单号": clean(row.get("ZFSQDH")),
        "附件": clean(row.get("FJ") or row.get("f_FJ")),
    }
    env.cr.execute(  # noqa: F821
        """
        INSERT INTO sc_p1_legacy_visible_alias_payload(model, res_id, payload, write_date)
        VALUES (%s, %s, %s::jsonb, now())
        ON CONFLICT (model, res_id)
        DO UPDATE SET payload = EXCLUDED.payload, write_date = now()
        """,
        [record._name, record.id, json.dumps(payload, ensure_ascii=False)],
    )


with gzip.open(INPUT, "rt", encoding="utf-8") as handle:
    rows = json.load(handle)["rows"]

ensure_payload_table()
Payment = env["sc.payment.execution"].sudo().with_context(active_test=False)  # noqa: F821
created = updated = reused_existing_key = 0
seen: set[str] = set()

for row in rows:
    key = clean(row.get("Id") or row.get("ID"))
    if not key:
        continue
    seen.add(key)
    record = Payment.search([("legacy_source_model", "=", SURFACE), ("legacy_record_id", "=", key)], limit=1)
    if not record:
        record = Payment.search([("legacy_record_id", "=", key), ("payment_family", "in", ["往来单位付款", "SCBS供应商付款"])], limit=1)
        if record:
            reused_existing_key += 1
    project = project_for(row)
    partner = partner_for(row)
    vals = {
        "name": clean(row.get("DJBH")) or key,
        "source_origin": "legacy",
        "source_kind": "actual_outflow",
        "state": "legacy_confirmed",
        "project_id": project.id,
        "partner_id": partner.id if partner else False,
        "date_payment": parse_date(row.get("f_FKRQ")),
        "document_no": clean(row.get("DJBH")),
        "payment_family": "往来单位付款",
        "payment_method": clean(row.get("f_FKFSMC")),
        "bank_account": clean(row.get("FKZH")),
        "payment_account_name": clean(row.get("FKZHMC")),
        "payment_account_no": clean(row.get("FKZH")),
        "receipt_account_name": clean(row.get("HM")),
        "receipt_account_no": clean(row.get("ZH")),
        "receipt_bank_name": clean(row.get("KHH")),
        "planned_amount": amount(row.get("f_FKJE")),
        "paid_amount": amount(row.get("f_FKJE")),
        "invoice_amount": amount(row.get("f_FPJE")),
        "currency_id": env.ref("base.CNY", raise_if_not_found=False).id,  # noqa: F821
        "legacy_source_model": SURFACE,
        "legacy_source_table": TABLE,
        "legacy_record_id": key,
        "legacy_document_state": clean(row.get("DJZT")),
        "legacy_attachment_ref": clean(row.get("FJ") or row.get("f_FJ")),
        "legacy_visible_document_no": clean(row.get("DJBH")),
        "legacy_visible_project_name": clean(row.get("D_BQJT_XMMC") or row.get("TSXMMC") or row.get("f_LYXM") or row.get("f_BM")),
        "legacy_visible_supplier_name": clean(row.get("f_SupplierName")),
        "legacy_visible_payment_date": clean(row.get("f_FKRQ"))[:10],
        "legacy_visible_note": clean(row.get("f_BZ") or row.get("BZ")),
        "legacy_visible_other_note": clean(row.get("Remark")),
        "legacy_visible_payment_method": clean(row.get("f_FKFSMC")),
        "legacy_visible_receipt_bank_name": clean(row.get("KHH")),
        "legacy_visible_receipt_account_no": clean(row.get("ZH")),
        "legacy_visible_payment_account_no": clean(row.get("FKZH")),
        "legacy_visible_payment_account_name": clean(row.get("FKZHMC")),
        "legacy_visible_request_no": clean(row.get("ZFSQDH")),
        "push_result": clean(row.get("TSJG") or row.get("D_SCBSJS_IsPush")),
        "kingdee_document_no": clean(row.get("OTHER_SYSTEM_CODE")),
        "creator_legacy_user_id": clean(row.get("LRRID")),
        "creator_name": clean(row.get("f_LRR") or row.get("LRR")),
        "created_time": parse_dt(row.get("f_LRSJ") or row.get("LRSJ")),
        "note": "SCBSLY old visible supplier payment mirror; old_key=%s; attachment=%s" % (key, clean(row.get("FJ") or row.get("f_FJ"))),
        "active": True,
    }
    if record:
        record.write(safe_vals(Payment, vals))
        updated += 1
    else:
        record = Payment.create(safe_vals(Payment, vals))
        created += 1
    write_payload(record, row)

stale = Payment.search([("legacy_source_model", "=", SURFACE), ("legacy_record_id", "not in", list(seen) or ["__none__"])])
stale_count = len(stale)
if stale:
    stale.write({"legacy_source_model": f"{SURFACE}:hidden", "active": False})

env.cr.commit()  # noqa: F821
final_count = Payment.search_count([("legacy_source_model", "=", SURFACE)])
action_count = Payment.search_count([("source_kind", "=", "actual_outflow"), ("payment_family", "in", ["往来单位付款", "SCBS供应商付款"])])
payload = {
    "status": "PASS" if final_count == len(rows) else "REVIEW",
    "old_rows": len(rows),
    "created": created,
    "updated": updated,
    "reused_existing_key": reused_existing_key,
    "stale_hidden": stale_count,
    "final_count": final_count,
    "direct_action_count": action_count,
    "surface": SURFACE,
}
print("SCBSLY_SUPPLIER_PAYMENT_ONLINE_PATCH=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
