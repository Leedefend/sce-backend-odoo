#!/usr/bin/env python3
"""Dump full old-system rows for selected SCBS55 List surfaces.

The old endpoint returns 502 for some one-shot large pages, so this script
uses deterministic page-by-page reads with the same payload builder as the
count probe.
"""

from __future__ import annotations

import csv
import gzip
import json
import os
import time
from pathlib import Path
from typing import Any

import requests

from scbs_55_old_system_list_count_probe import INPUT_CSV, api_get, api_post, list_payload, login


DUMP_DIR = Path(os.getenv("SCBS55_OLD_FULL_DUMP_DIR", "artifacts/migration"))
PAGE_SIZE = int(os.getenv("SCBS55_OLD_FULL_DUMP_PAGE_SIZE", "1000"))
SEQ_FILTER = {
    int(item)
    for item in os.getenv("SCBS55_OLD_FULL_DUMP_SEQS", "").replace("，", ",").split(",")
    if item.strip()
}


def path_for(seq: int, name: str) -> Path:
    slug = {
        1: "business_entity",
        2: "business_entity",
    }.get(seq, name)
    slug = str(slug).replace("/", "_").replace("\\", "_")
    return DUMP_DIR / f"scbs_55_old_live_full_rows_seq{seq:03d}_{slug}.json.gz"


def main() -> int:
    if not SEQ_FILTER:
        raise RuntimeError("SCBS55_OLD_FULL_DUMP_SEQS is required, e.g. 1,2")
    session = requests.Session()
    user = login(session)
    token = user["Token"]
    DUMP_DIR.mkdir(parents=True, exist_ok=True)
    manifest: list[dict[str, Any]] = []
    for csv_row in csv.DictReader(INPUT_CSV.open("r", encoding="utf-8-sig", newline="")):
        seq = int(csv_row["seq"])
        if seq not in SEQ_FILTER:
            continue
        item: dict[str, Any] = {
            "seq": seq,
            "name": csv_row["name"],
            "config_id": csv_row.get("config_id") or "",
            "main_table": csv_row.get("main_table") or "",
            "row_count": 0,
            "data_count": None,
            "path": "",
            "status": "FAIL",
            "error": "",
        }
        try:
            config = api_get(session, token, f"LowCode/FormApi/GetConfigById?Id={item['config_id']}&LoadInitData=true")["Data"]
            detail = json.loads(config.get("DETAIL_CONFIG") or "{}")
            other = detail.get("OtherConfig") or {}
            path = "LowCode/FormApi/ListByTableName"
            payload = list_payload(config)
            if other.get("ListApi"):
                path = str(other["ListApi"]).removeprefix("/api/")
            elif other.get("ListProcedure"):
                payload["Procedure"] = other["ListProcedure"]
                path = "LowCode/FormApi/ListByProcedure"

            rows: list[dict[str, Any]] = []
            page_index = 1
            data_count: int | None = None
            while True:
                payload["PageIndex"] = page_index
                payload["PageSize"] = PAGE_SIZE
                body = api_post(session, token, path, payload)
                page_rows = body.get("Data") or []
                if data_count is None:
                    data_count = int(body.get("DataCount") or 0)
                    item["data_count"] = data_count
                rows.extend(page_rows)
                print(
                    "[old-full-dump] seq=%03d page=%s got=%s total=%s expected=%s"
                    % (seq, page_index, len(page_rows), len(rows), data_count),
                    flush=True,
                )
                if not page_rows or len(rows) >= (data_count or 0):
                    break
                page_index += 1
                time.sleep(0.15)

            out_path = path_for(seq, str(item["name"]))
            with gzip.open(out_path, "wt", encoding="utf-8") as handle:
                json.dump(
                    {
                        "seq": seq,
                        "name": item["name"],
                        "main_table": item["main_table"],
                        "old_user": {
                            key: user.get(key)
                            for key in ("UserId", "UserName", "PersonName", "ProjectId", "ProjectName")
                        },
                        "rows": rows,
                    },
                    handle,
                    ensure_ascii=False,
                )
            item["row_count"] = len(rows)
            item["path"] = str(out_path)
            item["status"] = "PASS" if len(rows) == (data_count or 0) else "COUNT_MISMATCH"
        except Exception as exc:  # noqa: BLE001
            item["error"] = str(exc)
        manifest.append(item)
        print(
            "[old-full-dump] seq=%03d name=%s status=%s count=%s path=%s error=%s"
            % (seq, item["name"], item["status"], item["row_count"], item["path"], item["error"][:160]),
            flush=True,
        )
    manifest_path = DUMP_DIR / "scbs_55_old_live_full_rows_manifest.json"
    manifest_path.write_text(json.dumps({"rows": manifest}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0 if manifest and all(row["status"] == "PASS" for row in manifest) else 2


if __name__ == "__main__":
    raise SystemExit(main())
