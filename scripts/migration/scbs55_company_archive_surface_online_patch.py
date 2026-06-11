#!/usr/bin/env python3
"""Mirror old SCBS company document archive list into action 856."""

from __future__ import annotations

import gzip
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


PATH = Path("/tmp/scbs_55_old_live_full_rows_seq004_company_archive.json.gz")
SURFACE = "online_old_scbs:SGZL_RZRJ:list856"
ACTION_ID = 856


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
    legacy_project_id = clean(row.get("f_XMID"))
    if legacy_project_id and "legacy_project_id" in Project._fields:
        project = Project.search([("legacy_project_id", "=", legacy_project_id)], limit=1)
        if project:
            return project
    name = clean(row.get("f_GCMC"))
    if name:
        project = Project.search([("name", "ilike", name[:60])], limit=1)
        if project:
            return project
    return False


def row_key(row: dict[str, Any], index: int) -> str:
    header = clean(row.get("ID") or row.get("Id") or row.get("Pid"))
    child = clean(row.get("Id$SGZL_RZRJ_CB") or row.get("pid$SGZL_RZRJ_CB") or row.get("RowIndex") or index)
    return f"{header}:{child}"


def visible_payload(row: dict[str, Any]) -> dict[str, str]:
    return {
        "单据状态": state_label(row.get("DJZT")),
        "项目名称": clean(row.get("f_GCMC")),
        "资料类型": clean(row.get("ZLMC$SGZL_RZRJ_CB") or row.get("ZLMC")),
        "资料说明": clean(row.get("ZLSM$SGZL_RZRJ_CB") or row.get("f_SM")),
        "录入人": clean(row.get("LRR") or row.get("f_LRR")),
        "备注": clean(row.get("BZ")),
        "录入时间": clean(row.get("LRSJ") or row.get("f_LRSJ") or row.get("f_SJ")),
    }


ensure_payload_table()
with gzip.open(PATH, "rt", encoding="utf-8") as handle:
    rows = json.load(handle)["rows"]

Doc = env["sc.document.admin.document"].sudo().with_context(active_test=False)  # noqa: F821
Action = env["ir.actions.act_window"].sudo()  # noqa: F821
Currency = env.ref("base.CNY", raise_if_not_found=False)  # noqa: F821
created = updated = 0
seen: set[str] = set()

for index, row in enumerate(rows, start=1):
    key = row_key(row, index)
    seen.add(key)
    rec = Doc.search([("legacy_source_table", "=", SURFACE), ("legacy_source_id", "=", key)], limit=1)
    project = project_for(row)
    title = clean(row.get("ZLMC$SGZL_RZRJ_CB") or row.get("ZLSM$SGZL_RZRJ_CB") or row.get("DJBH") or key)
    vals = {
        "name": clean(row.get("DJBH")) or title,
        "document_no": clean(row.get("DJBH")),
        "fact_type": "company_document_archive",
        "project_id": project.id if project else False,
        "business_date": parse_date(row.get("f_SJ") or row.get("LRSJ")),
        "currency_id": Currency.id,
        "state": "done",
        "document_title": title,
        "description": clean(row.get("ZLSM$SGZL_RZRJ_CB") or row.get("f_SM")),
        "legacy_document_no": clean(row.get("DJBH")),
        "legacy_document_state": clean(row.get("DJZT")),
        "legacy_source_table": SURFACE,
        "legacy_source_id": key,
        "legacy_visible_project_name": clean(row.get("f_GCMC")),
        "legacy_visible_document_type": clean(row.get("ZLMC$SGZL_RZRJ_CB") or row.get("ZLMC")),
        "legacy_visible_description": clean(row.get("ZLSM$SGZL_RZRJ_CB") or row.get("f_SM")),
        "legacy_visible_creator_name": clean(row.get("LRR") or row.get("f_LRR")),
        "legacy_visible_note": clean(row.get("BZ")),
        "legacy_visible_created_time": parse_dt(row.get("LRSJ") or row.get("f_LRSJ") or row.get("f_SJ")),
        "active": True,
    }
    if rec:
        rec.write(vals)
        updated += 1
    else:
        rec = Doc.create(vals)
        created += 1
    write_payload(rec, visible_payload(row))

stale = Doc.search([("legacy_source_table", "=", SURFACE), ("legacy_source_id", "not in", list(seen) or ["__none__"])])
stale_count = len(stale)
if stale:
    stale.write({"legacy_source_table": f"{SURFACE}:hidden", "active": False})

domain = [("legacy_source_table", "=", SURFACE)]
Action.browse(ACTION_ID).write({"domain": repr(domain)})
final_count = Doc.search_count(domain)
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
