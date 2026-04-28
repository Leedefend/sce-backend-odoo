#!/usr/bin/env python3
"""Replay legacy user-project scope facts into a neutral carrier model."""

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
        if (candidate / "artifacts/migration/fresh_db_legacy_user_project_scope_replay_adapter_result_v1.json").exists():
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
INPUT_MANIFEST = REPO_ROOT / "artifacts/migration/fresh_db_legacy_user_project_scope_replay_adapter_result_v1.json"
INPUT_CSV = REPO_ROOT / "artifacts/migration/fresh_db_legacy_user_project_scope_replay_payload_v1.csv"
OUTPUT_JSON = ARTIFACT_ROOT / "fresh_db_legacy_user_project_scope_replay_write_result_v1.json"

COLUMNS = [
    "legacy_scope_key",
    "source_table",
    "legacy_assignment_id",
    "relation_name",
    "legacy_user_id",
    "company_legacy_id",
    "project_legacy_id",
    "scope_state",
    "created_by_legacy_user_id",
    "created_by_name",
    "created_time",
    "removed_by_legacy_user_id",
    "removed_by_name",
    "removed_time",
    "note",
    "active",
]

ensure_allowed_db()
manifest = json.loads(INPUT_MANIFEST.read_text(encoding="utf-8"))
uid = env.uid  # noqa: F821

bulk_load(INPUT_CSV, "tmp_legacy_user_project_scope", COLUMNS)

env.cr.execute("SELECT COUNT(*) FROM sc_legacy_user_project_scope")  # noqa: F821
before = env.cr.fetchone()[0]  # noqa: F821

env.cr.execute(  # noqa: F821
    """
    INSERT INTO sc_legacy_user_project_scope (
      legacy_scope_key, source_table, legacy_assignment_id, relation_name,
      legacy_user_id, user_id, company_legacy_id, project_legacy_id, project_id,
      scope_state, created_by_legacy_user_id, created_by_name, created_time,
      removed_by_legacy_user_id, removed_by_name, removed_time, note, active,
      create_uid, create_date, write_uid, write_date
    )
    SELECT
      t.legacy_scope_key,
      t.source_table,
      t.legacy_assignment_id,
      NULLIF(t.relation_name, ''),
      t.legacy_user_id,
      profile.user_id,
      NULLIF(t.company_legacy_id, ''),
      NULLIF(t.project_legacy_id, ''),
      project.id,
      t.scope_state,
      NULLIF(t.created_by_legacy_user_id, ''),
      NULLIF(t.created_by_name, ''),
      NULLIF(t.created_time, '')::timestamp,
      NULLIF(t.removed_by_legacy_user_id, ''),
      NULLIF(t.removed_by_name, ''),
      NULLIF(t.removed_time, '')::timestamp,
      NULLIF(t.note, ''),
      COALESCE(NULLIF(t.active, ''), '1') = '1',
      %s, NOW(), %s, NOW()
    FROM tmp_legacy_user_project_scope t
    LEFT JOIN sc_legacy_user_profile profile ON profile.legacy_user_id = t.legacy_user_id
    LEFT JOIN project_project project ON project.legacy_project_id = NULLIF(t.project_legacy_id, '')
    ON CONFLICT (legacy_scope_key) DO UPDATE SET
      source_table = EXCLUDED.source_table,
      legacy_assignment_id = EXCLUDED.legacy_assignment_id,
      relation_name = EXCLUDED.relation_name,
      legacy_user_id = EXCLUDED.legacy_user_id,
      user_id = EXCLUDED.user_id,
      company_legacy_id = EXCLUDED.company_legacy_id,
      project_legacy_id = EXCLUDED.project_legacy_id,
      project_id = EXCLUDED.project_id,
      scope_state = EXCLUDED.scope_state,
      created_by_legacy_user_id = EXCLUDED.created_by_legacy_user_id,
      created_by_name = EXCLUDED.created_by_name,
      created_time = EXCLUDED.created_time,
      removed_by_legacy_user_id = EXCLUDED.removed_by_legacy_user_id,
      removed_by_name = EXCLUDED.removed_by_name,
      removed_time = EXCLUDED.removed_time,
      note = EXCLUDED.note,
      active = EXCLUDED.active,
      write_uid = EXCLUDED.write_uid,
      write_date = NOW()
    """,
    [uid, uid],
)

env.cr.commit()  # noqa: F821

env.cr.execute("SELECT COUNT(*) FROM sc_legacy_user_project_scope")  # noqa: F821
after = env.cr.fetchone()[0]  # noqa: F821
env.cr.execute("SELECT COUNT(*) FROM sc_legacy_user_project_scope WHERE user_id IS NOT NULL")  # noqa: F821
user_linked = env.cr.fetchone()[0]  # noqa: F821
env.cr.execute("SELECT COUNT(*) FROM sc_legacy_user_project_scope WHERE project_id IS NOT NULL")  # noqa: F821
project_linked = env.cr.fetchone()[0]  # noqa: F821
env.cr.execute("SELECT COUNT(*) FROM sc_legacy_user_project_scope WHERE scope_state = 'current'")  # noqa: F821
current_rows = env.cr.fetchone()[0]  # noqa: F821
env.cr.execute("SELECT COUNT(*) FROM sc_legacy_user_project_scope WHERE scope_state = 'removed'")  # noqa: F821
removed_rows = env.cr.fetchone()[0]  # noqa: F821

payload = {
    "status": "PASS",
    "mode": "fresh_db_legacy_user_project_scope_replay_write",
    "database": env.cr.dbname,  # noqa: F821
    "input_rows": manifest.get("total_rows"),
    "before": before,
    "after": after,
    "delta": after - before,
    "current_rows": current_rows,
    "removed_rows": removed_rows,
    "user_linked": user_linked,
    "project_linked": project_linked,
    "db_writes": max(after - before, 0),
    "decision": "legacy_user_project_scope_replay_complete",
}
write_json(OUTPUT_JSON, payload)
print("FRESH_DB_LEGACY_USER_PROJECT_SCOPE_REPLAY_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
