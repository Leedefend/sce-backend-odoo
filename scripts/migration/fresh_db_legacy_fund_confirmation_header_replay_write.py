#!/usr/bin/env python3
"""Replay legacy fund confirmation headers into a neutral carrier model."""

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
        if (candidate / "artifacts/migration/fresh_db_legacy_fund_confirmation_header_replay_adapter_result_v1.json").exists():
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
INPUT_MANIFEST = REPO_ROOT / "artifacts/migration/fresh_db_legacy_fund_confirmation_header_replay_adapter_result_v1.json"
INPUT_CSV = REPO_ROOT / "artifacts/migration/fresh_db_legacy_fund_confirmation_header_replay_payload_v1.csv"
OUTPUT_JSON = ARTIFACT_ROOT / "fresh_db_legacy_fund_confirmation_header_replay_write_result_v1.json"

COLUMNS = [
    "legacy_header_id", "legacy_pid", "project_legacy_id", "project_name",
    "document_no", "period_no", "receipt_time", "contract_legacy_id",
    "contract_name", "contract_amount", "bid_date", "current_project_stage",
    "actual_fund_amount", "accumulated_invoice_amount", "filler_name",
    "document_state", "creator_legacy_user_id", "creator_name", "created_time",
    "modifier_legacy_user_id", "modifier_name", "modified_time",
    "related_receipt_ids", "application_balance_note", "invoice_receipt_note",
    "quality_return_note", "available_balance_note", "construction_deduction_note",
    "payable_construction_deduction_note", "attachment_ref", "note", "active",
]

ensure_allowed_db()
manifest = json.loads(INPUT_MANIFEST.read_text(encoding="utf-8"))
uid = env.uid  # noqa: F821
bulk_load(INPUT_CSV, "tmp_legacy_fund_confirmation_header", COLUMNS)

env.cr.execute("SELECT COUNT(*) FROM sc_legacy_fund_confirmation_header")  # noqa: F821
before = env.cr.fetchone()[0]  # noqa: F821

