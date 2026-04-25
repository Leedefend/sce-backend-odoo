#!/usr/bin/env python3
"""Replay 57 contract header retry rows into sc_migration_fresh."""

from __future__ import annotations

import csv
import json
import os
from collections import Counter
from pathlib import Path


def repo_root() -> Path:
    env_root = os.getenv("MIGRATION_REPO_ROOT")
    candidates = []
    if env_root:
        candidates.append(Path(env_root))
    candidates.extend([Path("/mnt"), Path.cwd()])
    for candidate in candidates:
        if (candidate / "artifacts/migration/contract_partner_source_57_design_rows_v1.csv").exists():
            return candidate
    return Path.cwd()


def ensure_allowed_db() -> None:
    allowlist = {
        item.strip()
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_migration_fresh").split(",")
        if item.strip()
    }
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_replay": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


REPO_ROOT = repo_root()
ARTIFACT_ROOT = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", str(REPO_ROOT / "artifacts/migration")))
DESIGN_CSV = REPO_ROOT / "artifacts/migration/contract_partner_source_57_design_rows_v1.csv"
RESOLUTION_CSV = REPO_ROOT / "artifacts/migration/fresh_db_contract_partner_12_anchor_replay_resolution_v1.csv"
OUTPUT_JSON = ARTIFACT_ROOT / "fresh_db_contract_57_retry_write_result_v1.json"
ROLLBACK_CSV = ARTIFACT_ROOT / "fresh_db_contract_57_retry_rollback_targets_v1.csv"
PRE_SNAPSHOT_CSV = ARTIFACT_ROOT / "fresh_db_contract_57_retry_pre_write_snapshot_v1.csv"
POST_SNAPSHOT_CSV = ARTIFACT_ROOT / "fresh_db_contract_57_retry_post_write_snapshot_v1.csv"
EXPECTED_ROWS = 57
SAFE_FIELDS = {
    "legacy_contract_id",
    "legacy_project_id",
    "project_id",
    "partner_id",
    "subject",
    "type",
    "legacy_counterparty_text",
}
SNAPSHOT_FIELDS = [
    "contract_id",
    "legacy_contract_id",
    "legacy_project_id",
    "project_id",
    "partner_id",
    "name",
    "subject",
    "type",
    "state",
    "line_count",
    "is_locked",
]


def clean(value: object) -> str:
    return "" if value is None else str(value).strip()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def snapshot(model, path: Path, ids: list[str]):
    records = model.search([("legacy_contract_id", "in", ids)], order="legacy_contract_id,id")
    rows = []
    for rec in records:
        rows.append(
            {
                "contract_id": rec.id,
                "legacy_contract_id": rec.legacy_contract_id or "",
                "legacy_project_id": rec.legacy_project_id or "",
                "project_id": rec.project_id.id or "",
                "partner_id": rec.partner_id.id or "",
                "name": rec.name or "",
                "subject": rec.subject or "",
                "type": rec.type or "",
                "state": rec.state or "",
                "line_count": len(rec.line_ids),
                "is_locked": bool(rec.is_locked),
            }
        )
    write_csv(path, SNAPSHOT_FIELDS, rows)
    return records


def resolution_index(rows: list[dict[str, str]]) -> dict[str, int]:
    return {clean(row.get("anchor_name")): int(clean(row.get("partner_id"))) for row in rows if clean(row.get("partner_id"))}


def build_vals(row: dict[str, str], project_id: int, partner_id: int) -> dict[str, object]:
    vals = {
        "legacy_contract_id": clean(row.get("legacy_contract_id")),
        "legacy_project_id": clean(row.get("legacy_project_id")),
        "project_id": project_id,
        "partner_id": partner_id,
        "subject": clean(row.get("contract_subject")),
        "type": clean(row.get("direction")),
        "legacy_counterparty_text": clean(row.get("counterparty_text")),
    }
    return {field: value for field, value in vals.items() if value not in ("", None)}


ensure_allowed_db()

Contract = env["construction.contract"].sudo()  # noqa: F821
Project = env["project.project"].sudo()  # noqa: F821
Partner = env["res.partner"].sudo()  # noqa: F821

design_rows = read_csv(DESIGN_CSV)
partner_by_name = resolution_index(read_csv(RESOLUTION_CSV))
ids = [clean(row.get("legacy_contract_id")) for row in design_rows]
duplicate_ids = sorted(identity for identity, count in Counter(ids).items() if identity and count > 1)
pre_records = snapshot(Contract, PRE_SNAPSHOT_CSV, ids)

errors: list[dict[str, object]] = []
if len(design_rows) != EXPECTED_ROWS:
    errors.append({"error": "unexpected_row_count", "actual": len(design_rows), "expected": EXPECTED_ROWS})
if duplicate_ids:
    errors.append({"error": "duplicate_input_legacy_contract_id", "ids": duplicate_ids[:20]})
