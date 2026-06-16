#!/usr/bin/env python3
"""Mirror old SCBS invoice list surfaces into action-specific rows."""

from __future__ import annotations

import gzip
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


SPECS = {
    39: {
        "path": "/tmp/scbs_55_old_live_full_rows_seq039_invoice_apply.json.gz",
        "action_id": 889,
        "surface": "online_old_scbs:C_JXXP_KJFPSQ:list889",
        "table": "C_JXXP_KJFPSQ",
        "source_kind": "output_invoice_tax",
        "direction": "output",
        "date": "SQRQ",
        "amount": "BCKPJE",
        "labels": ["状态", "开票状态", "合同编号", "项目名称", "单据编号", "申请人", "预计回款日期", "申请日期", "受票方名称", "累计开票金额", "合同额", "本次开票张数", "本次开票金额", "附件", "备注", "录入人", "录入时间"],
    },
    40: {
        "path": "/tmp/scbs_55_old_live_full_rows_seq040_invoice_register.json.gz",
        "action_id": 890,
        "surface": "online_old_scbs:C_JXXP_XXKPDJ:list890",
        "table": "C_JXXP_XXKPDJ",
        "source_kind": "output_invoice_tax",
        "direction": "output",
        "date": "SQRQ",
        "amount": "JE$C_JXXP_XXKPDJ_CB",
        "child": "Id$C_JXXP_XXKPDJ_CB",
        "labels": ["单据状态", "推送结果", "金蝶单据编号", "单据编号", "项目名称", "受票方名称", "含税金额", "税额", "不含税金额", "附加税", "开票张数", "税率", "关联回款金额", "发票号", "发票种类", "开票单位", "附件", "录入人", "开票日期", "录入时间"],
    },
    41: {
        "path": "/tmp/scbs_55_old_live_full_rows_seq041_prepaid_tax.json.gz",
        "action_id": 891,
        "surface": "online_old_scbs:C_JXXP_YJSKDJ:list891",
        "table": "C_JXXP_YJSKDJ",
        "source_kind": "prepaid_tax",
        "direction": "prepaid",
        "date": "SQRQ",
        "amount": "JE$C_JXXP_YJSKDJ_CB",
        "child": "Id$C_JXXP_YJSKDJ_CB",
        "labels": ["状态", "项目名称", "单据编号", "受票方名称", "交税类型", "金额", "发票开具日期", "预缴税款日期", "完税凭证号码", "附件", "录入人"],
    },
}


def clean(value: object) -> str:
    if value in (None, False):
        return ""
    text = re.sub(r"\s+", " ", str(value).replace("\u3000", " ").strip())
    return "" if text in {"False", "false", "None", "NULL"} else text


def parse_date(value: object):
    text = clean(value)
    if not text:
        return False
    try:
        return datetime.strptime(text[:10], "%Y-%m-%d").date()
    except ValueError:
        return False


def parse_dt(value: object):
    text = clean(value)
    if not text:
        return False
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
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


def amount_text(value: object) -> str:
    number = amount(value)
    return ("%.2f" % number).rstrip("0").rstrip(".")


def state_label(value: object) -> str:
    text = clean(value)
    return {"-1": "已作废", "0": "未审核", "1": "审核中", "2": "审核通过", "3": "已驳回", "4": "已作废"}.get(text, text)


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


def write_payload(record, payload: dict[str, str]) -> None:
    env.cr.execute(  # noqa: F821
        """
        INSERT INTO sc_p1_legacy_visible_alias_payload(model, res_id, payload, write_date)
        VALUES (%s, %s, %s::jsonb, now())
        ON CONFLICT (model, res_id)
        DO UPDATE SET payload = EXCLUDED.payload, write_date = now()
        """,
        [record._name, record.id, json.dumps(payload, ensure_ascii=False)],
    )


def project_for(row: dict[str, Any]):
    Project = env["project.project"].sudo().with_context(active_test=False)  # noqa: F821
    legacy_project_id = clean(row.get("XMID"))
    if legacy_project_id and "legacy_project_id" in Project._fields:
        project = Project.search([("legacy_project_id", "=", legacy_project_id)], limit=1)
        if project:
            return project
    name = clean(row.get("XMMC"))
    if name:
        project = Project.search([("name", "ilike", name[:60])], limit=1)
        if project:
            return project
    return Project.search([], limit=1)


def row_key(seq: int, row: dict[str, Any], index: int) -> str:
    spec = SPECS[seq]
    header = clean(row.get("Id") or row.get("pid"))
    child_key = spec.get("child")
    if child_key:
        child = clean(row.get(child_key) or row.get("RowIndex") or index)
        return f"{header}:{child}"
    return header or str(index)


