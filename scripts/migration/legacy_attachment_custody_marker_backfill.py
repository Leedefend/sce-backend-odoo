# -*- coding: utf-8 -*-
"""Backfill legacy URL attachment custody boundary markers.

Run through ``odoo shell``. The script is intentionally narrow: it only adds
``binary_embedded=false`` to ``ir.attachment.description`` for legacy URL
attachments that already point to ``legacy-file://`` or ``legacy-file-id://``.
It does not change URLs, bindings, business records, or physical files.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path


MARKER = "binary_embedded=false"
APPLY = os.getenv("LEGACY_ATTACHMENT_CUSTODY_MARKER_APPLY", "1").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
LIMIT = int(os.getenv("LEGACY_ATTACHMENT_CUSTODY_MARKER_LIMIT", "0") or "0")
EXAMPLE_LIMIT = int(os.getenv("LEGACY_ATTACHMENT_CUSTODY_MARKER_EXAMPLE_LIMIT", "20") or "20")
OUTPUT_JSON = Path(
    os.getenv(
        "LEGACY_ATTACHMENT_CUSTODY_MARKER_OUTPUT",
        "/tmp/legacy_attachment_custody_marker_backfill_result_v1.json",
    )
)


def _safe_output_path(path: Path) -> Path:
    candidates = [path, Path("/tmp/legacy_attachment_custody_marker_backfill_result_v1.json")]
    for candidate in candidates:
        try:
            candidate.parent.mkdir(parents=True, exist_ok=True)
            probe = candidate.parent / ".legacy_attachment_custody_marker_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return candidate
        except OSError:
            continue
    return candidates[-1]


def _fetchone(sql: str, params: list[object] | None = None) -> tuple[object, ...]:
    env.cr.execute(sql, params or [])  # noqa: F821
    return env.cr.fetchone() or (0,)  # noqa: F821


def _fetchall(sql: str, params: list[object] | None = None) -> list[tuple[object, ...]]:
    env.cr.execute(sql, params or [])  # noqa: F821
    return env.cr.fetchall()  # noqa: F821


def _candidate_where() -> str:
    return """
        type = 'url'
        AND (url LIKE 'legacy-file://%%' OR url LIKE 'legacy-file-id://%%')
        AND COALESCE(description, '') NOT ILIKE '%%binary_embedded=false%%'
    """


def _candidate_count() -> int:
    return int(_fetchone("SELECT COUNT(*) FROM ir_attachment WHERE " + _candidate_where())[0] or 0)


def _examples() -> list[dict[str, object]]:
    rows = _fetchall(
        """
        SELECT id, res_model, res_id, url, COALESCE(description, '')
        FROM ir_attachment
        WHERE """
        + _candidate_where()
        + """
        ORDER BY id
        LIMIT %s
        """,
        [EXAMPLE_LIMIT],
    )
    return [
        {
            "id": row[0],
            "res_model": row[1],
            "res_id": row[2],
            "url": row[3],
            "description": row[4],
        }
        for row in rows
    ]


def _backfill() -> int:
    if not APPLY:
        return 0
    if LIMIT:
        env.cr.execute(  # noqa: F821
            """
            WITH candidates AS (
                SELECT id
                FROM ir_attachment
                WHERE """
            + _candidate_where()
            + """
                ORDER BY id
                LIMIT %s
            ),
            updated AS (
                UPDATE ir_attachment attachment
                   SET description = CASE
                         WHEN COALESCE(attachment.description, '') = ''
                         THEN %s
                         ELSE attachment.description || '; ' || %s
                       END,
                       write_uid = 1,
                       write_date = NOW()
                  FROM candidates
                 WHERE attachment.id = candidates.id
                 RETURNING attachment.id
            )
            SELECT COUNT(*) FROM updated
            """,
            [LIMIT, MARKER, MARKER],
        )
    else:
        env.cr.execute(  # noqa: F821
            """
            WITH updated AS (
                UPDATE ir_attachment
                   SET description = CASE
                         WHEN COALESCE(description, '') = ''
                         THEN %s
                         ELSE description || '; ' || %s
                       END,
                       write_uid = 1,
                       write_date = NOW()
                 WHERE """
            + _candidate_where()
            + """
                 RETURNING id
            )
            SELECT COUNT(*) FROM updated
            """,
            [MARKER, MARKER],
        )
    updated = int((env.cr.fetchone() or [0])[0] or 0)  # noqa: F821
    env.cr.commit()  # noqa: F821
    return updated


before = _candidate_count()
examples_before = _examples()
updated_count = _backfill()
after = _candidate_count()

payload = {
    "status": "PASS" if after == max(before - updated_count, 0) else "FAIL",
    "mode": "legacy_attachment_custody_marker_backfill",
    "database": env.cr.dbname,  # noqa: F821
    "apply": APPLY,
    "limit": LIMIT,
    "marker": MARKER,
    "candidate_count_before": before,
    "updated_count": updated_count,
    "candidate_count_after": after,
    "db_writes": updated_count,
    "examples_before": examples_before,
    "generated_at": datetime.now(timezone.utc).isoformat(),
}

output_path = _safe_output_path(OUTPUT_JSON)
output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print("LEGACY_ATTACHMENT_CUSTODY_MARKER_BACKFILL=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
if payload["status"] != "PASS":
    raise SystemExit(1)
