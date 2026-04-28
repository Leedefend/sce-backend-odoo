#!/usr/bin/env python3
"""Project legacy construction diary facts into runtime construction diary."""

from __future__ import annotations

import json
import os
from pathlib import Path


def resolve_artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
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


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def scalar(sql: str) -> object:
    env.cr.execute(sql)  # noqa: F821
    row = env.cr.fetchone()  # noqa: F821
    return row[0] if row else None


artifact_root = resolve_artifact_root()
output_json = artifact_root / "fresh_db_construction_diary_projection_write_result_v1.json"
before = int(scalar("SELECT COUNT(*) FROM sc_construction_diary") or 0)

env.cr.execute(  # noqa: F821
    """
    INSERT INTO sc_construction_diary (
      name, source_origin, state, project_id, date_diary, document_no,
      title, diary_type, category, construction_unit, project_manager,
      quality_name, handler_name, description, header_description, note,
      legacy_source_model, legacy_source_table, legacy_record_id,
      legacy_header_id, legacy_document_state, legacy_quality_id,
      legacy_business_id, legacy_related_business_id, legacy_related_quality_type,
      legacy_attachment_ref, legacy_line_attachment_ref, legacy_attachment_name,
      legacy_attachment_path, active, create_uid, write_uid, create_date, write_date
    )
    SELECT
      COALESCE(NULLIF(l.document_no, ''), 'LEGACY-DIARY-' || l.legacy_line_id),
      'legacy',
      CASE WHEN COALESCE(l.document_state, '') = '2' THEN 'legacy_confirmed' ELSE 'draft' END,
      l.project_id,
      COALESCE(l.diary_date, l.created_time, NOW()),
      NULLIF(l.document_no, ''),
      NULLIF(l.title, ''),
      NULLIF(l.diary_type, ''),
      NULLIF(l.category, ''),
      NULLIF(l.construction_unit, ''),
      NULLIF(l.project_manager, ''),
      NULLIF(l.line_quality_name, ''),
      NULLIF(l.handler_name, ''),
      NULLIF(l.line_description, ''),
      NULLIF(l.header_description, ''),
      CONCAT_WS(E'\n',
        '[migration:construction_diary] legacy_line_id=' || l.legacy_line_id,
        NULLIF(l.header_note, '')
      ),
      'sc.legacy.construction.diary.line',
      l.source_table,
      l.legacy_line_id,
      NULLIF(l.legacy_header_id, ''),
      NULLIF(l.document_state, ''),
      NULLIF(l.line_quality_legacy_id, ''),
      NULLIF(l.business_legacy_id, ''),
      NULLIF(l.related_business_legacy_id, ''),
      NULLIF(l.related_quality_type, ''),
      NULLIF(l.attachment_ref, ''),
      NULLIF(l.line_attachment_ref, ''),
      NULLIF(l.attachment_name, ''),
      NULLIF(l.attachment_path, ''),
      l.active,
      1,
      1,
      NOW(),
      NOW()
    FROM sc_legacy_construction_diary_line l
    WHERE l.active
      AND l.project_id IS NOT NULL
    ON CONFLICT (legacy_source_model, legacy_record_id)
    DO UPDATE SET
      state = EXCLUDED.state,
      project_id = EXCLUDED.project_id,
      date_diary = EXCLUDED.date_diary,
      document_no = EXCLUDED.document_no,
      title = EXCLUDED.title,
      diary_type = EXCLUDED.diary_type,
      category = EXCLUDED.category,
      construction_unit = EXCLUDED.construction_unit,
      project_manager = EXCLUDED.project_manager,
      quality_name = EXCLUDED.quality_name,
      handler_name = EXCLUDED.handler_name,
      description = EXCLUDED.description,
      header_description = EXCLUDED.header_description,
      note = EXCLUDED.note,
      legacy_header_id = EXCLUDED.legacy_header_id,
      legacy_document_state = EXCLUDED.legacy_document_state,
      legacy_quality_id = EXCLUDED.legacy_quality_id,
      legacy_business_id = EXCLUDED.legacy_business_id,
      legacy_related_business_id = EXCLUDED.legacy_related_business_id,
      legacy_related_quality_type = EXCLUDED.legacy_related_quality_type,
      legacy_attachment_ref = EXCLUDED.legacy_attachment_ref,
      legacy_line_attachment_ref = EXCLUDED.legacy_line_attachment_ref,
      legacy_attachment_name = EXCLUDED.legacy_attachment_name,
      legacy_attachment_path = EXCLUDED.legacy_attachment_path,
      active = EXCLUDED.active,
      write_uid = 1,
      write_date = NOW()
    """,
)

env.cr.commit()  # noqa: F821

after = int(scalar("SELECT COUNT(*) FROM sc_construction_diary") or 0)
payload = {
    "status": "PASS",
    "mode": "fresh_db_construction_diary_projection_write",
    "database": env.cr.dbname,  # noqa: F821
    "before": before,
    "after": after,
    "delta": after - before,
    "legacy_rows": int(scalar("SELECT COUNT(*) FROM sc_construction_diary WHERE source_origin = 'legacy'") or 0),
    "legacy_with_project": int(
        scalar("SELECT COUNT(*) FROM sc_construction_diary WHERE source_origin = 'legacy' AND project_id IS NOT NULL")
        or 0
    ),
    "legacy_confirmed": int(
        scalar("SELECT COUNT(*) FROM sc_construction_diary WHERE source_origin = 'legacy' AND state = 'legacy_confirmed'")
        or 0
    ),
    "legacy_with_description": int(
        scalar(
            "SELECT COUNT(*) FROM sc_construction_diary "
            "WHERE source_origin = 'legacy' AND (COALESCE(description, '') <> '' OR COALESCE(header_description, '') <> '')"
        )
        or 0
    ),
    "legacy_with_attachment_ref": int(
        scalar(
            "SELECT COUNT(*) FROM sc_construction_diary "
            "WHERE source_origin = 'legacy' AND (legacy_attachment_path IS NOT NULL OR legacy_attachment_ref IS NOT NULL OR legacy_line_attachment_ref IS NOT NULL)"
        )
        or 0
    ),
}
write_json(output_json, payload)
print("CONSTRUCTION_DIARY_PROJECTION_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
