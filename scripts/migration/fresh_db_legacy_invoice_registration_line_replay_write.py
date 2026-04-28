#!/usr/bin/env python3
"""Replay legacy invoice registration line facts into a neutral carrier model."""

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
        if (candidate / "artifacts/migration/fresh_db_legacy_invoice_registration_line_replay_adapter_result_v1.json").exists():
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
INPUT_MANIFEST = REPO_ROOT / "artifacts/migration/fresh_db_legacy_invoice_registration_line_replay_adapter_result_v1.json"
INPUT_CSV = REPO_ROOT / "artifacts/migration/fresh_db_legacy_invoice_registration_line_replay_payload_v1.csv"
OUTPUT_JSON = ARTIFACT_ROOT / "fresh_db_legacy_invoice_registration_line_replay_write_result_v1.json"

COLUMNS = [
    "legacy_line_id",
    "legacy_header_id",
    "legacy_pid",
    "legacy_header_pid",
    "project_legacy_id",
    "project_name",
    "fee_project_legacy_id",
    "fee_project_name",
    "document_no",
    "document_date",
    "invoice_date",
    "recognition_date",
    "invoice_no",
    "invoice_code",
    "invoice_type",
    "invoice_type_id",
    "supplier_legacy_id",
    "supplier_name",
    "supplier_tax_no",
    "amount_no_tax",
    "tax_amount",
    "amount_total",
    "tax_rate",
    "tax_rate_id",
    "quantity",
    "invoice_content",
    "cost_category_id",
    "cost_category_name",
    "contract_legacy_id",
    "settlement_legacy_id",
    "related_invoice_line_id",
    "related_invoice_line_no",
    "handler_name",
    "header_state",
    "creator_legacy_user_id",
    "creator_name",
    "created_time",
    "modified_time",
    "invoice_holder",
    "accounting_state",
    "checksum",
    "voucher_no",
    "invoice_source",
    "project_cost_amount",
    "billing_unit",
    "attachment_ref",
    "attachment_name",
    "attachment_path",
    "note",
    "active",
]

ensure_allowed_db()
manifest = json.loads(INPUT_MANIFEST.read_text(encoding="utf-8"))
uid = env.uid  # noqa: F821

bulk_load(INPUT_CSV, "tmp_legacy_invoice_registration_line", COLUMNS)

env.cr.execute("SELECT COUNT(*) FROM sc_legacy_invoice_registration_line")  # noqa: F821
before = env.cr.fetchone()[0]  # noqa: F821

