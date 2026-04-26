#!/usr/bin/env python3
"""Replay receipt facts not already represented by runtime receive requests."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path


def repo_root() -> Path:
    env_root = os.getenv("MIGRATION_REPO_ROOT")
    candidates = []
    if env_root:
        candidates.append(Path(env_root))
    candidates.extend([Path("/mnt"), Path.cwd()])
    for candidate in candidates:
        if (candidate / "artifacts/migration/fresh_db_legacy_receipt_residual_replay_adapter_result_v1.json").exists():
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
INPUT_MANIFEST = REPO_ROOT / "artifacts/migration/fresh_db_legacy_receipt_residual_replay_adapter_result_v1.json"
INPUT_CSV = REPO_ROOT / "artifacts/migration/fresh_db_legacy_receipt_residual_replay_payload_v1.csv"
OUTPUT_JSON = ARTIFACT_ROOT / "fresh_db_legacy_receipt_residual_replay_write_result_v1.json"

COLUMNS = [
    "legacy_record_id",
    "legacy_pid",
    "document_no",
    "document_date",
    "document_state",
    "deleted_flag",
    "receipt_type",
    "income_category_legacy_id",
    "income_category",
    "project_legacy_id",
    "project_name",
    "partner_legacy_id",
    "partner_name",
    "partner_type",
    "contract_legacy_id",
    "contract_no",
    "amount",
    "deducted_invoice_amount",
    "deducted_tax_amount",
    "settlement_amount",
    "budget_amount",
    "payment_method_legacy_id",
    "payment_method",
    "receiving_account_legacy_id",
    "receiving_account",
    "bill_no",
    "invoice_ref",
    "manager_legacy_id",
    "manager_name",
    "creator_legacy_user_id",
    "creator_name",
    "created_time",
    "modifier_legacy_user_id",
    "modifier_name",
    "modified_time",
    "attachment_ref",
    "note",
    "active",
]

ensure_allowed_db()
manifest = json.loads(INPUT_MANIFEST.read_text(encoding="utf-8"))
uid = env.uid  # noqa: F821

bulk_load(INPUT_CSV, "tmp_legacy_receipt_residual", COLUMNS)

Request = env["payment.request"].sudo()  # noqa: F821
covered_receipts: set[str] = set()
receipt_re = re.compile(r"legacy_receipt_id=([^;\s]+)")
for rec in Request.search_read([("type", "=", "receive"), ("note", "ilike", "legacy_receipt_id=")], ["note"]):
    match = receipt_re.search(rec.get("note") or "")
    if match:
        covered_receipts.add(match.group(1))

env.cr.execute("DROP TABLE IF EXISTS tmp_legacy_receipt_residual_covered")  # noqa: F821
env.cr.execute("CREATE TEMP TABLE tmp_legacy_receipt_residual_covered (legacy_record_id text) ON COMMIT DROP")  # noqa: F821
if covered_receipts:
    env.cr.executemany(  # noqa: F821
        "INSERT INTO tmp_legacy_receipt_residual_covered (legacy_record_id) VALUES (%s)",
        [(item,) for item in covered_receipts],
    )

env.cr.execute("SELECT COUNT(*) FROM sc_legacy_receipt_residual_fact")  # noqa: F821
before = env.cr.fetchone()[0]  # noqa: F821

env.cr.execute(  # noqa: F821
    """
    INSERT INTO sc_legacy_receipt_residual_fact (
      legacy_record_id, legacy_pid, residual_reason, document_no,
      document_date, document_state, deleted_flag, receipt_type,
      income_category_legacy_id, income_category, project_legacy_id,
      project_name, project_id, partner_legacy_id, partner_name,
      partner_type, partner_id, contract_legacy_id, contract_no, amount,
      deducted_invoice_amount, deducted_tax_amount, settlement_amount,
      budget_amount, payment_method_legacy_id, payment_method,
      receiving_account_legacy_id, receiving_account, bill_no,
      invoice_ref, manager_legacy_id, manager_name, creator_legacy_user_id,
      creator_name, created_time, modifier_legacy_user_id, modifier_name,
      modified_time, attachment_ref, note, source_table, active,
      create_uid, create_date, write_uid, write_date
    )
    SELECT
      t.legacy_record_id,
      NULLIF(t.legacy_pid, ''),
      CASE
        WHEN COALESCE(NULLIF(t.deleted_flag, ''), '0') <> '0' THEN 'deleted'
        WHEN NULLIF(t.project_legacy_id, '') IS NOT NULL AND project.id IS NULL THEN 'missing_project_anchor'
        WHEN NULLIF(t.partner_legacy_id, '') IS NOT NULL AND partner.id IS NULL THEN 'missing_partner_anchor'
        WHEN NULLIF(t.contract_legacy_id, '') IS NOT NULL AND contract.id IS NULL THEN 'missing_contract_anchor'
        WHEN NULLIF(t.project_legacy_id, '') IS NULL AND NULLIF(t.partner_legacy_id, '') IS NULL AND NULLIF(t.contract_legacy_id, '') IS NULL THEN 'no_core_anchors'
        ELSE 'not_promoted_to_runtime_receive_request'
      END,
      NULLIF(t.document_no, ''),
      NULLIF(t.document_date, '')::date,
      NULLIF(t.document_state, ''),
      NULLIF(t.deleted_flag, ''),
      NULLIF(t.receipt_type, ''),
      NULLIF(t.income_category_legacy_id, ''),
      NULLIF(t.income_category, ''),
      NULLIF(t.project_legacy_id, ''),
      NULLIF(t.project_name, ''),
      project.id,
      NULLIF(t.partner_legacy_id, ''),
      NULLIF(t.partner_name, ''),
      NULLIF(t.partner_type, ''),
      partner.id,
      NULLIF(t.contract_legacy_id, ''),
      NULLIF(t.contract_no, ''),
      COALESCE(NULLIF(t.amount, '')::numeric, 0),
      COALESCE(NULLIF(t.deducted_invoice_amount, '')::numeric, 0),
      COALESCE(NULLIF(t.deducted_tax_amount, '')::numeric, 0),
      COALESCE(NULLIF(t.settlement_amount, '')::numeric, 0),
      COALESCE(NULLIF(t.budget_amount, '')::numeric, 0),
      NULLIF(t.payment_method_legacy_id, ''),
      NULLIF(t.payment_method, ''),
      NULLIF(t.receiving_account_legacy_id, ''),
      NULLIF(t.receiving_account, ''),
      NULLIF(t.bill_no, ''),
      NULLIF(t.invoice_ref, ''),
      NULLIF(t.manager_legacy_id, ''),
      NULLIF(t.manager_name, ''),
      NULLIF(t.creator_legacy_user_id, ''),
      NULLIF(t.creator_name, ''),
      NULLIF(t.created_time, '')::timestamp,
      NULLIF(t.modifier_legacy_user_id, ''),
      NULLIF(t.modifier_name, ''),
      NULLIF(t.modified_time, '')::timestamp,
      NULLIF(t.attachment_ref, ''),
      NULLIF(t.note, ''),
      'C_JFHKLR',
      COALESCE(NULLIF(t.active, ''), '1') = '1',
      %s, NOW(), %s, NOW()
    FROM tmp_legacy_receipt_residual t
    LEFT JOIN tmp_legacy_receipt_residual_covered covered ON covered.legacy_record_id = t.legacy_record_id
    LEFT JOIN (
      SELECT DISTINCT ON (legacy_project_id) legacy_project_id, id
      FROM project_project
      WHERE legacy_project_id IS NOT NULL
      ORDER BY legacy_project_id, id
    ) project ON project.legacy_project_id = NULLIF(t.project_legacy_id, '')
    LEFT JOIN (
      SELECT DISTINCT ON (legacy_partner_id) legacy_partner_id, id
      FROM res_partner
      WHERE legacy_partner_id IS NOT NULL
      ORDER BY legacy_partner_id, id
    ) partner ON partner.legacy_partner_id = NULLIF(t.partner_legacy_id, '')
    LEFT JOIN (
      SELECT DISTINCT ON (legacy_contract_id) legacy_contract_id, id
      FROM construction_contract
      WHERE legacy_contract_id IS NOT NULL
      ORDER BY legacy_contract_id, id
    ) contract ON contract.legacy_contract_id = NULLIF(t.contract_legacy_id, '')
    WHERE covered.legacy_record_id IS NULL
    ON CONFLICT (legacy_record_id) DO UPDATE SET
      legacy_pid = EXCLUDED.legacy_pid,
      residual_reason = EXCLUDED.residual_reason,
      document_no = EXCLUDED.document_no,
      document_date = EXCLUDED.document_date,
      document_state = EXCLUDED.document_state,
      deleted_flag = EXCLUDED.deleted_flag,
      receipt_type = EXCLUDED.receipt_type,
      income_category_legacy_id = EXCLUDED.income_category_legacy_id,
      income_category = EXCLUDED.income_category,
      project_legacy_id = EXCLUDED.project_legacy_id,
      project_name = EXCLUDED.project_name,
      project_id = EXCLUDED.project_id,
      partner_legacy_id = EXCLUDED.partner_legacy_id,
      partner_name = EXCLUDED.partner_name,
      partner_type = EXCLUDED.partner_type,
      partner_id = EXCLUDED.partner_id,
      contract_legacy_id = EXCLUDED.contract_legacy_id,
      contract_no = EXCLUDED.contract_no,
      amount = EXCLUDED.amount,
      deducted_invoice_amount = EXCLUDED.deducted_invoice_amount,
      deducted_tax_amount = EXCLUDED.deducted_tax_amount,
      settlement_amount = EXCLUDED.settlement_amount,
      budget_amount = EXCLUDED.budget_amount,
      payment_method_legacy_id = EXCLUDED.payment_method_legacy_id,
      payment_method = EXCLUDED.payment_method,
      receiving_account_legacy_id = EXCLUDED.receiving_account_legacy_id,
      receiving_account = EXCLUDED.receiving_account,
      bill_no = EXCLUDED.bill_no,
      invoice_ref = EXCLUDED.invoice_ref,
      manager_legacy_id = EXCLUDED.manager_legacy_id,
      manager_name = EXCLUDED.manager_name,
      creator_legacy_user_id = EXCLUDED.creator_legacy_user_id,
      creator_name = EXCLUDED.creator_name,
      created_time = EXCLUDED.created_time,
      modifier_legacy_user_id = EXCLUDED.modifier_legacy_user_id,
      modifier_name = EXCLUDED.modifier_name,
      modified_time = EXCLUDED.modified_time,
      attachment_ref = EXCLUDED.attachment_ref,
      note = EXCLUDED.note,
      active = EXCLUDED.active,
      write_uid = EXCLUDED.write_uid,
      write_date = NOW()
    """,
    [uid, uid],
)

env.cr.commit()  # noqa: F821

env.cr.execute("SELECT COUNT(*) FROM sc_legacy_receipt_residual_fact")  # noqa: F821
after = env.cr.fetchone()[0]  # noqa: F821
env.cr.execute("SELECT residual_reason, COUNT(*) FROM sc_legacy_receipt_residual_fact GROUP BY residual_reason ORDER BY residual_reason")  # noqa: F821
reason_counts = [{"reason": row[0], "count": row[1]} for row in env.cr.fetchall()]  # noqa: F821
env.cr.execute("SELECT COUNT(*) FROM sc_legacy_receipt_residual_fact WHERE active")  # noqa: F821
active_rows = env.cr.fetchone()[0]  # noqa: F821
env.cr.execute("SELECT COUNT(*) FROM sc_legacy_receipt_residual_fact WHERE project_id IS NOT NULL")  # noqa: F821
project_linked = env.cr.fetchone()[0]  # noqa: F821
env.cr.execute("SELECT COUNT(*) FROM sc_legacy_receipt_residual_fact WHERE partner_id IS NOT NULL")  # noqa: F821
partner_linked = env.cr.fetchone()[0]  # noqa: F821
env.cr.execute("SELECT COALESCE(SUM(amount), 0) FROM sc_legacy_receipt_residual_fact")  # noqa: F821
amount = env.cr.fetchone()[0]  # noqa: F821

payload = {
    "status": "PASS",
    "mode": "fresh_db_legacy_receipt_residual_replay_write",
    "database": env.cr.dbname,  # noqa: F821
    "input_rows": manifest.get("total_rows"),
    "runtime_covered_receipts": len(covered_receipts),
    "before": before,
    "after": after,
    "delta": after - before,
    "active_rows": active_rows,
    "project_linked": project_linked,
    "partner_linked": partner_linked,
    "amount": str(amount),
    "reason_counts": reason_counts,
    "db_writes": max(after - before, 0),
    "decision": "legacy_receipt_residual_replay_complete",
}
write_json(OUTPUT_JSON, payload)
print("FRESH_DB_LEGACY_RECEIPT_RESIDUAL_REPLAY_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
