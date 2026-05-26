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
default_issue_company_name = env.company.name  # noqa: F821
include_income_invoice_facts = os.getenv("INVOICE_REGISTRATION_INCLUDE_INCOME_INVOICE_FACTS") == "1"
before = int(scalar("SELECT COUNT(*) FROM sc_invoice_registration") or 0)

env.cr.execute(  # noqa: F821
    """
    ALTER TABLE sc_invoice_registration DROP CONSTRAINT IF EXISTS sc_invoice_registration_amount_no_tax_nonnegative;
    ALTER TABLE sc_invoice_registration DROP CONSTRAINT IF EXISTS sc_invoice_registration_tax_amount_nonnegative;
    ALTER TABLE sc_invoice_registration DROP CONSTRAINT IF EXISTS sc_invoice_registration_amount_total_nonnegative;
    """
)

env.cr.execute(  # noqa: F821
    """
    INSERT INTO sc_invoice_registration (
      name, source_origin, source_kind, direction, state, project_id, partner_id,
      contract_id, document_no, document_date, invoice_date, recognition_date,
      invoice_no, invoice_code, invoice_type, tax_rate, invoice_content,
      cost_category_name, invoice_issue_company, amount_no_tax, tax_amount, amount_total, currency_id,
      handler_name, invoice_holder, accounting_state, voucher_no,
      legacy_source_model, legacy_source_table, legacy_record_id,
      legacy_document_state, legacy_partner_id, legacy_partner_name,
      legacy_partner_tax_no, legacy_attachment_ref, creator_legacy_user_id,
      creator_name, created_time, note, active,
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
      NULLIF(l.billing_unit, ''),
      COALESCE(l.amount_no_tax, 0),
      COALESCE(l.tax_amount, 0),
      COALESCE(l.amount_total, COALESCE(l.amount_no_tax, 0) + COALESCE(l.tax_amount, 0)),
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
      NULLIF(l.creator_legacy_user_id, ''),
      NULLIF(l.creator_name, ''),
      l.created_time,
      CONCAT_WS(E'\n',
        '[migration:invoice_registration] legacy_line_id=' || l.legacy_line_id,
        CASE
          WHEN NULLIF(l.contract_legacy_id, '') IS NOT NULL AND LOWER(l.contract_legacy_id) <> 'null'
          THEN 'legacy_contract_id=' || l.contract_legacy_id
          ELSE NULL
        END,
        CASE WHEN NULLIF(l.voucher_no, '') IS NOT NULL THEN 'voucher_no=' || l.voucher_no ELSE NULL END,
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
        COALESCE(l.amount_total, 0) <> 0
        OR COALESCE(l.amount_no_tax, 0) <> 0
        OR COALESCE(l.tax_amount, 0) <> 0
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
      invoice_issue_company = EXCLUDED.invoice_issue_company,
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
      creator_legacy_user_id = EXCLUDED.creator_legacy_user_id,
      creator_name = EXCLUDED.creator_name,
      created_time = EXCLUDED.created_time,
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
      name, source_origin, source_kind, direction, state, project_id, partner_id,
      document_no, document_date, invoice_date, invoice_type,
      tax_rate, invoice_no, invoice_issue_company, push_result, kingdee_document_no,
      invoice_count, contract_amount, amount_no_tax, tax_amount, amount_total,
      surcharge_amount, related_receipt_amount, currency_id,
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
      partner_match.id,
      NULLIF(f.document_no, ''),
      f.document_date,
      COALESCE(f.document_date, CURRENT_DATE),
      NULLIF(f.invoice_type, ''),
      CASE
        WHEN COALESCE(f.source_tax_amount, 0) <> 0
         AND COALESCE(f.source_amount, 0) - COALESCE(f.source_tax_amount, 0) <> 0
        THEN RTRIM(RTRIM(TO_CHAR(ROUND(
          (
            ABS(COALESCE(f.source_tax_amount, 0))
            / NULLIF(ABS(COALESCE(f.source_amount, 0) - COALESCE(f.source_tax_amount, 0)), 0)
            * 100
          )::numeric,
          2
        ), 'FM999999990.00'), '0'), '.') || '%%'
        ELSE NULL
      END,
      NULLIF(surcharge.invoice_no, ''),
      CASE
        WHEN f.direction = 'output_invoice'
        THEN COALESCE(
          NULLIF(receipt_invoice.invoice_issue_company, ''),
          NULLIF(project_issue_company.invoice_issue_company, ''),
          NULLIF(%s, '')
        )
        ELSE NULL
      END,
      NULLIF(f.legacy_state, ''),
      NULLIF(f.document_no, ''),
      COALESCE(surcharge.invoice_count, 0),
      0,
      COALESCE(f.source_amount, 0) - COALESCE(f.source_tax_amount, 0),
      COALESCE(f.source_tax_amount, 0),
      COALESCE(f.source_amount, 0),
      COALESCE(surcharge.surcharge_amount, 0),
      0,
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
    LEFT JOIN LATERAL (
      SELECT
        MIN(NULLIF(s.invoice_no, '')) AS invoice_no,
        COUNT(DISTINCT NULLIF(s.invoice_no, ''))::integer AS invoice_count,
        COALESCE(SUM(s.surcharge_amount), 0) AS surcharge_amount
      FROM sc_legacy_invoice_surcharge_fact s
      WHERE s.active
        AND (
          (f.direction = 'output_invoice' AND s.direction = 'output')
          OR (f.direction = 'input_invoice' AND s.direction = 'input')
        )
        AND s.document_no = f.document_no
        AND (s.project_id = f.project_id OR s.project_id IS NULL OR f.project_id IS NULL)
    ) surcharge ON TRUE
    LEFT JOIN LATERAL (
      SELECT MIN(NULLIF(ril.invoice_issue_company, '')) AS invoice_issue_company
      FROM sc_legacy_invoice_surcharge_fact s2
      JOIN sc_receipt_invoice_line ril ON ril.active
        AND ril.invoice_no = s2.invoice_no
        AND NULLIF(ril.invoice_issue_company, '') IS NOT NULL
      WHERE s2.active
        AND f.direction = 'output_invoice'
        AND s2.direction = 'output'
        AND s2.document_no = f.document_no
        AND (s2.project_id = f.project_id OR s2.project_id IS NULL OR f.project_id IS NULL)
    ) receipt_invoice ON TRUE
    LEFT JOIN LATERAL (
      SELECT ranked.invoice_issue_company
      FROM (
        SELECT
          NULLIF(ril.invoice_issue_company, '') AS invoice_issue_company,
          COUNT(*) AS fact_count
        FROM sc_receipt_invoice_line ril
        WHERE ril.active
          AND f.direction = 'output_invoice'
          AND ril.project_id = f.project_id
          AND NULLIF(ril.invoice_issue_company, '') IS NOT NULL
        GROUP BY NULLIF(ril.invoice_issue_company, '')
      ) ranked
      ORDER BY ranked.fact_count DESC, ranked.invoice_issue_company
      LIMIT 1
    ) project_issue_company ON TRUE
    LEFT JOIN LATERAL (
      SELECT rp.id
        FROM res_partner rp
       WHERE rp.active
         AND (
           (f.legacy_partner_name IS NOT NULL AND rp.name = f.legacy_partner_name)
           OR (f.legacy_partner_tax_no IS NOT NULL AND rp.vat = f.legacy_partner_tax_no)
         )
       ORDER BY
         CASE WHEN f.legacy_partner_tax_no IS NOT NULL AND rp.vat = f.legacy_partner_tax_no THEN 0 ELSE 1 END,
         rp.id
       LIMIT 1
    ) partner_match ON TRUE
    WHERE f.project_id IS NOT NULL
      AND (COALESCE(f.source_amount, 0) <> 0 OR COALESCE(f.source_tax_amount, 0) <> 0)
    ON CONFLICT (legacy_source_model, legacy_record_id)
    DO UPDATE SET
      source_kind = EXCLUDED.source_kind,
      direction = EXCLUDED.direction,
      state = EXCLUDED.state,
      project_id = EXCLUDED.project_id,
      partner_id = EXCLUDED.partner_id,
      document_no = EXCLUDED.document_no,
      document_date = EXCLUDED.document_date,
      invoice_date = EXCLUDED.invoice_date,
      invoice_type = EXCLUDED.invoice_type,
      tax_rate = EXCLUDED.tax_rate,
      invoice_no = EXCLUDED.invoice_no,
      invoice_issue_company = EXCLUDED.invoice_issue_company,
      push_result = EXCLUDED.push_result,
      kingdee_document_no = EXCLUDED.kingdee_document_no,
      invoice_count = EXCLUDED.invoice_count,
      contract_amount = EXCLUDED.contract_amount,
      amount_no_tax = EXCLUDED.amount_no_tax,
      tax_amount = EXCLUDED.tax_amount,
      amount_total = EXCLUDED.amount_total,
      surcharge_amount = EXCLUDED.surcharge_amount,
      related_receipt_amount = EXCLUDED.related_receipt_amount,
      legacy_document_state = EXCLUDED.legacy_document_state,
      legacy_partner_id = EXCLUDED.legacy_partner_id,
      legacy_partner_name = EXCLUDED.legacy_partner_name,
      legacy_partner_tax_no = EXCLUDED.legacy_partner_tax_no,
      note = EXCLUDED.note,
      active = EXCLUDED.active,
      write_uid = 1,
      write_date = NOW()
    """,
    [default_issue_company_name, currency_id],
)

