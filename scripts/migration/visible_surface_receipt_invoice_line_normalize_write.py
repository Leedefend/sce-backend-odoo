#!/usr/bin/env python3
"""Normalize receipt invoice line visible source document facts."""

from __future__ import annotations

import json
import os
from pathlib import Path


def artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT") or os.getenv("ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.append(Path("/mnt/artifacts/migration"))
    candidates.append(Path(f"/tmp/history_continuity/{env.cr.dbname}/adhoc"))  # noqa: F821
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return candidate
        except Exception:
            continue
    return Path(f"/tmp/history_continuity/{env.cr.dbname}/adhoc")  # noqa: F821


def scalar(sql: str) -> object:
    env.cr.execute(sql)  # noqa: F821
    row = env.cr.fetchone()  # noqa: F821
    return row[0] if row else None


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


allowlist = {item.strip() for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "").split(",") if item.strip()}
if allowlist and env.cr.dbname not in allowlist:  # noqa: F821
    raise RuntimeError({"db_name_not_allowed_for_visible_surface_write": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821

before_missing = int(scalar("SELECT COUNT(*) FROM sc_receipt_invoice_line WHERE source_document_no IS NULL OR source_document_no = ''") or 0)

env.cr.execute(  # noqa: F821
    """
    UPDATE sc_receipt_invoice_line AS line
       SET source_document_no = NULLIF(substring(request.note FROM 'document_no=([^\\n;]+)'), ''),
           write_uid = 1,
           write_date = NOW()
      FROM payment_request AS request
     WHERE request.id = line.request_id
       AND (line.source_document_no IS NULL OR line.source_document_no = '')
       AND request.note LIKE '%[migration:receipt_core]%'
       AND NULLIF(substring(request.note FROM 'document_no=([^\\n;]+)'), '') IS NOT NULL
    """
)
updated = env.cr.rowcount  # noqa: F821
env.cr.commit()  # noqa: F821

after_missing = int(scalar("SELECT COUNT(*) FROM sc_receipt_invoice_line WHERE source_document_no IS NULL OR source_document_no = ''") or 0)
with_source_document_no = int(scalar("SELECT COUNT(*) FROM sc_receipt_invoice_line WHERE source_document_no IS NOT NULL AND source_document_no <> ''") or 0)
payload = {
    "status": "PASS",
    "mode": "visible_surface_receipt_invoice_line_normalize_write",
    "database": env.cr.dbname,  # noqa: F821
    "before_missing_source_document_no": before_missing,
    "after_missing_source_document_no": after_missing,
    "updated_rows": updated,
    "with_source_document_no": with_source_document_no,
    "decision": "receipt_invoice_line_source_document_no_backfilled_from_parent_receipt_fact",
}
write_json(artifact_root() / "visible_surface_receipt_invoice_line_normalize_write_result_v1.json", payload)
print("VISIBLE_SURFACE_RECEIPT_INVOICE_LINE_NORMALIZE_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
