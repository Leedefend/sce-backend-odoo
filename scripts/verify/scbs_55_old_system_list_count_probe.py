#!/usr/bin/env python3
"""Fetch old SCBS55 list DataCount values from the live old system."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests


ROOT = Path(__file__).resolve().parents[2]
INPUT_CSV = ROOT / "docs/migration_alignment/scbs_55_user_visible_surface_live_alignment_v1.csv"
OUTPUT = ROOT / "artifacts/migration/scbs_55_old_system_list_count_probe_result_v1.json"
BASE_URL = os.getenv("OLD_SCBS_BASE_URL", "https://www.builderp.cn/SCBS").rstrip("/")


def clean(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


def md5(value: str) -> str:
    return hashlib.md5(value.encode("utf-8")).hexdigest()


def api_get(session: requests.Session, token: str, path: str) -> dict[str, Any]:
    response = session.get(f"{BASE_URL}/api/{path}", headers={"Token": token}, timeout=60)
    response.raise_for_status()
    body = response.json()
    if str(body.get("Code")) != "10000":
        raise RuntimeError(f"GET {path} failed: {body.get('Code')} {body.get('Msg')}")
    return body


def api_post(session: requests.Session, token: str, path: str, payload: dict[str, Any]) -> dict[str, Any]:
    response = session.post(f"{BASE_URL}/api/{path}", json=payload, headers={"Token": token}, timeout=120)
    response.raise_for_status()
    body = response.json()
    if str(body.get("Code")) != "10000":
        raise RuntimeError(f"POST {path} failed: {body.get('Code')} {body.get('Msg')}")
    return body


def login(session: requests.Session) -> dict[str, Any]:
    username = os.getenv("OLD_SCBS_USERNAME")
    password = os.getenv("OLD_SCBS_PASSWORD")
    if not username or not password:
        raise RuntimeError("OLD_SCBS_USERNAME and OLD_SCBS_PASSWORD are required")
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
        raise RuntimeError(f"old login failed: {body.get('Code')} {body.get('Msg')}")
    return body["Data"]


def enclosure_ident(detail: dict[str, Any]) -> str:
    columns = detail.get("ContentTable", {}).get("TableConfig", {}).get("ColumnConfig") or []
    fields: list[str] = []
    for column in columns:
        info = column.get("Info") or {}
        field = clean(info.get("Field"))
        if field and clean(info.get("Format")).lower() == "enclosure":
            fields.append(field)
    return ",".join(fields) + ("," if fields else "")


def list_payload(config: dict[str, Any]) -> dict[str, Any]:
    detail = json.loads(config.get("DETAIL_CONFIG") or "{}")
    other = detail.get("OtherConfig") or {}
    main = other.get("MainTable") or {}
    where = deepcopy(detail.get("WhereInfo") or {})
    if other.get("IsApproval") is not False and clean(main.get("DJBH_Field")):
        where["DJZT"] = {"Field": "DJZT", "Manner": "主表", "Rule": "In", "Data": ["2", "1", "0", "-1"]}
    payload: dict[str, Any] = {
        "BusinessId": config.get("BUSINESSID"),
        "ConfigId": config.get("ID"),
        "OrderInfo": other.get("OrderInfo") or "pid desc",
        "PageIndex": 1,
        "PageSize": 1,
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
    if other.get("ListDisplayType", {}).get("FromTableShow"):
        payload["ListDisplayType"] = other.get("ListDisplayType")
    return payload


def main() -> int:
    session = requests.Session()
    user = login(session)
    token = user["Token"]
    result_rows: list[dict[str, Any]] = []
    for csv_row in csv.DictReader(INPUT_CSV.open("r", encoding="utf-8-sig", newline="")):
        row = {
            "seq": int(csv_row["seq"]),
            "name": csv_row["name"],
            "config_type": csv_row.get("config_type") or "",
            "config_id": csv_row.get("config_id") or "",
            "main_table": csv_row.get("main_table") or "",
            "old_count": None,
            "status": "SKIP",
            "error": "",
        }
        if row["config_type"] != "List" or not row["config_id"]:
            result_rows.append(row)
            continue
        try:
            config = api_get(session, token, f"LowCode/FormApi/GetConfigById?Id={row['config_id']}&LoadInitData=true")["Data"]
            path = "LowCode/FormApi/ListByTableName"
            detail = json.loads(config.get("DETAIL_CONFIG") or "{}")
            other = detail.get("OtherConfig") or {}
            payload = list_payload(config)
            if other.get("ListApi"):
                path = str(other["ListApi"]).removeprefix("/api/")
            elif other.get("ListProcedure"):
                payload["Procedure"] = other["ListProcedure"]
                path = "LowCode/FormApi/ListByProcedure"
            body = api_post(session, token, path, payload)
            row["old_count"] = int(body.get("DataCount") or 0)
            row["status"] = "PASS"
        except Exception as exc:  # noqa: BLE001
            row["status"] = "FAIL"
            row["error"] = str(exc)
        result_rows.append(row)
        print(f"[old-count] seq={row['seq']:03d} name={row['name']} status={row['status']} count={row['old_count']} error={row['error'][:120]}")
    failures = [row for row in result_rows if row["status"] == "FAIL"]
    payload = {
        "status": "PASS" if not failures else "FAIL",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "old_base_url": BASE_URL,
        "old_user": {key: user.get(key) for key in ("UserId", "UserName", "PersonName", "ProjectId", "ProjectName", "CompanyId", "CompanyName")},
        "row_count": len(result_rows),
        "checked_count": len([row for row in result_rows if row["status"] != "SKIP"]),
        "failure_count": len(failures),
        "failures": failures,
        "rows": result_rows,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"SCBS55_OLD_LIST_COUNT={payload['status']} output={OUTPUT}")
    return 0 if not failures else 2


if __name__ == "__main__":
    raise SystemExit(main())
