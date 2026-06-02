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
from copy import deepcopy
from pathlib import Path
from typing import Any

import requests

from scbs_55_old_system_list_count_probe import INPUT_CSV, api_get, api_post, list_payload, login


DUMP_DIR = Path(os.getenv("SCBS55_OLD_FULL_DUMP_DIR", "artifacts/migration"))
PAGE_SIZE = int(os.getenv("SCBS55_OLD_FULL_DUMP_PAGE_SIZE", "1000"))
DATAFETCH_PAGE_SIZE = int(os.getenv("SCBS55_OLD_FULL_DUMP_DATAFETCH_PAGE_SIZE", "100"))
DATAFETCH_CHUNK_SIZE = int(os.getenv("SCBS55_OLD_FULL_DUMP_DATAFETCH_CHUNK_SIZE", "5"))
CONFIG_RETRIES = int(os.getenv("SCBS55_OLD_FULL_DUMP_CONFIG_RETRIES", "8"))
REUSE_EXISTING = os.getenv("SCBS55_OLD_FULL_DUMP_REUSE_EXISTING", "1").strip().lower() not in {"0", "false", "no"}
SEQ_PAGE_SIZE_OVERRIDES = {
    int(seq): int(size)
    for item in os.getenv("SCBS55_OLD_FULL_DUMP_SEQ_PAGE_SIZE_OVERRIDES", "40:500,42:500").replace("，", ",").split(",")
    if item.strip() and ":" in item
    for seq, size in [item.split(":", 1)]
}
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


def existing_pass_item(item: dict[str, Any], path: Path) -> dict[str, Any] | None:
    if not REUSE_EXISTING or not path.exists():
        return None
    try:
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            payload = json.load(handle)
        rows = payload.get("rows") or []
        if not isinstance(rows, list):
            return None
        reused = dict(item)
        reused.update(
            {
                "row_count": len(rows),
                "data_count": len(rows),
                "data_fetch_count": int(payload.get("data_fetch_count") or 0),
                "datafetch_pages": int(payload.get("datafetch_pages") or 0),
                "path": str(path),
                "status": "PASS_REUSED",
                "error": "",
            }
        )
        return reused
    except Exception:
        return None


