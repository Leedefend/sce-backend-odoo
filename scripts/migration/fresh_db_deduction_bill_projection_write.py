"""Project legacy deduction adjustment lines into the user-facing deduction bill entry."""

from __future__ import annotations

import json
import os
from pathlib import Path

from odoo import fields


def repo_root() -> Path:
    file_name = globals().get("__file__")
    if file_name:
        return Path(file_name).resolve().parents[2]
    return Path.cwd()


def artifact_root() -> Path:
    root = os.environ.get("MIGRATION_ARTIFACT_ROOT") or os.environ.get("HISTORY_CONTINUITY_ARTIFACT_ROOT")
    if root:
        return Path(root)
    return repo_root() / "artifacts" / "migration"


output_json = artifact_root() / "fresh_db_deduction_bill_projection_write_result_v1.json"
output_json.parent.mkdir(parents=True, exist_ok=True)

Claim = env["sc.expense.claim"].sudo()  # noqa: F821
Line = env["sc.legacy.deduction.adjustment.line"].sudo()  # noqa: F821

source_domain = [
    ("active", "=", True),
    ("project_id", "!=", False),
]
candidate_count = Line.search_count(source_domain)
before = Claim.search_count([("claim_type", "=", "expense"), ("expense_type", "=", "扣款单")])

created = 0
updated = 0
skipped_no_amount = 0
skipped_missing_project = 0

for line in Line.search(source_domain, order="document_date desc, id desc"):
    if not line.project_id:
        skipped_missing_project += 1
        continue
    amount = line.current_actual_amount or line.current_planned_amount or 0.0
    if amount <= 0:
        skipped_no_amount += 1
        continue
    document_date = line.document_date.date() if line.document_date else fields.Date.context_today(Claim)
    item_name = (line.adjustment_item_name or "").strip()
    summary = " / ".join(part for part in ["扣款单", item_name, line.title or ""] if part)
    values = {
        "source_origin": "legacy",
        "claim_type": "expense",
        "state": "legacy_confirmed",
        "project_id": line.project_id.id,
        "applicant_name": line.registrant_name or line.creator_name,
        "payment_account_name": line.deduction_account,
        "date_claim": document_date,
        "expense_type": "扣款单",
        "summary": summary[:255],
        "amount": amount,
        "approved_amount": amount,
        "legacy_source_model": "sc.legacy.deduction.adjustment.line",
        "legacy_source_table": line.source_table,
        "legacy_record_id": line.legacy_line_id,
        "legacy_document_no": line.document_no,
        "legacy_document_state": line.document_state or "历史已确认",
        "note": (
            "[migration:deduction_bill] "
            f"legacy_deduction_adjustment_line_id={line.id}; "
            f"legacy_line_id={line.legacy_line_id}; "
            f"adjustment_item={item_name}; "
            f"returned_flag={line.returned_flag or ''}; "
            f"fund_plan_no={line.fund_plan_no or ''}"
        ),
    }
    existing = Claim.search(
        [
            ("legacy_source_model", "=", values["legacy_source_model"]),
            ("legacy_record_id", "=", values["legacy_record_id"]),
        ],
        limit=1,
    )
    if existing:
        env.cr.execute(  # noqa: F821
            """
            UPDATE sc_expense_claim
               SET claim_type = %s,
                   state = %s,
                   project_id = %s,
                   applicant_name = %s,
                   payment_account_name = %s,
                   date_claim = %s,
                   expense_type = %s,
                   summary = %s,
                   amount = %s,
                   approved_amount = %s,
                   legacy_source_table = %s,
                   legacy_document_no = %s,
                   legacy_document_state = %s,
                   note = %s,
                   write_date = NOW()
             WHERE id = %s
            """,
            [
                values["claim_type"],
                values["state"],
                values["project_id"],
                values["applicant_name"],
                values["payment_account_name"],
                values["date_claim"],
                values["expense_type"],
                values["summary"],
                values["amount"],
                values["approved_amount"],
                values["legacy_source_table"],
                values["legacy_document_no"],
                values["legacy_document_state"],
                values["note"],
                existing.id,
            ],
        )
        updated += 1
        continue
    values["name"] = f"KKD-{document_date.strftime('%Y%m%d')}-{created + 1:05d}"
    Claim.create(values)
    created += 1

env.cr.commit()  # noqa: F821

after = Claim.search_count([("claim_type", "=", "expense"), ("expense_type", "=", "扣款单")])
visible = Claim.search_count([("claim_type", "=", "expense"), ("expense_type", "=", "扣款单")])
expected_visible = candidate_count - skipped_missing_project - skipped_no_amount

result = {
    "mode": "fresh_db_deduction_bill_projection_write",
    "source_domain": source_domain,
    "candidate_count": candidate_count,
    "before_deduction_bill": before,
    "created": created,
    "updated": updated,
    "skipped_missing_project": skipped_missing_project,
    "skipped_no_amount": skipped_no_amount,
    "expected_visible_rows": expected_visible,
    "after_deduction_bill": after,
    "visible_rows": visible,
    "status": "PASS" if visible >= expected_visible and after > before else "REVIEW",
}

output_json.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, ensure_ascii=False, indent=2))
