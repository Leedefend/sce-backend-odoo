#!/usr/bin/env python3
"""Replay legacy task/todo evidence facts into a neutral carrier model."""

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
        if (candidate / "artifacts/migration/fresh_db_legacy_task_evidence_replay_adapter_result_v1.json").exists():
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
INPUT_MANIFEST = REPO_ROOT / "artifacts/migration/fresh_db_legacy_task_evidence_replay_adapter_result_v1.json"
INPUT_CSV = REPO_ROOT / "artifacts/migration/fresh_db_legacy_task_evidence_replay_payload_v1.csv"
OUTPUT_JSON = ARTIFACT_ROOT / "fresh_db_legacy_task_evidence_replay_write_result_v1.json"

COLUMNS = [
    "legacy_task_id",
    "legacy_pid",
    "project_legacy_id",
    "project_name",
    "bill_no",
    "subject",
    "description",
    "start_time",
    "due_time",
    "finish_time",
    "done_flag",
    "executor_legacy_ids",
    "primary_executor_legacy_id",
    "participant_legacy_ids",
    "pc_url",
    "app_url",
    "source",
    "source_id",
    "source_icbd",
    "created_time",
    "modified_time",
    "creator_legacy_user_id",
    "modifier_legacy_user_id",
    "priority",
    "finish_remark",
    "finish_attachment_ref",
    "task_type",
    "creator_name",
    "modifier_name",
    "finish_name",
    "read_time",
    "read_state",
    "business_id",
    "business_name",
    "param_text",
    "active",
]

ensure_allowed_db()
manifest = json.loads(INPUT_MANIFEST.read_text(encoding="utf-8"))
uid = env.uid  # noqa: F821

bulk_load(INPUT_CSV, "tmp_legacy_task_evidence", COLUMNS)

env.cr.execute("SELECT COUNT(*) FROM sc_legacy_task_evidence")  # noqa: F821
before = env.cr.fetchone()[0]  # noqa: F821

env.cr.execute(  # noqa: F821
    """
    INSERT INTO sc_legacy_task_evidence (
      legacy_task_id, legacy_pid, project_legacy_id, project_name, project_id,
      bill_no, subject, description, start_time, due_time, finish_time,
      done_flag, read_state, read_time, executor_legacy_ids,
      primary_executor_legacy_id, primary_executor_user_id, participant_legacy_ids,
      creator_legacy_user_id, creator_user_id, creator_name,
      modifier_legacy_user_id, modifier_name, modified_time, finish_name,
      finish_remark, finish_attachment_ref, pc_url, app_url, source, source_id,
      source_icbd, business_id, business_name, priority, task_type, param_text,
      source_table, active, create_uid, create_date, write_uid, write_date
    )
    SELECT
      t.legacy_task_id,
      NULLIF(t.legacy_pid, ''),
      NULLIF(t.project_legacy_id, ''),
      NULLIF(t.project_name, ''),
      project.id,
      NULLIF(t.bill_no, ''),
      COALESCE(NULLIF(t.subject, ''), t.legacy_task_id),
      NULLIF(t.description, ''),
      NULLIF(t.start_time, '')::timestamp,
      NULLIF(t.due_time, '')::timestamp,
      NULLIF(t.finish_time, '')::timestamp,
      NULLIF(t.done_flag, ''),
      NULLIF(t.read_state, ''),
      NULLIF(t.read_time, '')::timestamp,
      NULLIF(t.executor_legacy_ids, ''),
      NULLIF(t.primary_executor_legacy_id, ''),
      executor_profile.user_id,
      NULLIF(t.participant_legacy_ids, ''),
      NULLIF(t.creator_legacy_user_id, ''),
      creator_profile.user_id,
      NULLIF(t.creator_name, ''),
      NULLIF(t.modifier_legacy_user_id, ''),
      NULLIF(t.modifier_name, ''),
      NULLIF(t.modified_time, '')::timestamp,
      NULLIF(t.finish_name, ''),
      NULLIF(t.finish_remark, ''),
      NULLIF(t.finish_attachment_ref, ''),
      NULLIF(t.pc_url, ''),
      NULLIF(t.app_url, ''),
      NULLIF(t.source, ''),
      NULLIF(t.source_id, ''),
      NULLIF(t.source_icbd, ''),
      NULLIF(t.business_id, ''),
      NULLIF(t.business_name, ''),
      NULLIF(t.priority, ''),
      NULLIF(t.task_type, ''),
      NULLIF(t.param_text, ''),
      'T_BASE_TASKDONE',
      COALESCE(NULLIF(t.active, ''), '1') = '1',
      %s, NOW(), %s, NOW()
    FROM tmp_legacy_task_evidence t
    LEFT JOIN project_project project ON project.legacy_project_id = NULLIF(t.project_legacy_id, '')
    LEFT JOIN sc_legacy_user_profile executor_profile ON executor_profile.legacy_user_id = NULLIF(t.primary_executor_legacy_id, '')
    LEFT JOIN sc_legacy_user_profile creator_profile ON creator_profile.legacy_user_id = NULLIF(t.creator_legacy_user_id, '')
    ON CONFLICT (legacy_task_id) DO UPDATE SET
      legacy_pid = EXCLUDED.legacy_pid,
      project_legacy_id = EXCLUDED.project_legacy_id,
      project_name = EXCLUDED.project_name,
      project_id = EXCLUDED.project_id,
      bill_no = EXCLUDED.bill_no,
      subject = EXCLUDED.subject,
      description = EXCLUDED.description,
      start_time = EXCLUDED.start_time,
      due_time = EXCLUDED.due_time,
      finish_time = EXCLUDED.finish_time,
      done_flag = EXCLUDED.done_flag,
      read_state = EXCLUDED.read_state,
      read_time = EXCLUDED.read_time,
      executor_legacy_ids = EXCLUDED.executor_legacy_ids,
      primary_executor_legacy_id = EXCLUDED.primary_executor_legacy_id,
      primary_executor_user_id = EXCLUDED.primary_executor_user_id,
      participant_legacy_ids = EXCLUDED.participant_legacy_ids,
      creator_legacy_user_id = EXCLUDED.creator_legacy_user_id,
      creator_user_id = EXCLUDED.creator_user_id,
      creator_name = EXCLUDED.creator_name,
      modifier_legacy_user_id = EXCLUDED.modifier_legacy_user_id,
      modifier_name = EXCLUDED.modifier_name,
      modified_time = EXCLUDED.modified_time,
      finish_name = EXCLUDED.finish_name,
      finish_remark = EXCLUDED.finish_remark,
      finish_attachment_ref = EXCLUDED.finish_attachment_ref,
      pc_url = EXCLUDED.pc_url,
      app_url = EXCLUDED.app_url,
      source = EXCLUDED.source,
      source_id = EXCLUDED.source_id,
      source_icbd = EXCLUDED.source_icbd,
      business_id = EXCLUDED.business_id,
      business_name = EXCLUDED.business_name,
      priority = EXCLUDED.priority,
      task_type = EXCLUDED.task_type,
      param_text = EXCLUDED.param_text,
      active = EXCLUDED.active,
      write_uid = EXCLUDED.write_uid,
      write_date = NOW()
    """,
    [uid, uid],
)

