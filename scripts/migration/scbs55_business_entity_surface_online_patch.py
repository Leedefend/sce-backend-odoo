#!/usr/bin/env python3
"""Mirror old SCBS business-entity list surfaces into action-specific rows."""

from __future__ import annotations

import gzip
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


SPECS = {
    1: {
        "path": "/tmp/scbs_55_old_live_full_rows_seq001_business_entity.json.gz",
        "action_id": 853,
        "action_name": "SCBS55 010 供应商/合作单位",
        "surface": "online_old_scbs:T_Base_CooperatCompany:list853",
        "labels": [
            "单据状态",
            "推送结果",
            "项目名称",
            "单位编号",
            "合作类型",
            "单位名称",
            "开户银行",
            "账号",
            "统一社会信用代码",
            "主税率",
            "录入人",
            "录入时间",
            "账户信息",
            "营业执照",
            "开户信息或法人账号",
        ],
    },
    2: {
        "path": "/tmp/scbs_55_old_live_full_rows_seq002_business_entity.json.gz",
        "action_id": 854,
        "action_name": "SCBS55 020 往来单位",
        "surface": "online_old_scbs:T_Base_CooperatCompany:list854",
        "labels": [
            "单据状态",
            "项目名称",
            "单位名称",
            "收款金额",
            "付款金额",
            "开户姓名",
            "开户账号",
            "开户银行",
            "录入人",
            "录入时间",
            "银行账号",
        ],
    },
}


def clean(value: object) -> str:
    if value in (None, False):
        return ""
    text = re.sub(r"\s+", " ", str(value).replace("\u3000", " ").strip())
    return "" if text in {"False", "false", "None", "NULL"} else text


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
    return {
        "-1": "已作废",
        "0": "未审核",
        "1": "审核中",
        "2": "审核通过",
        "3": "已驳回",
        "4": "已作废",
    }.get(text, text)


def amount(value: object) -> str:
    text = clean(value)
    if not text:
        return ""
    try:
        number = float(text)
    except ValueError:
        return text
    return ("%.2f" % number).rstrip("0").rstrip(".")


def attachment(*values: object) -> str:
    parts = [clean(value) for value in values if clean(value)]
    return "；".join(parts)


def visible_values(seq: int, row: dict[str, Any]) -> dict[str, str]:
    values = {
        "单据状态": state_label(row.get("DJZT")),
        "推送结果": state_label(row.get("PJZT") or row.get("LYZT")),
        "项目名称": clean(row.get("XMMC") or row.get("XMBMC")),
        "单位编号": clean(row.get("DJBH") or row.get("DWID") or row.get("Id")),
        "合作类型": clean(row.get("HZLX") or row.get("ZGLX") or row.get("DWLX")),
        "单位名称": clean(row.get("DWMC") or row.get("DWJC")),
        "开户银行": clean(row.get("KHYH$T_Base_CooperatCompany_Account") or row.get("DGZHYH") or row.get("D_SCBSJS_KHYH")),
        "账号": clean(row.get("KHZH$T_Base_CooperatCompany_Account") or row.get("DGZHHM") or row.get("D_SCBSJS_YHZH")),
        "统一社会信用代码": clean(row.get("TYSHXYDM")),
        "主税率": clean(row.get("ZSLV")),
        "录入人": clean(row.get("LRR") or row.get("DJR")),
        "录入时间": clean(row.get("LRSJ") or row.get("DJRQ")),
        "账户信息": attachment(
            row.get("KHXM$T_Base_CooperatCompany_Account"),
            row.get("KHYH$T_Base_CooperatCompany_Account"),
            row.get("KHZH$T_Base_CooperatCompany_Account"),
        ),
        "营业执照": attachment(row.get("FJ_YYZZ_FJ"), row.get("FJ_YYZZ")),
        "开户信息或法人账号": attachment(
            row.get("FJ_KHXKZ_FJ"),
            row.get("FJ_KHXKZ"),
            row.get("DGZHMC"),
            row.get("DGZHHM"),
            row.get("DGZHYH"),
        ),
        "收款金额": amount(row.get("SKJE")),
        "付款金额": amount(row.get("FKJE")),
        "开户姓名": clean(row.get("KHXM$T_Base_CooperatCompany_Account") or row.get("DGZHMC")),
        "开户账号": clean(row.get("KHZH$T_Base_CooperatCompany_Account") or row.get("DGZHHM")),
        "银行账号": clean(row.get("KHZH$T_Base_CooperatCompany_Account") or row.get("DGZHHM")),
    }
    return {label: values.get(label, "") for label in SPECS[seq]["labels"]}