env.cr.execute(  # noqa: F821
    """
    INSERT INTO sc_legacy_fund_confirmation_header (
      legacy_header_id, legacy_pid, project_legacy_id, project_name, project_id,
      document_no, period_no, receipt_time, contract_legacy_id, contract_name,
      contract_amount, bid_date, current_project_stage, actual_fund_amount,
      accumulated_invoice_amount, filler_name, document_state, creator_legacy_user_id,
      creator_name, created_time, modifier_legacy_user_id, modifier_name, modified_time,
      related_receipt_ids, application_balance_note, invoice_receipt_note, quality_return_note,
      available_balance_note, construction_deduction_note, payable_construction_deduction_note,
      attachment_ref, note, source_table, active, create_uid, create_date, write_uid, write_date
    )
    SELECT
      t.legacy_header_id, NULLIF(t.legacy_pid, ''), NULLIF(t.project_legacy_id, ''),
      NULLIF(t.project_name, ''), project.id, NULLIF(t.document_no, ''),
      NULLIF(t.period_no, ''), NULLIF(t.receipt_time, '')::timestamp,
      NULLIF(t.contract_legacy_id, ''), NULLIF(t.contract_name, ''),
      COALESCE(NULLIF(t.contract_amount, '')::numeric, 0),
      NULLIF(t.bid_date, '')::timestamp, NULLIF(t.current_project_stage, ''),
      COALESCE(NULLIF(t.actual_fund_amount, '')::numeric, 0),
      COALESCE(NULLIF(t.accumulated_invoice_amount, '')::numeric, 0),
      NULLIF(t.filler_name, ''), NULLIF(t.document_state, ''),
      NULLIF(t.creator_legacy_user_id, ''), NULLIF(t.creator_name, ''),
      NULLIF(t.created_time, '')::timestamp, NULLIF(t.modifier_legacy_user_id, ''),
      NULLIF(t.modifier_name, ''), NULLIF(t.modified_time, '')::timestamp,
      NULLIF(t.related_receipt_ids, ''), NULLIF(t.application_balance_note, ''),
      NULLIF(t.invoice_receipt_note, ''), NULLIF(t.quality_return_note, ''),
      NULLIF(t.available_balance_note, ''), NULLIF(t.construction_deduction_note, ''),
      NULLIF(t.payable_construction_deduction_note, ''), NULLIF(t.attachment_ref, ''),
      NULLIF(t.note, ''), 'ZJGL_SZQR_DKQRB',
      COALESCE(NULLIF(t.active, ''), '1') = '1', %s, NOW(), %s, NOW()
    FROM tmp_legacy_fund_confirmation_header t
    LEFT JOIN project_project project ON project.legacy_project_id = NULLIF(t.project_legacy_id, '')
    ON CONFLICT (legacy_header_id) DO UPDATE SET
      legacy_pid = EXCLUDED.legacy_pid,
      project_legacy_id = EXCLUDED.project_legacy_id,
      project_name = EXCLUDED.project_name,
      project_id = EXCLUDED.project_id,
      document_no = EXCLUDED.document_no,
      period_no = EXCLUDED.period_no,
      receipt_time = EXCLUDED.receipt_time,
      contract_legacy_id = EXCLUDED.contract_legacy_id,
      contract_name = EXCLUDED.contract_name,
      contract_amount = EXCLUDED.contract_amount,
      bid_date = EXCLUDED.bid_date,
      current_project_stage = EXCLUDED.current_project_stage,
      actual_fund_amount = EXCLUDED.actual_fund_amount,
      accumulated_invoice_amount = EXCLUDED.accumulated_invoice_amount,
      filler_name = EXCLUDED.filler_name,
      document_state = EXCLUDED.document_state,
      creator_legacy_user_id = EXCLUDED.creator_legacy_user_id,
      creator_name = EXCLUDED.creator_name,
      created_time = EXCLUDED.created_time,
      modifier_legacy_user_id = EXCLUDED.modifier_legacy_user_id,
      modifier_name = EXCLUDED.modifier_name,
      modified_time = EXCLUDED.modified_time,
      related_receipt_ids = EXCLUDED.related_receipt_ids,
      application_balance_note = EXCLUDED.application_balance_note,
      invoice_receipt_note = EXCLUDED.invoice_receipt_note,
      quality_return_note = EXCLUDED.quality_return_note,
      available_balance_note = EXCLUDED.available_balance_note,
      construction_deduction_note = EXCLUDED.construction_deduction_note,
      payable_construction_deduction_note = EXCLUDED.payable_construction_deduction_note,
      attachment_ref = EXCLUDED.attachment_ref,
      note = EXCLUDED.note,
      active = EXCLUDED.active,
      write_uid = EXCLUDED.write_uid,
      write_date = EXCLUDED.write_date
    """,
    [uid, uid],
)
env.cr.commit()  # noqa: F821

env.cr.execute("SELECT COUNT(*) FROM sc_legacy_fund_confirmation_header")  # noqa: F821
after = env.cr.fetchone()[0]  # noqa: F821
env.cr.execute("SELECT COUNT(*) FROM sc_legacy_fund_confirmation_header WHERE active")  # noqa: F821
active_rows = env.cr.fetchone()[0]  # noqa: F821
env.cr.execute("SELECT COUNT(*) FROM sc_legacy_fund_confirmation_header WHERE project_id IS NOT NULL")  # noqa: F821
project_linked = env.cr.fetchone()[0]  # noqa: F821

payload = {
    "status": "PASS",
    "mode": "fresh_db_legacy_fund_confirmation_header_replay_write",
    "database": env.cr.dbname,  # noqa: F821
    "input_rows": manifest.get("total_rows"),
    "active_input_rows": manifest.get("active_header_rows"),
    "before": before,
    "after": after,
    "delta": after - before,
    "active_rows": active_rows,
    "project_linked": project_linked,
    "db_writes": max(after - before, 0),
    "decision": "legacy_fund_confirmation_header_replay_complete",
}
write_json(OUTPUT_JSON, payload)
print("FRESH_DB_LEGACY_FUND_CONFIRMATION_HEADER_REPLAY_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
