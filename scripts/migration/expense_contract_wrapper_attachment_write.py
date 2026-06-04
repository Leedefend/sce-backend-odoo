#!/usr/bin/env python3
"""Backfill attachment visibility for formal expense-contract wrappers."""

from __future__ import annotations

import json
import os
from pathlib import Path


SOURCE_SUPPLIER_MODEL = "sc.legacy.supplier.contract.pricing.fact"
BASE_CONTRACT_MODEL = "construction.contract"
EXPENSE_WRAPPER_MODEL = "construction.contract.expense"
SUPPLIER_MARKER = "[migration:direct_supplier_contract_pricing_to_expense_execution]"
WRAPPER_MARKER = "[migration:expense_contract_wrapper_attachment]"
OUTPUT_JSON_NAME = "expense_contract_wrapper_attachment_write_result_v1.json"


def ensure_allowed_db() -> None:
    allowlist = {
        item.strip()
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", env.cr.dbname).split(",")  # noqa: F821
        if item.strip()
    }
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_attachment_backfill": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.append(Path("/mnt/artifacts/migration"))
    candidates.append(Path(f"/tmp/expense_contract_wrapper_attachment/{env.cr.dbname}"))  # noqa: F821
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return candidate
        except Exception:
            continue
    return Path(f"/tmp/expense_contract_wrapper_attachment/{env.cr.dbname}")  # noqa: F821


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def scalar(sql: str, params: tuple | list | None = None) -> int:
    env.cr.execute(sql, params or [])  # noqa: F821
    row = env.cr.fetchone()  # noqa: F821
    return int(row[0] or 0) if row else 0


ensure_allowed_db()

visible_wrapper_count = scalar(
    """
    SELECT COUNT(*)
      FROM construction_contract_expense e
      JOIN construction_contract c ON c.id = e.contract_id
     WHERE c.state IN ('confirmed', 'running')
    """
)

# Primary path: accepted supplier-contract source attachments must be visible
# directly from the formal expense-contract menu model.
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
        EXPENSE_WRAPPER_MODEL,
        SUPPLIER_MARKER,
        SOURCE_SUPPLIER_MODEL,
        SOURCE_SUPPLIER_MODEL,
        EXPENSE_WRAPPER_MODEL,
        f"%{SUPPLIER_MARKER}%source_attachment_id=",
    ],
)
created_supplier_wrapper_attachments = env.cr.rowcount  # noqa: F821

# Secondary path: any attachment already attached to the delegated base contract
# should also be visible from the professional wrapper model used by the menu.
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
           %s || ' source_model=' || %s || '; source_contract_id=' || c.id || '; source_attachment_id=' || a.id,
           a.index_content, a.public, COALESCE(a.create_date, NOW()), NOW(), a.db_datas, COALESCE(a.original_id, a.id)
      FROM ir_attachment a
      JOIN construction_contract c
        ON a.res_model = %s
       AND a.res_id = c.id
       AND c.type = 'in'
      JOIN construction_contract_expense e
        ON e.contract_id = c.id
     WHERE COALESCE(a.description, '') NOT ILIKE %s
       AND NOT EXISTS (
        SELECT 1
          FROM ir_attachment target
         WHERE target.res_model = %s
           AND target.description ILIKE %s || a.id || '%%'
     )
    """,
    [
        EXPENSE_WRAPPER_MODEL,
        WRAPPER_MARKER,
        BASE_CONTRACT_MODEL,
        BASE_CONTRACT_MODEL,
        f"%{SUPPLIER_MARKER}%source_attachment_id=%",
        EXPENSE_WRAPPER_MODEL,
        f"%{WRAPPER_MARKER}%source_attachment_id=",
    ],
)
created_base_wrapper_attachments = env.cr.rowcount  # noqa: F821

env.cr.commit()  # noqa: F821

wrapper_attachment_count = scalar(
    "SELECT COUNT(*) FROM ir_attachment WHERE res_model = %s",
    [EXPENSE_WRAPPER_MODEL],
)
supplier_source_attachment_count = scalar(
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
    """,
    [SOURCE_SUPPLIER_MODEL],
)
missing_supplier_wrapper_attachment_count = scalar(
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
    [SOURCE_SUPPLIER_MODEL, EXPENSE_WRAPPER_MODEL, f"%{SUPPLIER_MARKER}%source_attachment_id="],
)
visible_wrapper_with_attachment_count = scalar(
    """
    SELECT COUNT(DISTINCT e.id)
      FROM construction_contract_expense e
      JOIN construction_contract c ON c.id = e.contract_id
      JOIN ir_attachment a
        ON a.res_model = %s
       AND a.res_id = e.id
     WHERE c.state IN ('confirmed', 'running')
    """,
    [EXPENSE_WRAPPER_MODEL],
)

payload = {
    "status": "PASS" if missing_supplier_wrapper_attachment_count == 0 else "FAIL",
    "mode": "expense_contract_wrapper_attachment_write",
    "database": env.cr.dbname,  # noqa: F821
    "visible_wrapper_count": visible_wrapper_count,
    "supplier_source_attachment_count": supplier_source_attachment_count,
    "created_supplier_wrapper_attachments": created_supplier_wrapper_attachments,
    "created_base_wrapper_attachments": created_base_wrapper_attachments,
    "wrapper_attachment_count": wrapper_attachment_count,
    "missing_supplier_wrapper_attachment_count": missing_supplier_wrapper_attachment_count,
    "visible_wrapper_with_attachment_count": visible_wrapper_with_attachment_count,
}
write_json(artifact_root() / OUTPUT_JSON_NAME, payload)
print("EXPENSE_CONTRACT_WRAPPER_ATTACHMENT_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
if payload["status"] != "PASS":
    raise RuntimeError(payload)
