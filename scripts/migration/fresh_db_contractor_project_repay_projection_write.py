"""Project contractor project repayment lines into the user-facing claim entry."""

from __future__ import annotations

import json
import os
from pathlib import Path


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


output_json = artifact_root() / "fresh_db_contractor_project_repay_projection_write_result_v1.json"
output_json.parent.mkdir(parents=True, exist_ok=True)

Claim = env["sc.expense.claim"].sudo()  # noqa: F821
Line = env["sc.legacy.account.transaction.line"].sudo()  # noqa: F821

domain = [
    ("source_table", "=", "C_FKGL_ZHJZJWL"),
    ("direction", "=", "income"),
    ("amount", ">", 0),
]
candidate_count = Line.search_count(domain)
before = Claim.search_count([("expense_type", "=", "承包人还项目款")])

created = 0
updated = 0
skipped_missing_project = 0

for line in Line.search(domain, order="transaction_date desc, id desc"):
    if not line.project_id:
        skipped_missing_project += 1
        continue
    values = {
        "source_origin": "legacy",
        "claim_type": "deposit_receive",
        "state": "legacy_confirmed",
        "project_id": line.project_id.id,
        "date_claim": line.transaction_date,
        "expense_type": "承包人还项目款",
        "summary": "承包人还项目款",
        "amount": line.amount,
        "approved_amount": line.amount,
        "legacy_source_model": "sc.legacy.account.transaction.line",
        "legacy_source_table": line.source_table,
        "legacy_record_id": line.source_key,
        "legacy_document_no": line.source_key.split(":", 1)[0],
        "legacy_document_state": "历史已确认",
        "note": (
            "[migration:contractor_project_repay] "
            f"legacy_account_transaction_line_id={line.id}; "
            f"source_key={line.source_key}; source_table={line.source_table}"
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
        existing.write(
            {
                "claim_type": values["claim_type"],
                "expense_type": values["expense_type"],
                "summary": values["summary"],
                "amount": values["amount"],
                "approved_amount": values["approved_amount"],
                "date_claim": values["date_claim"],
                "legacy_document_state": values["legacy_document_state"],
                "note": values["note"],
            }
        )
        updated += 1
        continue
    values["name"] = f"CBRHK-{line.transaction_date.strftime('%Y%m%d')}-{created + 1:03d}"
    Claim.create(values)
    created += 1

env.cr.commit()  # noqa: F821

after = Claim.search_count([("expense_type", "=", "承包人还项目款")])
visible = Claim.search_count(
    [("claim_type", "in", ["expense", "deposit_receive"]), ("expense_type", "=", "承包人还项目款")]
)

result = {
    "mode": "fresh_db_contractor_project_repay_projection_write",
    "source_domain": domain,
    "candidate_count": candidate_count,
    "before_contractor_project_repay": before,
    "created": created,
    "updated": updated,
    "skipped_missing_project": skipped_missing_project,
    "after_contractor_project_repay": after,
    "visible_rows": visible,
    "status": "PASS" if visible >= candidate_count - skipped_missing_project and after > before else "REVIEW",
}

output_json.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, ensure_ascii=False, indent=2))
