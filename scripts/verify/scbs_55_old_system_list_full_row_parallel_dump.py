#!/usr/bin/env python3
"""Parallel dump full old-system rows for one SCBS55 List surface."""

from __future__ import annotations

import csv
import gzip
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import requests

from scbs_55_old_system_list_count_probe import BASE_URL, INPUT_CSV, api_get, api_post, list_payload, login


SEQ = int(os.getenv("SCBS55_OLD_FULL_DUMP_SEQ", "0"))
PAGE_SIZE = int(os.getenv("SCBS55_OLD_FULL_DUMP_PAGE_SIZE", "500"))
WORKERS = int(os.getenv("SCBS55_OLD_FULL_DUMP_WORKERS", "6"))
REQUEST_TIMEOUT = int(os.getenv("SCBS55_OLD_FULL_DUMP_TIMEOUT", "45"))
PAGE_START = int(os.getenv("SCBS55_OLD_FULL_DUMP_PAGE_START", "1"))
PAGE_END = int(os.getenv("SCBS55_OLD_FULL_DUMP_PAGE_END", "0"))
OUTPUT = Path(os.getenv("SCBS55_OLD_FULL_DUMP_OUTPUT", f"artifacts/migration/scbs_55_old_live_full_rows_seq{SEQ:03d}_parallel.json.gz"))


def row_for_seq() -> dict[str, str]:
    for row in csv.DictReader(INPUT_CSV.open("r", encoding="utf-8-sig", newline="")):
        if int(row["seq"]) == SEQ:
            return row
    raise RuntimeError(f"seq not found: {SEQ}")


def prepare(session: requests.Session, token: str, csv_row: dict[str, str]) -> tuple[str, dict[str, Any], int]:
    config = api_get(session, token, f"LowCode/FormApi/GetConfigById?Id={csv_row['config_id']}&LoadInitData=true")["Data"]
    detail = json.loads(config.get("DETAIL_CONFIG") or "{}")
    other = detail.get("OtherConfig") or {}
    path = "LowCode/FormApi/ListByTableName"
    payload = list_payload(config)
    if other.get("ListApi"):
        path = str(other["ListApi"]).removeprefix("/api/")
    elif other.get("ListProcedure"):
        payload["Procedure"] = other["ListProcedure"]
        path = "LowCode/FormApi/ListByProcedure"
    payload["PageIndex"] = 1
    payload["PageSize"] = 1
    body = api_post(session, token, path, payload)
    return path, payload, int(body.get("DataCount") or 0)


def fetch_page(username: str, password: str, path: str, payload: dict[str, Any], page: int) -> tuple[int, list[dict[str, Any]]]:
    session = requests.Session()
    os.environ["OLD_SCBS_USERNAME"] = username
    os.environ["OLD_SCBS_PASSWORD"] = password
    token = login(session)["Token"]
    request_payload = json.loads(json.dumps(payload, ensure_ascii=False))
    request_payload["PageIndex"] = page
    request_payload["PageSize"] = PAGE_SIZE
    last_error: Exception | None = None
    for _ in range(3):
        try:
            response = session.post(
                f"{BASE_URL}/api/{path}",
                json=request_payload,
                headers={"Token": token},
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            body = response.json()
            if str(body.get("Code")) != "10000":
                raise RuntimeError(f"POST {path} failed: {body.get('Code')} {body.get('Msg')}")
            return page, body.get("Data") or []
        except Exception as exc:  # noqa: BLE001
            last_error = exc
    raise RuntimeError(f"page {page} failed after retries: {last_error}")


def main() -> int:
    if not SEQ:
        raise RuntimeError("SCBS55_OLD_FULL_DUMP_SEQ is required")
    username = os.environ["OLD_SCBS_USERNAME"]
    password = os.environ["OLD_SCBS_PASSWORD"]
    csv_row = row_for_seq()
    session = requests.Session()
    token = login(session)["Token"]
    path, payload, data_count = prepare(session, token, csv_row)
    page_count = (data_count + PAGE_SIZE - 1) // PAGE_SIZE
    page_start = max(1, PAGE_START)
    page_end = min(PAGE_END or page_count, page_count)
    rows_by_page: dict[int, list[dict[str, Any]]] = {}
    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        futures = {
            executor.submit(fetch_page, username, password, path, payload, page): page
            for page in range(page_start, page_end + 1)
        }
        for future in as_completed(futures):
            page, rows = future.result()
            rows_by_page[page] = rows
            print(
                "[old-parallel-dump] seq=%03d page=%s/%s got=%s collected=%s expected=%s"
                % (SEQ, page, page_count, len(rows), sum(len(value) for value in rows_by_page.values()), data_count),
                flush=True,
            )
    rows: list[dict[str, Any]] = []
    for page in range(page_start, page_end + 1):
        rows.extend(rows_by_page.get(page) or [])
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(OUTPUT, "wt", encoding="utf-8") as handle:
        json.dump(
            {
                "seq": SEQ,
                "name": csv_row["name"],
                "main_table": csv_row.get("main_table") or "",
                "data_count": data_count,
                "page_size": PAGE_SIZE,
                "page_start": page_start,
                "page_end": page_end,
                "page_count": page_count,
                "rows": rows,
            },
            handle,
            ensure_ascii=False,
        )
    expected_rows = data_count if page_start == 1 and page_end == page_count else None
    status = "PASS" if expected_rows is not None and len(rows) == expected_rows else "PARTIAL"
    print(json.dumps({"status": status, "path": str(OUTPUT), "rows": len(rows), "data_count": data_count, "page_start": page_start, "page_end": page_end}, ensure_ascii=False))
    return 0 if status == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
