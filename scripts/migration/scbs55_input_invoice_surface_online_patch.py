#!/usr/bin/env python3
"""Mirror old SCBS input-invoice reporting list surface."""

from __future__ import annotations

import gzip
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any


INPUT = Path(os.getenv("SCBS55_INPUT_INVOICE_SURFACE_INPUT") or "/tmp/scbs_55_old_live_full_rows_seq042_进项上报.json.gz")
SURFACE = "online_old_scbs:C_JXXP_ZYFPJJD:list892"
TABLE = "C_JXXP_ZYFPJJD"
LABELS = [
    "状态", "推送结果", "金蝶单据编号", "发票公司类型", "单据编号", "项目名称", "发票开具日期", "开票单位",
    "发票提供人/单位", "价税合计", "税额", "不含税金额", "发票号码", "发票类型", "附件", "录入人", "发票备注", "录入时间",
]


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


def amount(value: object) -> float:
    text = clean(value)
    if not text:
        return 0.0
    try:
        return float(text)
    except ValueError:
        return 0.0


def number_text(value: object) -> str:
    text = clean(value)
    if not text:
        return ""
    try:
        return ("%.2f" % float(text)).rstrip("0").rstrip(".")
    except ValueError:
        return text


def attachment_refs(row: dict[str, Any]) -> str:
    refs = [
        clean(row.get("FJ")),
        clean(row.get("FJ$C_JXXP_ZYFPJJD_CB")),
    ]
    return " ".join(item for item in dict.fromkeys(refs) if item)


def state_label(value: object) -> str:
    text = clean(value)
    return {"-1": "已作废", "0": "未审核", "1": "审核中", "2": "审核通过", "3": "已驳回", "4": "已作废"}.get(text, text)


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


def visible(row: dict[str, Any]) -> dict[str, str]:
    values = {
        "状态": state_label(row.get("DJZT")),
        "推送结果": clean(row.get("TSJG")),
        "金蝶单据编号": clean(row.get("OTHER_SYSTEM_CODE") or row.get("OTHER_SYSTEM_CODE$C_JXXP_ZYFPJJD_CB")),
        "发票公司类型": clean(row.get("D_SCBSJS_FPGSLX$C_JXXP_ZYFPJJD_CB") or row.get("D_SCBSJS_FPGSLX")),
        "单据编号": clean(row.get("DJBH")),
        "项目名称": clean(row.get("XMMC")),
        "发票开具日期": clean(row.get("KPRQ$C_JXXP_ZYFPJJD_CB"))[:10],
        "开票单位": clean(row.get("GYSMC$C_JXXP_ZYFPJJD_CB")),
        "发票提供人/单位": clean(row.get("FPTGF$C_JXXP_ZYFPJJD_CB")),
        "价税合计": number_text(row.get("HJJE$C_JXXP_ZYFPJJD_CB")),
        "税额": number_text(row.get("JXSE$C_JXXP_ZYFPJJD_CB")),
        "不含税金额": number_text(row.get("JE_NO$C_JXXP_ZYFPJJD_CB")),
        "发票号码": clean(row.get("FPHM$C_JXXP_ZYFPJJD_CB")),
        "发票类型": clean(row.get("FPLX$C_JXXP_ZYFPJJD_CB")),
        "附件": clean(row.get("f_FJ") or row.get("FJ$C_JXXP_ZYFPJJD_CB") or row.get("FJ")),
        "录入人": clean(row.get("LRR")),
        "发票备注": clean(row.get("D_SCBSJS_FPBZ$C_JXXP_ZYFPJJD_CB") or row.get("BZ$C_JXXP_ZYFPJJD_CB")),
        "录入时间": clean(row.get("LRSJ")),
    }
    return {label: values.get(label, "") for label in LABELS}


