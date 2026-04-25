#!/usr/bin/env python3
"""Bulk replay legacy file index facts into a neutral carrier model."""

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
        if (candidate / "artifacts/migration/fresh_db_legacy_file_index_replay_adapter_result_v1.json").exists():
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
INPUT_MANIFEST = REPO_ROOT / "artifacts/migration/fresh_db_legacy_file_index_replay_adapter_result_v1.json"
INPUT_CSV = REPO_ROOT / "artifacts/migration/fresh_db_legacy_file_index_replay_payload_v1.csv"
OUTPUT_JSON = ARTIFACT_ROOT / "fresh_db_legacy_file_index_replay_write_result_v1.json"

COLUMNS = [
    "legacy_file_key",
    "source_table",
    "legacy_file_id",
    "legacy_pid",
    "bill_id",
    "bill_type",
    "business_id",
    "file_system_data_id",
    "file_name",
    "file_path",
    "preview_path",
    "file_md5",
    "file_size",
    "extension",
    "uploader_legacy_user_id",
    "uploader_name",
    "upload_time",
    "deleter_legacy_user_id",
    "deleter_name",
    "delete_time",
    "encrypted_flag",
    "temporary_flag",
    "note",
    "active",
]

ensure_allowed_db()
manifest = json.loads(INPUT_MANIFEST.read_text(encoding="utf-8"))
uid = env.uid  # noqa: F821

bulk_load(INPUT_CSV, "tmp_legacy_file_index", COLUMNS)

env.cr.execute("SELECT COUNT(*) FROM sc_legacy_file_index")  # noqa: F821
before = env.cr.fetchone()[0]  # noqa: F821

env.cr.execute(  # noqa: F821
    """
    INSERT INTO sc_legacy_file_index (
      legacy_file_key, source_table, legacy_file_id, legacy_pid, bill_id,
      bill_type, business_id, file_system_data_id, file_name, file_path,
      preview_path, file_md5, file_size, extension, uploader_legacy_user_id,
      uploader_name, upload_time, deleter_legacy_user_id, deleter_name,
      delete_time, encrypted_flag, temporary_flag, note, active,
      create_uid, create_date, write_uid, write_date
    )
    SELECT
      t.legacy_file_key,
      t.source_table,
      t.legacy_file_id,
      NULLIF(t.legacy_pid, ''),
      NULLIF(t.bill_id, ''),
      NULLIF(t.bill_type, ''),
      NULLIF(t.business_id, ''),
      NULLIF(t.file_system_data_id, ''),
      COALESCE(NULLIF(t.file_name, ''), t.legacy_file_id),
      COALESCE(NULLIF(t.file_path, ''), t.legacy_file_id),
      NULLIF(t.preview_path, ''),
      NULLIF(t.file_md5, ''),
      COALESCE(NULLIF(t.file_size, '')::integer, 0),
      NULLIF(t.extension, ''),
      NULLIF(t.uploader_legacy_user_id, ''),
      NULLIF(t.uploader_name, ''),
      NULLIF(t.upload_time, '')::timestamp,
      NULLIF(t.deleter_legacy_user_id, ''),
      NULLIF(t.deleter_name, ''),
      NULLIF(t.delete_time, '')::timestamp,
      NULLIF(t.encrypted_flag, ''),
      NULLIF(t.temporary_flag, ''),
      NULLIF(t.note, ''),
      COALESCE(NULLIF(t.active, ''), '1') = '1',
      %s, NOW(), %s, NOW()
    FROM tmp_legacy_file_index t
    ON CONFLICT (legacy_file_key) DO UPDATE SET
      source_table = EXCLUDED.source_table,
      legacy_file_id = EXCLUDED.legacy_file_id,
      legacy_pid = EXCLUDED.legacy_pid,
      bill_id = EXCLUDED.bill_id,
      bill_type = EXCLUDED.bill_type,
      business_id = EXCLUDED.business_id,
      file_system_data_id = EXCLUDED.file_system_data_id,
      file_name = EXCLUDED.file_name,
      file_path = EXCLUDED.file_path,
      preview_path = EXCLUDED.preview_path,
      file_md5 = EXCLUDED.file_md5,
      file_size = EXCLUDED.file_size,
      extension = EXCLUDED.extension,
      uploader_legacy_user_id = EXCLUDED.uploader_legacy_user_id,
      uploader_name = EXCLUDED.uploader_name,
      upload_time = EXCLUDED.upload_time,
      deleter_legacy_user_id = EXCLUDED.deleter_legacy_user_id,
      deleter_name = EXCLUDED.deleter_name,
      delete_time = EXCLUDED.delete_time,
      encrypted_flag = EXCLUDED.encrypted_flag,
      temporary_flag = EXCLUDED.temporary_flag,
      note = EXCLUDED.note,
      active = EXCLUDED.active,
      write_uid = EXCLUDED.write_uid,
      write_date = NOW()
    """,
    [uid, uid],
)

env.cr.commit()  # noqa: F821

env.cr.execute("SELECT COUNT(*) FROM sc_legacy_file_index")  # noqa: F821
after = env.cr.fetchone()[0]  # noqa: F821
env.cr.execute("SELECT COUNT(*) FROM sc_legacy_file_index WHERE active")  # noqa: F821
active_rows = env.cr.fetchone()[0]  # noqa: F821
env.cr.execute("SELECT COUNT(*) FROM sc_legacy_file_index WHERE file_path IS NOT NULL AND file_path <> ''")  # noqa: F821
path_rows = env.cr.fetchone()[0]  # noqa: F821
env.cr.execute("SELECT COALESCE(SUM(file_size), 0) FROM sc_legacy_file_index")  # noqa: F821
total_size = int(env.cr.fetchone()[0] or 0)  # noqa: F821

payload = {
    "status": "PASS",
    "mode": "fresh_db_legacy_file_index_replay_write",
    "database": env.cr.dbname,  # noqa: F821
    "input_rows": manifest.get("total_rows"),
    "before": before,
    "after": after,
    "delta": after - before,
    "active_rows": active_rows,
    "path_rows": path_rows,
    "total_size": total_size,
    "db_writes": max(after - before, 0),
    "decision": "legacy_file_index_replay_complete",
}
write_json(OUTPUT_JSON, payload)
print("FRESH_DB_LEGACY_FILE_INDEX_REPLAY_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
