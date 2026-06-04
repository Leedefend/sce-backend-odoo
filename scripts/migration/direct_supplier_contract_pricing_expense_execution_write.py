#!/usr/bin/env python3
"""Bulk-cut accepted supplier-contract data into formal expense execution.

Authority: current user-accepted visible surface
``sc.legacy.supplier.contract.pricing.fact``. This does not replay legacy DB.

Run with:
    PROJECT=sc-backend-odoo-dev DB_NAME=sc_demo MIGRATION_REPLAY_DB_ALLOWLIST=sc_demo \
      bash scripts/ops/odoo_shell_exec.sh < scripts/migration/direct_supplier_contract_pricing_expense_execution_write.py
"""

from __future__ import annotations

import json
import os
from pathlib import Path


SOURCE_MODEL = "sc.legacy.supplier.contract.pricing.fact"
TARGET_MODEL = "construction.contract"
TARGET_WRAPPER_MODEL = "construction.contract.expense"
SOURCE_TABLE = "sc_legacy_supplier_contract_pricing_fact"
TARGET_TABLE = "construction_contract"
OUTPUT_JSON_NAME = "direct_supplier_contract_pricing_expense_execution_write_result_v1.json"
MIGRATION_MARKER = "[migration:direct_supplier_contract_pricing_to_expense_execution]"
LINE_MARKER = "[migration:direct_supplier_contract_pricing_amount_line]"


def ensure_allowed_db() -> None:
    allowlist = {
        item.strip()
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", env.cr.dbname).split(",")  # noqa: F821
        if item.strip()
    }
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_projection": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.append(Path("/mnt/artifacts/migration"))
    candidates.append(Path(f"/tmp/direct_supplier_contract_pricing/{env.cr.dbname}"))  # noqa: F821
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return candidate
        except Exception:
            continue
    return Path(f"/tmp/direct_supplier_contract_pricing/{env.cr.dbname}")  # noqa: F821


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def scalar(sql: str, params: tuple | list | None = None) -> int:
    env.cr.execute(sql, params or [])  # noqa: F821
    row = env.cr.fetchone()  # noqa: F821
    return int(row[0] or 0) if row else 0


ensure_allowed_db()

Contract = env[TARGET_MODEL].sudo().with_context(active_test=False)  # noqa: F821
tax = Contract._get_default_tax("in")
if not tax:
    raise RuntimeError({"missing_default_purchase_tax": True})
company = env.company  # noqa: F821
currency = company.currency_id

fact_count_before = scalar("SELECT COUNT(*) FROM sc_legacy_supplier_contract_pricing_fact WHERE legacy_source_table = 'T_GYSHT_INFO'")
source_attachment_count = scalar("SELECT COUNT(*) FROM ir_attachment WHERE res_model = %s", [SOURCE_MODEL])
visible_before = scalar(
    """
    SELECT COUNT(*)
      FROM construction_contract_expense e
      JOIN construction_contract c ON c.id = e.contract_id
     WHERE c.state IN ('confirmed', 'running')
    """
)

# Ensure every accepted fact has a supplier partner anchor. Prefer exact name
# match; create only for still-unmatched visible supplier names.
env.cr.execute(  # noqa: F821
    """
    UPDATE sc_legacy_supplier_contract_pricing_fact f
       SET partner_id = p.id,
           write_uid = 1,
           write_date = NOW()
      FROM res_partner p
     WHERE f.legacy_source_table = 'T_GYSHT_INFO'
       AND f.partner_id IS NULL
       AND COALESCE(NULLIF(f.partner_name, ''), '') <> ''
       AND p.name = f.partner_name
    """
)
partner_matched_by_name = env.cr.rowcount  # noqa: F821

