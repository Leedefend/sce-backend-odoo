#!/usr/bin/env python3
"""Mirror old SCBS deduction refund list into action 898."""

from __future__ import annotations

import gzip
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


PATH = Path("/tmp/scbs_55_old_live_full_rows_seq034_deduction_refund.json.gz")
SURFACE = "online_old_scbs:T_KK_SJTHB:list898"
ACTION_ID = 898
SOURCE_TABLE = "T_KK_SJTHB"


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


def row_key(row: dict[str, Any], index: int) -> str:
    header = clean(row.get("Id") or row.get("pid"))
    child = clean(row.get("Id$T_KK_SJTHB_CB") or row.get("pid$T_KK_SJTHB_CB") or row.get("RowIndex") or index)
    return f"{header}:{child}"


def visible_payload(row: dict[str, Any]) -> dict[str, str]:
    return {
        "单据状态": state_label(row.get("DJZT")),
        "项目名称": clean(row.get("XMMC")),
        "单据编号": clean(row.get("DJBH")),
        "本次实缴数": amount_text(row.get("BCSJS$T_KK_SJTHB_CB")),
        "本次退回数": amount_text(row.get("BCTHS$T_KK_SJTHB_CB")),
        "上缴内容": clean(row.get("NR$T_KK_SJTHB_CB")),
        "备注": clean(row.get("BZ")),
        "附件": clean(row.get("f_FJ") or row.get("FJ")),
        "录入人": clean(row.get("LRR")),
        "单据日期": clean(row.get("DJRQ"))[:10],
    }


ensure_payload_table()
with gzip.open(PATH, "rt", encoding="utf-8") as handle:
    rows = json.load(handle)["rows"]

Claim = env["sc.expense.claim"].sudo().with_context(active_test=False)  # noqa: F821
Action = env["ir.actions.act_window"].sudo()  # noqa: F821
Currency = env.ref("base.CNY", raise_if_not_found=False)  # noqa: F821
created = updated = 0
seen: set[str] = set()

for index, row in enumerate(rows, start=1):
    key = row_key(row, index)
    seen.add(key)
    rec = Claim.search([("legacy_source_model", "=", SURFACE), ("legacy_record_id", "=", key)], limit=1)
    project = project_for(row)
    vals = {
        "source_origin": "legacy",
        "claim_type": "deduction_refund",
        "state": "legacy_confirmed",
        "project_id": project.id,
        "name": clean(row.get("DJBH")) or key,
        "date_claim": parse_date(row.get("DJRQ")),
        "fill_date": parse_date(row.get("DJRQ")),
        "expense_type": "扣款实缴退回",
        "summary": clean(row.get("NR$T_KK_SJTHB_CB") or row.get("BZ") or row.get("DJBH")),
        "amount": amount(row.get("BCTHS$T_KK_SJTHB_CB")),
        "approved_amount": amount(row.get("BCTHS$T_KK_SJTHB_CB")),
        "currency_id": Currency.id,
        "legacy_source_model": SURFACE,
        "legacy_source_table": SOURCE_TABLE,
        "legacy_record_id": key,
        "legacy_document_no": clean(row.get("DJBH")),
        "legacy_document_state": clean(row.get("DJZT")),
        "legacy_visible_document_state": clean(row.get("DJZT")),
        "legacy_visible_document_no": clean(row.get("DJBH")),
        "legacy_visible_date": parse_dt(row.get("DJRQ")),
        "legacy_visible_project_name": clean(row.get("XMMC")),
        "legacy_visible_adjustment_item": clean(row.get("NR$T_KK_SJTHB_CB")),
        "legacy_visible_amount": amount_text(row.get("BCTHS$T_KK_SJTHB_CB")),
        "legacy_visible_note": clean(row.get("BZ") or row.get("BZ$T_KK_SJTHB_CB")),
        "legacy_visible_attachment": clean(row.get("FJ") or row.get("f_FJ")),
        "creator_legacy_user_id": clean(row.get("LRRID")),
        "creator_name": clean(row.get("LRR")),
        "created_time": parse_dt(row.get("LRSJ")),
        "note": "SCBS55 old visible surface mirror: %s; header=%s; child=%s; attachment=%s"
        % (SURFACE, clean(row.get("Id")), clean(row.get("Id$T_KK_SJTHB_CB")), clean(row.get("FJ") or row.get("f_FJ"))),
        "active": True,
    }
    if rec:
        rec.write(vals)
        updated += 1
    else:
        rec = Claim.create(vals)
        created += 1
    write_payload(rec, visible_payload(row))

stale = Claim.search([("legacy_source_model", "=", SURFACE), ("legacy_record_id", "not in", list(seen) or ["__none__"])])
stale_count = len(stale)
if stale:
    stale.write({"legacy_source_model": f"{SURFACE}:hidden", "active": False})

domain = [("legacy_source_model", "=", SURFACE)]
Action.browse(ACTION_ID).write({"domain": repr(domain)})
final_count = Claim.search_count(domain)
result = {
    "surface": SURFACE,
    "old": len(rows),
    "created": created,
    "updated": updated,
    "stale_hidden": stale_count,
    "final_count": final_count,
    "domain": repr(domain),
    "status": "OK" if final_count == len(rows) else "COUNT_MISMATCH",
}
env.cr.commit()  # noqa: F821
print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
