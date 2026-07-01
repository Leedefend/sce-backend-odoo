#!/usr/bin/env python3
"""Backfill formal office seal-use fields from historical visible fields.

Run with:
  DB_NAME=sc_demo scripts/ops/odoo_shell_exec.sh < scripts/migration/office_admin_seal_formal_fields_backfill_write.py
"""

from __future__ import annotations

import json
import os
from pathlib import Path


def _artifact_path() -> Path:
    root = Path(os.getenv("MIGRATION_ARTIFACT_ROOT") or "/tmp")
    root.mkdir(parents=True, exist_ok=True)
    return root / "office_admin_seal_formal_fields_backfill_result.json"


def _column_exists(table: str, column: str) -> bool:
    env.cr.execute(  # noqa: F821
        """
        SELECT 1
          FROM information_schema.columns
         WHERE table_name = %s
           AND column_name = %s
         LIMIT 1
        """,
        (table, column),
    )
    return bool(env.cr.fetchone())  # noqa: F821


TABLE = "sc_office_admin_document"
required_columns = {
    "seal_use_date",
    "seal_department_name",
    "seal_applicant_name",
    "seal_department_manager_sign",
    "seal_type_name",
    "seal_text",
    "seal_handler_sign",
    "seal_leader_sign",
    "seal_copy_count",
    "seal_return_date",
    "seal_contract_amount",
    "seal_contract_no",
    "seal_company_name",
    "seal_using_company_name",
    "seal_take_out_flag",
    "legacy_visible_seal_use_time",
    "legacy_visible_department",
    "legacy_visible_applicant",
    "legacy_visible_department_manager_sign",
    "legacy_visible_seal_type",
    "legacy_visible_seal_text",
    "legacy_visible_handler_sign",
    "legacy_visible_leader_sign",
    "legacy_visible_copy_count",
    "legacy_visible_return_time",
    "legacy_visible_contract_amount",
    "legacy_visible_contract_no",
    "legacy_visible_company",
    "legacy_visible_seal_company",
    "legacy_visible_take_out",
}
missing = sorted(column for column in required_columns if not _column_exists(TABLE, column))
if missing:
    result = {"mode": "office_admin_seal_formal_fields_backfill", "status": "skipped", "missing_columns": missing}
else:
    env.cr.execute(  # noqa: F821
        """
        UPDATE sc_office_admin_document
           SET seal_use_date = COALESCE(seal_use_date, legacy_visible_seal_use_time),
               seal_department_name = COALESCE(seal_department_name, legacy_visible_department),
               seal_applicant_name = COALESCE(seal_applicant_name, legacy_visible_applicant),
               seal_department_manager_sign = COALESCE(seal_department_manager_sign, legacy_visible_department_manager_sign),
               seal_type_name = COALESCE(seal_type_name, legacy_visible_seal_type),
               seal_text = COALESCE(seal_text, legacy_visible_seal_text),
               seal_handler_sign = COALESCE(seal_handler_sign, legacy_visible_handler_sign),
               seal_leader_sign = COALESCE(seal_leader_sign, legacy_visible_leader_sign),
               seal_copy_count = COALESCE(seal_copy_count, legacy_visible_copy_count),
               seal_return_date = COALESCE(seal_return_date, legacy_visible_return_time),
               seal_contract_amount = COALESCE(
                   seal_contract_amount,
                   CASE
                       WHEN regexp_replace(legacy_visible_contract_amount, '[^0-9.-]', '', 'g') ~ '^-?[0-9]+(\\.[0-9]+)?$'
                       THEN regexp_replace(legacy_visible_contract_amount, '[^0-9.-]', '', 'g')::numeric
                       ELSE NULL
                   END
               ),
               seal_contract_no = COALESCE(seal_contract_no, legacy_visible_contract_no),
               seal_company_name = COALESCE(seal_company_name, legacy_visible_company),
               seal_using_company_name = COALESCE(seal_using_company_name, legacy_visible_seal_company),
               seal_take_out_flag = COALESCE(seal_take_out_flag, legacy_visible_take_out),
               use_date = COALESCE(use_date, legacy_visible_seal_use_time),
               return_date = COALESCE(return_date, legacy_visible_return_time),
               use_purpose = COALESCE(use_purpose, legacy_visible_seal_text),
               amount = COALESCE(
                   amount,
                   CASE
                       WHEN regexp_replace(legacy_visible_contract_amount, '[^0-9.-]', '', 'g') ~ '^-?[0-9]+(\\.[0-9]+)?$'
                       THEN regexp_replace(legacy_visible_contract_amount, '[^0-9.-]', '', 'g')::numeric
                       ELSE NULL
                   END
               )
         WHERE fact_type = 'seal_use'
           AND legacy_source_table IS NOT NULL
        """
    )
    updated = env.cr.rowcount  # noqa: F821
    env.cr.commit()  # noqa: F821
    result = {"mode": "office_admin_seal_formal_fields_backfill", "status": "ok", "updated": updated}

output = _artifact_path()
output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, ensure_ascii=False, indent=2))
