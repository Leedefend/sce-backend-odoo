#!/usr/bin/env python3
"""Replay legacy purchase/general contract residual facts."""

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
        if (candidate / "artifacts/migration/fresh_db_legacy_purchase_contract_replay_adapter_result_v1.json").exists():
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
INPUT_MANIFEST = REPO_ROOT / "artifacts/migration/fresh_db_legacy_purchase_contract_replay_adapter_result_v1.json"
INPUT_CSV = REPO_ROOT / "artifacts/migration/fresh_db_legacy_purchase_contract_replay_payload_v1.csv"
OUTPUT_JSON = ARTIFACT_ROOT / "fresh_db_legacy_purchase_contract_replay_write_result_v1.json"

COLUMNS = [
    "legacy_record_id", "legacy_pid", "source_dataset", "document_no",
    "document_state", "submitted_time", "applicant_name",
    "applicant_department_legacy_id", "applicant_department",
    "project_legacy_id", "project_name", "contract_name", "contract_no",
    "signing_place", "contract_type_legacy_id", "contract_type",
    "completion_date", "expected_sign_date", "total_amount",
    "currency_legacy_id", "currency_name", "prepayment_amount",
    "install_debug_payment", "warranty_deposit", "payment_terms",
    "partner_legacy_id", "partner_name", "contact_name", "contact_phone",
    "bank_name", "bank_account", "sign_status", "purchase_engineer",
    "special_condition", "attachment_ref", "person_legacy_id",
    "creator_legacy_user_id", "creator_name", "created_time",
    "modifier_legacy_user_id", "modifier_name", "modified_time",
    "is_supplement_contract", "related_contract_legacy_id",
    "related_contract_no", "contract_attribute", "credit_code", "tax_rate",
    "note", "active",
]

ensure_allowed_db()
manifest = json.loads(INPUT_MANIFEST.read_text(encoding="utf-8"))
uid = env.uid  # noqa: F821
bulk_load(INPUT_CSV, "tmp_legacy_purchase_contract", COLUMNS)

env.cr.execute("SELECT COUNT(*) FROM sc_legacy_purchase_contract_fact")  # noqa: F821
before = env.cr.fetchone()[0]  # noqa: F821

