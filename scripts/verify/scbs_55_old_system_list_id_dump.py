#!/usr/bin/env python3
"""Dump live old-system primary keys for SCBS55 List surfaces."""

from __future__ import annotations

import csv
import gzip
import json
import os
from pathlib import Path
from typing import Any

from scbs_55_old_system_list_count_probe import INPUT_CSV, OUTPUT, api_get, api_post, list_payload, login


DUMP_DIR = Path(os.getenv("SCBS55_OLD_DUMP_DIR", "artifacts/migration/scbs_55_old_live_list_ids"))


def clean(value: object) -> str:
    return str(value or "").strip()


def main() -> int:
    count_payload = json.loads(OUTPUT.read_text(encoding="utf-8"))
    counts_by_seq = {int(row["seq"]): row for row in count_payload["rows"]}
    session = __import__("requests").Session()
    user = login(session)
    token = user["Token"]
    DUMP_DIR.mkdir(parents=True, exist_ok=True)
    manifest: list[dict[str, Any]] = []
    for csv_row in csv.DictReader(INPUT_CSV.open("r", encoding="utf-8-sig", newline="")):
        seq = int(csv_row["seq"])
        count_row = counts_by_seq.get(seq) or {}
        old_count = count_row.get("old_count")
        item = {
            "seq": seq,
            "name": csv_row["name"],
            "config_id": csv_row.get("config_id") or "",
            "main_table": csv_row.get("main_table") or "",
            "old_count": old_count,
            "dump_count": None,
            "path": "",
            "status": "SKIP",
            "error": "",
        }
        if csv_row.get("config_type") != "List" or not csv_row.get("config_id") or old_count is None:
            manifest.append(item)
            continue
        try:
            config = api_get(session, token, f"LowCode/FormApi/GetConfigById?Id={item['config_id']}&LoadInitData=true")["Data"]
            payload = list_payload(config)
            payload["PageSize"] = max(1, int(old_count))
            detail = json.loads(config.get("DETAIL_CONFIG") or "{}")
            other = detail.get("OtherConfig") or {}
            path = "LowCode/FormApi/ListByTableName"
            if other.get("ListApi"):
                path = str(other["ListApi"]).removeprefix("/api/")
            elif other.get("ListProcedure"):
                payload["Procedure"] = other["ListProcedure"]
                path = "LowCode/FormApi/ListByProcedure"
            body = api_post(session, token, path, payload)
            rows = body.get("Data") or []
            id_field = (other.get("MainTable") or {}).get("IdField") or "Id"
            slim_rows = []
            for row in rows:
                slim_rows.append(
                    {
                        "id": clean(row.get(id_field) or row.get("Id") or row.get("PID") or row.get("pid")),
                        "pid": clean(row.get("PID") or row.get("pid")),
                        "document_no": clean(row.get("DJBH") or row.get("BH") or row.get("BillNo") or row.get("Code")),
                        "date": clean(row.get("f_SQRQ") or row.get("RQ") or row.get("LRSJ") or row.get("f_LRSJ"))[:19],
                    }
                )
            out_path = DUMP_DIR / f"seq_{seq:03d}_{item['main_table'] or 'list'}.json.gz"
            with gzip.open(out_path, "wt", encoding="utf-8") as handle:
                json.dump({"seq": seq, "name": item["name"], "rows": slim_rows}, handle, ensure_ascii=False)
            item["dump_count"] = len(slim_rows)
            item["path"] = str(out_path)
            item["status"] = "PASS"
        except Exception as exc:  # noqa: BLE001
            item["status"] = "FAIL"
            item["error"] = str(exc)
        manifest.append(item)
        print("[old-dump] seq=%03d name=%s status=%s old=%s dump=%s error=%s" % (seq, item["name"], item["status"], old_count, item["dump_count"], item["error"][:120]), flush=True)
    manifest_path = DUMP_DIR / "manifest.json"
    manifest_path.write_text(json.dumps({"old_user": {k: user.get(k) for k in ("UserId", "UserName", "PersonName", "ProjectName")}, "rows": manifest}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"SCBS55_OLD_LIST_ID_DUMP={manifest_path}")
    return 0 if not [row for row in manifest if row["status"] == "FAIL"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
