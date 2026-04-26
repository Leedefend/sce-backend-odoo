#!/usr/bin/env python3
"""Project legacy invoice registration and tax facts into runtime invoice registration."""

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
output_json = artifact_root / "fresh_db_invoice_registration_projection_write_result_v1.json"
currency_id = env.company.currency_id.id  # noqa: F821
before = int(scalar("SELECT COUNT(*) FROM sc_invoice_registration") or 0)

env.cr.execute(  # noqa: F821
    """
    INSERT INTO sc_invoice_registration (
      name, source_origin, source_kind, direction, state, project_id, partner_id,
      contract_id, document_no, document_date, invoice_date, recognition_date,
      invoice_no, invoice_code, invoice_type, tax_rate, invoice_content,
      cost_category_name, amount_no_tax, tax_amount, amount_total, currency_id,
      handler_name, invoice_holder, accounting_state, voucher_no,
      legacy_source_model, legacy_source_table, legacy_record_id,
      legacy_document_state, legacy_partner_id, legacy_partner_name,
      legacy_partner_tax_no, legacy_attachment_ref, note, active,
      create_uid, write_uid, create_date, write_date
    )
    SELECT
      COALESCE(NULLIF(l.invoice_no, ''), NULLIF(l.document_no, ''), 'LEGACY-INVOICE-' || l.legacy_line_id),
      'legacy',
      'invoice_registration',
      'input',
      CASE WHEN COALESCE(l.header_state, '') = '2' THEN 'legacy_confirmed' ELSE 'draft' END,
      l.project_id,
      l.partner_id,
      c.id,
      NULLIF(l.document_no, ''),
      l.document_date::date,
      COALESCE(l.invoice_date::date, l.document_date::date, l.created_time::date, CURRENT_DATE),
      l.recognition_date::date,
      NULLIF(l.invoice_no, ''),
      NULLIF(l.invoice_code, ''),
      NULLIF(l.invoice_type, ''),
      NULLIF(l.tax_rate, ''),
      NULLIF(l.invoice_content, ''),
      NULLIF(l.cost_category_name, ''),
      GREATEST(COALESCE(l.amount_no_tax, 0), 0),
      GREATEST(COALESCE(l.tax_amount, 0), 0),
      GREATEST(COALESCE(l.amount_total, COALESCE(l.amount_no_tax, 0) + COALESCE(l.tax_amount, 0)), 0),
      %s,
      NULLIF(l.handler_name, ''),
      NULLIF(l.invoice_holder, ''),
      NULLIF(l.accounting_state, ''),
      NULLIF(l.voucher_no, ''),
      'sc.legacy.invoice.registration.line',
      l.source_table,
      l.legacy_line_id,
      NULLIF(l.header_state, ''),
      NULLIF(l.supplier_legacy_id, ''),
      NULLIF(l.supplier_name, ''),
      NULLIF(l.supplier_tax_no, ''),
      COALESCE(NULLIF(l.attachment_ref, ''), NULLIF(l.attachment_path, ''), NULLIF(l.attachment_name, '')),
      CONCAT_WS(E'\n',
        '[migration:invoice_registration] legacy_line_id=' || l.legacy_line_id,
        NULLIF(l.project_name, ''),
        NULLIF(l.supplier_name, ''),
        NULLIF(l.invoice_source, ''),
        NULLIF(l.note, '')
      ),
      l.active,
      1,
      1,
      NOW(),
      NOW()
    FROM sc_legacy_invoice_registration_line l
    LEFT JOIN (
      SELECT DISTINCT ON (legacy_contract_id) legacy_contract_id, id
      FROM construction_contract
      WHERE legacy_contract_id IS NOT NULL
      ORDER BY legacy_contract_id, id
    ) c ON c.legacy_contract_id = l.contract_legacy_id
    WHERE l.active
      AND l.project_id IS NOT NULL
      AND (
        GREATEST(COALESCE(l.amount_total, 0), 0) > 0
        OR GREATEST(COALESCE(l.amount_no_tax, 0), 0) > 0
        OR GREATEST(COALESCE(l.tax_amount, 0), 0) > 0
      )
    ON CONFLICT (legacy_source_model, legacy_record_id)
    DO UPDATE SET
      state = EXCLUDED.state,
      project_id = EXCLUDED.project_id,
      partner_id = EXCLUDED.partner_id,
      contract_id = EXCLUDED.contract_id,
      document_no = EXCLUDED.document_no,
      document_date = EXCLUDED.document_date,
      invoice_date = EXCLUDED.invoice_date,
      recognition_date = EXCLUDED.recognition_date,
      invoice_no = EXCLUDED.invoice_no,
      invoice_code = EXCLUDED.invoice_code,
      invoice_type = EXCLUDED.invoice_type,
      tax_rate = EXCLUDED.tax_rate,
      invoice_content = EXCLUDED.invoice_content,
      cost_category_name = EXCLUDED.cost_category_name,
      amount_no_tax = EXCLUDED.amount_no_tax,
      tax_amount = EXCLUDED.tax_amount,
      amount_total = EXCLUDED.amount_total,
      handler_name = EXCLUDED.handler_name,
      invoice_holder = EXCLUDED.invoice_holder,
      accounting_state = EXCLUDED.accounting_state,
      voucher_no = EXCLUDED.voucher_no,
      legacy_document_state = EXCLUDED.legacy_document_state,
      legacy_partner_id = EXCLUDED.legacy_partner_id,
      legacy_partner_name = EXCLUDED.legacy_partner_name,
      legacy_partner_tax_no = EXCLUDED.legacy_partner_tax_no,
      legacy_attachment_ref = EXCLUDED.legacy_attachment_ref,
      note = EXCLUDED.note,
      active = EXCLUDED.active,
      write_uid = 1,
      write_date = NOW()
    """,
    [currency_id],
)

