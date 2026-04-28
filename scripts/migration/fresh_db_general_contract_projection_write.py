#!/usr/bin/env python3
"""Project legacy purchase/general contract facts into runtime general contracts."""

from __future__ import annotations

import json
import os
from pathlib import Path


def resolve_artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.append(Path("/mnt/artifacts/migration"))
    candidates.append(Path(f"/tmp/history_continuity/{env.cr.dbname}/adhoc"))  # noqa: F821
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return candidate
        except Exception:
            continue
    return Path(f"/tmp/history_continuity/{env.cr.dbname}/adhoc")  # noqa: F821


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def scalar(sql: str) -> object:
    env.cr.execute(sql)  # noqa: F821
    row = env.cr.fetchone()  # noqa: F821
    return row[0] if row else None


allowlist = {item.strip() for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "").split(",") if item.strip()}
if allowlist and env.cr.dbname not in allowlist:  # noqa: F821
    raise RuntimeError({"db_name_not_allowed_for_replay": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821

artifact_root = resolve_artifact_root()
output_json = artifact_root / "fresh_db_general_contract_projection_write_result_v1.json"
currency_id = env.company.currency_id.id  # noqa: F821
before = int(scalar("SELECT COUNT(*) FROM sc_general_contract") or 0)

env.cr.execute(  # noqa: F821
    """
    INSERT INTO sc_general_contract (
      name, source_origin, state, project_id, partner_name_text, credit_code,
      contact_name, contact_phone, bank_name, bank_account, document_no,
      contract_no, contract_name, contract_type, contract_attribute,
      signing_place, contract_date, expected_sign_date, completion_date,
      amount_total, prepayment_amount, install_debug_payment,
      warranty_deposit, tax_rate, currency_id, payment_terms,
      special_condition, applicant_name, applicant_department,
      purchase_engineer, related_contract_no, is_supplement_contract,
      legacy_source_model, legacy_source_table, legacy_record_id,
      legacy_document_state, legacy_attachment_ref, note, active,
      create_uid, write_uid, create_date, write_date
    )
    SELECT
      COALESCE(NULLIF(f.document_no, ''), NULLIF(f.contract_no, ''), 'LEGACY-GENERAL-CONTRACT-' || f.legacy_record_id),
      'legacy',
      CASE WHEN COALESCE(f.document_state, '') = '2' THEN 'legacy_confirmed' ELSE 'draft' END,
      f.project_id,
      NULLIF(f.partner_name, ''),
      NULLIF(f.credit_code, ''),
      NULLIF(f.contact_name, ''),
      NULLIF(f.contact_phone, ''),
      NULLIF(f.bank_name, ''),
      NULLIF(f.bank_account, ''),
      NULLIF(f.document_no, ''),
      NULLIF(f.contract_no, ''),
      COALESCE(NULLIF(f.contract_name, ''), NULLIF(f.document_no, ''), '历史综合合同'),
      NULLIF(f.contract_type, ''),
      NULLIF(f.contract_attribute, ''),
      NULLIF(f.signing_place, ''),
      COALESCE(f.expected_sign_date::date, f.submitted_time::date, f.created_time::date, CURRENT_DATE),
      f.expected_sign_date::date,
      f.completion_date::date,
      GREATEST(COALESCE(f.total_amount, 0), 0),
      GREATEST(COALESCE(f.prepayment_amount, 0), 0),
      GREATEST(COALESCE(f.install_debug_payment, 0), 0),
      GREATEST(COALESCE(f.warranty_deposit, 0), 0),
      COALESCE(f.tax_rate, 0),
      %s,
      NULLIF(f.payment_terms, ''),
      NULLIF(f.special_condition, ''),
      NULLIF(f.applicant_name, ''),
      NULLIF(f.applicant_department, ''),
      NULLIF(f.purchase_engineer, ''),
      NULLIF(f.related_contract_no, ''),
      NULLIF(f.is_supplement_contract, ''),
      'sc.legacy.purchase.contract.fact',
      f.source_table,
      f.legacy_record_id,
      NULLIF(f.document_state, ''),
      NULLIF(f.attachment_ref, ''),
      CONCAT_WS(E'\n',
        '[migration:general_contract] legacy_record_id=' || f.legacy_record_id,
        NULLIF(f.project_name, ''),
        NULLIF(f.partner_name, ''),
        NULLIF(f.sign_status, ''),
        NULLIF(f.note, '')
      ),
      f.active,
      1,
      1,
      NOW(),
      NOW()
    FROM sc_legacy_purchase_contract_fact f
    WHERE f.active
      AND f.project_id IS NOT NULL
      AND GREATEST(COALESCE(f.total_amount, 0), 0) > 0
      AND COALESCE(NULLIF(f.contract_name, ''), NULLIF(f.document_no, '')) IS NOT NULL
    ON CONFLICT (legacy_source_model, legacy_record_id)
    DO UPDATE SET
      state = EXCLUDED.state,
      project_id = EXCLUDED.project_id,
      partner_name_text = EXCLUDED.partner_name_text,
      credit_code = EXCLUDED.credit_code,
      contact_name = EXCLUDED.contact_name,
      contact_phone = EXCLUDED.contact_phone,
      bank_name = EXCLUDED.bank_name,
      bank_account = EXCLUDED.bank_account,
      document_no = EXCLUDED.document_no,
      contract_no = EXCLUDED.contract_no,
      contract_name = EXCLUDED.contract_name,
      contract_type = EXCLUDED.contract_type,
      contract_attribute = EXCLUDED.contract_attribute,
      signing_place = EXCLUDED.signing_place,
      contract_date = EXCLUDED.contract_date,
      expected_sign_date = EXCLUDED.expected_sign_date,
      completion_date = EXCLUDED.completion_date,
      amount_total = EXCLUDED.amount_total,
      prepayment_amount = EXCLUDED.prepayment_amount,
      install_debug_payment = EXCLUDED.install_debug_payment,
      warranty_deposit = EXCLUDED.warranty_deposit,
      tax_rate = EXCLUDED.tax_rate,
      payment_terms = EXCLUDED.payment_terms,
      special_condition = EXCLUDED.special_condition,
      applicant_name = EXCLUDED.applicant_name,
      applicant_department = EXCLUDED.applicant_department,
      purchase_engineer = EXCLUDED.purchase_engineer,
      related_contract_no = EXCLUDED.related_contract_no,
      is_supplement_contract = EXCLUDED.is_supplement_contract,
      legacy_document_state = EXCLUDED.legacy_document_state,
      legacy_attachment_ref = EXCLUDED.legacy_attachment_ref,
      note = EXCLUDED.note,
      active = EXCLUDED.active,
      write_uid = 1,
      write_date = NOW()
    """,
    [currency_id],
)

env.cr.commit()  # noqa: F821

after = int(scalar("SELECT COUNT(*) FROM sc_general_contract") or 0)
payload = {
    "status": "PASS",
    "mode": "fresh_db_general_contract_projection_write",
    "database": env.cr.dbname,  # noqa: F821
    "before": before,
    "after": after,
    "delta": after - before,
    "legacy_rows": int(scalar("SELECT COUNT(*) FROM sc_general_contract WHERE source_origin = 'legacy'") or 0),
    "legacy_with_project": int(
        scalar("SELECT COUNT(*) FROM sc_general_contract WHERE source_origin = 'legacy' AND project_id IS NOT NULL") or 0
    ),
    "legacy_with_partner_text": int(
        scalar(
            "SELECT COUNT(*) FROM sc_general_contract WHERE source_origin = 'legacy' AND COALESCE(partner_name_text, '') <> ''"
        )
        or 0
    ),
    "legacy_confirmed": int(
        scalar("SELECT COUNT(*) FROM sc_general_contract WHERE source_origin = 'legacy' AND state = 'legacy_confirmed'") or 0
    ),
    "legacy_attachment_refs": int(
        scalar(
            "SELECT COUNT(*) FROM sc_general_contract WHERE source_origin = 'legacy' AND COALESCE(legacy_attachment_ref, '') <> ''"
        )
        or 0
    ),
    "legacy_amount_sum": float(
        scalar("SELECT COALESCE(SUM(amount_total), 0) FROM sc_general_contract WHERE source_origin = 'legacy'") or 0
    ),
}
write_json(output_json, payload)
print("GENERAL_CONTRACT_PROJECTION_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