if pre_records:
    errors.append({"error": "pre_existing_contracts", "count": len(pre_records), "samples": pre_records[:20].mapped("id")})

create_vals = []
for index, row in enumerate(design_rows, start=2):
    legacy_project_id = clean(row.get("legacy_project_id"))
    counterparty = clean(row.get("counterparty_text"))
    project = Project.search([("legacy_project_id", "=", legacy_project_id)], limit=2)
    partner_id = partner_by_name.get(counterparty)
    if len(project) != 1:
        errors.append({"line": index, "error": "project_anchor_not_unique", "legacy_project_id": legacy_project_id, "count": len(project)})
        continue
    if not partner_id or not Partner.browse(partner_id).exists():
        errors.append({"line": index, "error": "partner_anchor_missing", "counterparty_text": counterparty, "partner_id": partner_id or ""})
        continue
    vals = build_vals(row, project.id, partner_id)
    unsafe_fields = sorted(set(vals) - SAFE_FIELDS)
    if unsafe_fields:
        errors.append({"line": index, "error": "unsafe_fields", "fields": unsafe_fields})
    if vals.get("type") not in {"out", "in"}:
        errors.append({"line": index, "error": "invalid_contract_type", "type": vals.get("type")})
    if not vals.get("subject"):
        errors.append({"line": index, "error": "missing_subject"})
    create_vals.append(vals)

if errors:
    env.cr.rollback()  # noqa: F821
    raise RuntimeError({"precheck_failed": errors[:40]})

created = []
try:
    for vals in create_vals:
        rec = Contract.create(vals)
        created.append(
            {
                "contract_id": rec.id,
                "legacy_contract_id": rec.legacy_contract_id or "",
                "legacy_project_id": rec.legacy_project_id or "",
                "project_id": rec.project_id.id or "",
                "partner_id": rec.partner_id.id or "",
                "name": rec.name or "",
                "subject": rec.subject or "",
                "type": rec.type or "",
                "state": rec.state or "",
            }
        )
    env.cr.commit()  # noqa: F821
except Exception:
    env.cr.rollback()  # noqa: F821
    raise

post_records = snapshot(Contract, POST_SNAPSHOT_CSV, ids)
grouped: dict[str, list[object]] = {}
for rec in post_records:
    grouped.setdefault(rec.legacy_contract_id or "", []).append(rec)

rollback_rows = []
for rec in post_records:
    rollback_rows.append(
        {
            "contract_id": rec.id,
            "legacy_contract_id": rec.legacy_contract_id or "",
            "legacy_project_id": rec.legacy_project_id or "",
            "project_id": rec.project_id.id or "",
            "partner_id": rec.partner_id.id or "",
            "name": rec.name or "",
            "subject": rec.subject or "",
            "type": rec.type or "",
            "state": rec.state or "",
            "line_count": len(rec.line_ids),
            "is_locked": bool(rec.is_locked),
        }
    )
write_csv(ROLLBACK_CSV, SNAPSHOT_FIELDS, rollback_rows)

post_errors = []
if len(created) != EXPECTED_ROWS:
    post_errors.append({"error": "created_count_not_57", "created": len(created)})
if len(post_records) != EXPECTED_ROWS:
    post_errors.append({"error": "post_write_match_count_not_57", "matched": len(post_records)})
if any(len(records) > 1 for records in grouped.values()):
    post_errors.append({"error": "duplicate_legacy_identity_matches"})

status = "PASS" if not post_errors else "FAIL"
result = {
    "status": status,
    "mode": "fresh_db_contract_57_retry_write",
    "database": env.cr.dbname,  # noqa: F821
    "target_model": "construction.contract",
    "input_rows": len(design_rows),
    "created_rows": len(created),
    "post_write_match_count": len(post_records),
    "rollback_target_rows": len(rollback_rows),
    "updated_rows": 0,
    "contract_line_rows": 0,
    "payment_rows": 0,
    "settlement_rows": 0,
    "accounting_rows": 0,
    "demo_targets_executed": 0,
    "post_errors": post_errors,
    "artifacts": {
        "pre_write_snapshot": str(PRE_SNAPSHOT_CSV),
        "post_write_snapshot": str(POST_SNAPSHOT_CSV),
        "rollback_targets": str(ROLLBACK_CSV),
    },
    "decision": "contract_57_retry_write_complete" if status == "PASS" else "STOP_REVIEW_REQUIRED",
    "next_step": "refresh fresh database replay manifest and continue remaining migration layers",
}
write_json(OUTPUT_JSON, result)
print(
    "FRESH_DB_CONTRACT_57_RETRY_WRITE="
    + json.dumps(
        {
            "status": status,
            "input_rows": len(design_rows),
            "created_rows": len(created),
            "post_write_match_count": len(post_records),
            "db_writes": len(created),
        },
        ensure_ascii=False,
        sort_keys=True,
    )
)