env.cr.execute(  # noqa: F821
    """
    INSERT INTO sc_legacy_invoice_registration_line (
      legacy_line_id, legacy_header_id, legacy_pid, legacy_header_pid,
      project_legacy_id, project_name, project_id, fee_project_legacy_id,
      fee_project_name, document_no, document_date, invoice_date, recognition_date, invoice_no, invoice_code, invoice_type,
      invoice_type_id, supplier_legacy_id, supplier_name, supplier_tax_no,
      partner_id, amount_no_tax, tax_amount, amount_total, tax_rate, tax_rate_id,
      quantity, invoice_content, cost_category_id, cost_category_name,
      contract_legacy_id, settlement_legacy_id, related_invoice_line_id,
      related_invoice_line_no, handler_name, header_state,
      creator_legacy_user_id, creator_name, created_time, modified_time,
      invoice_holder, accounting_state, checksum, voucher_no, invoice_source,
      project_cost_amount, billing_unit, attachment_ref, attachment_name,
      attachment_path, note, source_table, active, create_uid, create_date,
      write_uid, write_date
    )
    SELECT
      t.legacy_line_id,
      NULLIF(t.legacy_header_id, ''),
      NULLIF(t.legacy_pid, ''),
      NULLIF(t.legacy_header_pid, ''),
      NULLIF(t.project_legacy_id, ''),
      NULLIF(t.project_name, ''),
      project.id,
      NULLIF(t.fee_project_legacy_id, ''),
      NULLIF(t.fee_project_name, ''),
      NULLIF(t.document_no, ''),
      NULLIF(t.document_date, '')::timestamp,
      NULLIF(t.invoice_date, '')::timestamp,
      NULLIF(t.recognition_date, '')::timestamp,
      NULLIF(t.invoice_no, ''),
      NULLIF(t.invoice_code, ''),
      NULLIF(t.invoice_type, ''),
      NULLIF(t.invoice_type_id, ''),
      NULLIF(t.supplier_legacy_id, ''),
      NULLIF(t.supplier_name, ''),
      NULLIF(t.supplier_tax_no, ''),
      partner.id,
      COALESCE(NULLIF(t.amount_no_tax, '')::numeric, 0),
      COALESCE(NULLIF(t.tax_amount, '')::numeric, 0),
      COALESCE(NULLIF(t.amount_total, '')::numeric, 0),
      NULLIF(t.tax_rate, ''),
      NULLIF(t.tax_rate_id, ''),
      COALESCE(NULLIF(t.quantity, '')::numeric, 0),
      NULLIF(t.invoice_content, ''),
      NULLIF(t.cost_category_id, ''),
      NULLIF(t.cost_category_name, ''),
      NULLIF(t.contract_legacy_id, ''),
      NULLIF(t.settlement_legacy_id, ''),
      NULLIF(t.related_invoice_line_id, ''),
      NULLIF(t.related_invoice_line_no, ''),
      NULLIF(t.handler_name, ''),
      NULLIF(t.header_state, ''),
      NULLIF(t.creator_legacy_user_id, ''),
      NULLIF(t.creator_name, ''),
      NULLIF(t.created_time, '')::timestamp,
      NULLIF(t.modified_time, '')::timestamp,
      NULLIF(t.invoice_holder, ''),
      NULLIF(t.accounting_state, ''),
      NULLIF(t.checksum, ''),
      NULLIF(t.voucher_no, ''),
      NULLIF(t.invoice_source, ''),
      COALESCE(NULLIF(t.project_cost_amount, '')::numeric, 0),
      NULLIF(t.billing_unit, ''),
      NULLIF(t.attachment_ref, ''),
      NULLIF(t.attachment_name, ''),
      NULLIF(t.attachment_path, ''),
      NULLIF(t.note, ''),
      'C_JXXP_ZYFPJJD_CB',
      COALESCE(NULLIF(t.active, ''), '1') = '1',
      %s, NOW(), %s, NOW()
    FROM tmp_legacy_invoice_registration_line t
    LEFT JOIN project_project project ON project.legacy_project_id = NULLIF(t.project_legacy_id, '')
    LEFT JOIN (
      SELECT legacy_partner_id, MIN(id) AS id
      FROM res_partner
      WHERE legacy_partner_id IS NOT NULL
      GROUP BY legacy_partner_id
    ) partner ON partner.legacy_partner_id = NULLIF(t.supplier_legacy_id, '')
    ON CONFLICT (legacy_line_id) DO UPDATE SET
      legacy_header_id = EXCLUDED.legacy_header_id,
      legacy_pid = EXCLUDED.legacy_pid,
      legacy_header_pid = EXCLUDED.legacy_header_pid,
      project_legacy_id = EXCLUDED.project_legacy_id,
      project_name = EXCLUDED.project_name,
      project_id = EXCLUDED.project_id,
      fee_project_legacy_id = EXCLUDED.fee_project_legacy_id,
      fee_project_name = EXCLUDED.fee_project_name,
      document_no = EXCLUDED.document_no,
      document_date = EXCLUDED.document_date,
      invoice_date = EXCLUDED.invoice_date,
      recognition_date = EXCLUDED.recognition_date,
      invoice_no = EXCLUDED.invoice_no,
      invoice_code = EXCLUDED.invoice_code,
      invoice_type = EXCLUDED.invoice_type,
      invoice_type_id = EXCLUDED.invoice_type_id,
      supplier_legacy_id = EXCLUDED.supplier_legacy_id,
      supplier_name = EXCLUDED.supplier_name,
      supplier_tax_no = EXCLUDED.supplier_tax_no,
      partner_id = EXCLUDED.partner_id,
      amount_no_tax = EXCLUDED.amount_no_tax,
      tax_amount = EXCLUDED.tax_amount,
      amount_total = EXCLUDED.amount_total,
      tax_rate = EXCLUDED.tax_rate,
      tax_rate_id = EXCLUDED.tax_rate_id,
      quantity = EXCLUDED.quantity,
      invoice_content = EXCLUDED.invoice_content,
      cost_category_id = EXCLUDED.cost_category_id,
      cost_category_name = EXCLUDED.cost_category_name,
      contract_legacy_id = EXCLUDED.contract_legacy_id,
      settlement_legacy_id = EXCLUDED.settlement_legacy_id,
      related_invoice_line_id = EXCLUDED.related_invoice_line_id,
      related_invoice_line_no = EXCLUDED.related_invoice_line_no,
      handler_name = EXCLUDED.handler_name,
      header_state = EXCLUDED.header_state,
      creator_legacy_user_id = EXCLUDED.creator_legacy_user_id,
      creator_name = EXCLUDED.creator_name,
      created_time = EXCLUDED.created_time,
      modified_time = EXCLUDED.modified_time,
      invoice_holder = EXCLUDED.invoice_holder,
      accounting_state = EXCLUDED.accounting_state,
      checksum = EXCLUDED.checksum,
      voucher_no = EXCLUDED.voucher_no,
      invoice_source = EXCLUDED.invoice_source,
      project_cost_amount = EXCLUDED.project_cost_amount,
      billing_unit = EXCLUDED.billing_unit,
      attachment_ref = EXCLUDED.attachment_ref,
      attachment_name = EXCLUDED.attachment_name,
      attachment_path = EXCLUDED.attachment_path,
      note = EXCLUDED.note,
      active = EXCLUDED.active,
      write_uid = EXCLUDED.write_uid,
      write_date = NOW()
    """,
    [uid, uid],
)