def visible_values(seq: int, row: dict[str, Any]) -> dict[str, str]:
    values = {
        "状态": state_label(row.get("DJZT")),
        "单据状态": state_label(row.get("DJZT")),
        "开票状态": clean(row.get("KPZT")),
        "合同编号": clean(row.get("HTBH")),
        "项目名称": clean(row.get("XMMC")),
        "单据编号": clean(row.get("DJBH")),
        "申请人": clean(row.get("SQR")),
        "预计回款日期": clean(row.get("YJHKRQ"))[:10],
        "申请日期": clean(row.get("SQRQ"))[:10],
        "受票方名称": clean(row.get("SPF_MC") or row.get("SPFMC")),
        "累计开票金额": amount_text(row.get("LJKPJE")),
        "合同额": amount_text(row.get("HTE")),
        "本次开票张数": amount_text(row.get("BCKP_ZS")),
        "本次开票金额": amount_text(row.get("BCKPJE")),
        "含税金额": amount_text(row.get("JE$C_JXXP_XXKPDJ_CB") or row.get("KPZJE")),
        "税额": amount_text(row.get("SE$C_JXXP_XXKPDJ_CB") or row.get("ZSE")),
        "不含税金额": amount_text(row.get("JE_NO$C_JXXP_XXKPDJ_CB") or row.get("BHSJE")),
        "附加税": amount_text(row.get("D_SCBSJS_FJS")),
        "开票张数": clean(row.get("KPZS")),
        "税率": clean(row.get("SLV$C_JXXP_XXKPDJ_CB")),
        "关联回款金额": amount_text(row.get("GLHKJE")),
        "发票号": clean(row.get("FPH$C_JXXP_XXKPDJ_CB")),
        "发票种类": clean(row.get("FPZL")),
        "开票单位": clean(row.get("KPDW")),
        "开票日期": clean(row.get("KPRQ$C_JXXP_XXKPDJ_CB") or row.get("FPKJRQ"))[:10],
        "推送结果": clean(row.get("TSJG") or row.get("D_SCBSJS_IsPush")),
        "金蝶单据编号": clean(row.get("OTHER_SYSTEM_CODE")),
        "交税类型": clean(row.get("JSLX$C_JXXP_YJSKDJ_CB")),
        "金额": amount_text(row.get("JE$C_JXXP_YJSKDJ_CB")),
        "发票开具日期": clean(row.get("FPKJRQ"))[:10],
        "预缴税款日期": clean(row.get("JNSJ$C_JXXP_YJSKDJ_CB"))[:10],
        "完税凭证号码": clean(row.get("WSPZHM$C_JXXP_YJSKDJ_CB")),
        "附件": clean(row.get("f_FJ") or row.get("FJ")),
        "备注": clean(row.get("BZ") or row.get("BZ$C_JXXP_XXKPDJ_CB") or row.get("BZ$C_JXXP_YJSKDJ_CB")),
        "录入人": clean(row.get("LRR")),
        "录入时间": clean(row.get("LRSJ")),
    }
    return {label: values.get(label, "") for label in SPECS[seq]["labels"]}


