#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dump SCBSLY direct-project SelectType=3 list status fields.

The old SCBSLY list page fills payment/settlement status fields through custom
Vue mixins instead of ``GetFormDatabyDataSourceConfig``:

* ``listPageReadFKZT`` -> ``Finance/PaymentApi/GetBusinessPaymentState``
* ``listPageReadJSZT`` -> ``Business/CurrentApi/GetBusinessSettlementState``

This script reproduces that page behavior with small pages and writes the
browser-visible status fields for later Odoo replay.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import time
from copy import deepcopy
from pathlib import Path
from typing import Any

import requests
from requests import exceptions as request_exceptions
from requests.exceptions import JSONDecodeError as RequestsJSONDecodeError

from scripts.verify.online_capture_security import require_online_capture


ROOT = Path(__file__).resolve().parents[2]
MENU_PROBE = ROOT / "artifacts/migration/scbsly_direct_project_acceptance_menu_probe_v1.json"
AUDIT_JSON = ROOT / "artifacts/migration/scbsly_direct_custom_component_datafetch_audit_20260603.json"
OUTPUT = Path(
    os.getenv(
        "SCBSLY_SELECT3_STATUS_OUTPUT",
        ROOT / "artifacts/migration/scbsly_direct_select3_status_online_dump_20260603.json",
    )
)
BASE_URL = os.getenv("SCBSLY_BASE_URL", "").rstrip("/")
USERNAME = os.getenv("SCBSLY_USERNAME")
PASSWORD = os.getenv("SCBSLY_PASSWORD")
PAGE_SIZE = int(os.getenv("SCBSLY_SELECT3_PAGE_SIZE", "20"))
SLEEP_SECONDS = float(os.getenv("SCBSLY_SELECT3_SLEEP_SECONDS", "0.03"))
MAX_PAGES = int(os.getenv("SCBSLY_SELECT3_MAX_PAGES", "0") or "0")
PRINT_EVERY = int(os.getenv("SCBSLY_SELECT3_PRINT_EVERY", "25") or "25")
REQUEST_RETRIES = int(os.getenv("SCBSLY_SELECT3_REQUEST_RETRIES", "4") or "4")
LABEL_FILTER = {
    item.strip()
    for item in os.getenv("SCBSLY_SELECT3_LABELS", "").replace("，", ",").split(",")
    if item.strip()
}
REQUEST_TIMEOUT = (8, 60)


def clean(value: Any) -> str:
    if value is None or (isinstance(value, bool) and value is False):
        return ""
    return re.sub(r"\s+", " ", str(value).strip())


def md5(value: str) -> str:
    return hashlib.md5(value.encode("utf-8")).hexdigest()


def api_post(session: requests.Session, token: str | None, path: str, payload: dict[str, Any]) -> dict[str, Any]:
    headers = {"Token": token} if token else {}
    last_error: Exception | None = None
    for attempt in range(1, REQUEST_RETRIES + 1):
        try:
            response = session.post(
                f"{BASE_URL}/api/{path}",
                json=payload,
                headers=headers,
                timeout=REQUEST_TIMEOUT,
            )
            try:
                response.raise_for_status()
            except request_exceptions.HTTPError as exc:
                raise RuntimeError(
                    {
                        "path": path,
                        "payload_page": payload.get("PageIndex"),
                        "payload_page_size": payload.get("PageSize"),
                        "status_code": response.status_code,
                        "response_preview": response.text[:500],
                    }
                ) from exc
            try:
                body = response.json()
            except RequestsJSONDecodeError as exc:
                preview = response.text[:500]
                raise RuntimeError(
                    {
                        "path": path,
                        "payload_page": payload.get("PageIndex"),
                        "payload_page_size": payload.get("PageSize"),
                        "status_code": response.status_code,
                        "json_error": str(exc),
                        "response_preview": preview,
                    }
                ) from exc
            break
        except (request_exceptions.Timeout, request_exceptions.ConnectionError) as exc:
            last_error = exc
            if attempt >= REQUEST_RETRIES:
                raise
            time.sleep(min(3 * attempt, 15))
    else:
        raise last_error or RuntimeError({"path": path, "message": "request failed"})
    if str(body.get("Code")) != "10000":
        raise RuntimeError({"path": path, "code": body.get("Code"), "message": body.get("Msg")})
    return body


def api_get(session: requests.Session, token: str, path: str) -> dict[str, Any]:
    response = session.get(f"{BASE_URL}/api/{path}", headers={"Token": token}, timeout=60)
    response.raise_for_status()
    body = response.json()
    if str(body.get("Code")) != "10000":
        raise RuntimeError({"path": path, "code": body.get("Code"), "message": body.get("Msg")})
    return body


