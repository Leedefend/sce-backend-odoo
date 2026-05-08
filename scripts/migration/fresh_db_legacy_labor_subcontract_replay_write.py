#!/usr/bin/env python3
"""Replay legacy labor and subcontract facts."""

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
        if (candidate / "artifacts/migration/fresh_db_legacy_labor_subcontract_replay_adapter_result_v1.json").exists():
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
INPUT_MANIFEST = REPO_ROOT / "artifacts/migration/fresh_db_legacy_labor_subcontract_replay_adapter_result_v1.json"
INPUT_CSV = REPO_ROOT / "artifacts/migration/fresh_db_legacy_labor_subcontract_replay_payload_v1.csv"
OUTPUT_JSON = ARTIFACT_ROOT / "fresh_db_legacy_labor_subcontract_replay_write_result_v1.json"

COLUMNS = [
    "legacy_record_id",
    "legacy_pid",
    "source_table",
    "source_dataset",
    "fact_type",
    "document_no",
    "document_state",
    "project_legacy_id",
    "project_name",
    "partner_legacy_id",
    "partner_name",
    "contract_legacy_id",
    "contract_no",
    "contract_name",
    "work_scope",
    "work_part",
    "department_name",
    "document_date",
    "start_date",
    "end_date",
    "created_time",
    "creator_name",
    "creator_legacy_user_id",
    "amount_total",
    "amount_contract",
    "amount_settlement",
    "amount_payable",
    "amount_deduction",
    "tax_rate",
    "bank_name",
    "bank_account",
    "attachment_ref",
    "note",
    "active",
]

ensure_allowed_db()
manifest = json.loads(INPUT_MANIFEST.read_text(encoding="utf-8"))
uid = env.uid  # noqa: F821
bulk_load(INPUT_CSV, "tmp_legacy_labor_subcontract", COLUMNS)

env.cr.execute("SELECT COUNT(*) FROM sc_legacy_labor_subcontract_fact")  # noqa: F821
before = env.cr.fetchone()[0]  # noqa: F821