env.cr.execute(  # noqa: F821
    """
    INSERT INTO sc_legacy_purchase_contract_fact (
      legacy_record_id, legacy_pid, source_dataset, document_no,
      document_state, submitted_time, applicant_name,
      applicant_department_legacy_id, applicant_department, project_legacy_id,
      project_name, project_id, contract_name, contract_no, signing_place,
      contract_type_legacy_id, contract_type, completion_date,
      expected_sign_date, total_amount, currency_legacy_id, currency_name,
      prepayment_amount, install_debug_payment, warranty_deposit,
      payment_terms, partner_legacy_id, partner_name, contact_name,
      contact_phone, bank_name, bank_account, sign_status, purchase_engineer,
      special_condition, attachment_ref, person_legacy_id,
      creator_legacy_user_id, creator_name, created_time,
      modifier_legacy_user_id, modifier_name, modified_time,
      is_supplement_contract, related_contract_legacy_id,
      related_contract_no, contract_attribute, credit_code, tax_rate, note,
      source_table, active, create_uid, create_date, write_uid, write_date
    )
    SELECT
      t.legacy_record_id,
      NULLIF(t.legacy_pid, ''),
      NULLIF(t.source_dataset, ''),
      NULLIF(t.document_no, ''),
      NULLIF(t.document_state, ''),
      NULLIF(t.submitted_time, '')::timestamp,
      NULLIF(t.applicant_name, ''),
      NULLIF(t.applicant_department_legacy_id, ''),
      NULLIF(t.applicant_department, ''),
      NULLIF(t.project_legacy_id, ''),
      NULLIF(t.project_name, ''),
      project.id,
      NULLIF(t.contract_name, ''),
      NULLIF(t.contract_no, ''),
      NULLIF(t.signing_place, ''),
      NULLIF(t.contract_type_legacy_id, ''),
      NULLIF(t.contract_type, ''),
      NULLIF(t.completion_date, '')::timestamp,
      NULLIF(t.expected_sign_date, '')::timestamp,
      COALESCE(NULLIF(t.total_amount, '')::numeric, 0),
      NULLIF(t.currency_legacy_id, ''),
      NULLIF(t.currency_name, ''),
      COALESCE(NULLIF(t.prepayment_amount, '')::numeric, 0),
      COALESCE(NULLIF(t.install_debug_payment, '')::numeric, 0),
      COALESCE(NULLIF(t.warranty_deposit, '')::numeric, 0),
      NULLIF(t.payment_terms, ''),
      NULLIF(t.partner_legacy_id, ''),
      NULLIF(t.partner_name, ''),
      NULLIF(t.contact_name, ''),
      NULLIF(t.contact_phone, ''),
      NULLIF(t.bank_name, ''),
      NULLIF(t.bank_account, ''),
      NULLIF(t.sign_status, ''),
      NULLIF(t.purchase_engineer, ''),
      NULLIF(t.special_condition, ''),
      NULLIF(t.attachment_ref, ''),
      NULLIF(t.person_legacy_id, ''),
      NULLIF(t.creator_legacy_user_id, ''),
      NULLIF(t.creator_name, ''),
      NULLIF(t.created_time, '')::timestamp,
      NULLIF(t.modifier_legacy_user_id, ''),
      NULLIF(t.modifier_name, ''),
      NULLIF(t.modified_time, '')::timestamp,
      NULLIF(t.is_supplement_contract, ''),
      NULLIF(t.related_contract_legacy_id, ''),
      NULLIF(t.related_contract_no, ''),
      NULLIF(t.contract_attribute, ''),
      NULLIF(t.credit_code, ''),
      COALESCE(NULLIF(t.tax_rate, '')::numeric, 0),
      NULLIF(t.note, ''),
      'T_CGHT_INFO',
      COALESCE(NULLIF(t.active, ''), '1') = '1',
      %s, NOW(), %s, NOW()
    FROM tmp_legacy_purchase_contract t
    LEFT JOIN (
      SELECT DISTINCT ON (legacy_project_id) legacy_project_id, id
      FROM project_project
      WHERE legacy_project_id IS NOT NULL
      ORDER BY legacy_project_id, id
    ) project ON project.legacy_project_id = NULLIF(t.project_legacy_id, '')
    ON CONFLICT (legacy_record_id) DO UPDATE SET
      legacy_pid = EXCLUDED.legacy_pid,
      source_dataset = EXCLUDED.source_dataset,
      document_no = EXCLUDED.document_no,
      document_state = EXCLUDED.document_state,
      submitted_time = EXCLUDED.submitted_time,
      applicant_name = EXCLUDED.applicant_name,
      applicant_department_legacy_id = EXCLUDED.applicant_department_legacy_id,
      applicant_department = EXCLUDED.applicant_department,
      project_legacy_id = EXCLUDED.project_legacy_id,
      project_name = EXCLUDED.project_name,
      project_id = EXCLUDED.project_id,
      contract_name = EXCLUDED.contract_name,
      contract_no = EXCLUDED.contract_no,
      signing_place = EXCLUDED.signing_place,
      contract_type_legacy_id = EXCLUDED.contract_type_legacy_id,
      contract_type = EXCLUDED.contract_type,
      completion_date = EXCLUDED.completion_date,
      expected_sign_date = EXCLUDED.expected_sign_date,
      total_amount = EXCLUDED.total_amount,
      currency_legacy_id = EXCLUDED.currency_legacy_id,
      currency_name = EXCLUDED.currency_name,
      prepayment_amount = EXCLUDED.prepayment_amount,
      install_debug_payment = EXCLUDED.install_debug_payment,
      warranty_deposit = EXCLUDED.warranty_deposit,
      payment_terms = EXCLUDED.payment_terms,
      partner_legacy_id = EXCLUDED.partner_legacy_id,
      partner_name = EXCLUDED.partner_name,
      contact_name = EXCLUDED.contact_name,
      contact_phone = EXCLUDED.contact_phone,
      bank_name = EXCLUDED.bank_name,
      bank_account = EXCLUDED.bank_account,
      sign_status = EXCLUDED.sign_status,
      purchase_engineer = EXCLUDED.purchase_engineer,
      special_condition = EXCLUDED.special_condition,
      attachment_ref = EXCLUDED.attachment_ref,
      person_legacy_id = EXCLUDED.person_legacy_id,
      creator_legacy_user_id = EXCLUDED.creator_legacy_user_id,
      creator_name = EXCLUDED.creator_name,
      created_time = EXCLUDED.created_time,
      modifier_legacy_user_id = EXCLUDED.modifier_legacy_user_id,
      modifier_name = EXCLUDED.modifier_name,
      modified_time = EXCLUDED.modified_time,
      is_supplement_contract = EXCLUDED.is_supplement_contract,
      related_contract_legacy_id = EXCLUDED.related_contract_legacy_id,
      related_contract_no = EXCLUDED.related_contract_no,
      contract_attribute = EXCLUDED.contract_attribute,
      credit_code = EXCLUDED.credit_code,
      tax_rate = EXCLUDED.tax_rate,
      note = EXCLUDED.note,
      source_table = EXCLUDED.source_table,
      active = EXCLUDED.active,
      write_uid = EXCLUDED.write_uid,
      write_date = NOW()
    """,
    [uid, uid],
)
env.cr.commit()  # noqa: F821

env.cr.execute("SELECT COUNT(*) FROM sc_legacy_purchase_contract_fact")  # noqa: F821
after = env.cr.fetchone()[0]  # noqa: F821
env.cr.execute("SELECT COUNT(*) FROM sc_legacy_purchase_contract_fact WHERE active")  # noqa: F821
active_rows = env.cr.fetchone()[0]  # noqa: F821
env.cr.execute("SELECT COUNT(*) FROM sc_legacy_purchase_contract_fact WHERE project_id IS NOT NULL")  # noqa: F821
project_linked = env.cr.fetchone()[0]  # noqa: F821
env.cr.execute("SELECT COALESCE(SUM(total_amount), 0) FROM sc_legacy_purchase_contract_fact")  # noqa: F821
amount_sum = env.cr.fetchone()[0]  # noqa: F821

payload = {
    "status": "PASS",
    "mode": "fresh_db_legacy_purchase_contract_replay_write",
    "database": env.cr.dbname,  # noqa: F821
    "input_rows": manifest.get("total_rows"),
    "before": before,
    "after": after,
    "delta": after - before,
    "active_rows": active_rows,
    "project_linked": project_linked,
    "amount_sum": str(amount_sum),
    "db_writes": max(after - before, 0),
    "decision": "legacy_purchase_contract_replay_complete",
}
write_json(OUTPUT_JSON, payload)
print("FRESH_DB_LEGACY_PURCHASE_CONTRACT_REPLAY_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
