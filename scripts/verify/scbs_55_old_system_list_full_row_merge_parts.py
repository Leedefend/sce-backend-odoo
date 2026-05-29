#!/usr/bin/env python3
"""Merge SCBS55 old full-row dump parts created by the parallel dumper."""

from __future__ import annotations

import gzip
import json
import os
from pathlib import Path


INPUT_GLOB = os.getenv("SCBS55_OLD_FULL_DUMP_PART_GLOB", "artifacts/migration/scbs_55_old_live_full_rows_seq042_part_*.json.gz")
OUTPUT = Path(os.getenv("SCBS55_OLD_FULL_DUMP_OUTPUT", "artifacts/migration/scbs_55_old_live_full_rows_seq042_input_invoice_parallel.json.gz"))


def main() -> int:
    rows = []
    meta = None
    pages = []
    for path in sorted(Path().glob(INPUT_GLOB)):
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            data = json.load(handle)
        meta = meta or {key: data.get(key) for key in ("seq", "name", "main_table", "data_count", "page_size", "page_count")}
        pages.append([data.get("page_start"), data.get("page_end"), len(data.get("rows") or [])])
        rows.extend(data.get("rows") or [])
    if meta is None:
        raise RuntimeError(f"no parts matched {INPUT_GLOB}")
    payload = {**meta, "parts": pages, "rows": rows}
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(OUTPUT, "wt", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False)
    status = "PASS" if len(rows) == int(meta.get("data_count") or 0) else "COUNT_MISMATCH"
    print(json.dumps({"status": status, "path": str(OUTPUT), "rows": len(rows), "data_count": meta.get("data_count"), "parts": pages}, ensure_ascii=False))
    return 0 if status == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