env.cr.execute(  # noqa: F821
    """
    WITH missing AS (
        SELECT DISTINCT NULLIF(f.partner_name, '') AS partner_name
          FROM sc_legacy_supplier_contract_pricing_fact f
         WHERE f.legacy_source_table = 'T_GYSHT_INFO'
           AND f.partner_id IS NULL
           AND COALESCE(NULLIF(f.partner_name, ''), '') <> ''
    )
    INSERT INTO res_partner
        (name, supplier_rank, active, company_id, create_uid, create_date, write_uid, write_date)
    SELECT m.partner_name, 1, TRUE, NULL, 1, NOW(), 1, NOW()
      FROM missing m
     WHERE NOT EXISTS (SELECT 1 FROM res_partner p WHERE p.name = m.partner_name)
    """
)
created_partner_count = env.cr.rowcount  # noqa: F821

env.cr.execute(  # noqa: F821
    """
    UPDATE sc_legacy_supplier_contract_pricing_fact f
       SET partner_id = p.id,
           write_uid = 1,
           write_date = NOW()
      FROM res_partner p
     WHERE f.legacy_source_table = 'T_GYSHT_INFO'
       AND f.partner_id IS NULL
       AND COALESCE(NULLIF(f.partner_name, ''), '') <> ''
       AND p.name = f.partner_name
    """
)
partner_backfilled_after_create = env.cr.rowcount  # noqa: F821

missing_anchor_count = scalar(
    """
    SELECT COUNT(*)
      FROM sc_legacy_supplier_contract_pricing_fact
     WHERE legacy_source_table = 'T_GYSHT_INFO'
       AND (project_id IS NULL OR partner_id IS NULL)
    """
)
if missing_anchor_count:
    raise RuntimeError({"supplier_contract_pricing_missing_project_or_partner": missing_anchor_count})

# Create only missing formal contracts. Existing supplier contracts are updated
# below, preserving their stable IDs.
env.cr.execute(  # noqa: F821
    """
    INSERT INTO construction_contract
        (
            project_id, partner_id, company_id, currency_id, tax_id,
            create_uid, create_date, write_uid, write_date,
            name, subject, type, state, active,
            legacy_contract_id, legacy_project_id, legacy_contract_no,
            legacy_document_no, legacy_external_contract_no, legacy_status,
            legacy_deleted_flag, legacy_counterparty_text,
            legacy_contract_amount_source, date_contract, note,
            attachment_text, amount_untaxed, amount_tax, amount_total,
            line_amount_total, amount_change, amount_final,
            legacy_contract_amount, visible_contract_amount,
            legacy_visible_document_state, legacy_visible_document_no,
            legacy_visible_archived, legacy_visible_counterparty,
            legacy_visible_project_name, legacy_visible_title,
            legacy_visible_category, legacy_visible_contract_no,
            legacy_visible_amount, legacy_visible_settlement_amount,
            legacy_visible_received_amount, legacy_visible_unreceived_amount,
            legacy_visible_creator_name, legacy_visible_contract_date,
            legacy_visible_created_time, legacy_visible_attachment
        )
    SELECT
            f.project_id, f.partner_id, %s, %s, %s,
            COALESCE(f.create_uid, 1), COALESCE(f.create_date, NOW()), 1, NOW(),
            COALESCE(NULLIF(f.contract_no, ''), 'SUP-' || substring(f.legacy_contract_id for 12)),
            COALESCE(NULLIF(f.title, ''), '历史供应合同 ' || COALESCE(NULLIF(f.partner_name, ''), f.legacy_contract_id)),
            'in', 'confirmed', TRUE,
            f.legacy_contract_id, f.project_legacy_id, f.contract_no,
            f.document_no, f.document_no, f.document_state,
            f.deleted_flag, f.partner_name,
            'sc.legacy.supplier.contract.pricing.fact.amount_total', f.sign_date,
            NULL,
            f.attachment_text,
            COALESCE(f.amount_total, 0), 0, COALESCE(f.amount_total, 0),
            COALESCE(f.amount_total, 0), 0, COALESCE(f.amount_total, 0),
            COALESCE(f.amount_total, 0), COALESCE(f.amount_total, 0),
            CASE
              WHEN COALESCE(f.deleted_flag, '') NOT IN ('', '0', 'false', 'False') THEN '已删除'
              WHEN f.document_state = '0' THEN '未审核'
              WHEN f.document_state = '1' THEN '审核中'
              WHEN f.document_state = '2' THEN '已审核'
              WHEN f.document_state = '-1' THEN '已驳回'
              ELSE COALESCE(f.document_state, '')
            END,
            f.document_no, f.original_contract_holder, f.partner_name,
            f.project_name, COALESCE(NULLIF(f.title, ''), '历史供应合同 ' || COALESCE(NULLIF(f.partner_name, ''), f.legacy_contract_id)),
            f.contract_type_text, f.contract_no,
            NULLIF(COALESCE(f.amount_total, 0)::text, '0'),
            NULLIF(COALESCE(f.settlement_amount, 0)::text, '0'),
            NULLIF(COALESCE(f.paid_amount, 0)::text, '0'),
            NULLIF(COALESCE(f.unpaid_amount, 0)::text, '0'),
            f.creator_name, f.sign_date, f.created_time, f.attachment_text
      FROM sc_legacy_supplier_contract_pricing_fact f
     WHERE f.legacy_source_table = 'T_GYSHT_INFO'
       AND NOT EXISTS (
            SELECT 1
              FROM construction_contract c
             WHERE c.type = 'in'
               AND c.legacy_contract_id = f.legacy_contract_id
       )
    """,
    [company.id, currency.id, tax.id],
)
created_contract_count = env.cr.rowcount  # noqa: F821