env.cr.execute(  # noqa: F821
    """
    INSERT INTO sc_invoice_registration (
      name, source_origin, source_kind, direction, state, project_id,
      document_no, document_date, invoice_date, invoice_type,
      amount_no_tax, tax_amount, amount_total, currency_id,
      legacy_source_model, legacy_source_table, legacy_record_id,
      legacy_document_state, legacy_partner_id, legacy_partner_name,
      legacy_partner_tax_no, note, active, create_uid, write_uid, create_date, write_date
    )
    SELECT
      COALESCE(NULLIF(f.document_no, ''), 'LEGACY-TAX-' || f.legacy_record_id),
      'legacy',
      CASE
        WHEN f.direction = 'output_invoice' THEN 'output_invoice_tax'
        WHEN f.direction = 'prepaid_tax' THEN 'prepaid_tax'
        ELSE 'input_invoice_tax'
      END,
      CASE
        WHEN f.direction = 'output_invoice' THEN 'output'
        WHEN f.direction = 'prepaid_tax' THEN 'prepaid'
        WHEN f.direction = 'input_invoice' THEN 'input'
        ELSE 'unknown'
      END,
      CASE WHEN COALESCE(f.legacy_state, '') = '2' THEN 'legacy_confirmed' ELSE 'draft' END,
      f.project_id,
      NULLIF(f.document_no, ''),
      f.document_date,
      COALESCE(f.document_date, CURRENT_DATE),
      NULLIF(f.invoice_type, ''),
      GREATEST(COALESCE(f.source_amount, 0) - COALESCE(f.source_tax_amount, 0), 0),
      GREATEST(COALESCE(f.source_tax_amount, 0), 0),
      GREATEST(COALESCE(f.source_amount, 0), 0),
      %s,
      'sc.legacy.invoice.tax.fact',
      f.legacy_source_table,
      f.legacy_record_id,
      NULLIF(f.legacy_state, ''),
      NULLIF(f.legacy_partner_id, ''),
      NULLIF(f.legacy_partner_name, ''),
      NULLIF(f.legacy_partner_tax_no, ''),
      CONCAT_WS(E'\n',
        '[migration:invoice_registration_tax] legacy_record_id=' || f.legacy_record_id,
        NULLIF(f.direction, ''),
        NULLIF(f.source_family, ''),
        NULLIF(f.legacy_project_name, ''),
        NULLIF(f.legacy_partner_name, ''),
        NULLIF(f.note, '')
      ),
      TRUE,
      1,
      1,
      NOW(),
      NOW()
    FROM sc_legacy_invoice_tax_fact f
    WHERE f.project_id IS NOT NULL
      AND (GREATEST(COALESCE(f.source_amount, 0), 0) > 0 OR GREATEST(COALESCE(f.source_tax_amount, 0), 0) > 0)
    ON CONFLICT (legacy_source_model, legacy_record_id)
    DO UPDATE SET
      source_kind = EXCLUDED.source_kind,
      direction = EXCLUDED.direction,
      state = EXCLUDED.state,
      project_id = EXCLUDED.project_id,
      document_no = EXCLUDED.document_no,
      document_date = EXCLUDED.document_date,
      invoice_date = EXCLUDED.invoice_date,
      invoice_type = EXCLUDED.invoice_type,
      amount_no_tax = EXCLUDED.amount_no_tax,
      tax_amount = EXCLUDED.tax_amount,
      amount_total = EXCLUDED.amount_total,
      legacy_document_state = EXCLUDED.legacy_document_state,
      legacy_partner_id = EXCLUDED.legacy_partner_id,
      legacy_partner_name = EXCLUDED.legacy_partner_name,
      legacy_partner_tax_no = EXCLUDED.legacy_partner_tax_no,
      note = EXCLUDED.note,
      active = EXCLUDED.active,
      write_uid = 1,
      write_date = NOW()
    """,
    [currency_id],
)

