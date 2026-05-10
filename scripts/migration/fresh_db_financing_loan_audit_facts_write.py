#!/usr/bin/env python3
"""Backfill legacy financing/borrowing audit fields into neutral and runtime records."""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path


def repo_root() -> Path:
    env_root = os.getenv("MIGRATION_REPO_ROOT")
    candidates = []
    if env_root:
        candidates.append(Path(env_root))
    candidates.extend([Path("/mnt"), Path.cwd()])
    for candidate in candidates:
        if (candidate / "artifacts/migration/fresh_db_financing_loan_audit_facts_payload_v1.csv").exists():
            return candidate
    return Path.cwd()


def artifact_root() -> Path:
    root = os.getenv("MIGRATION_ARTIFACT_ROOT") or os.getenv("HISTORY_CONTINUITY_ARTIFACT_ROOT")
    if root:
        return Path(root)
    candidates = [
        repo_root() / "artifacts/migration",
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


def clean(value: object) -> str:
    return "" if value is None else str(value).strip()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


allowlist = {item.strip() for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "").split(",") if item.strip()}
if allowlist and env.cr.dbname not in allowlist:  # noqa: F821
    raise RuntimeError({"db_name_not_allowed_for_replay": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821

REPO_ROOT = repo_root()
INPUT_CSV = REPO_ROOT / "artifacts/migration/fresh_db_financing_loan_audit_facts_payload_v1.csv"
OUTPUT_JSON = artifact_root() / "fresh_db_financing_loan_audit_facts_write_result_v1.json"
rows = read_csv(INPUT_CSV)

before_neutral_blank = env["sc.legacy.financing.loan.fact"].sudo().search_count([("creator_name", "=", False)])  # noqa: F821
before_runtime_blank = env["sc.financing.loan"].sudo().search_count([("creator_name", "=", False), ("source_origin", "=", "legacy")])  # noqa: F821

updated_neutral = 0
updated_runtime = 0
matched_rows = 0

for row in rows:
    source_table = clean(row.get("legacy_source_table"))
    legacy_id = clean(row.get("legacy_record_id"))
    if not source_table or not legacy_id:
        continue
    vals = {
        "creator_legacy_user_id": clean(row.get("creator_legacy_user_id")) or None,
        "creator_name": clean(row.get("creator_name")) or None,
        "created_time": clean(row.get("created_time")) or None,
        "modifier_legacy_user_id": clean(row.get("modifier_legacy_user_id")) or None,
        "modifier_name": clean(row.get("modifier_name")) or None,
        "modified_time": clean(row.get("modified_time")) or None,
    }
    env.cr.execute(  # noqa: F821
        """
        UPDATE sc_legacy_financing_loan_fact
        SET creator_legacy_user_id = %s,
            creator_name = %s,
            created_time = NULLIF(%s, '')::timestamp,
            modifier_legacy_user_id = %s,
            modifier_name = %s,
            modified_time = NULLIF(%s, '')::timestamp,
            write_date = NOW()
        WHERE legacy_source_table = %s
          AND legacy_record_id = %s
        """,
        [
            vals["creator_legacy_user_id"],
            vals["creator_name"],
            vals["created_time"] or "",
            vals["modifier_legacy_user_id"],
            vals["modifier_name"],
            vals["modified_time"] or "",
            source_table,
            legacy_id,
        ],
    )
    neutral_count = env.cr.rowcount  # noqa: F821
    updated_neutral += neutral_count
    env.cr.execute(  # noqa: F821
        """
        UPDATE sc_financing_loan
        SET creator_legacy_user_id = %s,
            creator_name = %s,
            created_time = NULLIF(%s, '')::timestamp,
            write_uid = 1,
            write_date = NOW()
        WHERE legacy_source_model = 'sc.legacy.financing.loan.fact'
          AND legacy_source_table = %s
          AND legacy_record_id = %s
        """,
        [
            vals["creator_legacy_user_id"],
            vals["creator_name"],
            vals["created_time"] or "",
            source_table,
            legacy_id,
        ],
    )
    runtime_count = env.cr.rowcount  # noqa: F821
    updated_runtime += runtime_count
    if neutral_count or runtime_count:
        matched_rows += 1

env.cr.commit()  # noqa: F821

after_neutral_blank = env["sc.legacy.financing.loan.fact"].sudo().search_count([("creator_name", "=", False)])  # noqa: F821
after_runtime_blank = env["sc.financing.loan"].sudo().search_count([("creator_name", "=", False), ("source_origin", "=", "legacy")])  # noqa: F821
borrow_domain = [
    ("loan_type", "=", "borrowing_request"),
    ("purpose", "ilike", "借"),
    ("purpose", "ilike", "项目"),
    ("purpose", "ilike", "款"),
    ("active", "=", True),
]
borrow_count = env["sc.financing.loan"].sudo().search_count(borrow_domain)  # noqa: F821
borrow_blank_creator = env["sc.financing.loan"].sudo().search_count(borrow_domain + [("creator_name", "=", False)])  # noqa: F821

payload = {
    "status": "PASS" if matched_rows else "REVIEW",
    "mode": "fresh_db_financing_loan_audit_facts_write",
    "database": env.cr.dbname,  # noqa: F821
    "input_rows": len(rows),
    "matched_rows": matched_rows,
    "updated_neutral": updated_neutral,
    "updated_runtime": updated_runtime,
    "before_neutral_blank_creator": before_neutral_blank,
    "after_neutral_blank_creator": after_neutral_blank,
    "before_runtime_blank_creator": before_runtime_blank,
    "after_runtime_blank_creator": after_runtime_blank,
    "contractor_project_borrow_count": borrow_count,
    "contractor_project_borrow_blank_creator": borrow_blank_creator,
}
OUTPUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("FINANCING_LOAN_AUDIT_FACTS_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
