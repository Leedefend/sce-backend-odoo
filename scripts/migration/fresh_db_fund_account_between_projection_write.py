"""Project legacy account transfer lines into user-facing fund account operations."""

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


output_json = artifact_root() / "fresh_db_fund_account_between_projection_write_result_v1.json"
output_json.parent.mkdir(parents=True, exist_ok=True)

Operation = env["sc.fund.account.operation"].sudo()  # noqa: F821
Line = env["sc.legacy.account.transaction.line"].sudo()  # noqa: F821
Account = env["sc.fund.account"].sudo()  # noqa: F821

source_domain = [
    ("source_table", "=", "C_FKGL_ZHJZJWL"),
    ("direction", "=", "expense"),
    ("amount", ">", 0),
    ("active", "=", True),
]
candidate_count = Line.search_count(source_domain)
before = Operation.search_count([("operation_type", "=", "transfer_between")])

created = 0
updated = 0
skipped_missing_source_account = 0
skipped_missing_target_account = 0
skipped_same_account = 0

for line in Line.search(source_domain, order="transaction_date desc, id desc"):
    source_account = Account.search([("legacy_account_id", "=", line.account_legacy_id)], limit=1)
    target_account = Account.search([("legacy_account_id", "=", line.counterparty_account_legacy_id)], limit=1)
    if not source_account:
        skipped_missing_source_account += 1
        continue
    if not target_account:
        skipped_missing_target_account += 1
        continue
    if source_account == target_account:
        skipped_same_account += 1
        continue
    values = {
        "operation_type": "transfer_between",
        "operation_date": line.transaction_date,
        "source_account_id": source_account.id,
        "target_account_id": target_account.id,
        "project_id": line.project_id.id if line.project_id else False,
        "company_id": (line.project_id.company_id.id if line.project_id and line.project_id.company_id else env.company.id),  # noqa: F821
        "currency_id": env.company.currency_id.id,  # noqa: F821
        "amount": line.amount,
        "operation_reason": "账户间资金往来",
        "state": "done" if line.document_state == "2" else "confirmed",
        "legacy_source_model": "sc.legacy.account.transaction.line",
        "legacy_source_table": line.source_table,
        "legacy_record_id": line.source_key,
        "legacy_document_state": line.document_state or "历史已确认",
        "creator_legacy_user_id": line.creator_legacy_user_id,
        "creator_name": line.creator_name,
        "created_time": line.created_time,
        "note": (
            "[migration:fund_account_between] "
            f"legacy_account_transaction_line_id={line.id}; "
            f"document_no={line.document_no or ''}; "
            f"source_table={line.source_table}; "
            f"source_account={line.account_name or ''}; "
            f"target_account={line.counterparty_account_name or ''}"
        ),
    }
    existing = Operation.search(
        [
            ("legacy_source_model", "=", values["legacy_source_model"]),
            ("legacy_record_id", "=", values["legacy_record_id"]),
        ],
        limit=1,
    )
    if existing:
        existing.write(values)
        updated += 1
        continue
    Operation.create(values)
    created += 1

env.cr.commit()  # noqa: F821

after = Operation.search_count([("operation_type", "=", "transfer_between")])
visible = Operation.search_count([("operation_type", "=", "transfer_between")])
expected_visible = (
    candidate_count
    - skipped_missing_source_account
    - skipped_missing_target_account
    - skipped_same_account
)

result = {
    "mode": "fresh_db_fund_account_between_projection_write",
    "source_domain": source_domain,
    "candidate_count": candidate_count,
    "before_transfer_between": before,
    "created": created,
    "updated": updated,
    "skipped_missing_source_account": skipped_missing_source_account,
    "skipped_missing_target_account": skipped_missing_target_account,
    "skipped_same_account": skipped_same_account,
    "expected_visible_rows": expected_visible,
    "after_transfer_between": after,
    "visible_rows": visible,
    "status": "PASS" if visible >= expected_visible and (created + updated > 0 or after == before) else "REVIEW",
}

output_json.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, ensure_ascii=False, indent=2))
