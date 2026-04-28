#!/usr/bin/env python3
"""Replay legacy expense reimbursement line facts into a neutral carrier model."""

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
        if (candidate / "artifacts/migration/fresh_db_legacy_expense_reimbursement_line_replay_adapter_result_v1.json").exists():
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
INPUT_MANIFEST = REPO_ROOT / "artifacts/migration/fresh_db_legacy_expense_reimbursement_line_replay_adapter_result_v1.json"
INPUT_CSV = REPO_ROOT / "artifacts/migration/fresh_db_legacy_expense_reimbursement_line_replay_payload_v1.csv"
OUTPUT_JSON = ARTIFACT_ROOT / "fresh_db_legacy_expense_reimbursement_line_replay_write_result_v1.json"

COLUMNS = [
    "legacy_line_id",
    "legacy_header_id",
    "legacy_pid",
    "legacy_header_pid",
    "document_no",
    "document_date",
    "document_state",
    "company_legacy_id",
    "company_name",
    "department_legacy_id",
    "department_name",
    "project_legacy_id",
    "project_name",
    "applicant_legacy_id",
    "applicant_name",
    "applicant_contact",
    "applicant_position",
    "reimbursement_type_legacy_id",
    "reimbursement_type",
    "finance_type_legacy_id",
    "finance_type",
    "line_project_legacy_id",
    "line_project_name",
    "line_date",
    "amount",
    "quantity",
    "unit_price",
    "allocated_amount",
    "summary",
    "participant",
    "participant_count",
    "deducted_participant",
    "deducted_count",
    "invoice_content",
    "payment_method",
    "payee",
    "payee_account",
    "payee_bank",
    "header_total",
    "requested_amount",
    "approved_amount",
    "writeoff_amount",
    "advance_amount",
    "creator_legacy_user_id",
    "creator_name",
    "created_time",
    "modifier_legacy_user_id",
    "modifier_name",
    "modified_time",
    "attachment_ref",
    "line_attachment_ref",
    "note",
    "header_note",
    "active",
]

NUMERIC_COLUMNS = [
    "amount",
    "quantity",
    "unit_price",
    "allocated_amount",
    "header_total",
    "requested_amount",
    "approved_amount",
    "writeoff_amount",
    "advance_amount",
]

ensure_allowed_db()
manifest = json.loads(INPUT_MANIFEST.read_text(encoding="utf-8"))
uid = env.uid  # noqa: F821

bulk_load(INPUT_CSV, "tmp_legacy_expense_reimbursement_line", COLUMNS)

env.cr.execute("SELECT COUNT(*) FROM sc_legacy_expense_reimbursement_line")  # noqa: F821
before = env.cr.fetchone()[0]  # noqa: F821