def import_rows() -> dict[str, Any]:
    rows = json.load(gzip.open(INPUT, "rt", encoding="utf-8")).get("rows") or []
    Model = env["sc.legacy.invoice.tax.fact"].sudo().with_context(active_test=False)  # noqa: F821
    existing = {
        rec["legacy_record_id"]: rec["id"]
        for rec in Model.search_read([("legacy_source_table", "=", SURFACE)], ["legacy_record_id"])
    }
    created = updated = 0
    seen: set[str] = set()
    buffer: list[dict[str, object]] = []
    payload_buffer: list[tuple[str, dict[str, str]]] = []
    for index, row in enumerate(rows, start=1):
        line_id = clean(row.get("Id$C_JXXP_ZYFPJJD_CB") or row.get("Id") or index)
        seen.add(line_id)
        project = project_for(row)
        vals = {
            "legacy_source_table": SURFACE,
            "legacy_record_id": line_id,
            "legacy_pid": clean(row.get("pid$C_JXXP_ZYFPJJD_CB") or row.get("pid")),
            "source_family": "input_invoice_report",
            "direction": "input_invoice",
            "document_no": clean(row.get("DJBH")),
            "document_date": parse_date(row.get("DJRQ") or row.get("KPRQ$C_JXXP_ZYFPJJD_CB") or row.get("LRSJ")),
            "legacy_state": clean(row.get("DJZT")),
            "invoice_type": clean(row.get("FPLX$C_JXXP_ZYFPJJD_CB") or row.get("FPLX")),
            "project_id": project.id,
            "legacy_project_id": clean(row.get("XMID")),
            "legacy_project_name": clean(row.get("XMMC")),
            "legacy_partner_id": clean(row.get("GYSID$C_JXXP_ZYFPJJD_CB") or row.get("FPTGFID$C_JXXP_ZYFPJJD_CB")),
            "legacy_partner_name": clean(row.get("GYSMC$C_JXXP_ZYFPJJD_CB") or row.get("FPTGF$C_JXXP_ZYFPJJD_CB")),
            "legacy_partner_tax_no": clean(row.get("GYSSH$C_JXXP_ZYFPJJD_CB")),
            "source_amount": amount(row.get("HJJE$C_JXXP_ZYFPJJD_CB")),
            "source_tax_amount": amount(row.get("JXSE$C_JXXP_ZYFPJJD_CB")),
            "source_amount_field": "HJJE$C_JXXP_ZYFPJJD_CB",
            "attachment_ref": attachment_refs(row),
            "note": "SCBS55 old visible surface mirror: %s; header=%s; attachment=%s; invoice_note=%s"
            % (
                SURFACE,
                clean(row.get("Id")),
                clean(row.get("f_FJ") or row.get("FJ")),
                clean(row.get("D_SCBSJS_FPBZ$C_JXXP_ZYFPJJD_CB") or row.get("BZ$C_JXXP_ZYFPJJD_CB")),
            ),
            "import_batch": "scbs55_old_visible_input_invoice_20260529",
        }
        if line_id in existing:
            rec = Model.browse(existing[line_id])
            rec.write(vals)
            write_payload(rec, visible(row))
            updated += 1
        else:
            buffer.append(vals)
            payload_buffer.append((line_id, visible(row)))
            if len(buffer) >= 500:
                created_records = Model.create(buffer)
                for rec, (_, payload) in zip(created_records, payload_buffer):
                    write_payload(rec, payload)
                created += len(buffer)
                buffer = []
                payload_buffer = []
    if buffer:
        created_records = Model.create(buffer)
        for rec, (_, payload) in zip(created_records, payload_buffer):
            write_payload(rec, payload)
        created += len(buffer)
    stale = Model.search([("legacy_source_table", "=", SURFACE), ("legacy_record_id", "not in", list(seen) or ["__none__"])])
    stale_count = len(stale)
    if stale:
        stale.write({"legacy_source_table": SURFACE + ":hidden"})
    return {
        "old_rows": len(rows),
        "created": created,
        "updated": updated,
        "stale_hidden": stale_count,
        "new_visible": Model.search_count([("legacy_source_table", "=", SURFACE)]),
    }


ensure_payload_table()
result = import_rows()
Path("/tmp/scbs55_input_invoice_surface_online_patch_result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
env.cr.commit()  # noqa: F821
print(json.dumps(result, ensure_ascii=False, indent=2))
