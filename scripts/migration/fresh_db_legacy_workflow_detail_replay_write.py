#!/usr/bin/env python3
"""Replay legacy workflow detail facts into Odoo."""

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
        if (candidate / "artifacts/migration/fresh_db_legacy_workflow_detail_replay_payload_v1.csv").exists():
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
INPUT_CSV = REPO_ROOT / "artifacts/migration/fresh_db_legacy_workflow_detail_replay_payload_v1.csv"
INPUT_JSON = REPO_ROOT / "artifacts/migration/fresh_db_legacy_workflow_detail_replay_adapter_result_v1.json"
OUTPUT_JSON = ARTIFACT_ROOT / "fresh_db_legacy_workflow_detail_replay_write_result_v1.json"

COLUMNS = [
    "source_table",
    "legacy_record_id",
    "legacy_parent_id",
    "legacy_pid",
    "fact_type",
    "source_dataset",
    "document_no",
    "document_title",
    "business_table",
    "business_id",
    "project_legacy_id",
    "project_name",
    "actor_legacy_user_id",
    "actor_name",
    "target_legacy_user_id",
    "target_name",
    "event_time",
    "status_code",
    "step_legacy_id",
    "step_name",
    "template_legacy_id",
    "detail_status_legacy_id",
    "detail_step_legacy_id",
    "message",
    "note",
    "attachment_ref",
    "pc_url",
    "mobile_url",
    "active",
]

ensure_allowed_db()
manifest = json.loads(INPUT_JSON.read_text(encoding="utf-8"))
uid = env.uid  # noqa: F821

bulk_load(INPUT_CSV, "tmp_legacy_workflow_detail", COLUMNS)

env.cr.execute("SELECT COUNT(*) FROM sc_legacy_workflow_detail_fact")  # noqa: F821
before = env.cr.fetchone()[0]  # noqa: F821

env.cr.execute(  # noqa: F821
    """
    INSERT INTO sc_legacy_workflow_detail_fact (
      source_table, legacy_record_id, legacy_parent_id, legacy_pid,
      fact_type, source_dataset, document_no, document_title,
      business_table, business_id, project_legacy_id, project_name,
      project_id, actor_legacy_user_id, actor_name, target_legacy_user_id,
      target_name, event_time, status_code, step_legacy_id, step_name,
      template_legacy_id, detail_status_legacy_id, detail_step_legacy_id,
      message, note, attachment_ref, pc_url, mobile_url, active,
      create_uid, create_date, write_uid, write_date
    )
    SELECT
      t.source_table,
      t.legacy_record_id,
      NULLIF(t.legacy_parent_id, ''),
      NULLIF(t.legacy_pid, ''),
      NULLIF(t.fact_type, ''),
      NULLIF(t.source_dataset, ''),
      NULLIF(t.document_no, ''),
      NULLIF(t.document_title, ''),
      NULLIF(t.business_table, ''),
      NULLIF(t.business_id, ''),
      NULLIF(t.project_legacy_id, ''),
      NULLIF(t.project_name, ''),
      project.id,
      NULLIF(t.actor_legacy_user_id, ''),
      NULLIF(t.actor_name, ''),
      NULLIF(t.target_legacy_user_id, ''),
      NULLIF(t.target_name, ''),
      NULLIF(t.event_time, '')::timestamp,
      NULLIF(t.status_code, ''),
      NULLIF(t.step_legacy_id, ''),
      NULLIF(t.step_name, ''),
      NULLIF(t.template_legacy_id, ''),
      NULLIF(t.detail_status_legacy_id, ''),
      NULLIF(t.detail_step_legacy_id, ''),
      NULLIF(t.message, ''),
      NULLIF(t.note, ''),
      NULLIF(t.attachment_ref, ''),
      NULLIF(t.pc_url, ''),
      NULLIF(t.mobile_url, ''),
      COALESCE(NULLIF(t.active, ''), '1') = '1',
      %s, NOW(), %s, NOW()
    FROM tmp_legacy_workflow_detail t
    LEFT JOIN (
      SELECT DISTINCT ON (legacy_project_id) legacy_project_id, id
      FROM project_project
      WHERE legacy_project_id IS NOT NULL
      ORDER BY legacy_project_id, id
    ) project ON project.legacy_project_id = NULLIF(t.project_legacy_id, '')
    ON CONFLICT (source_table, legacy_record_id) DO UPDATE SET
      legacy_parent_id = EXCLUDED.legacy_parent_id,
      legacy_pid = EXCLUDED.legacy_pid,
      fact_type = EXCLUDED.fact_type,
      source_dataset = EXCLUDED.source_dataset,
      document_no = EXCLUDED.document_no,
      document_title = EXCLUDED.document_title,
      business_table = EXCLUDED.business_table,
      business_id = EXCLUDED.business_id,
      project_legacy_id = EXCLUDED.project_legacy_id,
      project_name = EXCLUDED.project_name,
      project_id = EXCLUDED.project_id,
      actor_legacy_user_id = EXCLUDED.actor_legacy_user_id,
      actor_name = EXCLUDED.actor_name,
      target_legacy_user_id = EXCLUDED.target_legacy_user_id,
      target_name = EXCLUDED.target_name,
      event_time = EXCLUDED.event_time,
      status_code = EXCLUDED.status_code,
      step_legacy_id = EXCLUDED.step_legacy_id,
      step_name = EXCLUDED.step_name,
      template_legacy_id = EXCLUDED.template_legacy_id,
      detail_status_legacy_id = EXCLUDED.detail_status_legacy_id,
      detail_step_legacy_id = EXCLUDED.detail_step_legacy_id,
      message = EXCLUDED.message,
      note = EXCLUDED.note,
      attachment_ref = EXCLUDED.attachment_ref,
      pc_url = EXCLUDED.pc_url,
      mobile_url = EXCLUDED.mobile_url,
      active = EXCLUDED.active,
      write_uid = EXCLUDED.write_uid,
      write_date = NOW()
    """,
    [uid, uid],
)

env.cr.commit()  # noqa: F821

env.cr.execute("SELECT COUNT(*) FROM sc_legacy_workflow_detail_fact")  # noqa: F821
after = env.cr.fetchone()[0]  # noqa: F821
env.cr.execute("SELECT COUNT(*) FROM sc_legacy_workflow_detail_fact WHERE active")  # noqa: F821
active_rows = env.cr.fetchone()[0]  # noqa: F821
env.cr.execute("SELECT COUNT(*) FROM sc_legacy_workflow_detail_fact WHERE project_id IS NOT NULL")  # noqa: F821
project_linked = env.cr.fetchone()[0]  # noqa: F821
env.cr.execute("SELECT source_table, fact_type, COUNT(*) FROM sc_legacy_workflow_detail_fact GROUP BY source_table, fact_type ORDER BY source_table, fact_type")  # noqa: F821
source_counts = [{"source_table": row[0], "fact_type": row[1], "count": row[2]} for row in env.cr.fetchall()]  # noqa: F821

payload = {
    "status": "PASS",
    "mode": "fresh_db_legacy_workflow_detail_replay_write",
    "database": env.cr.dbname,  # noqa: F821
    "input_rows": manifest.get("total_rows"),
    "before": before,
    "after": after,
    "delta": after - before,
    "active_rows": active_rows,
    "project_linked": project_linked,
    "source_counts": source_counts,
    "db_writes": max(after - before, 0),
    "decision": "legacy_workflow_detail_replay_complete",
}
write_json(OUTPUT_JSON, payload)
print("FRESH_DB_LEGACY_WORKFLOW_DETAIL_REPLAY_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