def login(session: requests.Session) -> dict[str, Any]:
    if not USERNAME or not PASSWORD:
        raise RuntimeError("SCBSLY_USERNAME/SCBSLY_PASSWORD are required")
    return api_post(
        session,
        None,
        "System/UserApi/Login",
        {
            "Type": "Common",
            "Param": {
                "UserName": USERNAME,
                "IsEncrypt": False,
                "Password": PASSWORD,
                "PasswordMd5": md5(PASSWORD),
                "VerificationCodeKey": "",
                "VerificationCode": "",
                "EncryptLockKey": "",
                "PhoneNumber": "",
                "SMSVerificationCodeKey": "",
                "SMSVerificationCode": "",
            },
        },
    )["Data"]


def enclosure_ident(detail: dict[str, Any]) -> str:
    columns = detail.get("ContentTable", {}).get("TableConfig", {}).get("ColumnConfig") or []
    fields: list[str] = []
    for column in columns:
        info = column.get("Info") or {}
        field = clean(info.get("Field"))
        if field and clean(info.get("Format")).lower() == "enclosure":
            fields.append(field)
    return ",".join(fields) + ("," if fields else "")


def list_payload(config: dict[str, Any]) -> tuple[str, dict[str, Any], dict[str, Any]]:
    detail = json.loads(config.get("DETAIL_CONFIG") or "{}")
    other = detail.get("OtherConfig") if isinstance(detail.get("OtherConfig"), dict) else {}
    main = other.get("MainTable") if isinstance(other.get("MainTable"), dict) else {}
    where = deepcopy(detail.get("WhereInfo") if isinstance(detail.get("WhereInfo"), dict) else {})
    payload: dict[str, Any] = {
        "BusinessId": config.get("BUSINESSID"),
        "ConfigId": config.get("ID"),
        "OrderInfo": other.get("OrderInfo") or "pid desc",
        "PageIndex": 1,
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
    if other.get("ListDisplayType", {}).get("FromTableShow"):
        payload["ListDisplayType"] = other.get("ListDisplayType")
    return path, payload, detail


def build_select_values(fetch_config: dict[str, Any], page_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    values: list[dict[str, Any]] = []
    for index, row in enumerate(page_rows):
        item: dict[str, Any] = {"RowId": index}
        for rule in fetch_config.get("GetRule") or fetch_config.get("get_rule") or []:
            field = rule.get("Field")
            param_name = rule.get("ParamName") or field
            item[param_name] = "" if row.get(field) is None else row.get(field)
        values.append(item)
    return values


def merge_by_row_id(page_rows: list[dict[str, Any]], data_rows: list[dict[str, Any]], field_group: str) -> None:
    by_row_id = {
        str(item.get("RowId")): item
        for item in data_rows
        if item.get("RowId") is not None
    }
    for index, row in enumerate(page_rows):
        extra = by_row_id.get(str(index))
        if not extra:
            continue
        if field_group == "payment":
            row["CCCC_DJJE"] = extra.get("DJJE")
            row["CCCC_FKZT"] = extra.get("FKZT")
            row["CCCC_FKJE"] = extra.get("FKJE")
            row["CCCC_WFKJE"] = extra.get("WFKJE")
            row["CCCC_SQZT"] = extra.get("SQZT")
            row["CCCC_SQJE"] = extra.get("SQJE")
            row["CCCC_WSQJE"] = extra.get("WSQJE")
        elif field_group == "settlement":
            row["CCCC_DJJE"] = extra.get("DJJE")
            row["CCCC_JSZT"] = extra.get("JSZT")
            row["CCCC_JSJE"] = extra.get("JSJE")
            row["CCCC_WJSJE"] = extra.get("WJSJE")


def run_select3(session: requests.Session, token: str, fetch_config: dict[str, Any], page_rows: list[dict[str, Any]]) -> int:
    values = build_select_values(fetch_config, page_rows)
    event_name = fetch_config.get("EventName") or fetch_config.get("event_name")
    event_param = fetch_config.get("EventParam") or fetch_config.get("event_param") or {}
    if event_name == "listPageReadFKZT":
        body = api_post(
            session,
            token,
            "Finance/PaymentApi/GetBusinessPaymentState",
            {
                "SelectSql": event_param.get("SelectSql"),
                "SelectValue": values,
            },
        )
        data_rows = body.get("Data") or []
        merge_by_row_id(page_rows, data_rows, "payment")
        return len(data_rows)
    if event_name == "listPageReadJSZT":
        body = api_post(
            session,
            token,
            "Business/CurrentApi/GetBusinessSettlementState",
            {
                "SelectSql": event_param.get("SelectSql"),
                "SelectValue": values,
                "Type": event_param.get("Type"),
            },
        )
        data_rows = body.get("Data") or []
        merge_by_row_id(page_rows, data_rows, "settlement")
        return len(data_rows)
    return 0


def select3_specs() -> list[dict[str, Any]]:
    audit_rows = json.loads(AUDIT_JSON.read_text(encoding="utf-8")).get("rows") or []
    menu_rows = {
        row.get("label"): row
        for row in json.loads(MENU_PROBE.read_text(encoding="utf-8")).get("rows") or []
    }
    specs: list[dict[str, Any]] = []
    for row in audit_rows:
        if LABEL_FILTER and row.get("label") not in LABEL_FILTER:
            continue
        fetch_configs = [
            config
            for config in row.get("data_fetch_configs") or []
            if str(config.get("select_type")) == "3"
        ]
        if not fetch_configs:
            continue
        specs.append(
            {
                "label": row.get("label"),
                "category": row.get("category"),
                "config_id": row.get("config_id"),
                "expected_count": row.get("count"),
                "link_url": (menu_rows.get(row.get("label")) or {}).get("link_url"),
                "fetch_configs": fetch_configs,
            }
        )
    return specs


def main() -> int:
    require_online_capture(("scbsly",))
    session = requests.Session()
    user = login(session)
    token = user["Token"]
    selected_labels = {spec["label"] for spec in select3_specs()}
    if OUTPUT.exists():
        existing = json.loads(OUTPUT.read_text(encoding="utf-8"))
        output_rows: list[dict[str, Any]] = [
            row for row in existing.get("rows") or [] if row.get("label") not in selected_labels
        ]
    else:
        output_rows = []
    for spec in select3_specs():
        config = api_get(
            session,
            token,
            f"LowCode/FormApi/GetConfigById?Id={spec['config_id']}&LoadInitData=true",
        )["Data"]
        path, base_payload, _detail = list_payload(config)
        rows: list[dict[str, Any]] = []
        page = 1
        data_count: int | None = None
        select3_response_rows = 0
        while True:
            payload = deepcopy(base_payload)
            payload["PageIndex"] = page
            payload["PageSize"] = PAGE_SIZE
            body = api_post(session, token, path, payload)
            page_rows = body.get("Data") or []
            if data_count is None:
                data_count = int(body.get("DataCount") or 0)
            if not page_rows:
                break
            for fetch_config in spec["fetch_configs"]:
                select3_response_rows += run_select3(session, token, fetch_config, page_rows)
            rows.extend(page_rows)
            if page == 1 or (PRINT_EVERY and page % PRINT_EVERY == 0):
                print(
                    "[scbsly-select3] label=%s page=%s rows=%s total=%s expected=%s select3_rows=%s"
                    % (spec["label"], page, len(page_rows), len(rows), data_count, select3_response_rows),
                    flush=True,
                )
            if len(rows) >= (data_count or 0):
                break
            if MAX_PAGES and page >= MAX_PAGES:
                break
            page += 1
            time.sleep(SLEEP_SECONDS)
        fields = sorted(
            {
                field
                for field in (
                    "CCCC_DJJE",
                    "CCCC_FKZT",
                    "CCCC_FKJE",
                    "CCCC_WFKJE",
                    "CCCC_SQZT",
                    "CCCC_SQJE",
                    "CCCC_WSQJE",
                    "CCCC_JSZT",
                    "CCCC_JSJE",
                    "CCCC_WJSJE",
                )
                if any(clean(row.get(field)) for row in rows)
            }
        )
        counters: dict[str, dict[str, int]] = {}
        for field in fields:
            counter: dict[str, int] = {}
            for row in rows:
                value = clean(row.get(field))
                if value:
                    counter[value] = counter.get(value, 0) + 1
            counters[field] = counter
        output_rows = [row for row in output_rows if row.get("label") != spec["label"]]
        output_rows.append(
            {
                **spec,
                "data_count": data_count,
                "row_count": len(rows),
                "select3_response_rows": select3_response_rows,
                "fields": fields,
                "field_counters": counters,
                "rows": rows,
            }
        )
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(
            json.dumps(
                {
                    "base_url": BASE_URL,
                    "old_user": {key: user.get(key) for key in ("UserId", "UserName", "PersonName", "CompanyName", "ProjectName")},
                    "page_size": PAGE_SIZE,
                    "rows": output_rows,
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    print(json.dumps({"output": str(OUTPUT), "label_count": len(output_rows)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
