#!/usr/bin/env python3
"""Replay legacy construction diary line facts into a neutral carrier model."""

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
        if (candidate / "artifacts/migration/fresh_db_legacy_construction_diary_line_replay_adapter_result_v1.json").exists():
            return candidate
    return Path.cwd()


def ensure_allowed_db() -> None:
    allowlist = {item.strip() for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_migration_fresh").split(",") if item.strip()}
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_replay": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def bulk_load(csv_path: Path, temp_table: str, columns: list[str]) -> None:
    env.cr.execute(f"DROP TABLE IF EXISTS {temp_table}")  # noqa: F821
    env.cr.execute(f"CREATE TEMP TABLE {temp_table} ({', '.join(f'{col} text' for col in columns)}) ON COMMIT DROP")  # noqa: F821
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        env.cr.copy_expert(  # noqa: F821
            f"COPY {temp_table} ({', '.join(columns)}) FROM STDIN WITH CSV HEADER",
            handle,
        )


REPO_ROOT = repo_root()
ARTIFACT_ROOT = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", str(REPO_ROOT / "artifacts/migration")))
INPUT_MANIFEST = REPO_ROOT / "artifacts/migration/fresh_db_legacy_construction_diary_line_replay_adapter_result_v1.json"
INPUT_CSV = REPO_ROOT / "artifacts/migration/fresh_db_legacy_construction_diary_line_replay_payload_v1.csv"
OUTPUT_JSON = ARTIFACT_ROOT / "fresh_db_legacy_construction_diary_line_replay_write_result_v1.json"

COLUMNS = [
    "legacy_line_id",
    "legacy_header_id",
    "legacy_pid",
    "legacy_header_pid",
    "document_no",
    "document_state",
    "title",
    "diary_type",
    "category",
    "project_legacy_id",
    "project_name",
    "construction_unit",
    "project_manager",
    "diary_date",
    "header_description",
    "header_note",
    "line_quality_legacy_id",
    "line_quality_name",
    "line_description",
    "business_legacy_id",
    "related_business_legacy_id",
    "related_quality_type",
    "handler_name",
    "creator_legacy_user_id",
    "creator_name",
    "created_time",
    "modifier_legacy_user_id",
    "modifier_name",
    "modified_time",
    "attachment_ref",
    "line_attachment_ref",
    "attachment_name",
    "attachment_path",
    "active",
]

ensure_allowed_db()
manifest = json.loads(INPUT_MANIFEST.read_text(encoding="utf-8"))
uid = env.uid  # noqa: F821

bulk_load(INPUT_CSV, "tmp_legacy_construction_diary_line", COLUMNS)

env.cr.execute("SELECT COUNT(*) FROM sc_legacy_construction_diary_line")  # noqa: F821
before = env.cr.fetchone()[0]  # noqa: F821

env.cr.execute(  # noqa: F821
    """
    INSERT INTO sc_legacy_construction_diary_line (
      legacy_line_id, legacy_header_id, legacy_pid, legacy_header_pid,
      document_no, document_state, title, diary_type, category,
      project_legacy_id, project_name, project_id, construction_unit,
      project_manager, diary_date, header_description, header_note,
      line_quality_legacy_id, line_quality_name, line_description,
      business_legacy_id, related_business_legacy_id, related_quality_type,
      handler_name, creator_legacy_user_id, creator_name, created_time,
      modifier_legacy_user_id, modifier_name, modified_time, attachment_ref,
      line_attachment_ref, attachment_name, attachment_path, source_table,
      active, create_uid, create_date, write_uid, write_date
    )
    SELECT
      t.legacy_line_id,
      NULLIF(t.legacy_header_id, ''),
      NULLIF(t.legacy_pid, ''),
      NULLIF(t.legacy_header_pid, ''),
      NULLIF(t.document_no, ''),
      NULLIF(t.document_state, ''),
      NULLIF(t.title, ''),
      NULLIF(t.diary_type, ''),
      NULLIF(t.category, ''),
      NULLIF(t.project_legacy_id, ''),
      NULLIF(t.project_name, ''),
      project.id,
      NULLIF(t.construction_unit, ''),
      NULLIF(t.project_manager, ''),
      NULLIF(t.diary_date, '')::timestamp,
      NULLIF(t.header_description, ''),
      NULLIF(t.header_note, ''),
      NULLIF(t.line_quality_legacy_id, ''),
      NULLIF(t.line_quality_name, ''),
      NULLIF(t.line_description, ''),
      NULLIF(t.business_legacy_id, ''),
      NULLIF(t.related_business_legacy_id, ''),
      NULLIF(t.related_quality_type, ''),
      NULLIF(t.handler_name, ''),
      NULLIF(t.creator_legacy_user_id, ''),
      NULLIF(t.creator_name, ''),
      NULLIF(t.created_time, '')::timestamp,
      NULLIF(t.modifier_legacy_user_id, ''),
      NULLIF(t.modifier_name, ''),
      NULLIF(t.modified_time, '')::timestamp,
      NULLIF(t.attachment_ref, ''),
      NULLIF(t.line_attachment_ref, ''),
      NULLIF(t.attachment_name, ''),
      NULLIF(t.attachment_path, ''),
      'SGZL_RZRJ_CB',
      COALESCE(NULLIF(t.active, ''), '1') = '1',
      %s, NOW(), %s, NOW()
    FROM tmp_legacy_construction_diary_line t
    LEFT JOIN project_project project ON project.legacy_project_id = NULLIF(t.project_legacy_id, '')
    ON CONFLICT (legacy_line_id) DO UPDATE SET
      legacy_header_id = EXCLUDED.legacy_header_id,
      legacy_pid = EXCLUDED.legacy_pid,
      legacy_header_pid = EXCLUDED.legacy_header_pid,
      document_no = EXCLUDED.document_no,
      document_state = EXCLUDED.document_state,
      title = EXCLUDED.title,
      diary_type = EXCLUDED.diary_type,
      category = EXCLUDED.category,
      project_legacy_id = EXCLUDED.project_legacy_id,
      project_name = EXCLUDED.project_name,
      project_id = EXCLUDED.project_id,
      construction_unit = EXCLUDED.construction_unit,
      project_manager = EXCLUDED.project_manager,
      diary_date = EXCLUDED.diary_date,
      header_description = EXCLUDED.header_description,
      header_note = EXCLUDED.header_note,
      line_quality_legacy_id = EXCLUDED.line_quality_legacy_id,
      line_quality_name = EXCLUDED.line_quality_name,
      line_description = EXCLUDED.line_description,
      business_legacy_id = EXCLUDED.business_legacy_id,
      related_business_legacy_id = EXCLUDED.related_business_legacy_id,
      related_quality_type = EXCLUDED.related_quality_type,
      handler_name = EXCLUDED.handler_name,
      creator_legacy_user_id = EXCLUDED.creator_legacy_user_id,
      creator_name = EXCLUDED.creator_name,
      created_time = EXCLUDED.created_time,
      modifier_legacy_user_id = EXCLUDED.modifier_legacy_user_id,
      modifier_name = EXCLUDED.modifier_name,
      modified_time = EXCLUDED.modified_time,
      attachment_ref = EXCLUDED.attachment_ref,
      line_attachment_ref = EXCLUDED.line_attachment_ref,
      attachment_name = EXCLUDED.attachment_name,
      attachment_path = EXCLUDED.attachment_path,
      active = EXCLUDED.active,
      write_uid = EXCLUDED.write_uid,
      write_date = NOW()
    """,
    [uid, uid],
)

env.cr.commit()  # noqa: F821

env.cr.execute("SELECT COUNT(*) FROM sc_legacy_construction_diary_line")  # noqa: F821
after = env.cr.fetchone()[0]  # noqa: F821
env.cr.execute("SELECT COUNT(*) FROM sc_legacy_construction_diary_line WHERE active")  # noqa: F821
active_rows = env.cr.fetchone()[0]  # noqa: F821
env.cr.execute("SELECT COUNT(*) FROM sc_legacy_construction_diary_line WHERE project_id IS NOT NULL")  # noqa: F821
project_linked = env.cr.fetchone()[0]  # noqa: F821
env.cr.execute("SELECT COUNT(*) FROM sc_legacy_construction_diary_line WHERE attachment_path IS NOT NULL")  # noqa: F821
attachment_path_rows = env.cr.fetchone()[0]  # noqa: F821

payload = {
    "status": "PASS",
    "mode": "fresh_db_legacy_construction_diary_line_replay_write",
    "database": env.cr.dbname,  # noqa: F821
    "input_rows": manifest.get("total_rows"),
    "before": before,
    "after": after,
    "delta": after - before,
    "active_rows": active_rows,
    "project_linked": project_linked,
    "attachment_path_rows": attachment_path_rows,
    "db_writes": max(after - before, 0),
    "decision": "legacy_construction_diary_line_replay_complete",
}
write_json(OUTPUT_JSON, payload)
print("FRESH_DB_LEGACY_CONSTRUCTION_DIARY_LINE_REPLAY_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
