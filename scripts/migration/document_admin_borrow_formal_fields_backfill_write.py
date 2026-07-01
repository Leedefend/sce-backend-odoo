#!/usr/bin/env python3
"""Backfill formal document-borrow fields from historical visible columns."""

from __future__ import annotations

import json
import os
from pathlib import Path


def _artifact_path() -> Path:
    root = Path(os.getenv("MIGRATION_ARTIFACT_ROOT") or "/tmp")
    root.mkdir(parents=True, exist_ok=True)
    return root / "document_admin_borrow_formal_fields_backfill_result.json"


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


TABLE = "sc_document_admin_document"
required_columns = {
    "borrow_project_name",
    "application_date",
    "borrow_department_name",
    "borrower_name",
    "borrower_contact",
    "borrow_form",
    "responsible_person",
    "return_request_date",
    "return_apply_time",
    "returned_flag",
    "return_confirm_time",
    "actual_return_date",
    "modifier_name",
    "modified_at",
    "modify_note",
    "reviewer_name",
    "review_time",
    "review_opinion",
    "legacy_visible_project_name",
    "legacy_visible_application_date",
    "legacy_visible_department",
    "legacy_visible_borrower",
    "legacy_visible_contact",
    "legacy_visible_borrow_form",
    "legacy_visible_responsible_person",
    "legacy_visible_return_request_date",
    "legacy_visible_return_apply_time",
    "legacy_visible_returned",
    "legacy_visible_return_confirm_time",
    "legacy_visible_return_date",
    "legacy_visible_modifier",
    "legacy_visible_modified_date",
    "legacy_visible_modify_note",
    "legacy_visible_reviewer",
    "legacy_visible_review_time",
    "legacy_visible_review_opinion",
}
missing = sorted(column for column in required_columns if not _column_exists(TABLE, column))
if missing:
    result = {"mode": "document_admin_borrow_formal_fields_backfill", "status": "skipped", "missing_columns": missing}
else:
    env.cr.execute(  # noqa: F821
        """
        UPDATE sc_document_admin_document
           SET borrow_project_name = COALESCE(borrow_project_name, legacy_visible_project_name),
               application_date = COALESCE(application_date, legacy_visible_application_date),
               borrow_department_name = COALESCE(borrow_department_name, legacy_visible_department),
               borrower_name = COALESCE(borrower_name, legacy_visible_borrower),
               borrower_contact = COALESCE(borrower_contact, legacy_visible_contact),
               borrow_form = COALESCE(borrow_form, legacy_visible_borrow_form),
               responsible_person = COALESCE(responsible_person, legacy_visible_responsible_person),
               return_request_date = COALESCE(return_request_date, legacy_visible_return_request_date),
               return_apply_time = COALESCE(return_apply_time, legacy_visible_return_apply_time),
               returned_flag = COALESCE(returned_flag, legacy_visible_returned),
               return_confirm_time = COALESCE(return_confirm_time, legacy_visible_return_confirm_time),
               actual_return_date = COALESCE(actual_return_date, legacy_visible_return_date),
               modifier_name = COALESCE(modifier_name, legacy_visible_modifier),
               modified_at = COALESCE(modified_at, legacy_visible_modified_date),
               modify_note = COALESCE(modify_note, legacy_visible_modify_note),
               reviewer_name = COALESCE(reviewer_name, legacy_visible_reviewer),
               review_time = COALESCE(review_time, legacy_visible_review_time),
               review_opinion = COALESCE(review_opinion, legacy_visible_review_opinion)
         WHERE fact_type = 'document_borrow'
           AND legacy_source_table IS NOT NULL
        """
    )
    updated = env.cr.rowcount  # noqa: F821
    env.cr.commit()  # noqa: F821
    result = {"mode": "document_admin_borrow_formal_fields_backfill", "status": "ok", "updated": updated}

output = _artifact_path()
output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, ensure_ascii=False, indent=2))