def import_surface(seq: int) -> dict[str, Any]:
    spec = SPECS[seq]
    with gzip.open(Path(spec["path"]), "rt", encoding="utf-8") as handle:
        rows = json.load(handle)["rows"]
    Invoice = env["sc.invoice.registration"].sudo().with_context(active_test=False)  # noqa: F821
    Action = env["ir.actions.act_window"].sudo()  # noqa: F821
    Currency = env.ref("base.CNY", raise_if_not_found=False)  # noqa: F821
    created = updated = 0
    seen: set[str] = set()
    for index, row in enumerate(rows, start=1):
        key = row_key(seq, row, index)
        seen.add(key)
        rec = Invoice.search([("legacy_source_model", "=", spec["surface"]), ("legacy_record_id", "=", key)], limit=1)
        project = project_for(row)
        vals = {
            "source_origin": "legacy",
            "source_kind": spec["source_kind"],
            "direction": spec["direction"],
            "state": "legacy_confirmed",
            "project_id": project.id,
            "name": clean(row.get("DJBH")) or key,
            "document_no": clean(row.get("DJBH")),
            "document_date": parse_date(row.get(spec["date"])),
            "invoice_date": parse_date(row.get("FPKJRQ") or row.get("KPRQ$C_JXXP_XXKPDJ_CB") or row.get(spec["date"])),
            "recognition_date": parse_date(row.get(spec["date"])),
            "invoice_no": clean(row.get("FPH$C_JXXP_XXKPDJ_CB") or row.get("FBFPHM$C_JXXP_YJSKDJ_CB")),
            "invoice_type": clean(row.get("FPZL") or row.get("KPF_FPZL")),
            "tax_rate": clean(row.get("SLV$C_JXXP_XXKPDJ_CB") or row.get("SLBL$C_JXXP_YJSKDJ_CB")),
            "tax_type": clean(row.get("JSLX$C_JXXP_YJSKDJ_CB")),
            "legacy_visible_project_name": clean(row.get("XMMC")),
            "legacy_visible_contract_no": clean(row.get("HTBH")),
            "legacy_visible_application_date": parse_dt(row.get("SQRQ")),
            "legacy_visible_invoice_state": clean(row.get("KPZT")),
            "legacy_visible_partner_name": clean(row.get("SPF_MC") or row.get("SPFMC")),
            "legacy_visible_cumulative_invoice_amount": amount_text(row.get("LJKPJE")),
            "legacy_visible_invoice_count": clean(row.get("KPZS") or row.get("BCKP_ZS")),
            "legacy_visible_current_invoice_amount": amount_text(row.get(spec["amount"])),
            "legacy_visible_note": clean(row.get("BZ") or row.get("BZ$C_JXXP_XXKPDJ_CB") or row.get("BZ$C_JXXP_YJSKDJ_CB")),
            "legacy_visible_kingdee_no": clean(row.get("OTHER_SYSTEM_CODE")),
            "legacy_visible_surcharge_amount": amount_text(row.get("D_SCBSJS_FJS")),
            "legacy_visible_tax_rate": clean(row.get("SLV$C_JXXP_XXKPDJ_CB") or row.get("SLBL$C_JXXP_YJSKDJ_CB")),
            "legacy_visible_related_receipt_amount": amount_text(row.get("GLHKJE")),
            "legacy_visible_invoice_no": clean(row.get("FPH$C_JXXP_XXKPDJ_CB")),
            "legacy_visible_invoice_type": clean(row.get("FPZL") or row.get("KPF_FPZL")),
            "legacy_visible_invoice_issue_company": clean(row.get("KPDW")),
            "prepaid_tax_date": parse_date(row.get("JNSJ$C_JXXP_YJSKDJ_CB")),
            "tax_certificate_no": clean(row.get("WSPZHM$C_JXXP_YJSKDJ_CB")),
            "invoice_issue_company": clean(row.get("KPDW")),
            "push_result": clean(row.get("TSJG") or row.get("D_SCBSJS_IsPush")),
            "kingdee_document_no": clean(row.get("OTHER_SYSTEM_CODE")),
            "expected_receipt_date": parse_date(row.get("YJHKRQ")),
            "applicant_name": clean(row.get("SQR")),
            "invoice_count": int(amount(row.get("KPZS") or row.get("BCKP_ZS"))),
            "amount_no_tax": amount(row.get("JE_NO$C_JXXP_XXKPDJ_CB") or row.get("KPZJE_NO")),
            "tax_amount": amount(row.get("SE$C_JXXP_XXKPDJ_CB") or row.get("KPSE")),
            "amount_total": amount(row.get(spec["amount"])),
            "surcharge_amount": amount(row.get("D_SCBSJS_FJS")),
            "currency_id": Currency.id,
            "legacy_source_model": spec["surface"],
            "legacy_source_table": spec["table"],
            "legacy_record_id": key,
            "legacy_document_state": clean(row.get("DJZT")),
            "legacy_partner_name": clean(row.get("SPF_MC") or row.get("SPFMC")),
            "legacy_partner_tax_no": clean(row.get("SPF_SBH") or row.get("D_BYK_SPF_NSSBH")),
            "legacy_attachment_ref": clean(row.get("FJ") or row.get("f_FJ")),
            "creator_legacy_user_id": clean(row.get("LRRID")),
            "creator_name": clean(row.get("LRR")),
            "created_time": parse_dt(row.get("LRSJ")),
            "note": "SCBS55 old visible surface mirror: %s; old_key=%s" % (spec["surface"], key),
            "active": True,
        }
        if rec:
            allowed_existing = {
                "note",
                "active",
                "creator_legacy_user_id",
                "creator_name",
                "created_time",
                "tax_type",
                "prepaid_tax_date",
                "tax_certificate_no",
                "legacy_attachment_ref",
            }
            rec.write({key: vals[key] for key in allowed_existing if key in vals})
            updated += 1
        else:
            rec = Invoice.create(vals)
            created += 1
        write_payload(rec, visible_values(seq, row))
    stale = Invoice.search([("legacy_source_model", "=", spec["surface"]), ("legacy_record_id", "not in", list(seen) or ["__none__"])])
    stale_count = len(stale)
    if stale:
        stale.write({"legacy_source_model": f"{spec['surface']}:hidden", "active": False})
    domain = [("legacy_source_model", "=", spec["surface"])]
    Action.browse(spec["action_id"]).write({"domain": repr(domain)})
    final_count = Invoice.search_count(domain)
    return {"seq": seq, "surface": spec["surface"], "old": len(rows), "created": created, "updated": updated, "stale_hidden": stale_count, "final_count": final_count, "domain": repr(domain), "status": "OK" if final_count == len(rows) else "COUNT_MISMATCH"}


ensure_payload_table()
result = {"surfaces": [import_surface(seq) for seq in sorted(SPECS)]}
env.cr.commit()  # noqa: F821
print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