env.cr.execute(  # noqa: F821
    """
    INSERT INTO sc_legacy_labor_subcontract_fact (
      legacy_record_id, legacy_pid, source_table, source_dataset,
      fact_type, document_no, document_state, state, project_legacy_id,
      project_name, project_id, partner_legacy_id, partner_name,
      contract_legacy_id, contract_no, contract_name, work_scope,
      work_part, department_name, document_date, start_date, end_date,
      created_time, creator_name, creator_legacy_user_id,
      amount_total, amount_contract, amount_settlement, amount_payable,
      amount_deduction, tax_rate, bank_name, bank_account,
      attachment_ref, note, active,
      create_uid, create_date, write_uid, write_date
    )
    SELECT
      t.legacy_record_id,
      NULLIF(t.legacy_pid, ''),
      t.source_table,
      NULLIF(t.source_dataset, ''),
      t.fact_type,
      NULLIF(t.document_no, ''),
      NULLIF(t.document_state, ''),
      CASE WHEN COALESCE(NULLIF(t.active, ''), '1') = '1' THEN 'legacy_confirmed' ELSE 'cancel' END,
      NULLIF(t.project_legacy_id, ''),
      NULLIF(t.project_name, ''),
      project.id,
      NULLIF(t.partner_legacy_id, ''),
      NULLIF(t.partner_name, ''),
      NULLIF(t.contract_legacy_id, ''),
      NULLIF(t.contract_no, ''),
      NULLIF(t.contract_name, ''),
      NULLIF(t.work_scope, ''),
      NULLIF(t.work_part, ''),
      NULLIF(t.department_name, ''),
      NULLIF(t.document_date, '')::timestamp,
      NULLIF(t.start_date, '')::timestamp,
      NULLIF(t.end_date, '')::timestamp,
      NULLIF(t.created_time, '')::timestamp,
      NULLIF(t.creator_name, ''),
      NULLIF(t.creator_legacy_user_id, ''),
      COALESCE(NULLIF(t.amount_total, '')::numeric, 0),
      COALESCE(NULLIF(t.amount_contract, '')::numeric, 0),
      COALESCE(NULLIF(t.amount_settlement, '')::numeric, 0),
      COALESCE(NULLIF(t.amount_payable, '')::numeric, 0),
      COALESCE(NULLIF(t.amount_deduction, '')::numeric, 0),
      COALESCE(NULLIF(t.tax_rate, '')::numeric, 0),
      NULLIF(t.bank_name, ''),
      NULLIF(t.bank_account, ''),
      NULLIF(t.attachment_ref, ''),
      NULLIF(t.note, ''),
      COALESCE(NULLIF(t.active, ''), '1') = '1',
      %s, NOW(), %s, NOW()
    FROM tmp_legacy_labor_subcontract t
    LEFT JOIN (
      SELECT DISTINCT ON (legacy_project_id) legacy_project_id, id
      FROM project_project
      WHERE legacy_project_id IS NOT NULL
      ORDER BY legacy_project_id, id
    ) project ON project.legacy_project_id = NULLIF(t.project_legacy_id, '')
    ON CONFLICT (source_table, legacy_record_id) DO UPDATE SET
      legacy_pid = EXCLUDED.legacy_pid,
      source_dataset = EXCLUDED.source_dataset,
      fact_type = EXCLUDED.fact_type,
      document_no = EXCLUDED.document_no,
      document_state = EXCLUDED.document_state,
      state = EXCLUDED.state,
      project_legacy_id = EXCLUDED.project_legacy_id,
      project_name = EXCLUDED.project_name,
      project_id = EXCLUDED.project_id,
      partner_legacy_id = EXCLUDED.partner_legacy_id,
      partner_name = EXCLUDED.partner_name,
      contract_legacy_id = EXCLUDED.contract_legacy_id,
      contract_no = EXCLUDED.contract_no,
      contract_name = EXCLUDED.contract_name,
      work_scope = EXCLUDED.work_scope,
      work_part = EXCLUDED.work_part,
      department_name = EXCLUDED.department_name,
      document_date = EXCLUDED.document_date,
      start_date = EXCLUDED.start_date,
      end_date = EXCLUDED.end_date,
      created_time = EXCLUDED.created_time,
      creator_name = EXCLUDED.creator_name,
      creator_legacy_user_id = EXCLUDED.creator_legacy_user_id,
      amount_total = EXCLUDED.amount_total,
      amount_contract = EXCLUDED.amount_contract,
      amount_settlement = EXCLUDED.amount_settlement,
      amount_payable = EXCLUDED.amount_payable,
      amount_deduction = EXCLUDED.amount_deduction,
      tax_rate = EXCLUDED.tax_rate,
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

env.cr.execute("SELECT COUNT(*) FROM sc_legacy_labor_subcontract_fact")  # noqa: F821
after = env.cr.fetchone()[0]  # noqa: F821
env.cr.execute("SELECT COUNT(*) FROM sc_legacy_labor_subcontract_fact WHERE active")  # noqa: F821
active_rows = env.cr.fetchone()[0]  # noqa: F821
env.cr.execute("SELECT COUNT(*) FROM sc_legacy_labor_subcontract_fact WHERE project_id IS NOT NULL")  # noqa: F821
project_linked = env.cr.fetchone()[0]  # noqa: F821
env.cr.execute(  # noqa: F821
    """
    SELECT
      COALESCE(SUM(amount_total), 0),
      COALESCE(SUM(amount_contract), 0),
      COALESCE(SUM(amount_settlement), 0),
      COALESCE(SUM(amount_payable), 0)
    FROM sc_legacy_labor_subcontract_fact
    """
)
amount_total, amount_contract, amount_settlement, amount_payable = env.cr.fetchone()  # noqa: F821
env.cr.execute("SELECT source_table, COUNT(*) FROM sc_legacy_labor_subcontract_fact GROUP BY source_table ORDER BY source_table")  # noqa: F821
source_counts = dict(env.cr.fetchall())  # noqa: F821
env.cr.execute("SELECT fact_type, COUNT(*) FROM sc_legacy_labor_subcontract_fact GROUP BY fact_type ORDER BY fact_type")  # noqa: F821
fact_type_counts = dict(env.cr.fetchall())  # noqa: F821

payload = {
    "status": "PASS",
    "mode": "fresh_db_legacy_labor_subcontract_replay_write",
    "database": env.cr.dbname,  # noqa: F821
    "input_rows": manifest.get("total_rows"),
    "before": before,
    "after": after,
    "delta": after - before,
    "active_rows": active_rows,
    "project_linked": project_linked,
    "amount_total_sum": str(amount_total),
    "amount_contract_sum": str(amount_contract),
    "amount_settlement_sum": str(amount_settlement),
    "amount_payable_sum": str(amount_payable),
    "source_counts": source_counts,
    "fact_type_counts": fact_type_counts,
    "db_writes": max(after - before, 0),
    "decision": "legacy_labor_subcontract_replay_complete",
}
write_json(OUTPUT_JSON, payload)
print("FRESH_DB_LEGACY_LABOR_SUBCONTRACT_REPLAY_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
