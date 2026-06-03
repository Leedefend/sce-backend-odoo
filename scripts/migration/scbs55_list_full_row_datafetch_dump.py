#!/usr/bin/env python3
"""Dump old SCBS55 list rows with legacy page DataFetchConfig values.

Some old-system list fields are not returned by ListByTableName. The legacy
page calls LowCode/FormApi/GetFormDatabyDataSourceConfig after each page load
and merges those values into the rendered rows. This script reproduces that
page behavior for full-list dumps.
"""

from __future__ import annotations

import gzip
import json
import os
import sys
import time
from copy import deepcopy
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parents[2]
VERIFY_DIR = ROOT / "scripts" / "verify"
if str(VERIFY_DIR) not in sys.path:
    sys.path.insert(0, str(VERIFY_DIR))

from scbs_55_old_system_list_count_probe import api_get, api_post, list_payload, login  # noqa: E402


DEFAULT_CONFIG_ID = "164b665cc3674384aeaa89f3122895cf"
DEFAULT_NAME = "施工合同"
DUMP_DIR = Path(os.getenv("SCBS55_DATAFETCH_DUMP_DIR", "artifacts/migration"))
CONFIG_ID = os.getenv("SCBS55_DATAFETCH_CONFIG_ID", DEFAULT_CONFIG_ID)
NAME = os.getenv("SCBS55_DATAFETCH_NAME", DEFAULT_NAME)
PAGE_SIZE = int(os.getenv("SCBS55_DATAFETCH_PAGE_SIZE", "100"))
SLEEP_SECONDS = float(os.getenv("SCBS55_DATAFETCH_SLEEP_SECONDS", "0.1"))
OUTPUT = os.getenv("SCBS55_DATAFETCH_OUTPUT", "")
MAX_PAGES = int(os.getenv("SCBS55_DATAFETCH_MAX_PAGES", "0") or "0")


def output_path() -> Path:
    if OUTPUT:
        return Path(OUTPUT)
    slug = NAME.replace("/", "_").replace("\\", "_")
    return DUMP_DIR / f"scbs55_full_rows_datafetch_{CONFIG_ID}_{slug}.json.gz"


def row_index_key(value: Any) -> str:
    return str(value)


def build_datafetch_payload(fetch_config: dict[str, Any], page_rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    fields = [
        rule.get("Field")
        for rule in (fetch_config.get("SetRule") or [])
        if rule.get("Field")
    ]
    select_values: list[dict[str, Any]] = []
    for index, row in enumerate(page_rows):
        item: dict[str, Any] = {"RowId": index}
        include = True
        for rule in fetch_config.get("GetRule") or []:
            field = rule.get("Field")
            param_name = rule.get("ParamName") or field
            value = row.get(field)
            if rule.get("Required") and value in (None, ""):
                include = False
                break
            item[param_name] = value
        if include:
            select_values.append(item)
    if not select_values:
        return None
    return {
        "SelectType": fetch_config.get("SelectType") or "0",
        "SelectValue": select_values,
        "GetField": fields,
        "CustomSQL": fetch_config.get("CustomSQL"),
        "SQLID": fetch_config.get("SQLID") or "",
    }


def merge_datafetch_rows(page_rows: list[dict[str, Any]], data_rows: list[dict[str, Any]]) -> None:
    by_row_id = {
        row_index_key(item.get("RowId")): item
        for item in data_rows
        if item.get("RowId") is not None
    }
    if by_row_id:
        for index, row in enumerate(page_rows):
            extra = by_row_id.get(row_index_key(index))
            if extra:
                merge_one(row, extra)
        return

    # Some legacy CustomSQL snippets do not project RowId. The old frontend
    # merges those result rows by response order.
    for index, extra in enumerate(data_rows):
        if index >= len(page_rows):
            break
        merge_one(page_rows[index], extra)


def merge_one(target: dict[str, Any], extra: dict[str, Any]) -> None:
    for key, value in extra.items():
        if key not in {"RowId", "RowId1"}:
            target[key] = value


def main() -> int:
    session = requests.Session()
    user = login(session)
    token = user["Token"]
    config = api_get(
        session,
        token,
        f"LowCode/FormApi/GetConfigById?Id={CONFIG_ID}&LoadInitData=true",
    )["Data"]
    detail = json.loads(config.get("DETAIL_CONFIG") or "{}")
    other = detail.get("OtherConfig") or {}
    fetch_configs = other.get("DataFetchConfig") or []
    list_path = "LowCode/FormApi/ListByTableName"
    base_payload = list_payload(config)
    if other.get("ListApi"):
        list_path = str(other["ListApi"]).removeprefix("/api/")
    elif other.get("ListProcedure"):
        base_payload["Procedure"] = other["ListProcedure"]
        list_path = "LowCode/FormApi/ListByProcedure"

    all_rows: list[dict[str, Any]] = []
    page_index = 1
    data_count: int | None = None
    while True:
        payload = deepcopy(base_payload)
        payload["PageIndex"] = page_index
        payload["PageSize"] = PAGE_SIZE
        body = api_post(session, token, list_path, payload)
        page_rows = body.get("Data") or []
        if data_count is None:
            data_count = int(body.get("DataCount") or 0)
        if not page_rows:
            break

        for fetch_config in fetch_configs:
            fetch_payload = build_datafetch_payload(fetch_config, page_rows)
            if not fetch_payload:
                continue
            fetch_body = api_post(
                session,
                token,
                "LowCode/FormApi/GetFormDatabyDataSourceConfig",
                fetch_payload,
            )
            merge_datafetch_rows(page_rows, fetch_body.get("Data") or [])

        all_rows.extend(page_rows)
        print(
            "[scbs55-datafetch-dump] config=%s page=%s got=%s total=%s expected=%s"
            % (CONFIG_ID, page_index, len(page_rows), len(all_rows), data_count),
            flush=True,
        )
        if len(all_rows) >= (data_count or 0):
            break
        if MAX_PAGES and page_index >= MAX_PAGES:
            break
        page_index += 1
        time.sleep(SLEEP_SECONDS)

    out_path = output_path()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "config_id": CONFIG_ID,
        "name": NAME,
        "main_table": config.get("MAIN_TABLENAME") or "",
        "data_fetch_count": len(fetch_configs),
        "data_count": data_count,
        "row_count": len(all_rows),
        "old_user": {
            key: user.get(key)
            for key in ("UserId", "UserName", "PersonName", "ProjectId", "ProjectName", "CompanyId", "CompanyName")
        },
        "rows": all_rows,
    }
    with gzip.open(out_path, "wt", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False)

    if len(all_rows) == (data_count or 0):
        status = "PASS"
    elif MAX_PAGES:
        status = "PARTIAL"
    else:
        status = "COUNT_MISMATCH"
    print(
        json.dumps(
            {
                "status": status,
                "output": str(out_path),
                "config_id": CONFIG_ID,
                "row_count": len(all_rows),
                "data_count": data_count,
                "data_fetch_count": len(fetch_configs),
                "max_pages": MAX_PAGES,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if status in {"PASS", "PARTIAL"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