# Update all matching formal contracts to the accepted visible values and make
# them visible in 支出合同执行.
env.cr.execute(  # noqa: F821
    """
    UPDATE construction_contract c
       SET project_id = f.project_id,
           partner_id = f.partner_id,
           company_id = %s,
           currency_id = %s,
           tax_id = %s,
           write_uid = 1,
           write_date = NOW(),
           subject = COALESCE(NULLIF(f.title, ''), '历史供应合同 ' || COALESCE(NULLIF(f.partner_name, ''), f.legacy_contract_id)),
           type = 'in',
           state = 'confirmed',
           active = TRUE,
           legacy_project_id = f.project_legacy_id,
           legacy_contract_no = f.contract_no,
           legacy_document_no = f.document_no,
           legacy_external_contract_no = f.document_no,
           legacy_status = f.document_state,
           legacy_deleted_flag = f.deleted_flag,
           legacy_counterparty_text = f.partner_name,
           legacy_contract_amount_source = 'sc.legacy.supplier.contract.pricing.fact.amount_total',
           date_contract = f.sign_date,
           note = NULL,
           attachment_text = f.attachment_text,
           amount_untaxed = COALESCE(f.amount_total, 0),
           amount_tax = 0,
           amount_total = COALESCE(f.amount_total, 0),
           line_amount_total = COALESCE(f.amount_total, 0),
           amount_change = 0,
           amount_final = COALESCE(f.amount_total, 0),
           legacy_contract_amount = COALESCE(f.amount_total, 0),
           visible_contract_amount = COALESCE(f.amount_total, 0),
           legacy_visible_document_state = CASE
              WHEN COALESCE(f.deleted_flag, '') NOT IN ('', '0', 'false', 'False') THEN '已删除'
              WHEN f.document_state = '0' THEN '未审核'
              WHEN f.document_state = '1' THEN '审核中'
              WHEN f.document_state = '2' THEN '已审核'
              WHEN f.document_state = '-1' THEN '已驳回'
              ELSE COALESCE(f.document_state, '')
           END,
           legacy_visible_document_no = f.document_no,
           legacy_visible_archived = f.original_contract_holder,
           legacy_visible_counterparty = f.partner_name,
           legacy_visible_project_name = f.project_name,
           legacy_visible_title = COALESCE(NULLIF(f.title, ''), '历史供应合同 ' || COALESCE(NULLIF(f.partner_name, ''), f.legacy_contract_id)),
           legacy_visible_category = f.contract_type_text,
           legacy_visible_contract_no = f.contract_no,
           legacy_visible_amount = NULLIF(COALESCE(f.amount_total, 0)::text, '0'),
           legacy_visible_settlement_amount = NULLIF(COALESCE(f.settlement_amount, 0)::text, '0'),
           legacy_visible_received_amount = NULLIF(COALESCE(f.paid_amount, 0)::text, '0'),
           legacy_visible_unreceived_amount = NULLIF(COALESCE(f.unpaid_amount, 0)::text, '0'),
           legacy_visible_creator_name = f.creator_name,
           legacy_visible_contract_date = f.sign_date,
           legacy_visible_created_time = f.created_time,
           legacy_visible_attachment = f.attachment_text
      FROM sc_legacy_supplier_contract_pricing_fact f
     WHERE f.legacy_source_table = 'T_GYSHT_INFO'
       AND c.type = 'in'
       AND c.legacy_contract_id = f.legacy_contract_id
    """,
    [company.id, currency.id, tax.id],
)
updated_contract_count = env.cr.rowcount  # noqa: F821

