#!/usr/bin/env python3
"""Mirror old SCBS tender guarantee list surfaces into action-specific rows."""

from __future__ import annotations

import gzip
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


SPECS = {
    18: {
        "path": "/tmp/scbs_55_old_live_full_rows_seq018_tender_guarantee.json.gz",
        "action_id": 868,
        "surface": "online_old_scbs:ZJGL_BZJGL_Branch_SBZJDJ:list868",
        "table": "ZJGL_BZJGL_Branch_SBZJDJ",
        "type": "out",
        "amount": "JE",
        "date": "DJRQ",
        "doc": "DJBH",
        "project": "XMMC",
        "tender": "TBXMMC",
        "labels": ["状态", "单据编号", "投标项目名称", "项目名称", "所属公司", "金额", "已退保证金金额", "转款单位", "汇款方式", "保证金类型", "收款账户", "收款账户名称", "备注", "附件", "录入人", "录入时间"],
    },
    19: {
        "path": "/tmp/scbs_55_old_live_full_rows_seq019_tender_guarantee_return.json.gz",
        "action_id": 869,
        "surface": "online_old_scbs:ZJGL_BZJGL_Branch_SBZJTH:list869",
        "table": "ZJGL_BZJGL_Branch_SBZJTH",
        "type": "return",
        "amount": "THJE",
        "date": "DJRQ",
        "doc": "DJBH",
        "project": "XMMC",
        "tender": "TBXMMC",
        "labels": ["状态", "收保证金单号", "单据编号", "项目名称", "投标项目名称", "退还金额", "备注", "退还账号", "退还开户行", "单位", "收款开户行", "收款账号", "录入人", "录入时间", "附件"],
    },
    20: {
        "path": "/tmp/scbs_55_old_live_full_rows_seq020_tender_guarantee_pay.json.gz",
        "action_id": 870,
        "surface": "online_old_scbs:ZJGL_BZJGL_Pay_FBZJ:list870",
        "table": "ZJGL_BZJGL_Pay_FBZJ",
        "type": "out",
        "amount": "BZJJE",
        "date": "TXRQ",
        "doc": "DJBH",
        "project": "XMMC",
        "tender": "TBXMMC",
        "labels": ["状态", "推送结果", "金蝶单据编号", "单据编号", "投标项目", "工程项目", "保证金类型", "所属公司", "保证金金额", "已退金额", "未退金额", "是否需要退回", "收款单位", "支付账户", "备注", "附件", "录入人", "录入时间"],
    },
    21: {
        "path": "/tmp/scbs_55_old_live_full_rows_seq021_tender_guarantee_pay_return.json.gz",
        "action_id": 871,
        "surface": "online_old_scbs:ZJGL_BZJGL_Pay_FBZJTH:list871",
        "table": "ZJGL_BZJGL_Pay_FBZJTH",
        "type": "return",
        "amount": "THJE",
        "date": "THRQ",
        "doc": "DJBH",
        "project": "XMMC",
        "tender": "TBXMMC",
        "labels": ["状态", "推送结果", "退回单编号", "所属公司", "投标项目名称", "保证金类型", "退回项目", "退回金额", "退回账户", "收款单位", "备注", "录入人", "退回日期", "附件"],
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


def fact_id(value: str) -> int:
    return int(hashlib.sha1(value.encode("utf-8")).hexdigest()[:12], 16) % 2147483647


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


def row_id(row: dict[str, Any], index: int) -> str:
    return clean(row.get("Id") or row.get("ID") or row.get("pid") or index)


def visible_values(seq: int, row: dict[str, Any]) -> dict[str, str]:
    values = {
        "状态": state_label(row.get("DJZT")),
        "单据编号": clean(row.get("DJBH")),
        "收保证金单号": clean(row.get("SBZJDH")),
        "退回单编号": clean(row.get("DJBH")),
        "投标项目名称": clean(row.get("TBXMMC")),
        "投标项目": clean(row.get("TBXMMC")),
        "项目名称": clean(row.get("XMMC")),
        "工程项目": clean(row.get("XMMC")),
        "退回项目": clean(row.get("XMMC")),
        "所属公司": clean(row.get("SSGS")),
        "金额": amount_text(row.get("JE")),
        "保证金金额": amount_text(row.get("BZJJE") or row.get("Y_BZJJE")),
        "退还金额": amount_text(row.get("THJE")),
        "退回金额": amount_text(row.get("THJE")),
        "已退保证金金额": amount_text(row.get("YTBZJJE")),
        "已退金额": amount_text(row.get("YTJE") or row.get("D_QKXYJD_THJE")),
        "未退金额": amount_text(row.get("WTJE")),
        "转款单位": clean(row.get("DW")),
        "汇款方式": clean(row.get("HKFS")),
        "保证金类型": clean(row.get("BZJLX") or row.get("Y_BZJLX")),
        "收款账户": clean(row.get("SKZH")),
        "收款账户名称": clean(row.get("SKZHMC")),
        "收款单位": clean(row.get("SKDW") or row.get("Y_SKDW")),
        "收款开户行": clean(row.get("SKKHH")),
        "收款账号": clean(row.get("SKZH")),
        "退还账号": clean(row.get("THKHHZH")),
        "退还开户行": clean(row.get("THKHH")),
        "退回账户": clean(row.get("ZHHM") or row.get("THZH")),
        "支付账户": clean(row.get("ZFZH")),
        "单位": clean(row.get("DW")),
        "备注": clean(row.get("BZ") or row.get("Y_BZ") or row.get("SM")),
        "附件": clean(row.get("f_FJ") or row.get("FJ")),
        "录入人": clean(row.get("LRR")),
        "录入时间": clean(row.get("LRSJ")),
        "退回日期": clean(row.get("THRQ"))[:10],
        "推送结果": clean(row.get("TSJG") or row.get("D_SCBSJS_IsPush")),
        "金蝶单据编号": clean(row.get("OTHER_SYSTEM_CODE")),
        "是否需要退回": clean(row.get("D_SCBSJS_SFXYTH")),
    }
    return {label: values.get(label, "") for label in SPECS[seq]["labels"]}


def import_surface(seq: int) -> dict[str, Any]:
    spec = SPECS[seq]
    with gzip.open(Path(spec["path"]), "rt", encoding="utf-8") as handle:
        rows = json.load(handle)["rows"]
    Bid = env["tender.bid"].sudo().with_context(active_test=False)  # noqa: F821
    Guarantee = env["tender.guarantee"].sudo().with_context(active_test=False)  # noqa: F821
    Action = env["ir.actions.act_window"].sudo()  # noqa: F821
    created = updated = 0
    seen: set[int] = set()
    for index, row in enumerate(rows, start=1):
        old_id = row_id(row, index)
        legacy_fact_id = fact_id(f"{spec['surface']}:{old_id}")
        seen.add(legacy_fact_id)
        project = project_for(row)
        bid = Bid.search([("legacy_fact_model", "=", spec["surface"]), ("legacy_fact_id", "=", legacy_fact_id)], limit=1)
        bid_vals = {
            "name": clean(row.get(spec["doc"])) or old_id,
            "tender_name": clean(row.get(spec["tender"]) or row.get(spec["project"]) or row.get(spec["doc"]) or old_id),
            "project_id": project.id,
            "state": "submitted",
            "legacy_fact_model": spec["surface"],
            "legacy_fact_id": legacy_fact_id,
            "legacy_fact_type": spec["table"],
            "legacy_note": f"SCBS55 old visible surface mirror: {spec['surface']}; old_id={old_id}",
            "legacy_visible_document_state": clean(row.get("DJZT")),
            "legacy_visible_project_name": clean(row.get(spec["project"])),
            "legacy_visible_registration_time": parse_dt(row.get("LRSJ")),
            "legacy_visible_creator_name": clean(row.get("LRR")),
        }
        if bid:
            bid.write(bid_vals)
        else:
            bid = Bid.create(bid_vals)
        guarantee = Guarantee.search([("bid_id", "=", bid.id)], limit=1)
        guarantee_vals = {
            "bid_id": bid.id,
            "type": spec["type"],
            "date": parse_date(row.get(spec["date"])),
            "amount": amount(row.get(spec["amount"])),
            "state": "confirmed",
            "legacy_visible_document_state": clean(row.get("DJZT")),
            "legacy_visible_document_no": clean(row.get(spec["doc"])),
            "legacy_visible_project_name": clean(row.get(spec["project"])),
            "legacy_visible_creator_name": clean(row.get("LRR")),
            "legacy_visible_created_time": parse_dt(row.get("LRSJ")),
            "remark": f"SCBS55 old visible surface: {spec['surface']}; old_id={old_id}; {clean(row.get('BZ') or row.get('Y_BZ') or row.get('SM'))}",
        }
        if guarantee:
            guarantee.write(guarantee_vals)
            updated += 1
        else:
            guarantee = Guarantee.create(guarantee_vals)
            created += 1
        write_payload(guarantee, visible_values(seq, row))
    stale_bids = Bid.search([("legacy_fact_model", "=", spec["surface"]), ("legacy_fact_id", "not in", list(seen) or [-1])])
    stale_count = len(stale_bids)
    if stale_bids:
        stale_bids.write({"legacy_fact_model": f"{spec['surface']}:hidden"})
    domain = [("bid_id.legacy_fact_model", "=", spec["surface"])]
    Action.browse(spec["action_id"]).write({"domain": repr(domain)})
    final_count = Guarantee.search_count(domain)
    return {
        "seq": seq,
        "surface": spec["surface"],
        "old": len(rows),
        "created": created,
        "updated": updated,
        "stale_hidden": stale_count,
        "final_count": final_count,
        "domain": repr(domain),
        "status": "OK" if final_count == len(rows) else "COUNT_MISMATCH",
    }


ensure_payload_table()
result = {"surfaces": [import_surface(seq) for seq in sorted(SPECS)]}
env.cr.commit()  # noqa: F821
print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
