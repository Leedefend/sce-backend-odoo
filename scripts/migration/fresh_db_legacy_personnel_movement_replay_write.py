#!/usr/bin/env python3
"""Replay privacy-restricted legacy personnel movement facts."""

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
        if (candidate / "artifacts/migration/fresh_db_legacy_personnel_movement_replay_adapter_result_v1.json").exists():
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
        env.cr.copy_expert(f"COPY {temp_table} ({', '.join(columns)}) FROM STDIN WITH CSV HEADER", handle)  # noqa: F821


REPO_ROOT = repo_root()
ARTIFACT_ROOT = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", str(REPO_ROOT / "artifacts/migration")))
INPUT_MANIFEST = REPO_ROOT / "artifacts/migration/fresh_db_legacy_personnel_movement_replay_adapter_result_v1.json"
INPUT_CSV = REPO_ROOT / "artifacts/migration/fresh_db_legacy_personnel_movement_replay_payload_v1.csv"
OUTPUT_JSON = ARTIFACT_ROOT / "fresh_db_legacy_personnel_movement_replay_write_result_v1.json"

COLUMNS = [
    "legacy_movement_id", "legacy_pid", "document_no", "person_legacy_id",
    "person_name", "movement_type", "movement_code", "department_legacy_id",
    "position_legacy_id", "entry_date", "leave_date", "leave_reason",
    "salary_month", "notify_user_legacy_ids", "notify_user_names",
    "creator_legacy_user_id", "creator_name", "created_time", "attachment_ref",
    "attachment_name", "attachment_path", "note", "active",
]

ensure_allowed_db()
manifest = json.loads(INPUT_MANIFEST.read_text(encoding="utf-8"))
uid = env.uid  # noqa: F821
bulk_load(INPUT_CSV, "tmp_legacy_personnel_movement", COLUMNS)

env.cr.execute("SELECT COUNT(*) FROM sc_legacy_personnel_movement")  # noqa: F821
before = env.cr.fetchone()[0]  # noqa: F821

env.cr.execute(  # noqa: F821
    """
    INSERT INTO sc_legacy_personnel_movement (
      legacy_movement_id, legacy_pid, document_no, person_legacy_id, person_name,
      movement_type, movement_code, department_legacy_id, department_name,
      position_legacy_id, entry_date, leave_date, leave_reason, salary_month,
      notify_user_legacy_ids, notify_user_names, creator_legacy_user_id,
      creator_user_id, creator_name, created_time, attachment_ref,
      attachment_name, attachment_path, note, source_table, active,
      create_uid, create_date, write_uid, write_date
    )
    SELECT
      t.legacy_movement_id,
      NULLIF(t.legacy_pid, ''),
      NULLIF(t.document_no, ''),
      NULLIF(t.person_legacy_id, ''),
      NULLIF(t.person_name, ''),
      NULLIF(t.movement_type, ''),
      NULLIF(t.movement_code, ''),
      NULLIF(t.department_legacy_id, ''),
      dept.name,
      NULLIF(t.position_legacy_id, ''),
      NULLIF(t.entry_date, '')::timestamp,
      NULLIF(t.leave_date, '')::timestamp,
      NULLIF(t.leave_reason, ''),
      NULLIF(t.salary_month, ''),
      NULLIF(t.notify_user_legacy_ids, ''),
      NULLIF(t.notify_user_names, ''),
      NULLIF(t.creator_legacy_user_id, ''),
      profile.user_id,
      NULLIF(t.creator_name, ''),
      NULLIF(t.created_time, '')::timestamp,
      NULLIF(t.attachment_ref, ''),
      NULLIF(t.attachment_name, ''),
      NULLIF(t.attachment_path, ''),
      NULLIF(t.note, ''),
      'PM_RYYDGL',
      COALESCE(NULLIF(t.active, ''), '1') = '1',
      %s, NOW(), %s, NOW()
    FROM tmp_legacy_personnel_movement t
    LEFT JOIN sc_legacy_department dept ON dept.legacy_department_id = NULLIF(t.department_legacy_id, '')
    LEFT JOIN sc_legacy_user_profile profile ON profile.legacy_user_id = NULLIF(t.creator_legacy_user_id, '')
    ON CONFLICT (legacy_movement_id) DO UPDATE SET
      legacy_pid = EXCLUDED.legacy_pid,
      document_no = EXCLUDED.document_no,
      person_legacy_id = EXCLUDED.person_legacy_id,
      person_name = EXCLUDED.person_name,
      movement_type = EXCLUDED.movement_type,
      movement_code = EXCLUDED.movement_code,
      department_legacy_id = EXCLUDED.department_legacy_id,
      department_name = EXCLUDED.department_name,
      position_legacy_id = EXCLUDED.position_legacy_id,
      entry_date = EXCLUDED.entry_date,
      leave_date = EXCLUDED.leave_date,
      leave_reason = EXCLUDED.leave_reason,
      salary_month = EXCLUDED.salary_month,
      notify_user_legacy_ids = EXCLUDED.notify_user_legacy_ids,
      notify_user_names = EXCLUDED.notify_user_names,
      creator_legacy_user_id = EXCLUDED.creator_legacy_user_id,
      creator_user_id = EXCLUDED.creator_user_id,
      creator_name = EXCLUDED.creator_name,
      created_time = EXCLUDED.created_time,
      attachment_ref = EXCLUDED.attachment_ref,
      attachment_name = EXCLUDED.attachment_name,
      attachment_path = EXCLUDED.attachment_path,
      note = EXCLUDED.note,
      active = EXCLUDED.active,
      write_uid = EXCLUDED.write_uid,
      write_date = NOW()
    """,
    [uid, uid],
)
env.cr.commit()  # noqa: F821

env.cr.execute("SELECT COUNT(*) FROM sc_legacy_personnel_movement")  # noqa: F821
after = env.cr.fetchone()[0]  # noqa: F821
env.cr.execute("SELECT COUNT(*) FROM sc_legacy_personnel_movement WHERE active")  # noqa: F821
active_rows = env.cr.fetchone()[0]  # noqa: F821
env.cr.execute("SELECT COUNT(*) FROM sc_legacy_personnel_movement WHERE creator_user_id IS NOT NULL")  # noqa: F821
creator_linked = env.cr.fetchone()[0]  # noqa: F821
env.cr.execute("SELECT COUNT(*) FROM sc_legacy_personnel_movement WHERE department_name IS NOT NULL")  # noqa: F821
department_linked = env.cr.fetchone()[0]  # noqa: F821
env.cr.execute("SELECT COUNT(*) FROM sc_legacy_personnel_movement WHERE leave_date IS NOT NULL")  # noqa: F821
leave_date_rows = env.cr.fetchone()[0]  # noqa: F821

payload = {
    "status": "PASS",
    "mode": "fresh_db_legacy_personnel_movement_replay_write",
    "database": env.cr.dbname,  # noqa: F821
    "input_rows": manifest.get("total_rows"),
    "before": before,
    "after": after,
    "delta": after - before,
    "active_rows": active_rows,
    "creator_linked": creator_linked,
    "department_linked": department_linked,
    "leave_date_rows": leave_date_rows,
    "privacy_boundary": "restricted_config_admin_only",
    "db_writes": max(after - before, 0),
    "decision": "legacy_personnel_movement_replay_complete",
}
write_json(OUTPUT_JSON, payload)
print("FRESH_DB_LEGACY_PERSONNEL_MOVEMENT_REPLAY_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