env.cr.execute(  # noqa: F821
    """
    INSERT INTO sc_invoice_registration (
      name, source_origin, source_kind, direction, state, project_id, partner_id,
      document_no, document_date, invoice_date, tax_type, prepaid_tax_date,
      tax_certificate_no, invoice_no, invoice_code, invoice_type, tax_rate, invoice_content,
      amount_no_tax, tax_amount, amount_total, currency_id,
      legacy_source_model, legacy_source_table, legacy_record_id,
      legacy_document_state, legacy_partner_id, legacy_partner_name,
      legacy_partner_tax_no, legacy_attachment_ref, creator_legacy_user_id,
      creator_name, created_time, note, active, create_uid, write_uid, create_date, write_date
    )
    SELECT
      COALESCE(NULLIF(f.document_no, ''), 'LEGACY-PREPAID-TAX-' || f.legacy_record_id),
      'legacy',
      'prepaid_tax',
      'prepaid',
      CASE WHEN COALESCE(f.document_state, '') = '2' THEN 'legacy_confirmed' ELSE 'draft' END,
      f.project_id,
      partner_match.id,
      NULLIF(f.document_no, ''),
      f.document_date::date,
      COALESCE(f.expected_receipt_date::date, f.document_date::date, f.created_time::date, CURRENT_DATE),
      NULLIF(f.tax_type, ''),
      f.invoice_date::date,
      NULLIF(f.tax_certificate_no, ''),
      NULLIF(f.invoice_no, ''),
      NULLIF(f.invoice_code, ''),
      COALESCE(NULLIF(f.invoice_type, ''), NULLIF(header_fact.invoice_type, '')),
      CASE
        WHEN COALESCE(f.tax_rate, 0) > 0
        THEN RTRIM(RTRIM(TO_CHAR(ROUND((f.tax_rate * 100)::numeric, 2), 'FM999999990.00'), '0'), '.') || '%%'
        WHEN COALESCE(f.tax_amount, 0) <> 0 AND COALESCE(f.amount_no_tax, 0) <> 0
        THEN RTRIM(RTRIM(TO_CHAR(ROUND((ABS(f.tax_amount) / NULLIF(ABS(f.amount_no_tax), 0) * 100)::numeric, 2), 'FM999999990.00'), '0'), '.') || '%%'
        WHEN COALESCE(header_fact.tax_rate, 0) > 0
        THEN RTRIM(RTRIM(TO_CHAR(ROUND((header_fact.tax_rate * 100)::numeric, 2), 'FM999999990.00'), '0'), '.') || '%%'
        WHEN COALESCE(header_fact.tax_amount, 0) <> 0 AND COALESCE(header_fact.amount_no_tax, 0) <> 0
        THEN RTRIM(RTRIM(TO_CHAR(ROUND((ABS(header_fact.tax_amount) / NULLIF(ABS(header_fact.amount_no_tax), 0) * 100)::numeric, 2), 'FM999999990.00'), '0'), '.') || '%%'
        ELSE NULL
      END,
      COALESCE(NULLIF(f.invoice_content, ''), NULLIF(header_fact.invoice_content, '')),
      COALESCE(NULLIF(f.amount_no_tax, 0), header_fact.amount_no_tax, 0),
      COALESCE(NULLIF(f.tax_amount, 0), header_fact.tax_amount, 0),
      COALESCE(f.amount_total, 0),
      %s,
      'sc.legacy.income.invoice.fact',
      f.source_table,
      f.legacy_record_id,
      NULLIF(f.document_state, ''),
      NULLIF(f.partner_legacy_id, ''),
      NULLIF(f.partner_name, ''),
      NULLIF(f.partner_tax_no, ''),
      NULLIF(f.attachment_ref, ''),
      NULLIF(f.creator_legacy_user_id, ''),
      NULLIF(f.creator_name, ''),
      f.created_time,
      NULLIF(f.note, ''),
      f.active,
      1,
      1,
      NOW(),
      NOW()
    FROM sc_legacy_income_invoice_fact f
    LEFT JOIN LATERAL (
      SELECT h.invoice_type, h.invoice_content, h.tax_rate, h.amount_no_tax, h.tax_amount
        FROM sc_legacy_income_invoice_fact h
       WHERE h.active
         AND h.fact_type = 'prepaid_tax'
         AND h.document_no = f.document_no
         AND (h.project_id = f.project_id OR h.project_id IS NULL OR f.project_id IS NULL)
       ORDER BY
         CASE WHEN h.project_id = f.project_id THEN 0 ELSE 1 END,
         h.id
       LIMIT 1
    ) header_fact ON TRUE
    LEFT JOIN LATERAL (
      SELECT rp.id
        FROM res_partner rp
       WHERE rp.active
         AND (
           (f.partner_name IS NOT NULL AND rp.name = f.partner_name)
           OR (f.partner_tax_no IS NOT NULL AND rp.vat = f.partner_tax_no)
         )
       ORDER BY
         CASE WHEN f.partner_tax_no IS NOT NULL AND rp.vat = f.partner_tax_no THEN 0 ELSE 1 END,
         rp.id
       LIMIT 1
    ) partner_match ON TRUE
    WHERE f.active
      AND f.project_id IS NOT NULL
      AND f.fact_type = 'prepaid_tax_line'
      AND COALESCE(f.amount_total, 0) <> 0
    ON CONFLICT (legacy_source_model, legacy_record_id)
    DO UPDATE SET
      source_kind = EXCLUDED.source_kind,
      direction = EXCLUDED.direction,
      state = EXCLUDED.state,
      project_id = EXCLUDED.project_id,
      partner_id = EXCLUDED.partner_id,
      document_no = EXCLUDED.document_no,
      document_date = EXCLUDED.document_date,
      invoice_date = EXCLUDED.invoice_date,
      tax_type = EXCLUDED.tax_type,
      prepaid_tax_date = EXCLUDED.prepaid_tax_date,
      tax_certificate_no = EXCLUDED.tax_certificate_no,
      invoice_no = EXCLUDED.invoice_no,
      invoice_code = EXCLUDED.invoice_code,
      invoice_type = EXCLUDED.invoice_type,
      tax_rate = EXCLUDED.tax_rate,
      invoice_content = EXCLUDED.invoice_content,
      amount_no_tax = EXCLUDED.amount_no_tax,
      tax_amount = EXCLUDED.tax_amount,
      amount_total = EXCLUDED.amount_total,
      legacy_document_state = EXCLUDED.legacy_document_state,
      legacy_partner_id = EXCLUDED.legacy_partner_id,
      legacy_partner_name = EXCLUDED.legacy_partner_name,
      legacy_partner_tax_no = EXCLUDED.legacy_partner_tax_no,
      legacy_attachment_ref = EXCLUDED.legacy_attachment_ref,
      creator_legacy_user_id = EXCLUDED.creator_legacy_user_id,
      creator_name = EXCLUDED.creator_name,
      created_time = EXCLUDED.created_time,
      note = EXCLUDED.note,
      active = EXCLUDED.active,
      write_uid = 1,
      write_date = NOW()
    """,
    [currency_id],
)

