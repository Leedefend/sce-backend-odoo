#!/usr/bin/env python3
"""Fetch old SCBS55 list DataCount values from the live old system."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import time
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

from online_capture_security import require_online_capture


ROOT = Path(__file__).resolve().parents[2]
INPUT_CSV = ROOT / "docs/migration_alignment/scbs_55_user_visible_surface_live_alignment_v1.csv"
OUTPUT = ROOT / "artifacts/migration/scbs_55_old_system_list_count_probe_result_v1.json"
BASE_URL = os.getenv("OLD_SCBS_BASE_URL", "").rstrip("/")
GET_TIMEOUT = int(os.getenv("OLD_SCBS_GET_TIMEOUT", "90"))
POST_TIMEOUT = int(os.getenv("OLD_SCBS_POST_TIMEOUT", "180"))
LOGIN_TIMEOUT = int(os.getenv("OLD_SCBS_LOGIN_TIMEOUT", "90"))
API_RETRIES = int(os.getenv("OLD_SCBS_API_RETRIES", "8"))
API_RETRY_SLEEP = float(os.getenv("OLD_SCBS_API_RETRY_SLEEP", "2"))
SEQ_FILTER = {
    int(item)
    for item in (
        os.getenv("SCBS55_OLD_LIST_COUNT_SEQS")
        or os.getenv("ONLINE_VISIBLE_SURFACE_SEQS")
        or os.getenv("SCBS55_OLD_FULL_DUMP_SEQS", "")
    )
    .replace("，", ",")
    .split(",")
    if item.strip()
}


def clean(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


def md5(value: str) -> str:
    return hashlib.md5(value.encode("utf-8")).hexdigest()


def sm3(value: str) -> str:
    digest = hashlib.new("sm3")
    digest.update(value.encode("utf-8"))
    return digest.hexdigest()


def _json_request_with_retry(session: requests.Session, method: str, url: str, **kwargs: Any) -> dict[str, Any]:
    last_exc: Exception | None = None
    for attempt in range(1, max(API_RETRIES, 1) + 1):
        try:
            response = session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except (
            requests.exceptions.ConnectionError,
            requests.exceptions.HTTPError,
            requests.exceptions.Timeout,
            ValueError,
        ) as exc:
            last_exc = exc
            if attempt >= max(API_RETRIES, 1):
                break
            time.sleep(API_RETRY_SLEEP * attempt)
    assert last_exc is not None
    raise last_exc


def api_get(session: requests.Session, token: str, path: str) -> dict[str, Any]:
    body = _json_request_with_retry(
        session,
        "GET",
        f"{BASE_URL}/api/{path}",
        headers={"Token": token},
        timeout=GET_TIMEOUT,
    )
    if str(body.get("Code")) != "10000":
        raise RuntimeError(f"GET {path} failed: {body.get('Code')} {body.get('Msg')}")
    return body


def api_post(session: requests.Session, token: str, path: str, payload: dict[str, Any]) -> dict[str, Any]:
    body = _json_request_with_retry(
        session,
        "POST",
        f"{BASE_URL}/api/{path}",
        json=payload,
        headers={"Token": token},
        timeout=POST_TIMEOUT,
    )
    if str(body.get("Code")) != "10000":
        raise RuntimeError(f"POST {path} failed: {body.get('Code')} {body.get('Msg')}")
    return body


def login(session: requests.Session) -> dict[str, Any]:
    require_online_capture(("scbs",))
    username = os.getenv("OLD_SCBS_USERNAME")
    password = os.getenv("OLD_SCBS_PASSWORD")
    if not username or not password:
        raise RuntimeError("OLD_SCBS_USERNAME and OLD_SCBS_PASSWORD are required")
    encrypted_login = os.getenv("OLD_SCBS_ENCRYPTED_LOGIN", "1").strip().lower() not in {"0", "false", "no"}
    payloads = []
    if encrypted_login:
        payloads.append(
            {
                "Type": "Common",
                "Param": {
                    "UserName": username,
                    "IsEncrypt": True,
                    "Password": sm3(password),
                    "PasswordMd5": md5(password),
                    "VerificationCodeKey": None,
                    "VerificationCode": None,
                    "EncryptLockKey": None,
                    "PhoneNumber": None,
                    "SMSVerificationCodeKey": None,
                    "SMSVerificationCode": None,
                },
            }
        )
    payloads.append(
        {
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
    )
    last_body = None
    last_exc = None
    for payload in payloads:
        try:
            body = _json_request_with_retry(
                session,
                "POST",
                f"{BASE_URL}/api/System/UserApi/Login",
                json=payload,
                timeout=LOGIN_TIMEOUT,
            )
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            continue
        last_body = body
        if str(body.get("Code")) == "10000" and body.get("Data", {}).get("Token"):
            return body["Data"]
    if last_body is not None:
        raise RuntimeError(f"old login failed: {last_body.get('Code')} {last_body.get('Msg')}")
    if last_exc is not None:
        raise last_exc
    raise RuntimeError("old login failed")


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
    require_online_capture(("scbs",))
    session = requests.Session()
    user = login(session)
    token = user["Token"]
    result_rows: list[dict[str, Any]] = []
    for csv_row in csv.DictReader(INPUT_CSV.open("r", encoding="utf-8-sig", newline="")):
        seq = int(csv_row["seq"])
        if SEQ_FILTER and seq not in SEQ_FILTER:
            continue
        row = {
            "seq": seq,
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
