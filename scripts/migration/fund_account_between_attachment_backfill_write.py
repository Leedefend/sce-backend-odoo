#!/usr/bin/env python3
"""Backfill legacy attachment refs for formal account-transfer operations."""

from __future__ import annotations

import gzip
import json
import os
import re
from pathlib import Path


SOURCE_GLOB = "/mnt/artifacts/migration/live_old_system_strict_parity_gate/*/scbs55_old_live_rows/scbs_55_old_live_full_rows_seq032_账户间资金往来.json.gz"


def clean(value):
    if value is None or value is False:
        return ""
    text = re.sub(r"\s+", " ", str(value).replace("\u3000", " ").strip())
    return "" if text in {"False", "false", "None", "NULL"} else text


def ensure_allowed_db():
    allowlist = {
        item.strip()
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_demo").split(",")
        if item.strip()
    }
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_attachment_backfill": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def source_path() -> Path:
    configured = os.getenv("FUND_ACCOUNT_BETWEEN_SOURCE_JSON")
    if configured:
        path = Path(configured)
        if path.exists():
            return path
    paths = sorted(Path("/").glob(SOURCE_GLOB.lstrip("/")))
    if not paths:
        raise RuntimeError({"missing_seq032_source_json": SOURCE_GLOB})
    return paths[-1]


def read_rows(path: Path) -> list[dict]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        payload = json.load(handle)
    return payload.get("rows") if isinstance(payload, dict) else payload


ensure_allowed_db()
Operation = env["sc.fund.account.operation"].sudo().with_context(active_test=False)  # noqa: F821
path = source_path()
rows = read_rows(path)

attachment_by_document_no = {}
duplicate_document_no = set()
for row in rows:
    document_no = clean(row.get("DJBH"))
    attachment_ref = clean(row.get("FJ") or row.get("f_FJ"))
    if not document_no:
        continue
    if document_no in attachment_by_document_no and attachment_by_document_no[document_no] != attachment_ref:
        duplicate_document_no.add(document_no)
    if attachment_ref:
        attachment_by_document_no[document_no] = attachment_ref

domain = [
    ("operation_type", "=", "transfer_between"),
    ("legacy_source_table", "=", "C_FKGL_ZHJZJWL"),
]
records = Operation.search(domain)
updated = 0
matched = 0
missing_source_attachment = []
for record in records:
    document_no = clean(record.legacy_visible_document_no or record.name)
    attachment_ref = attachment_by_document_no.get(document_no, "")
    if not attachment_ref:
        missing_source_attachment.append({"id": record.id, "document_no": document_no})
        continue
    matched += 1
    if clean(record.legacy_attachment_ref) != attachment_ref:
        record.write({"legacy_attachment_ref": attachment_ref})
        updated += 1

env.cr.commit()  # noqa: F821

with_attachment = Operation.search_count(domain + [("legacy_attachment_ref", "!=", False)])
payload = {
    "status": "PASS" if with_attachment == len(records) and not missing_source_attachment and not duplicate_document_no else "FAIL",
    "database": env.cr.dbname,  # noqa: F821
    "mode": "fund_account_between_attachment_backfill_write",
    "source_path": str(path),
    "source_rows": len(rows),
    "source_with_attachment": len(attachment_by_document_no),
    "formal_records": len(records),
    "matched": matched,
    "updated": updated,
    "with_attachment": with_attachment,
    "missing_source_attachment": missing_source_attachment[:20],
    "duplicate_document_no": sorted(duplicate_document_no)[:20],
}
print("FUND_ACCOUNT_BETWEEN_ATTACHMENT_BACKFILL=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
if payload["status"] != "PASS":
    raise SystemExit(2)
