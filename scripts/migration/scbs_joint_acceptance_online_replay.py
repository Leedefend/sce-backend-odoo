# -*- coding: utf-8 -*-
"""Replay SCBS joint acceptance surfaces from the online old system.

Run inside ``odoo shell`` with OLD_SCBS_USERNAME and OLD_SCBS_PASSWORD set.
The replay deliberately separates the SCBS joint old-system rows from the
SCBSLY direct-project rows by source identifiers, so same-label menus do not
pollute each other.
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
PAGE_SIZE = int(os.getenv("SCBS_JOINT_ACCEPTANCE_PAGE_SIZE", "100"))
REQUEST_TIMEOUT = int(os.getenv("SCBS_JOINT_ACCEPTANCE_REQUEST_TIMEOUT", "60"))
REQUEST_RETRIES = int(os.getenv("SCBS_JOINT_ACCEPTANCE_REQUEST_RETRIES", "3"))
SOURCE_SYSTEM = "online_old_scbs"
ARTIFACT_ROOT = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", "artifacts/migration"))
OUTPUT_JSON = ARTIFACT_ROOT / "scbs_joint_acceptance_online_replay_result_v1.json"

SELF_FUNDING_SPECS = {
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

CONTRACT_SPECS = {
    "supplier_contract": {
        "name": "供货合同",
        "category": "合同类单据",
        "config_id": "77585134a02a48e7bd578e8ee3dd5bf2",
        "expected_count": 5492,
    },
    "labor_contract": {
        "name": "劳务合同",
        "category": "合同类单据",
        "config_id": "838f5d5f02f34770977a6195d072ba30",
        "expected_count": 22,
    },
    "rental_contract": {
        "name": "租赁合同",
        "category": "合同类单据",
        "config_id": "a83d43fc44fa43d2abf8b94739e7f7be",
        "expected_count": 27,
    },
}

DOCUMENT_NO_FIELDS = ("DJBH", "HTBH", "f_HTBH", "WBHTBH", "BH", "DJH", "JSDH")
TITLE_FIELDS = ("HTBT", "BT", "f_GCMC", "FBNR", "f_HTNR", "GCMC", "CLMC", "MC")
DATE_FIELDS = ("DJRQ", "RQ", "QDSJ", "f_QDRQ", "f_LRRQ", "LRSJ", "f_LRSJ", "HTDLRQ", "f_HTDLRQ")
PROJECT_ID_FIELDS = ("XMID", "ProjectId", "SJBXXMID")
PROJECT_NAME_FIELDS = ("ProjectName", "XMMC", "f_XMMC", "TSXMMC", "f_GCMC", "SJBXXM")
PARTNER_FIELDS = ("f_GYSName", "f_BZZ", "FBDW", "CBF", "FBF", "GYDW", "SGDW", "JSDW", "ZLDW", "WLDWMC")
AMOUNT_FIELDS = ("ZJE", "ZHSJE", "JE", "HTJE", "GCYSZJ", "YKPJE", "YFKJE", "WFKJE", "WKPJE")
QUANTITY_FIELDS = ("ZSL", "SL", "GCSL")
STATE_FIELDS = ("DJZTText", "DJZT", "ZT")
CREATOR_FIELDS = ("LRR", "f_LRR", "BZR", "DJR", "CJR")
CREATOR_ID_FIELDS = ("LRRID", "BXRID", "DJRID", "CJRID")
CREATED_TIME_FIELDS = ("LRSJ", "f_LRSJ", "f_LRRQ", "XGSJ", "CJSJ")
ATTACHMENT_FIELDS = ("f_FJ", "FJ")
NOTE_FIELDS = ("BZ1", "BZ", "f_BZ", "SXSM", "SM", "NR")


def clean(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


def md5(value: str) -> str:
    return hashlib.md5(value.encode("utf-8")).hexdigest()


def amount(value: object) -> float:
    text = clean(value).replace(",", "").replace("￥", "").replace("¥", "")
    if not text:
        return 0.0
    try:
        return float(text)
    except ValueError:
        match = re.search(r"-?\d+(?:\.\d+)?", text)
        return float(match.group(0)) if match else 0.0


def first_text(row: dict, fields: tuple[str, ...]) -> str:
    for field in fields:
        value = clean(row.get(field))
        if value:
            return value
    return ""


def first_amount(row: dict, fields: tuple[str, ...]) -> float:
    for field in fields:
        value = amount(row.get(field))
        if value:
            return value
    return 0.0


def date_value(value: object) -> str | bool:
    text = clean(value)
    return text[:10] if text else False


def datetime_value(value: object) -> str | bool:
    text = clean(value).replace("T", " ").replace("/", "-")
    if not text:
        return False
    text = re.sub(r"\.\d+$", "", text)
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            length = 19 if "%S" in fmt else 16 if "%M" in fmt else 10
            parsed = datetime.strptime(text[:length], fmt)
            return parsed.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue
    return False


def state_label(value: object, fallback: object = "") -> str:
    text = clean(fallback)
    if text:
        return text
    return {"2": "已审核", "1": "审核中", "0": "未审核", "-1": "已驳回"}.get(clean(value), clean(value))


def login() -> tuple[requests.Session, str, dict]:
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
            "PasswordMd5": md5(password),
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
    user = body["Data"]
    return session, user["Token"], user


def api_get(session: requests.Session, token: str, path: str) -> dict:
    response = session.get(urljoin(f"{BASE_URL}/api/", path), headers={"Token": token}, timeout=60)
    response.raise_for_status()
    body = response.json()
    if str(body.get("Code")) != "10000":
        raise RuntimeError({"old_system_get_failed": path, "Code": body.get("Code"), "Msg": body.get("Msg")})
    return body["Data"]


def api_post(session: requests.Session, token: str, path: str, payload: dict) -> dict:
    last_error = None
    for attempt in range(1, REQUEST_RETRIES + 1):
        try:
            response = session.post(
                urljoin(f"{BASE_URL}/api/", path),
                json=payload,
                headers={"Token": token},
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            body = response.json()
            if str(body.get("Code")) != "10000":
                raise RuntimeError({"Code": body.get("Code"), "Msg": body.get("Msg")})
            return body
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            print(
                "SCBS_JOINT_ACCEPTANCE_API_RETRY="
                + json.dumps(
                    {
                        "path": path,
                        "config_id": payload.get("ConfigId"),
                        "page_index": payload.get("PageIndex"),
                        "attempt": attempt,
                        "error": str(exc)[:240],
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                ),
                flush=True,
            )
    raise RuntimeError(
        {
            "old_system_post_failed": path,
            "config_id": payload.get("ConfigId"),
            "page_index": payload.get("PageIndex"),
            "error": str(last_error),
        }
    )


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
    other = detail.get("OtherConfig") if isinstance(detail.get("OtherConfig"), dict) else {}
    main = other.get("MainTable") if isinstance(other.get("MainTable"), dict) else {}
    where = deepcopy(detail.get("WhereInfo") if isinstance(detail.get("WhereInfo"), dict) else {})
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
        "BMFiled": other.get("BMFiled"),
        "IsSearchNextGS": other.get("IsSearchNextGS") or False,
        "FWZDFiled": other.get("FWZDFiled"),
        "IsEmptyAllVisible": other.get("IsEmptyAllVisible"),
        "ShowDataToUserIdByDJZT": other.get("ShowDataToUserIdByDJZT"),
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
    path = "LowCode/FormApi/ListByTableName"
    if other.get("ListApi"):
        path = str(other["ListApi"]).removeprefix("/api/")
    elif other.get("ListProcedure"):
        payload["Procedure"] = other["ListProcedure"]
        path = "LowCode/FormApi/ListByProcedure"
    if other.get("SelectSQLID"):
        payload["SelectSQLID"] = other.get("SelectSQLID")
    elif other.get("CustomSelectSql"):
        payload["CustomSelectSql"] = other.get("CustomSelectSql")
    if main.get("IsProjectSearch") is False:
        payload["FieldName"].pop("ProjectIdField", None)
    if isinstance(other.get("ListDisplayType"), dict) and other["ListDisplayType"].get("FromTableShow"):
        payload["ListDisplayType"] = other["ListDisplayType"]
    return path, payload


def fetch_rows(session: requests.Session, token: str, config_id: str, name: str) -> tuple[int, list[dict]]:
    config = api_get(session, token, f"LowCode/FormApi/GetConfigById?Id={config_id}&LoadInitData=true")
    rows: list[dict] = []
    total = 0
    page = 1
    while True:
        path, payload = list_payload(config, page)
        body = api_post(session, token, path, payload)
        total = int(body.get("DataCount") or 0)
        batch = body.get("Data") or []
        rows.extend(row for row in batch if isinstance(row, dict))
        print(
            "SCBS_JOINT_ACCEPTANCE_FETCH_PAGE="
            + json.dumps(
                {
                    "name": name,
                    "config_id": config_id,
                    "page": page,
                    "batch": len(batch),
                    "fetched": len(rows),
                    "total": total,
                },
                ensure_ascii=False,
                sort_keys=True,
            ),
            flush=True,
        )
        if len(rows) >= total or not batch:
            break
        page += 1
    return total, rows


def ensure_allowed_db() -> None:
    allowlist = {
        item.strip()
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_odoo,sc_demo").split(",")
        if item.strip()
    }
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_replay": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def project_id_for(legacy_id: str, name: str) -> int | bool:
    Project = env["project.project"].sudo().with_context(active_test=False)  # noqa: F821
    rec = Project.browse()
    if legacy_id and "legacy_project_id" in Project._fields:
        rec = Project.search([("legacy_project_id", "=", legacy_id)], limit=1)
    if not rec and name:
        rec = Project.search([("name", "=", name)], limit=1)
    return rec.id if rec else False


def partner_id_for(legacy_id: str, name: str) -> int | bool:
    Partner = env["res.partner"].sudo().with_context(active_test=False)  # noqa: F821
    rec = Partner.browse()
    for field in ("legacy_partner_id", "sc_legacy_partner_id"):
        if legacy_id and field in Partner._fields:
            rec = Partner.search([(field, "=", legacy_id)], limit=1)
            if rec:
                return rec.id
    if name:
        rec = Partner.search([("name", "=", name)], limit=1)
    return rec.id if rec else False


def self_funding_vals(line_type: str, source_table: str, row: dict) -> dict:
    if line_type == "income_visible":
        self_amount = amount(row.get("f_JE"))
        refund_amount = amount(row.get("THJE") or row.get("CZJE"))
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
            "deleted_flag": clean(row.get("DEL")) or "0",
            "project_legacy_id": clean(row.get("XMID")),
            "project_name": clean(row.get("XMMC")),
            "project_id": project_id_for(clean(row.get("XMID")), clean(row.get("XMMC"))),
            "partner_legacy_id": clean(row.get("WLDWID")),
            "partner_name": clean(row.get("WLDWMC")),
            "partner_id": partner_id_for(clean(row.get("WLDWID")), clean(row.get("WLDWMC"))),
            "income_category": clean(row.get("f_SRLBName")),
            "receipt_type": clean(row.get("type")),
            "legacy_category": clean(row.get("LX") or "自筹垫付"),
            "title": clean(row.get("BT")),
            "need_refund": clean(row.get("SFTH") or row.get("SFXYTHID")),
            "self_funding_amount": self_amount,
            "refund_amount": refund_amount,
            "unreturned_amount": amount(row.get("WTJE") or row.get("YSJE")) - refund_amount
            if clean(row.get("YSJE"))
            else self_amount - refund_amount,
            "payment_method": clean(row.get("FKFSMC")),
            "account_name": clean(row.get("SKZH")),
            "attachment_text": clean(row.get("f_FJ") or row.get("FJ")),
            "entry_user": clean(row.get("LRR")),
            "entry_time": datetime_value(row.get("LRSJ")),
            "note": clean(row.get("f_BZ") or row.get("BZ")),
            "import_batch": "online_old_scbs_joint_acceptance_v1",
            "active": True,
        }
    refund_amount = amount(row.get("THJE") or row.get("f_JE"))
    return {
        "source_table": source_table,
        "legacy_record_id": clean(row.get("Id")),
        "legacy_pid": clean(row.get("pid") or row.get("PID")),
        "line_type": line_type,
        "document_no": clean(row.get("DJBH")),
        "document_date": date_value(row.get("DJRQ") or row.get("f_RQ")),
        "document_state": clean(row.get("DJZT")),
        "document_state_label": state_label(row.get("DJZT"), row.get("DJZTText")),
        "push_result": clean(row.get("TSJG") or row.get("D_SCBSJS_IsPush")),
        "deleted_flag": clean(row.get("DEL")) or "0",
        "project_legacy_id": clean(row.get("XMID")),
        "project_name": clean(row.get("XMMC")),
        "project_id": project_id_for(clean(row.get("XMID")), clean(row.get("XMMC"))),
        "partner_legacy_id": clean(row.get("XMJLID") or row.get("WLDWID")),
        "partner_name": clean(row.get("WLDWFKDW") or row.get("XMJLMC") or row.get("WLDWMC")),
        "partner_id": partner_id_for(
            clean(row.get("XMJLID") or row.get("WLDWID")),
            clean(row.get("WLDWFKDW") or row.get("XMJLMC") or row.get("WLDWMC")),
        ),
        "legacy_category": clean(row.get("SJBMC") or "自筹垫付退回"),
        "refund_amount": refund_amount,
        "unreturned_amount": 0 - refund_amount,
        "attachment_text": clean(row.get("f_FJ") or row.get("FJ")),
        "entry_user": clean(row.get("LRR")),
        "entry_time": datetime_value(row.get("LRSJ")),
        "note": clean(row.get("BZ") or row.get("f_BZ")),
        "import_batch": "online_old_scbs_joint_acceptance_v1",
        "active": True,
    }


def replay_self_funding(session: requests.Session, token: str) -> dict:
    Model = env["sc.legacy.self.funding.fact"].sudo().with_context(active_test=False)  # noqa: F821
    result = {}
    for line_type, spec in SELF_FUNDING_SPECS.items():
        expected_count, rows = fetch_rows(session, token, spec["config_id"], spec["name"])
        source_table = spec["source_table"]
        seen: set[str] = set()
        created = updated = skipped = 0
        for row in rows:
            vals = self_funding_vals(line_type, source_table, row)
            key = vals["legacy_record_id"]
            if not key or key in seen:
                skipped += 1
                continue
            seen.add(key)
            rec = Model.search(
                [("source_table", "=", source_table), ("line_type", "=", line_type), ("legacy_record_id", "=", key)],
                limit=1,
            )
            if rec:
                rec.write(vals)
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
        stale.write({"active": False})
        active_count = Model.search_count([("source_table", "=", source_table), ("line_type", "=", line_type), ("active", "=", True)])
        result[line_type] = {
            "name": spec["name"],
            "config_id": spec["config_id"],
            "expected_old_count": expected_count,
            "fetched_rows": len(rows),
            "active_count": active_count,
            "created": created,
            "updated": updated,
            "skipped": skipped,
            "stale_deactivated": len(stale),
            "status": "PASS" if expected_count == len(rows) == active_count else "FAIL",
        }
    return result


def row_identity(row: dict) -> str:
    for field in ("Id", "id", "DJBH", "PID", "Pid", "pid"):
        value = clean(row.get(field))
        if value:
            return value
    payload = json.dumps(row, ensure_ascii=False, sort_keys=True, default=str)
    return "hash:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def direct_acceptance_vals(spec: dict, row: dict) -> dict:
    project_legacy_id = first_text(row, PROJECT_ID_FIELDS)
    project_name = first_text(row, PROJECT_NAME_FIELDS)
    return {
        "source_system": SOURCE_SYSTEM,
        "acceptance_label": spec["name"],
        "category": spec.get("category") or "",
        "legacy_config_id": spec["config_id"],
        "legacy_record_id": row_identity(row),
        "legacy_parent_id": first_text(row, ("PID", "Pid", "pid")),
        "document_no": first_text(row, DOCUMENT_NO_FIELDS),
        "document_title": first_text(row, TITLE_FIELDS),
        "document_date": first_datetime(row, DATE_FIELDS),
        "document_state": first_text(row, STATE_FIELDS),
        "project_id": project_id_for(project_legacy_id, project_name),
        "project_legacy_id": project_legacy_id,
        "project_name": project_name,
        "partner_name": first_text(row, PARTNER_FIELDS),
        "amount_total": first_amount(row, AMOUNT_FIELDS),
        "quantity": first_amount(row, QUANTITY_FIELDS),
        "creator_name": first_text(row, CREATOR_FIELDS),
        "creator_legacy_user_id": first_text(row, CREATOR_ID_FIELDS),
        "created_time": first_datetime(row, CREATED_TIME_FIELDS),
        "attachment_ref": first_text(row, ATTACHMENT_FIELDS),
        "note": first_text(row, NOTE_FIELDS),
        "raw_payload": json.dumps(row, ensure_ascii=False, sort_keys=True, default=str),
        "active": True,
    }


def first_datetime(row: dict, fields: tuple[str, ...]) -> str | bool:
    for field in fields:
        value = datetime_value(row.get(field))
        if value:
            return value
    return False


def replay_contracts(session: requests.Session, token: str) -> dict:
    Model = env["sc.legacy.direct.acceptance.fact"].sudo().with_context(active_test=False)  # noqa: F821
    result = {}
    for key, spec in CONTRACT_SPECS.items():
        expected_count, rows = fetch_rows(session, token, spec["config_id"], spec["name"])
        seen: set[str] = set()
        created = updated = skipped = 0
        for row in rows:
            vals = direct_acceptance_vals(spec, row)
            legacy_id = vals["legacy_record_id"]
            if not legacy_id or legacy_id in seen:
                skipped += 1
                continue
            seen.add(legacy_id)
            rec = Model.search(
                [
                    ("source_system", "=", SOURCE_SYSTEM),
                    ("acceptance_label", "=", spec["name"]),
                    ("legacy_record_id", "=", legacy_id),
                ],
                limit=1,
            )
            if rec:
                rec.write(vals)
                updated += 1
            else:
                Model.create(vals)
                created += 1
        stale = Model.search(
            [
                ("source_system", "=", SOURCE_SYSTEM),
                ("acceptance_label", "=", spec["name"]),
                ("legacy_config_id", "=", spec["config_id"]),
                ("legacy_record_id", "not in", list(seen) or ["__none__"]),
            ]
        )
        stale.write({"active": False})
        active_count = Model.search_count(
            [
                ("source_system", "=", SOURCE_SYSTEM),
                ("acceptance_label", "=", spec["name"]),
                ("legacy_config_id", "=", spec["config_id"]),
                ("active", "=", True),
            ]
        )
        result[key] = {
            "name": spec["name"],
            "config_id": spec["config_id"],
            "expected_old_count": expected_count,
            "locked_expected_count": spec["expected_count"],
            "fetched_rows": len(rows),
            "active_count": active_count,
            "created": created,
            "updated": updated,
            "skipped": skipped,
            "stale_deactivated": len(stale),
            "status": "PASS"
            if expected_count == spec["expected_count"] == len(rows) == active_count
            else "FAIL",
        }
    return result


def write_json(path: Path, payload: dict) -> None:
    target = path
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except PermissionError:
        target = Path("/tmp") / path.name
        target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    payload["output_json"] = str(target)


def main() -> None:
    ensure_allowed_db()
    session, token, user = login()
    self_funding = replay_self_funding(session, token)
    contracts = replay_contracts(session, token)
    env.cr.commit()  # noqa: F821
    failures = [
        {"kind": "self_funding", **item}
        for item in self_funding.values()
        if item["status"] != "PASS"
    ] + [{"kind": "contract", **item} for item in contracts.values() if item["status"] != "PASS"]
    summary = {
        "status": "PASS" if not failures else "FAIL",
        "mode": "scbs_joint_acceptance_online_replay",
        "db_name": env.cr.dbname,  # noqa: F821
        "source_system": SOURCE_SYSTEM,
        "old_user": {
            "UserId": user.get("UserId"),
            "UserName": user.get("UserName"),
            "PersonName": user.get("PersonName"),
            "ProjectId": user.get("ProjectId"),
            "ProjectName": user.get("ProjectName"),
            "CompanyId": user.get("CompanyId"),
            "CompanyName": user.get("CompanyName"),
        },
        "self_funding": self_funding,
        "contracts": contracts,
        "failures": failures,
    }
    write_json(OUTPUT_JSON, summary)
    print("SCBS_JOINT_ACCEPTANCE_ONLINE_REPLAY=" + json.dumps(summary, ensure_ascii=False, sort_keys=True))
    if failures:
        raise RuntimeError(summary)


main()