# Ensure _inherits wrapper exists for every target contract.
env.cr.execute(  # noqa: F821
    """
    INSERT INTO construction_contract_expense
        (contract_id, create_uid, create_date, write_uid, write_date)
    SELECT c.id, COALESCE(c.create_uid, 1), COALESCE(c.create_date, NOW()), 1, NOW()
      FROM construction_contract c
      JOIN sc_legacy_supplier_contract_pricing_fact f
        ON f.legacy_source_table = 'T_GYSHT_INFO'
       AND f.legacy_contract_id = c.legacy_contract_id
      LEFT JOIN construction_contract_expense e ON e.contract_id = c.id
     WHERE c.type = 'in'
       AND e.id IS NULL
    """
)
created_wrapper_count = env.cr.rowcount  # noqa: F821

# Rebuild one formal amount line per accepted supplier contract.
env.cr.execute(  # noqa: F821
    """
    DELETE FROM construction_contract_line l
     USING construction_contract c
     JOIN sc_legacy_supplier_contract_pricing_fact f
       ON f.legacy_source_table = 'T_GYSHT_INFO'
      AND f.legacy_contract_id = c.legacy_contract_id
    WHERE l.contract_id = c.id
      AND l.note ILIKE %s
    """,
    [f"%{LINE_MARKER}%"],
)
deleted_marker_line_count = env.cr.rowcount  # noqa: F821

env.cr.execute(  # noqa: F821
    """
    INSERT INTO construction_contract_line
        (
            contract_id, project_id, currency_id, sequence,
            create_uid, create_date, write_uid, write_date,
            note, qty_contract, price_contract, amount_contract,
            amount_contract_leaf, boq_amount_leaf, delta_amount,
            boq_amount_source, active
        )
    SELECT c.id, c.project_id, c.currency_id, 10,
           1, NOW(), 1, NOW(),
           %s || ' source_id=' || f.id || '; legacy_contract_id=' || f.legacy_contract_id,
           CASE WHEN COALESCE(f.amount_total, 0) = 0 THEN 0 ELSE 1 END,
           COALESCE(f.amount_total, 0),
           COALESCE(f.amount_total, 0),
           COALESCE(f.amount_total, 0),
           0,
           COALESCE(f.amount_total, 0),
           'none',
           TRUE
      FROM construction_contract c
      JOIN sc_legacy_supplier_contract_pricing_fact f
        ON f.legacy_source_table = 'T_GYSHT_INFO'
       AND f.legacy_contract_id = c.legacy_contract_id
     WHERE c.type = 'in'
    """,
    [LINE_MARKER],
)
created_line_count = env.cr.rowcount  # noqa: F821

