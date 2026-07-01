#!/usr/bin/env python3
"""Backfill editable tender.bid formal fields from legacy/source values."""

from __future__ import annotations

import json
import os
from pathlib import Path


def repo_root() -> Path:
    env_root = os.getenv("MIGRATION_REPO_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.extend([Path("/mnt"), Path.cwd()])
    for candidate in candidates:
        if (candidate / "addons/smart_construction_core").exists():
            return candidate
    return Path.cwd()


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


REPO_ROOT = repo_root()
ARTIFACT_ROOT = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", str(REPO_ROOT / "artifacts/migration")))
OUTPUT_JSON = ARTIFACT_ROOT / "tender_bid_formal_fields_backfill_write_result_v1.json"

env.cr.execute("SELECT COUNT(*) FROM tender_bid")  # noqa: F821
total_rows = env.cr.fetchone()[0]  # noqa: F821

env.cr.execute(  # noqa: F821
    """
    UPDATE tender_bid tb
       SET applicant_name = COALESCE(NULLIF(tb.applicant_name, ''), tb.legacy_visible_creator_name, tb.source_created_by),
           apply_date = COALESCE(
               tb.apply_date,
               tb.legacy_visible_registration_time::date,
               tb.source_created_at::date,
               tb.create_date::date
           ),
           note = COALESCE(NULLIF(tb.note, ''), tb.legacy_note),
           created_time = COALESCE(tb.created_time, tb.source_created_at, tb.legacy_visible_registration_time, tb.create_date),
           write_date = NOW()
     WHERE COALESCE(NULLIF(tb.applicant_name, ''), tb.legacy_visible_creator_name, tb.source_created_by) IS DISTINCT FROM tb.applicant_name
        OR COALESCE(
               tb.apply_date,
               tb.legacy_visible_registration_time::date,
               tb.source_created_at::date,
               tb.create_date::date
           ) IS DISTINCT FROM tb.apply_date
        OR COALESCE(NULLIF(tb.note, ''), tb.legacy_note) IS DISTINCT FROM tb.note
        OR COALESCE(tb.created_time, tb.source_created_at, tb.legacy_visible_registration_time, tb.create_date) IS DISTINCT FROM tb.created_time
    """
)
updated_rows = env.cr.rowcount  # noqa: F821
env.cr.commit()  # noqa: F821

env.cr.execute(  # noqa: F821
    """
    SELECT
      COUNT(*) FILTER (WHERE applicant_name IS NOT NULL AND applicant_name != ''),
      COUNT(*) FILTER (WHERE apply_date IS NOT NULL),
      COUNT(*) FILTER (WHERE note IS NOT NULL AND note != ''),
      COUNT(*) FILTER (WHERE created_time IS NOT NULL)
    FROM tender_bid
    """
)
applicant_rows, apply_date_rows, note_rows, created_time_rows = env.cr.fetchone()  # noqa: F821

payload = {
    "status": "PASS",
    "mode": "tender_bid_formal_fields_backfill_write",
    "database": env.cr.dbname,  # noqa: F821
    "total_rows": total_rows,
    "updated_rows": updated_rows,
    "formal_filled": {
        "applicant_name": applicant_rows,
        "apply_date": apply_date_rows,
        "note": note_rows,
        "created_time": created_time_rows,
    },
    "decision": "tender_bid_history_values_absorbed_into_formal_fields",
}
write_json(OUTPUT_JSON, payload)
print("TENDER_BID_FORMAL_FIELDS_BACKFILL_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
