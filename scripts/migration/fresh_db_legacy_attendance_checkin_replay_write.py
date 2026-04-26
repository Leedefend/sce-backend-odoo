#!/usr/bin/env python3
"""Replay privacy-restricted legacy attendance check-in facts."""

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
        if (candidate / "artifacts/migration/fresh_db_legacy_attendance_checkin_replay_adapter_result_v1.json").exists():
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
INPUT_MANIFEST = REPO_ROOT / "artifacts/migration/fresh_db_legacy_attendance_checkin_replay_adapter_result_v1.json"
INPUT_CSV = REPO_ROOT / "artifacts/migration/fresh_db_legacy_attendance_checkin_replay_payload_v1.csv"
OUTPUT_JSON = ARTIFACT_ROOT / "fresh_db_legacy_attendance_checkin_replay_write_result_v1.json"

COLUMNS = [
    "legacy_checkin_id", "legacy_pid", "legacy_user_id", "group_name",
    "checkin_type", "exception_type", "checkin_datetime", "checkin_date_text",
    "checkin_time_text", "department_legacy_id", "department_name",
    "project_legacy_id", "project_name", "location_title", "location_detail",
    "wifi_name", "wifi_mac", "latitude", "longitude", "media_refs", "notes",
    "created_time", "modified_time", "active",
]

ensure_allowed_db()
manifest = json.loads(INPUT_MANIFEST.read_text(encoding="utf-8"))
uid = env.uid  # noqa: F821
bulk_load(INPUT_CSV, "tmp_legacy_attendance_checkin", COLUMNS)

env.cr.execute("SELECT COUNT(*) FROM sc_legacy_attendance_checkin")  # noqa: F821
before = env.cr.fetchone()[0]  # noqa: F821

env.cr.execute(  # noqa: F821
    """
    INSERT INTO sc_legacy_attendance_checkin (
      legacy_checkin_id, legacy_pid, legacy_user_id, user_id, group_name,
      checkin_type, exception_type, checkin_datetime, checkin_date_text,
      checkin_time_text, department_legacy_id, department_name, project_legacy_id,
      project_name, project_id, location_title, location_detail, wifi_name,
      wifi_mac, latitude, longitude, media_refs, notes, created_time,
      modified_time, source_table, active, create_uid, create_date, write_uid, write_date
    )
    SELECT
      t.legacy_checkin_id,
      NULLIF(t.legacy_pid, ''),
      NULLIF(t.legacy_user_id, ''),
      profile.user_id,
      NULLIF(t.group_name, ''),
      NULLIF(t.checkin_type, ''),
      NULLIF(t.exception_type, ''),
      NULLIF(t.checkin_datetime, '')::timestamp,
      NULLIF(t.checkin_date_text, ''),
      NULLIF(t.checkin_time_text, ''),
      NULLIF(t.department_legacy_id, ''),
      NULLIF(t.department_name, ''),
      NULLIF(t.project_legacy_id, ''),
      NULLIF(t.project_name, ''),
      project.id,
      NULLIF(t.location_title, ''),
      NULLIF(t.location_detail, ''),
      NULLIF(t.wifi_name, ''),
      NULLIF(t.wifi_mac, ''),
      NULLIF(t.latitude, ''),
      NULLIF(t.longitude, ''),
      NULLIF(t.media_refs, ''),
      NULLIF(t.notes, ''),
      NULLIF(t.created_time, '')::timestamp,
      NULLIF(t.modified_time, '')::timestamp,
      'CheckInData',
      COALESCE(NULLIF(t.active, ''), '1') = '1',
      %s, NOW(), %s, NOW()
    FROM tmp_legacy_attendance_checkin t
    LEFT JOIN sc_legacy_user_profile profile ON profile.legacy_user_id = NULLIF(t.legacy_user_id, '')
    LEFT JOIN project_project project ON project.legacy_project_id = NULLIF(t.project_legacy_id, '')
    ON CONFLICT (legacy_checkin_id) DO UPDATE SET
      legacy_pid = EXCLUDED.legacy_pid,
      legacy_user_id = EXCLUDED.legacy_user_id,
      user_id = EXCLUDED.user_id,
      group_name = EXCLUDED.group_name,
      checkin_type = EXCLUDED.checkin_type,
      exception_type = EXCLUDED.exception_type,
      checkin_datetime = EXCLUDED.checkin_datetime,
      checkin_date_text = EXCLUDED.checkin_date_text,
      checkin_time_text = EXCLUDED.checkin_time_text,
      department_legacy_id = EXCLUDED.department_legacy_id,
      department_name = EXCLUDED.department_name,
      project_legacy_id = EXCLUDED.project_legacy_id,
      project_name = EXCLUDED.project_name,
      project_id = EXCLUDED.project_id,
      location_title = EXCLUDED.location_title,
      location_detail = EXCLUDED.location_detail,
      wifi_name = EXCLUDED.wifi_name,
      wifi_mac = EXCLUDED.wifi_mac,
      latitude = EXCLUDED.latitude,
      longitude = EXCLUDED.longitude,
      media_refs = EXCLUDED.media_refs,
      notes = EXCLUDED.notes,
      created_time = EXCLUDED.created_time,
      modified_time = EXCLUDED.modified_time,
      active = EXCLUDED.active,
      write_uid = EXCLUDED.write_uid,
      write_date = NOW()
    """,
    [uid, uid],
)
env.cr.commit()  # noqa: F821

env.cr.execute("SELECT COUNT(*) FROM sc_legacy_attendance_checkin")  # noqa: F821
after = env.cr.fetchone()[0]  # noqa: F821
env.cr.execute("SELECT COUNT(*) FROM sc_legacy_attendance_checkin WHERE active")  # noqa: F821
active_rows = env.cr.fetchone()[0]  # noqa: F821
env.cr.execute("SELECT COUNT(*) FROM sc_legacy_attendance_checkin WHERE user_id IS NOT NULL")  # noqa: F821
user_linked = env.cr.fetchone()[0]  # noqa: F821
env.cr.execute("SELECT COUNT(*) FROM sc_legacy_attendance_checkin WHERE project_id IS NOT NULL")  # noqa: F821
project_linked = env.cr.fetchone()[0]  # noqa: F821

payload = {
    "status": "PASS",
    "mode": "fresh_db_legacy_attendance_checkin_replay_write",
    "database": env.cr.dbname,  # noqa: F821
    "input_rows": manifest.get("total_rows"),
    "before": before,
    "after": after,
    "delta": after - before,
    "active_rows": active_rows,
    "user_linked": user_linked,
    "project_linked": project_linked,
    "privacy_boundary": "restricted_config_admin_only",
    "db_writes": max(after - before, 0),
    "decision": "legacy_attendance_checkin_replay_complete",
}
write_json(OUTPUT_JSON, payload)
print("FRESH_DB_LEGACY_ATTENDANCE_CHECKIN_REPLAY_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