env.cr.execute(  # noqa: F821
    """
    INSERT INTO sc_legacy_expense_reimbursement_line (
      legacy_line_id, legacy_header_id, legacy_pid, legacy_header_pid,
      document_no, document_date, document_state, company_legacy_id,
      company_name, department_legacy_id, department_name, project_legacy_id,
      project_name, project_id, applicant_legacy_id, applicant_name,
      applicant_contact, applicant_position, reimbursement_type_legacy_id,
      reimbursement_type, finance_type_legacy_id, finance_type,
      line_project_legacy_id, line_project_name, line_date, amount,
      quantity, unit_price, allocated_amount, summary, participant,
      participant_count, deducted_participant, deducted_count,
      invoice_content, payment_method, payee, payee_account, payee_bank,
      header_total, requested_amount, approved_amount, writeoff_amount,
      advance_amount, creator_legacy_user_id, creator_name, created_time,
      modifier_legacy_user_id, modifier_name, modified_time, attachment_ref,
      line_attachment_ref, note, header_note, source_table, active,
      create_uid, create_date, write_uid, write_date
    )
    SELECT
      t.legacy_line_id,
      NULLIF(t.legacy_header_id, ''),
      NULLIF(t.legacy_pid, ''),
      NULLIF(t.legacy_header_pid, ''),
      NULLIF(t.document_no, ''),
      NULLIF(t.document_date, ''),
      NULLIF(t.document_state, ''),
      NULLIF(t.company_legacy_id, ''),
      NULLIF(t.company_name, ''),
      NULLIF(t.department_legacy_id, ''),
      NULLIF(t.department_name, ''),
      NULLIF(t.project_legacy_id, ''),
      NULLIF(t.project_name, ''),
      project.id,
      NULLIF(t.applicant_legacy_id, ''),
      NULLIF(t.applicant_name, ''),
      NULLIF(t.applicant_contact, ''),
      NULLIF(t.applicant_position, ''),
      NULLIF(t.reimbursement_type_legacy_id, ''),
      NULLIF(t.reimbursement_type, ''),
      NULLIF(t.finance_type_legacy_id, ''),
      NULLIF(t.finance_type, ''),
      NULLIF(t.line_project_legacy_id, ''),
      NULLIF(t.line_project_name, ''),
      NULLIF(t.line_date, ''),
      COALESCE(NULLIF(t.amount, '')::numeric, 0),
      COALESCE(NULLIF(t.quantity, '')::numeric, 0),
      COALESCE(NULLIF(t.unit_price, '')::numeric, 0),
      COALESCE(NULLIF(t.allocated_amount, '')::numeric, 0),
      NULLIF(t.summary, ''),
      NULLIF(t.participant, ''),
      NULLIF(t.participant_count, ''),
      NULLIF(t.deducted_participant, ''),
      NULLIF(t.deducted_count, ''),
      NULLIF(t.invoice_content, ''),
      NULLIF(t.payment_method, ''),
      NULLIF(t.payee, ''),
      NULLIF(t.payee_account, ''),
      NULLIF(t.payee_bank, ''),
      COALESCE(NULLIF(t.header_total, '')::numeric, 0),
      COALESCE(NULLIF(t.requested_amount, '')::numeric, 0),
      COALESCE(NULLIF(t.approved_amount, '')::numeric, 0),
      COALESCE(NULLIF(t.writeoff_amount, '')::numeric, 0),
      COALESCE(NULLIF(t.advance_amount, '')::numeric, 0),
      NULLIF(t.creator_legacy_user_id, ''),
      NULLIF(t.creator_name, ''),
      NULLIF(t.created_time, '')::timestamp,
      NULLIF(t.modifier_legacy_user_id, ''),
      NULLIF(t.modifier_name, ''),
      NULLIF(t.modified_time, '')::timestamp,
      NULLIF(t.attachment_ref, ''),
      NULLIF(t.line_attachment_ref, ''),
      NULLIF(t.note, ''),
      NULLIF(t.header_note, ''),
      'CWGL_FYBX_CB',
      COALESCE(NULLIF(t.active, ''), '1') = '1',
      %s, NOW(), %s, NOW()
    FROM tmp_legacy_expense_reimbursement_line t
    LEFT JOIN project_project project ON project.legacy_project_id = COALESCE(NULLIF(t.line_project_legacy_id, ''), NULLIF(t.project_legacy_id, ''))
    ON CONFLICT (legacy_line_id) DO UPDATE SET
      legacy_header_id = EXCLUDED.legacy_header_id,
      legacy_pid = EXCLUDED.legacy_pid,
      legacy_header_pid = EXCLUDED.legacy_header_pid,
      document_no = EXCLUDED.document_no,
      document_date = EXCLUDED.document_date,
      document_state = EXCLUDED.document_state,
      company_legacy_id = EXCLUDED.company_legacy_id,
      company_name = EXCLUDED.company_name,
      department_legacy_id = EXCLUDED.department_legacy_id,
      department_name = EXCLUDED.department_name,
      project_legacy_id = EXCLUDED.project_legacy_id,
      project_name = EXCLUDED.project_name,
      project_id = EXCLUDED.project_id,
      applicant_legacy_id = EXCLUDED.applicant_legacy_id,
      applicant_name = EXCLUDED.applicant_name,
      applicant_contact = EXCLUDED.applicant_contact,
      applicant_position = EXCLUDED.applicant_position,
      reimbursement_type_legacy_id = EXCLUDED.reimbursement_type_legacy_id,
      reimbursement_type = EXCLUDED.reimbursement_type,
      finance_type_legacy_id = EXCLUDED.finance_type_legacy_id,
      finance_type = EXCLUDED.finance_type,
      line_project_legacy_id = EXCLUDED.line_project_legacy_id,
      line_project_name = EXCLUDED.line_project_name,
      line_date = EXCLUDED.line_date,
      amount = EXCLUDED.amount,
      quantity = EXCLUDED.quantity,
      unit_price = EXCLUDED.unit_price,
      allocated_amount = EXCLUDED.allocated_amount,
      summary = EXCLUDED.summary,
      participant = EXCLUDED.participant,
      participant_count = EXCLUDED.participant_count,
      deducted_participant = EXCLUDED.deducted_participant,
      deducted_count = EXCLUDED.deducted_count,
      invoice_content = EXCLUDED.invoice_content,
      payment_method = EXCLUDED.payment_method,
      payee = EXCLUDED.payee,
      payee_account = EXCLUDED.payee_account,
      payee_bank = EXCLUDED.payee_bank,
      header_total = EXCLUDED.header_total,
      requested_amount = EXCLUDED.requested_amount,
      approved_amount = EXCLUDED.approved_amount,
      writeoff_amount = EXCLUDED.writeoff_amount,
      advance_amount = EXCLUDED.advance_amount,
      creator_legacy_user_id = EXCLUDED.creator_legacy_user_id,
      creator_name = EXCLUDED.creator_name,
      created_time = EXCLUDED.created_time,
      modifier_legacy_user_id = EXCLUDED.modifier_legacy_user_id,
      modifier_name = EXCLUDED.modifier_name,
      modified_time = EXCLUDED.modified_time,
      attachment_ref = EXCLUDED.attachment_ref,
      line_attachment_ref = EXCLUDED.line_attachment_ref,
      note = EXCLUDED.note,
      header_note = EXCLUDED.header_note,
      active = EXCLUDED.active,
      write_uid = EXCLUDED.write_uid,
      write_date = NOW()
    """,
    [uid, uid],
)

