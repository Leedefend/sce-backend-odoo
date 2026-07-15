#!/usr/bin/env python3
"""Dump full rows for direct-project SCBSLY config IDs.

This complements the SCBS55 CSV-based dumper.  Direct-project menu entries are
discovered from the live SCBSLY menu/config surface, so they are supplied from a
JSON manifest instead of the fixed 55-row acceptance CSV.
"""

from __future__ import annotations

import gzip
import json
import os
import time
from pathlib import Path
from typing import Any

import requests

from scbsly_direct_project_acceptance_menu_probe import api_get, api_post, list_payload, login


INPUT_JSON = Path(
    os.getenv(
        "SCBSLY_DIRECT_CONFIG_COUNTS_JSON",
        "artifacts/migration/scbsly_direct_20260530/direct_unresolved_config_counts.json",
    )
)
DUMP_DIR = Path(os.getenv("SCBSLY_DIRECT_FULL_DUMP_DIR", "artifacts/migration/scbsly_direct_20260530/full_rows"))
PAGE_SIZE = int(os.getenv("SCBSLY_DIRECT_FULL_DUMP_PAGE_SIZE", "500"))
NAME_FILTER = {
    item.strip()
    for item in os.getenv("SCBSLY_DIRECT_FULL_DUMP_NAMES", "").replace("，", ",").split(",")
    if item.strip()
}
TABLE_FILTER = {
    item.strip()
    for item in os.getenv("SCBSLY_DIRECT_FULL_DUMP_TABLES", "").replace("，", ",").split(",")
    if item.strip()
}
INCLUDE_ZERO = os.getenv("SCBSLY_DIRECT_FULL_DUMP_INCLUDE_ZERO", "").lower() in {"1", "true", "yes"}


def selected(row: dict[str, Any]) -> bool:
    if row.get("status") != "PASS":
        return False
    if not INCLUDE_ZERO and not int(row.get("count") or 0):
        return False
    if NAME_FILTER and str(row.get("name") or "") not in NAME_FILTER:
        return False
    if TABLE_FILTER and str(row.get("table") or "") not in TABLE_FILTER:
        return False
    return True


def path_for(row: dict[str, Any]) -> Path:
    name = str(row.get("name") or "unknown").replace("/", "_").replace("\\", "_")
    table = str(row.get("table") or "unknown").replace("/", "_").replace("\\", "_")
    config_id = str(row.get("config_id") or "")[:8]
    return DUMP_DIR / f"scbsly_direct_full_rows_{table}_{name}_{config_id}.json.gz"


def main() -> int:
    rows = json.loads(INPUT_JSON.read_text(encoding="utf-8")).get("rows") or []
    targets = [row for row in rows if selected(row)]
    if not targets:
        raise RuntimeError({"no_selected_direct_configs": str(INPUT_JSON)})

    session = requests.Session()
    user = login(session)
    token = user["Token"]
    DUMP_DIR.mkdir(parents=True, exist_ok=True)
    manifest: list[dict[str, Any]] = []

    for row in targets:
        item = {
            "name": row.get("name") or "",
            "config_id": row.get("config_id") or "",
            "main_table": row.get("table") or "",
            "expected_count": int(row.get("count") or 0),
            "row_count": 0,
            "path": "",
            "status": "FAIL",
            "error": "",
        }
        try:
            config = api_get(session, token, f"LowCode/FormApi/GetConfigById?Id={item['config_id']}&LoadInitData=true")["Data"]
            path, payload, _policy = list_payload(config)

            full_rows: list[dict[str, Any]] = []
            page_index = 1
            data_count: int | None = None
            while True:
                payload["PageIndex"] = page_index
                payload["PageSize"] = PAGE_SIZE
                body = api_post(session, token, path, payload)
                page_rows = body.get("Data") or []
                if data_count is None:
                    data_count = int(body.get("DataCount") or 0)
                    item["expected_count"] = data_count
                full_rows.extend(page_rows)
                print(
                    "[direct-full-dump] table=%s name=%s page=%s got=%s total=%s expected=%s"
                    % (item["main_table"], item["name"], page_index, len(page_rows), len(full_rows), data_count),
                    flush=True,
                )
                if not page_rows or len(full_rows) >= (data_count or 0):
                    break
                page_index += 1
                time.sleep(0.15)

            out_path = path_for(row)
            with gzip.open(out_path, "wt", encoding="utf-8") as handle:
                json.dump(
                    {
                        "name": item["name"],
                        "config_id": item["config_id"],
                        "main_table": item["main_table"],
                        "old_user": {
                            key: user.get(key)
                            for key in ("UserId", "UserName", "PersonName", "ProjectId", "ProjectName")
                        },
                        "rows": full_rows,
                    },
                    handle,
                    ensure_ascii=False,
                )
            item["row_count"] = len(full_rows)
            item["path"] = str(out_path)
            item["status"] = "PASS" if len(full_rows) == (data_count or 0) else "COUNT_MISMATCH"
        except Exception as exc:  # noqa: BLE001
            item["error"] = str(exc)
        manifest.append(item)
        print(
            "[direct-full-dump] table=%s name=%s status=%s count=%s path=%s error=%s"
            % (item["main_table"], item["name"], item["status"], item["row_count"], item["path"], item["error"][:160]),
            flush=True,
        )

    manifest_path = DUMP_DIR / "scbsly_direct_full_rows_manifest.json"
    manifest_path.write_text(json.dumps({"rows": manifest}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0 if manifest and all(row["status"] == "PASS" for row in manifest) else 2


if __name__ == "__main__":
    raise SystemExit(main())
