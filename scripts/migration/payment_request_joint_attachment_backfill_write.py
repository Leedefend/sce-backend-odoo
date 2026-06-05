#!/usr/bin/env python3
"""Backfill joint payment request attachment links from the live C_ZFSQGL rows."""

from __future__ import annotations

import gzip
import json
import os
import re
from pathlib import Path


def clean(value):
    if value is None or value is False:
        return ""
    return re.sub(r"\s+", " ", str(value).strip())


def ensure_allowed_db():
    allowlist = {
        item.strip()
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_demo").split(",")
        if item.strip()
    }
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_replay": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def source_path() -> Path:
    candidates = [
        os.getenv("PAYMENT_REQUEST_JOINT_LIVE_ROWS_JSON"),
        "/mnt/artifacts/migration/scbs_55_old_live_full_rows_current/seq029.json.gz",
        "artifacts/migration/scbs_55_old_live_full_rows_current/seq029.json.gz",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return Path(candidate)
    raise RuntimeError({"payment_request_joint_live_rows_missing": [item for item in candidates if item]})


def attachment_label(display, ref):
    display = clean(display) or "历史附件"
    ref = clean(ref)
    if not ref:
        return display or False
    if "legacy-file-id://" in display:
        return display
    return f"{display} | legacy-file-id://{ref}"


ensure_allowed_db()

path = source_path()
with gzip.open(path, "rt", encoding="utf-8") as handle:
    rows = json.load(handle).get("rows") or []

rows_by_id = {clean(row.get("Id")): row for row in rows if clean(row.get("Id")) and clean(row.get("FJ"))}
Payment = env["payment.request"].sudo().with_context(active_test=False)  # noqa: F821
Attachment = env["ir.attachment"].sudo()  # noqa: F821
records = Payment.search(
    [
        ("legacy_source_table", "=", "C_ZFSQGL"),
        ("operation_strategy", "=", "joint"),
        ("legacy_record_id", "in", list(rows_by_id)),
    ]
)

stats = {
    "source_path": str(path),
    "source_rows_with_fj": len(rows_by_id),
    "matched_records": len(records),
    "updated_visible": 0,
    "attachments_created": 0,
    "attachments_reused": 0,
    "relations_linked": 0,
}

for record in records:
    row = rows_by_id.get(clean(record.legacy_record_id)) or {}
    ref = clean(row.get("FJ"))
    if not ref:
        continue
    label = attachment_label(row.get("f_FJ"), ref)
    if clean(record.legacy_visible_attachment) != label:
        record.write({"legacy_visible_attachment": label})
        stats["updated_visible"] += 1
    url = f"legacy-file-id://{ref}"
    attachment = Attachment.search(
        [("res_model", "=", "payment.request"), ("res_id", "=", record.id), ("url", "=", url)],
        limit=1,
    )
    if attachment:
        stats["attachments_reused"] += 1
    else:
        attachment = Attachment.create(
            {
                "name": clean(row.get("f_FJ")) or f"历史附件-{record.name or record.id}",
                "type": "url",
                "url": url,
                "res_model": "payment.request",
                "res_id": record.id,
            }
        )
        stats["attachments_created"] += 1
    if attachment and "attachment_ids" in Payment._fields and attachment not in record.attachment_ids:
        record.write({"attachment_ids": [(4, attachment.id)]})
        stats["relations_linked"] += 1

stats["missing_record"] = len(rows_by_id) - len(records)
env.cr.commit()  # noqa: F821

print(
    "PAYMENT_REQUEST_JOINT_ATTACHMENT_BACKFILL="
    + json.dumps(
        {
            "database": env.cr.dbname,  # noqa: F821
            "mode": "payment_request_joint_attachment_backfill_write",
            "status": "PASS",
            **stats,
            "decision": "linked_C_ZFSQGL_FJ_bill_ids_to_formal_payment_request_attachments",
        },
        ensure_ascii=False,
        sort_keys=True,
    )
)