def visible_model_values(payload: dict[str, str]) -> dict[str, object]:
    return {
        "legacy_visible_document_state": clean(payload.get("单据状态")) or False,
        "legacy_visible_push_result": clean(payload.get("推送结果")) or False,
        "legacy_visible_cooperation_type": clean(payload.get("合作类型")) or False,
        "legacy_visible_bank_name": clean(payload.get("开户银行")) or False,
        "legacy_visible_account_no": clean(payload.get("账号") or payload.get("开户账号") or payload.get("银行账号")) or False,
        "legacy_visible_account_holder": clean(payload.get("开户姓名")) or False,
        "legacy_visible_social_credit_code": clean(payload.get("统一社会信用代码")) or False,
        "legacy_visible_main_tax_rate": clean(payload.get("主税率")) or False,
        "legacy_visible_receipt_amount": clean(payload.get("收款金额")) or False,
        "legacy_visible_payment_amount": clean(payload.get("付款金额")) or False,
    }


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


def row_legacy_key(seq: int, surface: str, row: dict[str, Any], index: int) -> str:
    old_id = clean(row.get("Id") or row.get("pid"))
    if seq == 2:
        child_id = clean(
            row.get("Id$T_Base_CooperatCompany_Account")
            or row.get("pid$T_Base_CooperatCompany_Account")
            or row.get("RowIndex")
            or index
        )
        return f"{surface}:{old_id}:{child_id}"
    return f"{surface}:{old_id}"


def import_surface(seq: int) -> dict[str, Any]:
    spec = SPECS[seq]
    path = Path(spec["path"])
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        payload = json.load(handle)
    rows = payload["rows"]
    Entity = env["sc.business.entity"].sudo().with_context(active_test=False)  # noqa: F821
    Action = env["ir.actions.act_window"].sudo()  # noqa: F821
    company = env.company  # noqa: F821
    surface = spec["surface"]
    created = updated = 0
    seen_legacy_xmids: set[str] = set()
    for index, row in enumerate(rows, start=1):
        old_id = clean(row.get("Id") or row.get("pid"))
        if not old_id:
            continue
        legacy_xmid = row_legacy_key(seq, surface, row, index)
        seen_legacy_xmids.add(legacy_xmid)
        rec = Entity.search(
            [
                ("company_id", "=", company.id),
                ("legacy_company_id", "=", surface),
                ("legacy_xmid", "=", legacy_xmid),
            ],
            limit=1,
        )
        visible_payload = visible_values(seq, row)
        vals = {
            "sequence": index,
            "name": clean(row.get("DWMC") or row.get("DWJC") or row.get("DJBH") or old_id),
            "company_id": company.id,
            "entity_type": "unknown",
            "mapping_state": "candidate",
            "legacy_xmid": legacy_xmid,
            "legacy_xmmc": clean(row.get("DWMC") or row.get("DWJC")),
            "legacy_company_id": surface,
            "legacy_company_name": clean(row.get("XMMC") or row.get("XMBMC")),
            "legacy_visible_created_time": parse_dt(row.get("LRSJ") or row.get("DJRQ")),
            "legacy_visible_creator_name": clean(row.get("LRR") or row.get("DJR")),
            "note": "SCBS55 old visible surface mirror: %s; old_id=%s; document_no=%s"
            % (surface, old_id, clean(row.get("DJBH"))),
            "active": True,
        }
        vals.update(visible_model_values(visible_payload))
        if rec:
            rec.write(vals)
            updated += 1
        else:
            rec = Entity.create(vals)
            created += 1
        write_payload(rec, visible_payload)

    stale = Entity.search(
        [
            ("company_id", "=", company.id),
            ("legacy_company_id", "=", surface),
            ("legacy_xmid", "not in", list(seen_legacy_xmids) or ["__none__"]),
        ]
    )
    stale_count = len(stale)
    if stale:
        stale.write({"legacy_company_id": f"{surface}:hidden", "active": False})

    domain = [("legacy_company_id", "=", surface)]
    action = Action.browse(spec["action_id"])
    if action.exists():
        action.write({"domain": repr(domain)})
    else:
        action = Action.search([("name", "=", spec["action_name"]), ("res_model", "=", "sc.business.entity")], limit=1)
        if action:
            action.write({"domain": repr(domain)})
    final_count = Entity.search_count(domain)
    return {
        "seq": seq,
        "surface": surface,
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
