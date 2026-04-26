#!/usr/bin/env python3
"""Read-only probe for migrated legacy attachment custody and access surfaces."""

from __future__ import annotations

import json
import os
from pathlib import Path


def repo_root() -> Path:
    env_root = os.getenv("MIGRATION_REPO_ROOT")
    candidates = []
    if env_root:
        candidates.append(Path(env_root))
    candidates.extend([Path("/mnt"), Path.cwd()])
    for candidate in candidates:
        if (candidate / "addons/smart_construction_core/__manifest__.py").exists():
            return candidate
    return Path.cwd()


def resolve_artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = []
    if env_root:
        candidates.append(Path(env_root))
    candidates.append(repo_root() / "artifacts/migration")
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


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_report(path: Path, payload: dict[str, object]) -> None:
    lines = [
        "# History Attachment Custody Probe v1",
        "",
        f"Status: {payload['status']}",
        "",
        "## Decision",
        "",
        f"`{payload['decision']}`",
        "",
        "## Counts",
        "",
        "```json",
        json.dumps(payload["counts"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## URL Attachments By Model",
        "",
        "```json",
        json.dumps(payload["legacy_url_attachments_by_model"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Samples",
        "",
        "```json",
        json.dumps(payload["samples"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Notes",
        "",
        "- This probe is read-only.",
        "- `legacy-file://` and `legacy-file-id://` URLs preserve old file facts and external custody references.",
        "- Binary bytes are not embedded in Odoo by this lane.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def scalar(sql: str, params: list[object] | None = None) -> int:
    env.cr.execute(sql, params or [])  # noqa: F821
    return int(env.cr.fetchone()[0] or 0)  # noqa: F821


def fetchall(sql: str, params: list[object] | None = None) -> list[tuple[object, ...]]:
    env.cr.execute(sql, params or [])  # noqa: F821
    return env.cr.fetchall()  # noqa: F821


ARTIFACT_ROOT = resolve_artifact_root()
OUTPUT_JSON = ARTIFACT_ROOT / "history_attachment_custody_probe_result_v1.json"
OUTPUT_REPORT = ARTIFACT_ROOT / "history_attachment_custody_probe_report_v1.md"

counts = {
    "legacy_file_index_rows": scalar("SELECT COUNT(*) FROM sc_legacy_file_index"),
    "legacy_file_index_active_rows": scalar("SELECT COUNT(*) FROM sc_legacy_file_index WHERE active"),
    "legacy_file_index_with_path": scalar("SELECT COUNT(*) FROM sc_legacy_file_index WHERE file_path IS NOT NULL AND file_path <> ''"),
    "legacy_file_index_total_bytes": scalar("SELECT COALESCE(SUM(file_size), 0) FROM sc_legacy_file_index"),
    "legacy_url_attachments": scalar(
        """
        SELECT COUNT(*)
        FROM ir_attachment
        WHERE type = 'url'
          AND (url LIKE 'legacy-file://%%' OR url LIKE 'legacy-file-id://%%')
        """
    ),
    "receipt_invoice_attachment_runtime_records": scalar(
        "SELECT COUNT(*) FROM ir_attachment WHERE res_model = 'sc.receipt.invoice.line' AND type = 'url'"
    ),
    "legacy_attachment_backfill_runtime_records": scalar(
        "SELECT COUNT(*) FROM ir_attachment WHERE description ILIKE '%%[migration:legacy_attachment_backfill]%%'"
    ),
    "legacy_url_attachments_missing_res_id": scalar(
        """
        SELECT COUNT(*)
        FROM ir_attachment
        WHERE type = 'url'
          AND (url LIKE 'legacy-file://%%' OR url LIKE 'legacy-file-id://%%')
          AND (res_model IS NULL OR res_model = '' OR res_id IS NULL OR res_id = 0)
        """
    ),
    "legacy_url_attachments_without_boundary_marker": scalar(
        """
        SELECT COUNT(*)
        FROM ir_attachment
        WHERE type = 'url'
          AND (url LIKE 'legacy-file://%%' OR url LIKE 'legacy-file-id://%%')
          AND COALESCE(description, '') NOT ILIKE '%%binary_embedded=false%%'
        """
    ),
    "receipt_invoice_lines_with_attachments": scalar(
        """
        SELECT COUNT(DISTINCT res_id)
        FROM ir_attachment
        WHERE res_model = 'sc.receipt.invoice.line'
          AND type = 'url'
          AND res_id IS NOT NULL
        """
    ),
    "payment_request_lines_with_attachments": scalar(
        """
        SELECT COUNT(DISTINCT res_id)
        FROM ir_attachment
        WHERE res_model = 'payment.request.line'
          AND type = 'url'
          AND res_id IS NOT NULL
        """
    ),
    "payment_requests_with_attachments": scalar(
        """
        SELECT COUNT(DISTINCT res_id)
        FROM ir_attachment
        WHERE res_model = 'payment.request'
          AND type = 'url'
          AND res_id IS NOT NULL
        """
    ),
}

by_model = [
    {"res_model": row[0], "count": int(row[1])}
    for row in fetchall(
        """
        SELECT res_model, COUNT(*)
        FROM ir_attachment
        WHERE type = 'url'
          AND (url LIKE 'legacy-file://%%' OR url LIKE 'legacy-file-id://%%')
        GROUP BY res_model
        ORDER BY COUNT(*) DESC, res_model
        """
    )
]

samples = {
    "legacy_file_index": [
        {
            "legacy_file_id": row[0],
            "file_name": row[1],
            "file_path": row[2],
            "file_size": row[3],
        }
        for row in fetchall(
            """
            SELECT legacy_file_id, file_name, file_path, file_size
            FROM sc_legacy_file_index
            WHERE file_path IS NOT NULL AND file_path <> ''
            ORDER BY upload_time DESC NULLS LAST, id DESC
            LIMIT 5
            """
        )
    ],
    "legacy_url_attachments": [
        {
            "id": row[0],
            "name": row[1],
            "res_model": row[2],
            "res_id": row[3],
            "url": row[4],
        }
        for row in fetchall(
            """
            SELECT id, name, res_model, res_id, url
            FROM ir_attachment
            WHERE type = 'url'
              AND (url LIKE 'legacy-file://%%' OR url LIKE 'legacy-file-id://%%')
            ORDER BY id
            LIMIT 5
            """
        )
    ],
}

gaps = {
    "missing_legacy_file_index": counts["legacy_file_index_rows"] == 0,
    "missing_legacy_url_attachments": counts["legacy_url_attachments"] == 0,
    "legacy_url_attachment_unbound": counts["legacy_url_attachments_missing_res_id"] > 0,
    "legacy_url_attachment_boundary_marker_gap": counts["legacy_url_attachments_without_boundary_marker"] > 0,
}
failing_gaps = [key for key, value in gaps.items() if value]
decision = "history_attachment_custody_ready" if not failing_gaps else "history_attachment_custody_gap"

payload = {
    "status": "PASS",
    "mode": "history_attachment_custody_probe",
    "database": env.cr.dbname,  # noqa: F821
    "db_writes": 0,
    "counts": counts,
    "legacy_url_attachments_by_model": by_model,
    "samples": samples,
    "gaps": gaps,
    "decision": decision,
}

write_json(OUTPUT_JSON, payload)
write_report(OUTPUT_REPORT, payload)
print(
    "HISTORY_ATTACHMENT_CUSTODY_PROBE="
    + json.dumps(
        {
            "status": payload["status"],
            "database": payload["database"],
            "decision": decision,
            "gap_count": len(failing_gaps),
            "legacy_url_attachments": counts["legacy_url_attachments"],
            "db_writes": 0,
        },
        ensure_ascii=False,
        sort_keys=True,
    )
)