env.cr.commit()  # noqa: F821

env.cr.execute("SELECT COUNT(*) FROM sc_legacy_task_evidence")  # noqa: F821
after = env.cr.fetchone()[0]  # noqa: F821
env.cr.execute("SELECT COUNT(*) FROM sc_legacy_task_evidence WHERE active")  # noqa: F821
active_rows = env.cr.fetchone()[0]  # noqa: F821
env.cr.execute("SELECT COUNT(*) FROM sc_legacy_task_evidence WHERE done_flag = '1'")  # noqa: F821
done_rows = env.cr.fetchone()[0]  # noqa: F821
env.cr.execute("SELECT COUNT(*) FROM sc_legacy_task_evidence WHERE read_state = '1'")  # noqa: F821
read_rows = env.cr.fetchone()[0]  # noqa: F821
env.cr.execute("SELECT COUNT(*) FROM sc_legacy_task_evidence WHERE primary_executor_user_id IS NOT NULL")  # noqa: F821
executor_linked = env.cr.fetchone()[0]  # noqa: F821
env.cr.execute("SELECT COUNT(*) FROM sc_legacy_task_evidence WHERE creator_user_id IS NOT NULL")  # noqa: F821
creator_linked = env.cr.fetchone()[0]  # noqa: F821
env.cr.execute("SELECT COUNT(*) FROM sc_legacy_task_evidence WHERE project_id IS NOT NULL")  # noqa: F821
project_linked = env.cr.fetchone()[0]  # noqa: F821

payload = {
    "status": "PASS",
    "mode": "fresh_db_legacy_task_evidence_replay_write",
    "database": env.cr.dbname,  # noqa: F821
    "input_rows": manifest.get("total_rows"),
    "before": before,
    "after": after,
    "delta": after - before,
    "active_rows": active_rows,
    "done_rows": done_rows,
    "read_rows": read_rows,
    "executor_linked": executor_linked,
    "creator_linked": creator_linked,
    "project_linked": project_linked,
    "db_writes": max(after - before, 0),
    "decision": "legacy_task_evidence_replay_complete",
}
write_json(OUTPUT_JSON, payload)
print("FRESH_DB_LEGACY_TASK_EVIDENCE_REPLAY_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