env.cr.commit()  # noqa: F821

after = int(scalar("SELECT COUNT(*) FROM sc_invoice_registration") or 0)
payload = {
    "status": "PASS",
    "mode": "fresh_db_invoice_registration_projection_write",
    "database": env.cr.dbname,  # noqa: F821
    "before": before,
    "after": after,
    "delta": after - before,
    "legacy_rows": int(scalar("SELECT COUNT(*) FROM sc_invoice_registration WHERE source_origin = 'legacy'") or 0),
    "legacy_with_project": int(
        scalar("SELECT COUNT(*) FROM sc_invoice_registration WHERE source_origin = 'legacy' AND project_id IS NOT NULL")
        or 0
    ),
    "legacy_with_partner": int(
        scalar("SELECT COUNT(*) FROM sc_invoice_registration WHERE source_origin = 'legacy' AND partner_id IS NOT NULL")
        or 0
    ),
    "legacy_invoice_registration": int(
        scalar(
            "SELECT COUNT(*) FROM sc_invoice_registration WHERE legacy_source_model = 'sc.legacy.invoice.registration.line'"
        )
        or 0
    ),
    "legacy_invoice_tax": int(
        scalar("SELECT COUNT(*) FROM sc_invoice_registration WHERE legacy_source_model = 'sc.legacy.invoice.tax.fact'")
        or 0
    ),
    "legacy_confirmed": int(
        scalar("SELECT COUNT(*) FROM sc_invoice_registration WHERE source_origin = 'legacy' AND state = 'legacy_confirmed'")
        or 0
    ),
    "legacy_amount_total_sum": float(
        scalar("SELECT COALESCE(SUM(amount_total), 0) FROM sc_invoice_registration WHERE source_origin = 'legacy'") or 0
    ),
    "legacy_tax_amount_sum": float(
        scalar("SELECT COALESCE(SUM(tax_amount), 0) FROM sc_invoice_registration WHERE source_origin = 'legacy'") or 0
    ),
}
write_json(output_json, payload)
print("INVOICE_REGISTRATION_PROJECTION_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
