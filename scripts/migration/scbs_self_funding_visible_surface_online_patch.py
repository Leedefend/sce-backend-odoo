# -*- coding: utf-8 -*-
"""Mirror old SCBS self-funding visible list rows into Odoo.

Run inside ``odoo shell`` with OLD_SCBS_USERNAME and OLD_SCBS_PASSWORD set.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin

import requests

sys.path.insert(0, str(Path.cwd()))
from scripts.verify.online_capture_security import require_online_capture  # noqa: E402


BASE_URL = os.getenv("OLD_SCBS_BASE_URL", "").rstrip("/")
PAGE_SIZE = int(os.getenv("SCBS_SELF_FUNDING_VISIBLE_PAGE_SIZE", "500"))
SPECS = {
    "income_visible": {
        "name": "自筹垫付收入",
        "config_id": "cd66fc4948074ccb935d328a19f08a64",
        "source_table": "online_old_scbs:C_JFHKLR:self_funding_income",
    },
    "refund_visible": {
        "name": "自筹垫付退回",
        "config_id": "758c318d761548c4875859fc6ecc665c",
        "source_table": "online_old_scbs:C_JFHKLR_TH_ZCDF:self_funding_refund",
    },
}


def clean(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


def amount(value: object) -> float:
    text = clean(value).replace(",", "")
    return float(text) if text else 0.0


def date_value(value: object) -> str | bool:
    text = clean(value)
    return text[:10] if text else False


def datetime_value(value: object) -> str | bool:
    text = clean(value)
    if not text:
        return False
    text = text.replace("T", " ")
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            parsed = datetime.strptime(text[:19] if "%H" in fmt else text[:10], fmt)
            return parsed.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue
    return False


def state_label(value: object, fallback: object = "") -> str:
    text = clean(fallback)
    if text:
        return text
    return {"2": "已审核", "1": "审核中", "0": "未审核", "-1": "已驳回"}.get(clean(value), clean(value))


def login() -> tuple[requests.Session, str]:
    require_online_capture(("scbs",))
    username = os.getenv("OLD_SCBS_USERNAME")
    password = os.getenv("OLD_SCBS_PASSWORD")
    if not username or not password:
        raise RuntimeError("OLD_SCBS_USERNAME and OLD_SCBS_PASSWORD are required")
    session = requests.Session()
    payload = {
        "Type": "Common",
        "Param": {
            "UserName": username,
            "IsEncrypt": False,
            "Password": password,
            "PasswordMd5": hashlib.md5(password.encode("utf-8")).hexdigest(),
            "VerificationCodeKey": "",
            "VerificationCode": "",
            "EncryptLockKey": "",
            "PhoneNumber": "",
            "SMSVerificationCodeKey": "",
            "SMSVerificationCode": "",
        },
    }
    response = session.post(f"{BASE_URL}/api/System/UserApi/Login", json=payload, timeout=60)
    response.raise_for_status()
    body = response.json()
    if str(body.get("Code")) != "10000" or not body.get("Data", {}).get("Token"):
        raise RuntimeError({"old_system_login_failed": {"Code": body.get("Code"), "Msg": body.get("Msg")}})
    return session, body["Data"]["Token"]


def api_get(session: requests.Session, token: str, path: str) -> dict:
    response = session.get(urljoin(f"{BASE_URL}/api/", path), headers={"Token": token}, timeout=60)
    response.raise_for_status()
    body = response.json()
    if str(body.get("Code")) != "10000":
        raise RuntimeError({"old_system_get_failed": path, "Code": body.get("Code"), "Msg": body.get("Msg")})
    return body["Data"]


def api_post(session: requests.Session, token: str, path: str, payload: dict) -> dict:
    response = session.post(urljoin(f"{BASE_URL}/api/", path), json=payload, headers={"Token": token}, timeout=120)
    response.raise_for_status()
    body = response.json()
    if str(body.get("Code")) != "10000":
        raise RuntimeError({"old_system_post_failed": path, "Code": body.get("Code"), "Msg": body.get("Msg")})
    return body


def enclosure_ident(detail: dict) -> str:
    fields: list[str] = []

    def visit(items: list[dict]) -> None:
        for item in items or []:
            info = item.get("Info") or {}
            if clean(info.get("Format")).lower() == "enclosure" and clean(info.get("Field")):
                fields.append(clean(info.get("Field")))
            visit(item.get("ChildConfig") or [])

    visit(detail.get("ContentTable", {}).get("TableConfig", {}).get("ColumnConfig") or [])
    return ",".join(fields) + ("," if fields else "")


def list_payload(config: dict, page: int) -> tuple[str, dict]:
    detail = json.loads(config.get("DETAIL_CONFIG") or "{}")
    other = detail.get("OtherConfig") or {}
    main = other.get("MainTable") or {}
    where = deepcopy(detail.get("WhereInfo") or {})
    if other.get("IsApproval") is not False and clean(main.get("DJBH_Field")):
        where["DJZT"] = {"Field": "DJZT", "Manner": "主表", "Rule": "In", "Data": ["2", "1", "0", "-1"]}
    payload = {
        "BusinessId": config.get("BUSINESSID"),
        "ConfigId": config.get("ID"),
        "OrderInfo": other.get("OrderInfo") or "pid desc",
        "PageIndex": page,
        "PageSize": PAGE_SIZE,
        "WhereInfo": where,
        "TableName": main.get("TableName"),
        "ShowType": other.get("ShowType") or [],
        "ShowTypeList": other.get("ShowTypeList") or [],
        "IsSearchNextGS": other.get("IsSearchNextGS") or False,
        "FieldName": {
            "IdField": main.get("IdField") or "Id",
            "ProjectIdField": main.get("ProjectIdField"),
            "LRRID_Field": main.get("LRRID_Field"),
            "Delete_Field": main.get("Delete_Field"),
            "IsShowAdminProject": other.get("IsShowAdminProject"),
        },
        "EnclosureIdent": enclosure_ident(detail),
        "SpecialUserId": other.get("SpecialUserId") or "",
        "SpecialConfig": other.get("SpecialConfig") or {},
        "IsDelData": False,
        "JudgeDeleteField": main.get("JudgeDeleteField", True),
        "OrderInfoSQL": {"SQLID": "", "IsDesc": False},
    }
    if other.get("SelectSQLID"):
        payload["SelectSQLID"] = other.get("SelectSQLID")
    elif other.get("CustomSelectSql"):
        payload["CustomSelectSql"] = other.get("CustomSelectSql")
    if main.get("IsProjectSearch") is False:
        payload["FieldName"].pop("ProjectIdField", None)
    path = "LowCode/FormApi/ListByTableName"
    if other.get("ListApi"):
        path = str(other["ListApi"]).removeprefix("/api/")
    elif other.get("ListProcedure"):
        payload["Procedure"] = other["ListProcedure"]
        path = "LowCode/FormApi/ListByProcedure"
    return path, payload


def fetch_rows(session: requests.Session, token: str, config_id: str) -> tuple[int, list[dict]]:
    config = api_get(session, token, f"LowCode/FormApi/GetConfigById?Id={config_id}&LoadInitData=true")
    rows: list[dict] = []
    total = 0
    page = 1
    while True:
        path, payload = list_payload(config, page)
        body = api_post(session, token, path, payload)
        total = int(body.get("DataCount") or 0)
        batch = body.get("Data") or []
        rows.extend(batch)
        if len(rows) >= total or not batch:
            break
        page += 1
    return total, rows


def vals_for_row(line_type: str, source_table: str, row: dict) -> dict:
    if line_type == "income_visible":
        self_amount = amount(row.get("f_JE"))
        refund_amount = amount(row.get("THJE"))
        return {
            "source_table": source_table,
            "legacy_record_id": clean(row.get("Id")),
            "legacy_pid": clean(row.get("PID") or row.get("pid")),
            "line_type": line_type,
            "document_no": clean(row.get("DJBH")),
            "document_date": date_value(row.get("f_RQ")),
            "document_state": clean(row.get("DJZT")),
            "document_state_label": state_label(row.get("DJZT"), row.get("DJZTText")),
            "push_result": clean(row.get("TSJG") or row.get("D_SCBSJS_IsPush")),
            "kingdee_document_no": clean(row.get("OTHER_SYSTEM_CODE")),
            "project_legacy_id": clean(row.get("XMID")),
            "project_name": clean(row.get("XMMC")),
            "partner_legacy_id": clean(row.get("WLDWID")),
            "partner_name": clean(row.get("WLDWMC")),
            "income_category": clean(row.get("f_SRLBName")),
            "receipt_type": clean(row.get("type")),
            "legacy_category": clean(row.get("LX")),
            "title": clean(row.get("BT")),
            "need_refund": clean(row.get("SFTH")),
            "self_funding_amount": self_amount,
            "refund_amount": refund_amount,
            "unreturned_amount": amount(row.get("WTJE")) if clean(row.get("WTJE")) else self_amount - refund_amount,
            "payment_method": clean(row.get("FKFSMC")),
            "account_name": clean(row.get("SKZH")),
            "attachment_text": clean(row.get("f_FJ")),
            "entry_user": clean(row.get("LRR")),
            "entry_time": datetime_value(row.get("LRSJ")),
            "note": clean(row.get("f_BZ")),
            "deleted_flag": clean(row.get("DEL")) or "0",
            "import_batch": "online_old_scbs_self_funding_visible_v1",
            "active": True,
        }
    refund_amount = amount(row.get("THJE"))
    return {
        "source_table": source_table,
        "legacy_record_id": clean(row.get("Id")),
        "legacy_pid": clean(row.get("pid") or row.get("PID")),
        "line_type": line_type,
        "document_no": clean(row.get("DJBH")),
        "document_date": date_value(row.get("DJRQ")),
        "document_state": clean(row.get("DJZT")),
        "document_state_label": state_label(row.get("DJZT"), row.get("DJZTText")),
        "push_result": clean(row.get("TSJG") or row.get("D_SCBSJS_IsPush")),
        "project_legacy_id": clean(row.get("XMID")),
        "project_name": clean(row.get("XMMC")),
        "partner_legacy_id": clean(row.get("XMJLID")),
        "partner_name": clean(row.get("WLDWFKDW") or row.get("XMJLMC")),
        "legacy_category": clean(row.get("SJBMC") or "自筹垫付退回"),
        "refund_amount": refund_amount,
        "unreturned_amount": 0 - refund_amount,
        "attachment_text": clean(row.get("f_FJ")),
        "entry_user": clean(row.get("LRR")),
        "entry_time": datetime_value(row.get("LRSJ")),
        "note": clean(row.get("BZ")),
        "deleted_flag": clean(row.get("DEL")) or "0",
        "import_batch": "online_old_scbs_self_funding_visible_v1",
        "active": True,
    }


session, token = login()
Model = env["sc.legacy.self.funding.fact"].sudo().with_context(active_test=False)  # noqa: F821
summary = {}
for line_type, spec in SPECS.items():
    expected_count, old_rows = fetch_rows(session, token, spec["config_id"])
    source_table = spec["source_table"]
    existing = {
        rec["legacy_record_id"]: rec["id"]
        for rec in Model.search_read(
            [("source_table", "=", source_table), ("line_type", "=", line_type)],
            ["legacy_record_id"],
        )
    }
    seen: set[str] = set()
    created = 0
    updated = 0
    for row in old_rows:
        vals = vals_for_row(line_type, source_table, row)
        key = vals["legacy_record_id"]
        if not key:
            continue
        seen.add(key)
        rec_id = existing.get(key)
        if rec_id:
            Model.browse(rec_id).write(vals)
            updated += 1
        else:
            Model.create(vals)
            created += 1
    stale = Model.search(
        [
            ("source_table", "=", source_table),
            ("line_type", "=", line_type),
            ("legacy_record_id", "not in", list(seen) or ["__none__"]),
        ]
    )
    stale_count = len(stale)
    stale.unlink()
    actual_count = Model.search_count([("source_table", "=", source_table), ("line_type", "=", line_type)])
    summary[line_type] = {
        "name": spec["name"],
        "config_id": spec["config_id"],
        "expected_old_count": expected_count,
        "fetched_rows": len(old_rows),
        "created": created,
        "updated": updated,
        "deleted_stale": stale_count,
        "actual_new_count": actual_count,
    }

env.cr.commit()  # noqa: F821
status = "PASS" if all(item["expected_old_count"] == item["actual_new_count"] for item in summary.values()) else "FAIL"
print("SCBS_SELF_FUNDING_VISIBLE_SURFACE_ONLINE_PATCH=" + json.dumps({"status": status, "summary": summary}, ensure_ascii=False, sort_keys=True))
