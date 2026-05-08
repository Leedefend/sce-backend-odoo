#!/usr/bin/env python3
"""Replay legacy tender registration facts."""

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
        if (candidate / "artifacts/migration/fresh_db_legacy_tender_registration_replay_adapter_result_v1.json").exists():
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
INPUT_MANIFEST = REPO_ROOT / "artifacts/migration/fresh_db_legacy_tender_registration_replay_adapter_result_v1.json"
INPUT_CSV = REPO_ROOT / "artifacts/migration/fresh_db_legacy_tender_registration_replay_payload_v1.csv"
OUTPUT_JSON = ARTIFACT_ROOT / "fresh_db_legacy_tender_registration_replay_write_result_v1.json"

COLUMNS = [
    "legacy_record_id",
    "legacy_pid",
    "source_dataset",
    "document_no",
    "document_state",
    "project_legacy_id",
    "project_name",
    "owner_name",
    "construction_unit_name",
    "project_manager_name",
    "contact_name",
    "registration_time",
    "bid_time",
    "opening_time",
    "guarantee_deadline",
    "created_time",
    "creator_name",
    "creator_legacy_user_id",
    "guarantee_amount",
    "document_fee_amount",
    "max_price",
    "tender_status",
    "bid_participation",
    "bid_method",
    "bid_opening_place",
    "bank_name",
    "bank_account",
    "attachment_ref",
    "note",
    "active",
]

ensure_allowed_db()
manifest = json.loads(INPUT_MANIFEST.read_text(encoding="utf-8"))
uid = env.uid  # noqa: F821
bulk_load(INPUT_CSV, "tmp_legacy_tender_registration", COLUMNS)

env.cr.execute("SELECT COUNT(*) FROM sc_legacy_tender_registration_fact")  # noqa: F821
before = env.cr.fetchone()[0]  # noqa: F821