# Copy attachments from accepted fact records to formal contracts. The source
# attachment id in description makes this idempotent.
env.cr.execute(  # noqa: F821
    """
    INSERT INTO ir_attachment
        (
            res_id, company_id, file_size, create_uid, write_uid, name,
            res_model, res_field, type, url, access_token, store_fname,
            checksum, mimetype, description, index_content, public,
            create_date, write_date, db_datas, original_id
        )
    SELECT c.id, a.company_id, a.file_size, COALESCE(a.create_uid, 1), 1, a.name,
           %s, NULL, a.type, a.url, a.access_token, a.store_fname,
           a.checksum, a.mimetype,
           %s || ' source_model=' || %s || '; source_id=' || f.id || '; source_attachment_id=' || a.id,
           a.index_content, a.public, COALESCE(a.create_date, NOW()), NOW(), a.db_datas, COALESCE(a.original_id, a.id)
      FROM ir_attachment a
      JOIN sc_legacy_supplier_contract_pricing_fact f
        ON a.res_model = %s
       AND a.res_id = f.id
       AND f.legacy_source_table = 'T_GYSHT_INFO'
      JOIN construction_contract c
        ON c.type = 'in'
       AND c.legacy_contract_id = f.legacy_contract_id
     WHERE NOT EXISTS (
        SELECT 1
          FROM ir_attachment target
         WHERE target.res_model = %s
           AND target.description ILIKE %s || a.id || '%%'
     )
    """,
    [TARGET_MODEL, MIGRATION_MARKER, SOURCE_MODEL, SOURCE_MODEL, TARGET_MODEL, f"%{MIGRATION_MARKER}%source_attachment_id="],
)
copied_attachment_count = env.cr.rowcount  # noqa: F821

env.cr.execute(  # noqa: F821
    """
    INSERT INTO ir_attachment
        (
            res_id, company_id, file_size, create_uid, write_uid, name,
            res_model, res_field, type, url, access_token, store_fname,
            checksum, mimetype, description, index_content, public,
            create_date, write_date, db_datas, original_id
        )
    SELECT e.id, a.company_id, a.file_size, COALESCE(a.create_uid, 1), 1, a.name,
           %s, NULL, a.type, a.url, a.access_token, a.store_fname,
           a.checksum, a.mimetype,
           %s || ' wrapper_model=' || %s || '; source_model=' || %s || '; source_id=' || f.id || '; source_attachment_id=' || a.id,
           a.index_content, a.public, COALESCE(a.create_date, NOW()), NOW(), a.db_datas, COALESCE(a.original_id, a.id)
      FROM ir_attachment a
      JOIN sc_legacy_supplier_contract_pricing_fact f
        ON a.res_model = %s
       AND a.res_id = f.id
       AND f.legacy_source_table = 'T_GYSHT_INFO'
      JOIN construction_contract c
        ON c.type = 'in'
       AND c.legacy_contract_id = f.legacy_contract_id
      JOIN construction_contract_expense e
        ON e.contract_id = c.id
     WHERE NOT EXISTS (
        SELECT 1
          FROM ir_attachment target
         WHERE target.res_model = %s
           AND target.description ILIKE %s || a.id || '%%'
     )
    """,
    [
        TARGET_WRAPPER_MODEL,
        MIGRATION_MARKER,
        TARGET_WRAPPER_MODEL,
        SOURCE_MODEL,
        SOURCE_MODEL,
        TARGET_WRAPPER_MODEL,
        f"%{MIGRATION_MARKER}%source_attachment_id=",
    ],
)
copied_wrapper_attachment_count = env.cr.rowcount  # noqa: F821

env.cr.commit()  # noqa: F821