env.cr.execute(  # noqa: F821
    """
    UPDATE sc_invoice_registration target
       SET active = FALSE,
           write_uid = 1,
           write_date = NOW()
      FROM sc_legacy_income_invoice_fact fact
     WHERE target.source_kind = 'prepaid_tax'
      AND target.direction = 'prepaid'
      AND target.legacy_source_model = 'sc.legacy.income.invoice.fact'
      AND target.legacy_record_id = fact.legacy_record_id
      AND fact.fact_type = 'prepaid_tax'
    """
)

env.cr.execute(  # noqa: F821
    """
    UPDATE sc_invoice_registration summary
       SET active = FALSE,
           write_uid = 1,
           write_date = NOW()
     WHERE summary.source_kind = 'prepaid_tax'
       AND summary.direction = 'prepaid'
       AND summary.legacy_source_model = 'sc.legacy.invoice.tax.fact'
       AND EXISTS (
           SELECT 1
             FROM sc_invoice_registration detail
            WHERE detail.source_kind = 'prepaid_tax'
              AND detail.direction = 'prepaid'
              AND detail.legacy_source_model = 'sc.legacy.income.invoice.fact'
              AND detail.active
       )
    """
)

env.cr.execute(  # noqa: F821
    """
    INSERT INTO sc_invoice_registration (
      name, source_origin, source_kind, direction, state, project_id, partner_id,
      contract_id, document_no, document_date, invoice_date, expected_receipt_date,
      invoice_no, invoice_code, invoice_type, tax_rate, invoice_content,
      invoice_issue_company, push_result, kingdee_document_no, applicant_name,
      invoice_count, contract_amount, amount_no_tax, tax_amount, amount_total,
      surcharge_amount, related_receipt_amount, currency_id,
      legacy_source_model, legacy_source_table, legacy_record_id,
      legacy_document_state, legacy_partner_id, legacy_partner_name,
      legacy_partner_tax_no, legacy_attachment_ref, creator_legacy_user_id,
      creator_name, created_time, note, active, create_uid, write_uid, create_date, write_date
    )
    SELECT
      COALESCE(NULLIF(f.invoice_no, ''), NULLIF(f.document_no, ''), 'LEGACY-INCOME-INVOICE-' || f.legacy_record_id),
      'legacy',
      'output_invoice_tax',
      'output',
      CASE WHEN COALESCE(f.document_state, '') = '2' THEN 'legacy_confirmed' ELSE 'draft' END,
      f.project_id,
      partner_match.id,
      contract_match.id,
      NULLIF(f.document_no, ''),
      f.document_date::date,
      COALESCE(f.invoice_date::date, f.document_date::date, f.created_time::date, CURRENT_DATE),
      f.expected_receipt_date::date,
      NULLIF(f.invoice_no, ''),
      NULLIF(f.invoice_code, ''),
      NULLIF(f.invoice_type, ''),
      CASE
        WHEN COALESCE(f.tax_rate, 0) > 0
        THEN RTRIM(RTRIM(TO_CHAR(ROUND(f.tax_rate::numeric, 2), 'FM999999990.00'), '0'), '.') || '%%'
        WHEN COALESCE(f.tax_amount, 0) <> 0 AND COALESCE(f.amount_no_tax, 0) <> 0
        THEN RTRIM(RTRIM(TO_CHAR(ROUND((ABS(f.tax_amount) / NULLIF(ABS(f.amount_no_tax), 0) * 100)::numeric, 2), 'FM999999990.00'), '0'), '.') || '%%'
        ELSE NULL
      END,
      NULLIF(f.invoice_content, ''),
      COALESCE(
        NULLIF(receipt_invoice.invoice_issue_company, ''),
        NULLIF(project_issue_company.invoice_issue_company, ''),
        NULLIF(%s, '')
      ),
      NULLIF(f.document_state, ''),
      NULLIF(f.document_no, ''),
      NULLIF(f.creator_name, ''),
      CASE
        WHEN COALESCE(f.qty, 0) > 0 THEN GREATEST(ROUND(f.qty)::integer, 1)
        WHEN NULLIF(f.invoice_no, '') IS NOT NULL THEN 1
        ELSE 0
      END,
      GREATEST(COALESCE(f.amount_contract, 0), 0),
      COALESCE(f.amount_no_tax, 0),
      COALESCE(f.tax_amount, 0),
      COALESCE(f.amount_total, COALESCE(f.amount_no_tax, 0) + COALESCE(f.tax_amount, 0)),
      0,
      COALESCE(f.amount_received, 0),
      %s,
      'sc.legacy.income.invoice.fact',
      f.source_table,
      f.legacy_record_id,
      NULLIF(f.document_state, ''),
      NULLIF(f.partner_legacy_id, ''),
      NULLIF(f.partner_name, ''),
      NULLIF(f.partner_tax_no, ''),
      NULLIF(f.attachment_ref, ''),
      NULLIF(f.creator_legacy_user_id, ''),
      NULLIF(f.creator_name, ''),
      f.created_time,
      CONCAT_WS(E'\n',
        '[migration:income_invoice] legacy_record_id=' || f.legacy_record_id,
        NULLIF(f.fact_type, ''),
        NULLIF(f.source_table, ''),
        NULLIF(f.project_name, ''),
        NULLIF(f.partner_name, ''),
        NULLIF(f.contract_no, ''),
        NULLIF(f.note, '')
      ),
      f.active,
      1,
      1,
      NOW(),
      NOW()
    FROM sc_legacy_income_invoice_fact f
    LEFT JOIN LATERAL (
      SELECT MIN(NULLIF(ril.invoice_issue_company, '')) AS invoice_issue_company
      FROM sc_receipt_invoice_line ril
      WHERE ril.active
        AND NULLIF(f.invoice_no, '') IS NOT NULL
        AND ril.invoice_no = f.invoice_no
    ) receipt_invoice ON TRUE
    LEFT JOIN LATERAL (
      SELECT ranked.invoice_issue_company
      FROM (
        SELECT
          NULLIF(ril.invoice_issue_company, '') AS invoice_issue_company,
          COUNT(*) AS fact_count
        FROM sc_receipt_invoice_line ril
        WHERE ril.active
          AND ril.project_id = f.project_id
          AND NULLIF(ril.invoice_issue_company, '') IS NOT NULL
        GROUP BY NULLIF(ril.invoice_issue_company, '')
      ) ranked
      ORDER BY ranked.fact_count DESC, ranked.invoice_issue_company
      LIMIT 1
    ) project_issue_company ON TRUE
    LEFT JOIN LATERAL (
      SELECT rp.id
        FROM res_partner rp
       WHERE rp.active
         AND (
           (f.partner_name IS NOT NULL AND rp.name = f.partner_name)
           OR (f.partner_tax_no IS NOT NULL AND rp.vat = f.partner_tax_no)
         )
       ORDER BY
         CASE WHEN f.partner_tax_no IS NOT NULL AND rp.vat = f.partner_tax_no THEN 0 ELSE 1 END,
         rp.id
       LIMIT 1
    ) partner_match ON TRUE
    LEFT JOIN LATERAL (
      SELECT c.id
        FROM construction_contract c
       WHERE (
           (f.contract_legacy_id IS NOT NULL AND c.legacy_contract_id = f.contract_legacy_id)
           OR (f.contract_no IS NOT NULL AND c.name = f.contract_no)
       )
       ORDER BY c.id
       LIMIT 1
    ) contract_match ON TRUE
    WHERE f.active
      AND f.project_id IS NOT NULL
      AND %s
      AND f.fact_type IN ('invoice_application', 'invoice_application_line', 'invoice_issue', 'invoice_issue_line')
      AND (
        COALESCE(f.amount_total, 0) <> 0
        OR COALESCE(f.amount_no_tax, 0) <> 0
        OR COALESCE(f.tax_amount, 0) <> 0
      )
    ON CONFLICT (legacy_source_model, legacy_record_id)
    DO UPDATE SET
      source_kind = EXCLUDED.source_kind,
      direction = EXCLUDED.direction,
      state = EXCLUDED.state,
      project_id = EXCLUDED.project_id,
      partner_id = EXCLUDED.partner_id,
      contract_id = EXCLUDED.contract_id,
      document_no = EXCLUDED.document_no,
      document_date = EXCLUDED.document_date,
      invoice_date = EXCLUDED.invoice_date,
      expected_receipt_date = EXCLUDED.expected_receipt_date,
      invoice_no = EXCLUDED.invoice_no,
      invoice_code = EXCLUDED.invoice_code,
      invoice_type = EXCLUDED.invoice_type,
      tax_rate = EXCLUDED.tax_rate,
      invoice_content = EXCLUDED.invoice_content,
      invoice_issue_company = EXCLUDED.invoice_issue_company,
      push_result = EXCLUDED.push_result,
      kingdee_document_no = EXCLUDED.kingdee_document_no,
      applicant_name = EXCLUDED.applicant_name,
      invoice_count = EXCLUDED.invoice_count,
      contract_amount = EXCLUDED.contract_amount,
      amount_no_tax = EXCLUDED.amount_no_tax,
      tax_amount = EXCLUDED.tax_amount,
      amount_total = EXCLUDED.amount_total,
      surcharge_amount = EXCLUDED.surcharge_amount,
      related_receipt_amount = EXCLUDED.related_receipt_amount,
      legacy_document_state = EXCLUDED.legacy_document_state,
      legacy_partner_id = EXCLUDED.legacy_partner_id,
      legacy_partner_name = EXCLUDED.legacy_partner_name,
      legacy_partner_tax_no = EXCLUDED.legacy_partner_tax_no,
      legacy_attachment_ref = EXCLUDED.legacy_attachment_ref,
      creator_legacy_user_id = EXCLUDED.creator_legacy_user_id,
      creator_name = EXCLUDED.creator_name,
      created_time = EXCLUDED.created_time,
      note = EXCLUDED.note,
      active = EXCLUDED.active,
      write_uid = 1,
      write_date = NOW()
    """,
    [default_issue_company_name, currency_id, include_income_invoice_facts],
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
    "legacy_income_invoice": int(
        scalar("SELECT COUNT(*) FROM sc_invoice_registration WHERE legacy_source_model = 'sc.legacy.income.invoice.fact'")
        or 0
    ),
    "include_income_invoice_facts": include_income_invoice_facts,
    "income_invoice_projection_policy": (
        "opt_in_only; current output invoice adjustment ledger scope is "
        "sc.legacy.invoice.tax.fact/C_JXXP_XXKPDJ"
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
