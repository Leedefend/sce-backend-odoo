#!/usr/bin/env python3
"""Dump the current SCBS visible input-tax report rows for seq 42.

This intentionally uses the live list payload only. It is for row identity and
count reconciliation of the user-visible acceptance surface.
"""

from __future__ import annotations

import csv
import gzip
import json
import os
import time
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

import requests

from scbs_55_old_system_list_count_probe import BASE_URL, INPUT_CSV, api_get, list_payload, login


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = Path(
    os.getenv("SCBS55_INPUT_TAX_CURRENT_DUMP")
    or "/tmp/scbs55_current_input_tax_visible_rows_seq042.json.gz"
)
PAGE_SIZE = int(os.getenv("SCBS55_INPUT_TAX_CURRENT_PAGE_SIZE", "100"))
PAGE_SLEEP = float(os.getenv("SCBS55_INPUT_TAX_CURRENT_PAGE_SLEEP", "0.05"))
API_RETRIES = int(os.getenv("OLD_SCBS_API_RETRIES", "8"))
API_RETRY_SLEEP = float(os.getenv("OLD_SCBS_API_RETRY_SLEEP", "2"))


def post_list_json(session: requests.Session, token: str, payload: dict) -> dict:
    last_exc: Exception | None = None
    for attempt in range(1, max(API_RETRIES, 1) + 1):
        response = session.post(
            f"{BASE_URL}/api/LowCode/FormApi/ListByTableName",
            json=payload,
            headers={"Token": token},
            timeout=int(os.getenv("OLD_SCBS_POST_TIMEOUT", "180")),
        )
        response.raise_for_status()
        try:
            return response.json()
        except ValueError as exc:
            last_exc = exc
            text = response.text
            repaired = text.replace(
                '"D_SCBSJS_FJS$C_JXXP_ZYFPJJDnull',
                '"D_SCBSJS_FJS$C_JXXP_ZYFPJJD_CB":null',
            )
            if repaired != text:
                print("[scbs55-input-tax-current] repaired malformed enclosure json field", flush=True)
                return json.loads(repaired)
            raw_path = Path("/tmp/scbs55_input_tax_malformed_page.json")
            raw_path.write_text(text, encoding="utf-8", errors="replace")
            print(
                "[scbs55-input-tax-current] retry malformed page=%s attempt=%s/%s saved=%s error=%s"
                % (payload.get("PageIndex"), attempt, max(API_RETRIES, 1), raw_path, exc),
                flush=True,
            )
            if attempt < max(API_RETRIES, 1):
                time.sleep(API_RETRY_SLEEP * attempt)
                continue
            raise
    assert last_exc is not None
    raise last_exc


def seq42_config_row() -> dict[str, str]:
    for row in csv.DictReader(INPUT_CSV.open("r", encoding="utf-8-sig", newline="")):
        if int(row["seq"]) == 42:
            return row
    raise RuntimeError("missing seq=42 in SCBS55 visible surface alignment CSV")


def main() -> int:
    session = requests.Session()
    user = login(session)
    token = user["Token"]
    row = seq42_config_row()
    config = api_get(session, token, f"LowCode/FormApi/GetConfigById?Id={row['config_id']}&LoadInitData=true")["Data"]
    base_payload = list_payload(config)

    rows: list[dict] = []
    page = 1
    expected_count: int | None = None
    while True:
        payload = deepcopy(base_payload)
        payload["PageIndex"] = page
        payload["PageSize"] = PAGE_SIZE
        body = post_list_json(session, token, payload)
        page_rows = body.get("Data") or []
        if expected_count is None:
            expected_count = int(body.get("DataCount") or 0)
        rows.extend(page_rows)
        print(
            "[scbs55-input-tax-current] page=%s got=%s total=%s/%s"
            % (page, len(page_rows), len(rows), expected_count),
            flush=True,
        )
        if not page_rows or len(rows) >= expected_count:
            break
        page += 1
        time.sleep(PAGE_SLEEP)

    payload = {
        "source_system": os.getenv("OLD_SCBS_BASE_URL", "https://www.builderp.cn/SCBS").rstrip("/"),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "seq": 42,
        "name": row["name"],
        "config_id": row["config_id"],
        "data_count": expected_count,
        "actual_count": len(rows),
        "old_user": {
            key: user.get(key)
            for key in ("UserId", "UserName", "PersonName", "ProjectName", "CompanyName")
        },
        "rows": rows,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(OUTPUT, "wt", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False)
    print("SCBS55_INPUT_TAX_CURRENT_DUMP=%s rows=%s expected=%s" % (OUTPUT, len(rows), expected_count))
    return 0 if len(rows) == expected_count else 2


if __name__ == "__main__":
    raise SystemExit(main())