def load_config_and_detail(session: requests.Session, token: str, config_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    last_exc: Exception | None = None
    for attempt in range(1, max(CONFIG_RETRIES, 1) + 1):
        try:
            config = api_get(session, token, f"LowCode/FormApi/GetConfigById?Id={config_id}&LoadInitData=true")["Data"]
            return config, json.loads(config.get("DETAIL_CONFIG") or "{}")
        except (ValueError, RuntimeError, requests.exceptions.RequestException) as exc:
            last_exc = exc
            if attempt >= max(CONFIG_RETRIES, 1):
                break
            time.sleep(0.5 * attempt)
    assert last_exc is not None
    raise last_exc


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

    # Some old CustomSQL responses omit RowId; the legacy page merges those
    # values back by response order.
    for index, extra in enumerate(data_rows):
        if index >= len(page_rows):
            break
        merge_one(page_rows[index], extra)


def merge_one(target: dict[str, Any], extra: dict[str, Any]) -> None:
    for key, value in extra.items():
        if key not in {"RowId", "RowId1"}:
            target[key] = value


def apply_datafetch_configs(
    session: requests.Session,
    token: str,
    fetch_configs: list[dict[str, Any]],
    page_rows: list[dict[str, Any]],
) -> int:
    applied = 0
    for fetch_index, fetch_config in enumerate(fetch_configs, start=1):
        for start in range(0, len(page_rows), max(DATAFETCH_CHUNK_SIZE, 1)):
            chunk_rows = page_rows[start : start + max(DATAFETCH_CHUNK_SIZE, 1)]
            fetch_payload = build_datafetch_payload(fetch_config, chunk_rows)
            if not fetch_payload:
                continue
            try:
                fetch_body = api_post(
                    session,
                    token,
                    "LowCode/FormApi/GetFormDatabyDataSourceConfig",
                    fetch_payload,
                )
            except Exception as exc:
                fields = ",".join(str(field) for field in fetch_payload.get("GetField") or [])
                raise RuntimeError(
                    "DataFetch failed fetch_index=%s chunk_start=%s chunk_size=%s fields=%s error=%s"
                    % (fetch_index, start, len(chunk_rows), fields, exc)
                ) from exc
            merge_datafetch_rows(chunk_rows, fetch_body.get("Data") or [])
            applied += 1
    return applied


def main() -> int:
    if not SEQ_FILTER:
        raise RuntimeError("SCBS55_OLD_FULL_DUMP_SEQS is required, e.g. 1,2")
    DUMP_DIR.mkdir(parents=True, exist_ok=True)
    manifest: list[dict[str, Any]] = []
    selected_rows = [
        row
        for row in csv.DictReader(INPUT_CSV.open("r", encoding="utf-8-sig", newline=""))
        if int(row["seq"]) in SEQ_FILTER
    ]
    items_to_fetch: list[tuple[dict[str, str], dict[str, Any], Path]] = []
    for csv_row in selected_rows:
        seq = int(csv_row["seq"])
        item: dict[str, Any] = {
            "seq": seq,
            "name": csv_row["name"],
            "config_id": csv_row.get("config_id") or "",
            "main_table": csv_row.get("main_table") or "",
            "row_count": 0,
            "data_count": None,
            "data_fetch_count": 0,
            "datafetch_pages": 0,
            "path": "",
            "status": "FAIL",
            "error": "",
        }
        out_path = path_for(seq, str(item["name"]))
        reused = existing_pass_item(item, out_path)
        if reused:
            manifest.append(reused)
            print(
                "[old-full-dump] seq=%03d name=%s status=%s count=%s path=%s error="
                % (seq, reused["name"], reused["status"], reused["row_count"], reused["path"]),
                flush=True,
            )
        else:
            items_to_fetch.append((csv_row, item, out_path))
    if not items_to_fetch:
        manifest_path = DUMP_DIR / "scbs_55_old_live_full_rows_manifest.json"
        manifest_path.write_text(json.dumps({"rows": manifest}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return 0

    session = requests.Session()
    user = login(session)
    token = user["Token"]
    for csv_row, item, out_path in items_to_fetch:
        seq = int(csv_row["seq"])
        try:
            config, detail = load_config_and_detail(session, token, str(item["config_id"]))
            other = detail.get("OtherConfig") or {}
            fetch_configs = other.get("DataFetchConfig") or []
            path = "LowCode/FormApi/ListByTableName"
            payload = list_payload(config)
            if other.get("ListApi"):
                path = str(other["ListApi"]).removeprefix("/api/")
            elif other.get("ListProcedure"):
                payload["Procedure"] = other["ListProcedure"]
                path = "LowCode/FormApi/ListByProcedure"

            rows: list[dict[str, Any]] = []
            page_index = 1
            page_size = SEQ_PAGE_SIZE_OVERRIDES.get(seq, min(PAGE_SIZE, DATAFETCH_PAGE_SIZE) if fetch_configs else PAGE_SIZE)
            data_count: int | None = None
            datafetch_pages = 0
            while True:
                page_payload = deepcopy(payload)
                page_payload["PageIndex"] = page_index
                page_payload["PageSize"] = page_size
                body = api_post(session, token, path, page_payload)
                page_rows = body.get("Data") or []
                if data_count is None:
                    data_count = int(body.get("DataCount") or 0)
                    item["data_count"] = data_count
                if page_rows and fetch_configs:
                    datafetch_pages += apply_datafetch_configs(session, token, fetch_configs, page_rows)
                rows.extend(page_rows)
                print(
                    "[old-full-dump] seq=%03d page=%s got=%s total=%s expected=%s datafetch=%s"
                    % (seq, page_index, len(page_rows), len(rows), data_count, len(fetch_configs)),
                    flush=True,
                )
                if not page_rows or len(rows) >= (data_count or 0):
                    break
                page_index += 1
                time.sleep(0.15)

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
                        "data_fetch_count": len(fetch_configs),
                        "datafetch_pages": datafetch_pages,
                        "rows": rows,
                    },
                    handle,
                    ensure_ascii=False,
                )
            item["row_count"] = len(rows)
            item["path"] = str(out_path)
            item["data_fetch_count"] = len(fetch_configs)
            item["datafetch_pages"] = datafetch_pages
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
    return 0 if manifest and all(row["status"] in {"PASS", "PASS_REUSED"} for row in manifest) else 2


if __name__ == "__main__":
    raise SystemExit(main())
