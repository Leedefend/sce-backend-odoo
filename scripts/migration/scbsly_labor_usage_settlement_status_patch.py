# -*- coding: utf-8 -*-
"""Patch SCBSLY labor usage settlement status from browser-verified old data.

Run through ``odoo shell``. The old SCBSLY list renders settlement status from
``CCCC_JSZT`` after its custom ``listPageReadJSZT`` event. The plain list API
does not include that field, so replayed rows need this browser-verified value.
"""

from __future__ import annotations

import json
import os
from pathlib import Path


ROOT = Path(os.getenv("MIGRATION_REPO_ROOT", "/mnt"))
if not (ROOT / "artifacts/migration/scbsly_labor_usage_browser_vue_status_full_20260603.json").exists():
    ROOT = Path.cwd()

SOURCE_JSON = Path(
    os.getenv("SCBSLY_LABOR_USAGE_STATUS_SOURCE")
    or ROOT / "artifacts/migration/scbsly_labor_usage_browser_vue_status_full_20260603.json"
)

STATUS_TEXT = {
    "0": "未结算",
    "1": "部分结算",
    "2": "已结算",
}


def load_rows():
    payload = json.loads(SOURCE_JSON.read_text(encoding="utf-8"))
    rows = payload.get("rows") or []
    by_id = {}
    by_document_no = {}
    for row in rows:
        legacy_id = str(row.get("Id") or "").strip()
        document_no = str(row.get("DJBH") or "").strip()
        status = row.get("CCCC_JSZT")
        if status is None:
            continue
        status_text = str(status).strip()
        if legacy_id:
            by_id[legacy_id] = status_text
        if document_no:
            by_document_no[document_no] = status_text
    return payload, by_id, by_document_no


def main():
    payload, status_by_id, status_by_document_no = load_rows()
    model = env["sc.legacy.direct.acceptance.fact"].sudo()  # noqa: F821
    records = model.search([("active", "=", True), ("acceptance_label", "=", "方单")])
    updated = 0
    missing = []
    counters = {}
    for record in records:
        status = status_by_id.get(record.legacy_record_id) or status_by_document_no.get(record.document_no)
        if status is None:
            missing.append(record.legacy_record_id or record.document_no)
            continue
        raw = record._legacy_raw_payload_dict()
        if raw.get("CCCC_JSZT") != status:
            raw["CCCC_JSZT"] = status
            record.write({"raw_payload": json.dumps(raw, ensure_ascii=False, sort_keys=True)})
            updated += 1
        counters[status] = counters.get(status, 0) + 1

    result = {
        "source_json": str(SOURCE_JSON),
        "source_row_count": payload.get("rowCount"),
        "source_status_counters": payload.get("statusCounters"),
        "record_count": len(records),
        "updated": updated,
        "missing_count": len(missing),
        "missing_sample": missing[:10],
        "applied_status_counters": {
            STATUS_TEXT.get(key, key): value
            for key, value in sorted(counters.items())
        },
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    if missing:
        raise RuntimeError(result)
    env.cr.commit()  # noqa: F821


main()