env.cr.commit()  # noqa: F821

env.cr.execute("SELECT COUNT(*) FROM sc_legacy_expense_reimbursement_line")  # noqa: F821
after = env.cr.fetchone()[0]  # noqa: F821
env.cr.execute("SELECT COUNT(*) FROM sc_legacy_expense_reimbursement_line WHERE active")  # noqa: F821
active_rows = env.cr.fetchone()[0]  # noqa: F821
env.cr.execute("SELECT COUNT(*) FROM sc_legacy_expense_reimbursement_line WHERE project_id IS NOT NULL")  # noqa: F821
project_linked = env.cr.fetchone()[0]  # noqa: F821
env.cr.execute("SELECT COALESCE(SUM(amount), 0), COALESCE(SUM(approved_amount), 0) FROM sc_legacy_expense_reimbursement_line")  # noqa: F821
amount, approved_amount = env.cr.fetchone()  # noqa: F821

payload = {
    "status": "PASS",
    "mode": "fresh_db_legacy_expense_reimbursement_line_replay_write",
    "database": env.cr.dbname,  # noqa: F821
    "input_rows": manifest.get("total_rows"),
    "before": before,
    "after": after,
    "delta": after - before,
    "active_rows": active_rows,
    "project_linked": project_linked,
    "line_amount": str(amount),
    "line_header_approved_amount_sum": str(approved_amount),
    "db_writes": max(after - before, 0),
    "decision": "legacy_expense_reimbursement_line_replay_complete",
}
write_json(OUTPUT_JSON, payload)
print("FRESH_DB_LEGACY_EXPENSE_REIMBURSEMENT_LINE_REPLAY_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