env.cr.commit()  # noqa: F821

env.cr.execute("SELECT COUNT(*) FROM sc_legacy_invoice_registration_line")  # noqa: F821
after = env.cr.fetchone()[0]  # noqa: F821
env.cr.execute("SELECT COUNT(*) FROM sc_legacy_invoice_registration_line WHERE active")  # noqa: F821
active_rows = env.cr.fetchone()[0]  # noqa: F821
env.cr.execute("SELECT COUNT(*) FROM sc_legacy_invoice_registration_line WHERE project_id IS NOT NULL")  # noqa: F821
project_linked = env.cr.fetchone()[0]  # noqa: F821
env.cr.execute("SELECT COUNT(*) FROM sc_legacy_invoice_registration_line WHERE partner_id IS NOT NULL")  # noqa: F821
partner_linked = env.cr.fetchone()[0]  # noqa: F821
env.cr.execute("SELECT COALESCE(SUM(amount_no_tax), 0), COALESCE(SUM(tax_amount), 0), COALESCE(SUM(amount_total), 0) FROM sc_legacy_invoice_registration_line")  # noqa: F821
amount_no_tax, tax_amount, amount_total = env.cr.fetchone()  # noqa: F821

payload = {
    "status": "PASS",
    "mode": "fresh_db_legacy_invoice_registration_line_replay_write",
    "database": env.cr.dbname,  # noqa: F821
    "input_rows": manifest.get("total_rows"),
    "before": before,
    "after": after,
    "delta": after - before,
    "active_rows": active_rows,
    "project_linked": project_linked,
    "partner_linked": partner_linked,
    "amount_no_tax": str(amount_no_tax),
    "tax_amount": str(tax_amount),
    "amount_total": str(amount_total),
    "db_writes": max(after - before, 0),
    "decision": "legacy_invoice_registration_line_replay_complete",
}
write_json(OUTPUT_JSON, payload)
print("FRESH_DB_LEGACY_INVOICE_REGISTRATION_LINE_REPLAY_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
