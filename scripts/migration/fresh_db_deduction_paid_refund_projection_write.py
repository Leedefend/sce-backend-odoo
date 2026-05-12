"""Project legacy deduction payment refund lines into the user-facing refund entry."""

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
    candidates = [
        repo_root() / "artifacts" / "migration",
        Path("/mnt/artifacts/migration"),
        Path(f"/tmp/history_continuity/{env.cr.dbname}/adhoc"),  # noqa: F821
    ]
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


output_json = artifact_root() / "fresh_db_deduction_paid_refund_projection_write_result_v1.json"
output_json.parent.mkdir(parents=True, exist_ok=True)

Claim = env["sc.expense.claim"].sudo()  # noqa: F821
Line = env["sc.legacy.account.transaction.line"].sudo()  # noqa: F821

source_domain = [
    ("source_table", "=", "T_KK_SJTHB_CB"),
    ("direction", "=", "income"),
    ("amount", ">", 0),
    ("active", "=", True),
    ("project_id", "!=", False),
]
target_domain = [("claim_type", "=", "deduction_refund"), ("expense_type", "=", "扣款实缴退回")]
candidate_count = Line.search_count(source_domain)
before = Claim.search_count(target_domain)

created = 0
updated = 0
skipped_missing_project = 0

for line in Line.search(source_domain, order="transaction_date desc, id desc"):
    if not line.project_id:
        skipped_missing_project += 1
        continue
    date_claim = line.transaction_date or fields.Date.context_today(Claim)
    summary = " / ".join(part for part in ["扣款实缴退回", line.category or "", line.source_summary or ""] if part)
    values = {
        "source_origin": "legacy",
        "claim_type": "deduction_refund",
        "state": "legacy_confirmed",
        "project_id": line.project_id.id,
        "payment_account_name": line.counterparty_account_name,
        "receipt_account_name": line.account_name,
        "payee": line.counterparty_account_name,
        "date_claim": date_claim,
        "expense_type": "扣款实缴退回",
        "summary": summary[:255],
        "amount": line.amount,
        "approved_amount": line.amount,
        "legacy_source_model": "sc.legacy.account.transaction.line",
        "legacy_source_table": line.source_table,
        "legacy_record_id": line.source_key,
        "legacy_document_no": line.document_no,
        "legacy_document_state": line.document_state or "历史已确认",
        "creator_legacy_user_id": line.creator_legacy_user_id,
        "creator_name": line.creator_name,
        "created_time": line.created_time,
        "note": (
            "[migration:deduction_paid_refund] "
            f"legacy_account_transaction_line_id={line.id}; "
            f"source_key={line.source_key}; "
            f"account={line.account_name or ''}; "
            f"counterparty={line.counterparty_account_name or ''}"
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
                   payment_account_name = %s,
                   receipt_account_name = %s,
                   payee = %s,
                   date_claim = %s,
                   expense_type = %s,
                   summary = %s,
                   amount = %s,
                   approved_amount = %s,
                   legacy_source_table = %s,
                   legacy_document_no = %s,
                   legacy_document_state = %s,
                   creator_legacy_user_id = %s,
                   creator_name = %s,
                   created_time = %s,
                   note = %s,
                   write_date = NOW()
             WHERE id = %s
            """,
            [
                values["claim_type"],
                values["state"],
                values["project_id"],
                values["payment_account_name"],
                values["receipt_account_name"],
                values["payee"],
                values["date_claim"],
                values["expense_type"],
                values["summary"],
                values["amount"],
                values["approved_amount"],
                values["legacy_source_table"],
                values["legacy_document_no"],
                values["legacy_document_state"],
                values["creator_legacy_user_id"],
                values["creator_name"],
                values["created_time"],
                values["note"],
                existing.id,
            ],
        )
        updated += 1
        continue
    values["name"] = f"KKSJTH-{date_claim.strftime('%Y%m%d')}-{created + 1:04d}"
    Claim.create(values)
    created += 1

env.cr.commit()  # noqa: F821

after = Claim.search_count(target_domain)
visible = Claim.search_count(target_domain)
expected_visible = candidate_count - skipped_missing_project

result = {
    "mode": "fresh_db_deduction_paid_refund_projection_write",
    "source_domain": source_domain,
    "target_domain": target_domain,
    "candidate_count": candidate_count,
    "before_deduction_paid_refund": before,
    "created": created,
    "updated": updated,
    "skipped_missing_project": skipped_missing_project,
    "expected_visible_rows": expected_visible,
    "after_deduction_paid_refund": after,
    "visible_rows": visible,
    "status": "PASS" if visible >= expected_visible and (created + updated > 0 or after == before) else "REVIEW",
}

output_json.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, ensure_ascii=False, indent=2))