fact_count = fact_count_before
target_contract_count = scalar(
    """
    SELECT COUNT(*)
      FROM construction_contract c
      JOIN sc_legacy_supplier_contract_pricing_fact f
        ON f.legacy_source_table = 'T_GYSHT_INFO'
       AND f.legacy_contract_id = c.legacy_contract_id
     WHERE c.type = 'in'
    """
)
target_visible_count = scalar(
    """
    SELECT COUNT(*)
      FROM construction_contract_expense e
      JOIN construction_contract c ON c.id = e.contract_id
     WHERE c.state IN ('confirmed', 'running')
    """
)
target_attachment_count = scalar(
    "SELECT COUNT(*) FROM ir_attachment WHERE res_model = %s AND description ILIKE %s",
    [TARGET_MODEL, f"%{MIGRATION_MARKER}%"],
)
target_wrapper_attachment_count = scalar(
    "SELECT COUNT(*) FROM ir_attachment WHERE res_model = %s AND description ILIKE %s",
    [TARGET_WRAPPER_MODEL, f"%{MIGRATION_MARKER}%"],
)
missing_target_count = scalar(
    """
    SELECT COUNT(*)
      FROM sc_legacy_supplier_contract_pricing_fact f
     WHERE f.legacy_source_table = 'T_GYSHT_INFO'
       AND NOT EXISTS (
            SELECT 1
              FROM construction_contract c
             WHERE c.type = 'in'
               AND c.legacy_contract_id = f.legacy_contract_id
       )
    """
)
missing_attachment_count = scalar(
    """
    SELECT COUNT(*)
      FROM ir_attachment a
      JOIN sc_legacy_supplier_contract_pricing_fact f
        ON a.res_model = %s
       AND a.res_id = f.id
       AND f.legacy_source_table = 'T_GYSHT_INFO'
     WHERE NOT EXISTS (
        SELECT 1
          FROM ir_attachment target
         WHERE target.res_model = %s
           AND target.description ILIKE %s || a.id || '%%'
     )
    """,
    [SOURCE_MODEL, TARGET_MODEL, f"%{MIGRATION_MARKER}%source_attachment_id="],
)
missing_wrapper_attachment_count = scalar(
    """
    SELECT COUNT(*)
      FROM ir_attachment a
      JOIN sc_legacy_supplier_contract_pricing_fact f
        ON a.res_model = %s
       AND a.res_id = f.id
       AND f.legacy_source_table = 'T_GYSHT_INFO'
      JOIN construction_contract c
        ON c.type = 'in'
       AND c.legacy_contract_id = f.legacy_contract_id
      JOIN construction_contract_expense e
        ON e.contract_id = c.id
     WHERE NOT EXISTS (
        SELECT 1
          FROM ir_attachment target
         WHERE target.res_model = %s
           AND target.description ILIKE %s || a.id || '%%'
     )
    """,
    [SOURCE_MODEL, TARGET_WRAPPER_MODEL, f"%{MIGRATION_MARKER}%source_attachment_id="],
)

payload = {
    "status": "PASS" if missing_target_count == 0 and target_visible_count >= fact_count and missing_attachment_count == 0 and missing_wrapper_attachment_count == 0 else "FAIL",
    "mode": "direct_supplier_contract_pricing_expense_execution_write",
    "database": env.cr.dbname,  # noqa: F821
    "source_model": SOURCE_MODEL,
    "target_model": TARGET_MODEL,
    "source_fact_count": fact_count,
    "visible_before": visible_before,
    "target_contract_count": target_contract_count,
    "target_expense_execution_visible_count": target_visible_count,
    "missing_target_count": missing_target_count,
    "source_attachment_count": source_attachment_count,
    "target_attachment_count": target_attachment_count,
    "target_wrapper_attachment_count": target_wrapper_attachment_count,
    "missing_attachment_count": missing_attachment_count,
    "missing_wrapper_attachment_count": missing_wrapper_attachment_count,
    "created_partner_count": created_partner_count,
    "partner_matched_by_name": partner_matched_by_name,
    "partner_backfilled_after_create": partner_backfilled_after_create,
    "created_contract_count": created_contract_count,
    "updated_contract_count": updated_contract_count,
    "created_wrapper_count": created_wrapper_count,
    "deleted_marker_line_count": deleted_marker_line_count,
    "created_line_count": created_line_count,
    "copied_attachment_count": copied_attachment_count,
    "copied_wrapper_attachment_count": copied_wrapper_attachment_count,
    "decision": "accepted_supplier_contract_data_cut_to_formal_expense_contract_execution",
}
write_json(artifact_root() / OUTPUT_JSON_NAME, payload)
print("DIRECT_SUPPLIER_CONTRACT_PRICING_EXPENSE_EXECUTION_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
if payload["status"] != "PASS":
    raise RuntimeError(payload)
