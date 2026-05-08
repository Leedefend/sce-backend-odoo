#!/usr/bin/env python3
"""Replay remaining legacy business facts into the residual carrier model."""

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
        if (candidate / "artifacts/migration/fresh_db_legacy_business_fact_residual_replay_adapter_result_v1.json").exists():
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
INPUT_MANIFEST = REPO_ROOT / "artifacts/migration/fresh_db_legacy_business_fact_residual_replay_adapter_result_v1.json"
INPUT_CSV = REPO_ROOT / "artifacts/migration/fresh_db_legacy_business_fact_residual_replay_payload_v1.csv"
OUTPUT_JSON = ARTIFACT_ROOT / "fresh_db_legacy_business_fact_residual_replay_write_result_v1.json"

COLUMNS = [
    "source_label",
    "source_container",
    "source_database",
    "source_table",
    "source_dataset",
    "legacy_record_id",
    "legacy_parent_id",
    "legacy_pid",
    "family",
    "classification",
    "business_signal_score",
    "document_no",
    "document_date",
    "project_legacy_id",
    "project_name",
    "partner_legacy_id",
    "partner_name",
    "amount_total",
    "raw_payload",
    "active",
]

ensure_allowed_db()
manifest = json.loads(INPUT_MANIFEST.read_text(encoding="utf-8"))
uid = env.uid  # noqa: F821
bulk_load(INPUT_CSV, "tmp_legacy_business_fact_residual", COLUMNS)

env.cr.execute("SELECT COUNT(*) FROM sc_legacy_business_fact_residual")  # noqa: F821
before = env.cr.fetchone()[0]  # noqa: F821
env.cr.execute(  # noqa: F821
    """
    DELETE FROM sc_legacy_business_fact_residual
    WHERE source_database IN (
      SELECT DISTINCT source_database FROM tmp_legacy_business_fact_residual
    )
    """
)
deleted_before_reload = env.cr.rowcount  # noqa: F821

env.cr.execute(  # noqa: F821
    """
    INSERT INTO sc_legacy_business_fact_residual (
      source_label, source_container, source_database, source_table, source_dataset,
      legacy_record_id, legacy_parent_id, legacy_pid, family, classification,
      business_signal_score, document_no, document_date, project_legacy_id, project_name,
      partner_legacy_id, partner_name, amount_total, raw_payload, active,
      create_uid, create_date, write_uid, write_date
    )
    SELECT
      t.source_label,
      NULLIF(t.source_container, ''),
      t.source_database,
      t.source_table,
      NULLIF(t.source_dataset, ''),
      t.legacy_record_id,
      NULLIF(t.legacy_parent_id, ''),
      NULLIF(t.legacy_pid, ''),
      NULLIF(t.family, ''),
      NULLIF(t.classification, ''),
      COALESCE(NULLIF(t.business_signal_score, '')::integer, 0),
      NULLIF(t.document_no, ''),
      NULLIF(t.document_date, '')::timestamp,
      NULLIF(t.project_legacy_id, ''),
      NULLIF(t.project_name, ''),
      NULLIF(t.partner_legacy_id, ''),
      NULLIF(t.partner_name, ''),
      COALESCE(NULLIF(t.amount_total, '')::numeric, 0),
      NULLIF(t.raw_payload, ''),
      COALESCE(NULLIF(t.active, ''), '1') = '1',
      %s, NOW(), %s, NOW()
    FROM tmp_legacy_business_fact_residual t
    ON CONFLICT (source_database, source_table, legacy_record_id) DO UPDATE SET
      source_label = EXCLUDED.source_label,
      source_container = EXCLUDED.source_container,
      source_dataset = EXCLUDED.source_dataset,
      legacy_parent_id = EXCLUDED.legacy_parent_id,
      legacy_pid = EXCLUDED.legacy_pid,
      family = EXCLUDED.family,
      classification = EXCLUDED.classification,
      business_signal_score = EXCLUDED.business_signal_score,
      document_no = EXCLUDED.document_no,
      document_date = EXCLUDED.document_date,
      project_legacy_id = EXCLUDED.project_legacy_id,
      project_name = EXCLUDED.project_name,
      partner_legacy_id = EXCLUDED.partner_legacy_id,
      partner_name = EXCLUDED.partner_name,
      amount_total = EXCLUDED.amount_total,
      raw_payload = EXCLUDED.raw_payload,
      active = EXCLUDED.active,
      write_uid = EXCLUDED.write_uid,
      write_date = NOW()
    """,
    [uid, uid],
)
env.cr.commit()  # noqa: F821

env.cr.execute("SELECT COUNT(*) FROM sc_legacy_business_fact_residual")  # noqa: F821
after = env.cr.fetchone()[0]  # noqa: F821
env.cr.execute("SELECT COUNT(*) FROM sc_legacy_business_fact_residual WHERE active")  # noqa: F821
active_rows = env.cr.fetchone()[0]  # noqa: F821
env.cr.execute("SELECT source_database, COUNT(*) FROM sc_legacy_business_fact_residual GROUP BY source_database ORDER BY source_database")  # noqa: F821
source_database_counts = dict(env.cr.fetchall())  # noqa: F821
env.cr.execute("SELECT family, COUNT(*) FROM sc_legacy_business_fact_residual GROUP BY family ORDER BY COUNT(*) DESC, family")  # noqa: F821
family_counts = dict(env.cr.fetchall())  # noqa: F821

payload = {
    "status": "PASS",
    "mode": "fresh_db_legacy_business_fact_residual_replay_write",
    "database": env.cr.dbname,  # noqa: F821
    "input_rows": manifest.get("total_rows"),
    "before": before,
    "deleted_before_reload": deleted_before_reload,
    "after": after,
    "delta": after - before,
    "active_rows": active_rows,
    "source_database_counts": source_database_counts,
    "family_counts": family_counts,
    "db_writes": after,
    "decision": "full_candidate_legacy_business_fact_residual_replay_complete",
}
write_json(OUTPUT_JSON, payload)
print("FRESH_DB_LEGACY_BUSINESS_FACT_RESIDUAL_REPLAY_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