env.cr.execute(  # noqa: F821
    """
    INSERT INTO sc_legacy_tender_registration_fact (
      legacy_record_id, legacy_pid, source_table, source_dataset,
      document_no, document_state, state, project_legacy_id, project_name,
      project_id, owner_name, construction_unit_name, project_manager_name,
      contact_name, registration_time, bid_time, opening_time,
      guarantee_deadline, created_time, creator_name, creator_legacy_user_id,
      guarantee_amount, document_fee_amount, max_price, tender_status,
      bid_participation, bid_method, bid_opening_place, bank_name,
      bank_account, attachment_ref, note, active,
      create_uid, create_date, write_uid, write_date
    )
    SELECT
      t.legacy_record_id,
      NULLIF(t.legacy_pid, ''),
      'P_ZTB_GCBMGL',
      NULLIF(t.source_dataset, ''),
      NULLIF(t.document_no, ''),
      NULLIF(t.document_state, ''),
      CASE WHEN COALESCE(NULLIF(t.active, ''), '1') = '1' THEN 'legacy_confirmed' ELSE 'cancel' END,
      NULLIF(t.project_legacy_id, ''),
      NULLIF(t.project_name, ''),
      project.id,
      NULLIF(t.owner_name, ''),
      NULLIF(t.construction_unit_name, ''),
      NULLIF(t.project_manager_name, ''),
      NULLIF(t.contact_name, ''),
      NULLIF(t.registration_time, '')::timestamp,
      NULLIF(t.bid_time, '')::timestamp,
      NULLIF(t.opening_time, '')::timestamp,
      NULLIF(t.guarantee_deadline, '')::timestamp,
      NULLIF(t.created_time, '')::timestamp,
      NULLIF(t.creator_name, ''),
      NULLIF(t.creator_legacy_user_id, ''),
      COALESCE(NULLIF(t.guarantee_amount, '')::numeric, 0),
      COALESCE(NULLIF(t.document_fee_amount, '')::numeric, 0),
      COALESCE(NULLIF(t.max_price, '')::numeric, 0),
      NULLIF(t.tender_status, ''),
      NULLIF(t.bid_participation, ''),
      NULLIF(t.bid_method, ''),
      NULLIF(t.bid_opening_place, ''),
      NULLIF(t.bank_name, ''),
      NULLIF(t.bank_account, ''),
      NULLIF(t.attachment_ref, ''),
      NULLIF(t.note, ''),
      COALESCE(NULLIF(t.active, ''), '1') = '1',
      %s, NOW(), %s, NOW()
    FROM tmp_legacy_tender_registration t
    LEFT JOIN (
      SELECT DISTINCT ON (legacy_project_id) legacy_project_id, id
      FROM project_project
      WHERE legacy_project_id IS NOT NULL
      ORDER BY legacy_project_id, id
    ) project ON project.legacy_project_id = NULLIF(t.project_legacy_id, '')
    ON CONFLICT (source_table, legacy_record_id) DO UPDATE SET
      legacy_pid = EXCLUDED.legacy_pid,
      source_dataset = EXCLUDED.source_dataset,
      document_no = EXCLUDED.document_no,
      document_state = EXCLUDED.document_state,
      state = EXCLUDED.state,
      project_legacy_id = EXCLUDED.project_legacy_id,
      project_name = EXCLUDED.project_name,
      project_id = EXCLUDED.project_id,
      owner_name = EXCLUDED.owner_name,
      construction_unit_name = EXCLUDED.construction_unit_name,
      project_manager_name = EXCLUDED.project_manager_name,
      contact_name = EXCLUDED.contact_name,
      registration_time = EXCLUDED.registration_time,
      bid_time = EXCLUDED.bid_time,
      opening_time = EXCLUDED.opening_time,
      guarantee_deadline = EXCLUDED.guarantee_deadline,
      created_time = EXCLUDED.created_time,
      creator_name = EXCLUDED.creator_name,
      creator_legacy_user_id = EXCLUDED.creator_legacy_user_id,
      guarantee_amount = EXCLUDED.guarantee_amount,
      document_fee_amount = EXCLUDED.document_fee_amount,
      max_price = EXCLUDED.max_price,
      tender_status = EXCLUDED.tender_status,
      bid_participation = EXCLUDED.bid_participation,
      bid_method = EXCLUDED.bid_method,
      bid_opening_place = EXCLUDED.bid_opening_place,
      bank_name = EXCLUDED.bank_name,
      bank_account = EXCLUDED.bank_account,
      attachment_ref = EXCLUDED.attachment_ref,
      note = EXCLUDED.note,
      active = EXCLUDED.active,
      write_uid = EXCLUDED.write_uid,
      write_date = NOW()
    """,
    [uid, uid],
)
env.cr.commit()  # noqa: F821

env.cr.execute("SELECT COUNT(*) FROM sc_legacy_tender_registration_fact")  # noqa: F821
after = env.cr.fetchone()[0]  # noqa: F821
env.cr.execute("SELECT COUNT(*) FROM sc_legacy_tender_registration_fact WHERE active")  # noqa: F821
active_rows = env.cr.fetchone()[0]  # noqa: F821
env.cr.execute("SELECT COUNT(*) FROM sc_legacy_tender_registration_fact WHERE project_id IS NOT NULL")  # noqa: F821
project_linked = env.cr.fetchone()[0]  # noqa: F821
env.cr.execute("SELECT COALESCE(SUM(guarantee_amount), 0), COALESCE(SUM(document_fee_amount), 0) FROM sc_legacy_tender_registration_fact")  # noqa: F821
guarantee_amount, document_fee_amount = env.cr.fetchone()  # noqa: F821

payload = {
    "status": "PASS",
    "mode": "fresh_db_legacy_tender_registration_replay_write",
    "database": env.cr.dbname,  # noqa: F821
    "input_rows": manifest.get("total_rows"),
    "before": before,
    "after": after,
    "delta": after - before,
    "active_rows": active_rows,
    "project_linked": project_linked,
    "guarantee_amount_sum": str(guarantee_amount),
    "document_fee_amount_sum": str(document_fee_amount),
    "db_writes": max(after - before, 0),
    "decision": "legacy_tender_registration_replay_complete",
}
write_json(OUTPUT_JSON, payload)
print("FRESH_DB_LEGACY_TENDER_REGISTRATION_REPLAY_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
