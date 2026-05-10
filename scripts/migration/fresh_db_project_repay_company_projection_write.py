#!/usr/bin/env python3
"""Project legacy project-to-company repayments into the user-facing claim entry."""

from __future__ import annotations

import json
import os
from pathlib import Path


def artifact_root() -> Path:
    root = os.environ.get("MIGRATION_ARTIFACT_ROOT") or os.environ.get("HISTORY_CONTINUITY_ARTIFACT_ROOT")
    if root:
        return Path(root)
    file_name = globals().get("__file__")
    if file_name:
        return Path(file_name).resolve().parents[2] / "artifacts" / "migration"
    return Path.cwd() / "artifacts" / "migration"


def clean(value) -> str | None:
    text = str(value or "").strip()
    return text or None


output_json = artifact_root() / "fresh_db_project_repay_company_projection_write_result_v1.json"
output_json.parent.mkdir(parents=True, exist_ok=True)

Claim = env["sc.expense.claim"].sudo()  # noqa: F821
Line = env["sc.legacy.account.transaction.line"].sudo().with_context(active_test=False)  # noqa: F821

domain = [
    ("source_table", "=", "C_FKGL_ZHJZJWL"),
    ("direction", "=", "income"),
    ("amount", ">", 0),
    ("project_id", "!=", False),
    "|",
    "|",
    ("source_summary", "ilike", "归还公司款"),
    ("source_summary", "ilike", "还公司款"),
    ("source_summary", "ilike", "项目还款"),
]
target_domain = [("claim_type", "=", "project_company_repay"), ("expense_type", "=", "项目还公司款登记")]

candidate_count = Line.search_count(domain)
before = Claim.search_count(target_domain)
created = 0
updated = 0

for line in Line.search(domain, order="transaction_date desc, id desc"):
    values = {
        "source_origin": "legacy",
        "claim_type": "project_company_repay",
        "state": "legacy_confirmed",
        "project_id": line.project_id.id,
        "date_claim": line.transaction_date,
        "fill_date": line.transaction_date,
        "expense_type": "项目还公司款登记",
        "summary": clean(line.source_summary) or "项目还公司款登记",
        "amount": float(line.amount or 0.0),
        "approved_amount": float(line.amount or 0.0),
        "payee": clean(line.account_name),
        "receipt_account_name": clean(line.account_name),
        "payee_account": clean(line.account_legacy_id),
        "payment_account_name": clean(line.counterparty_account_name),
        "legacy_source_model": "sc.legacy.account.transaction.line",
        "legacy_source_table": line.source_table,
        "legacy_record_id": line.source_key,
        "legacy_document_no": clean(line.document_no),
        "legacy_document_state": clean(line.document_state) or "历史已确认",
        "note": (
            "[migration:project_repay_company] "
            f"legacy_account_transaction_line_id={line.id}; "
            f"source_key={line.source_key}; "
            f"source_summary={clean(line.source_summary) or ''}"
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
                expense_type = %s,
                summary = %s,
                amount = %s,
                approved_amount = %s,
                date_claim = %s,
                fill_date = %s,
                payee = %s,
                receipt_account_name = %s,
                payee_account = %s,
                payment_account_name = %s,
                legacy_document_no = %s,
                legacy_document_state = %s,
                note = %s,
                write_uid = 1,
                write_date = NOW()
            WHERE id = %s
            """,
            [
                values["claim_type"],
                values["expense_type"],
                values["summary"],
                values["amount"],
                values["approved_amount"],
                values["date_claim"],
                values["fill_date"],
                values["payee"],
                values["receipt_account_name"],
                values["payee_account"],
                values["payment_account_name"],
                values["legacy_document_no"],
                values["legacy_document_state"],
                values["note"],
                existing.id,
            ],
        )
        updated += 1
        continue
    values["name"] = f"XMHGS-{line.transaction_date.strftime('%Y%m%d')}-{created + 1:04d}"
    Claim.create(values)
    created += 1

env.cr.commit()  # noqa: F821

after = Claim.search_count(target_domain)
visible = Claim.search_count(target_domain + [("active", "=", True)])
result = {
    "mode": "fresh_db_project_repay_company_projection_write",
    "source_domain": domain,
    "candidate_count": candidate_count,
    "before_project_repay_company": before,
    "created": created,
    "updated": updated,
    "after_project_repay_company": after,
    "visible_rows": visible,
    "amount_sum": sum(Claim.search(target_domain).mapped("amount")),
    "status": "PASS" if after == candidate_count and visible == candidate_count else "FAIL",
}
output_json.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, ensure_ascii=False, indent=2))
if result["status"] != "PASS":
    raise SystemExit(1)
