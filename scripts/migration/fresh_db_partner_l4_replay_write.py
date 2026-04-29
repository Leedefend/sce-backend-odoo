#!/usr/bin/env python3
"""Replay partner L4 anchors into sc_migration_fresh."""

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
        if (candidate / "artifacts/migration/fresh_db_replay_manifest_v1.json").exists():
            return candidate
    return Path.cwd()


def ensure_allowed_db() -> None:
    allowlist = {item.strip() for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_migration_fresh").split(",") if item.strip()}
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_replay": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


REPO_ROOT = repo_root()
ARTIFACT_ROOT = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", str(REPO_ROOT / "artifacts/migration")))
INPUT_CSV = REPO_ROOT / "artifacts/migration/fresh_db_partner_l4_replay_payload_v1.csv"
OUTPUT_JSON = ARTIFACT_ROOT / "fresh_db_partner_l4_replay_write_result_v1.json"
ROLLBACK_CSV = ARTIFACT_ROOT / "fresh_db_partner_l4_replay_rollback_targets_v1.csv"
EXPECTED_ROWS = int(os.getenv("FRESH_DB_PARTNER_L4_EXPECTED_ROWS", "6541"))
SAFE_FIELDS = [
    "name",
    "company_type",
    "customer_rank",
    "supplier_rank",
    "legacy_partner_id",
    "legacy_partner_source",
    "legacy_partner_name",
    "legacy_credit_code",
    "legacy_tax_no",
    "legacy_deleted_flag",
    "legacy_source_evidence",
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


def build_vals(row: dict[str, str]) -> dict[str, object]:
    source = clean(row.get("legacy_partner_source"))
    source_type = clean(row.get("source_type"))
    tax_no = clean(row.get("tax_no"))
    is_supplier = source == "supplier" or source_type == "supplier"
    is_company_supplier = source == "company_supplier"
    return {
        "name": clean(row.get("name")),
        "company_type": "company",
        "customer_rank": 1 if not is_supplier or is_company_supplier else 0,
        "supplier_rank": 1 if is_supplier or is_company_supplier else 0,
        "legacy_partner_id": clean(row.get("legacy_partner_id")),
        "legacy_partner_source": source,
        "legacy_partner_name": clean(row.get("name")),
        "legacy_credit_code": tax_no,
        "legacy_tax_no": tax_no,
        "legacy_deleted_flag": clean(row.get("deleted_flag")),
        "legacy_source_evidence": clean(row.get("evidence_file")) or "fresh_db_partner_l4_replay_payload_v1.csv",
    }


ensure_allowed_db()

Partner = env["res.partner"].sudo()  # noqa: F821
missing_fields = [field for field in SAFE_FIELDS if field not in Partner._fields]
if missing_fields:
    raise RuntimeError({"missing_partner_fields": missing_fields})

rows = read_csv(INPUT_CSV)
errors: list[dict[str, object]] = []
if len(rows) != EXPECTED_ROWS:
    errors.append({"error": "unexpected_row_count", "actual": len(rows), "expected": EXPECTED_ROWS})

keys = [(clean(row.get("legacy_partner_source")), clean(row.get("legacy_partner_id"))) for row in rows]
key_counts = Counter(keys)
duplicates = [key for key, count in key_counts.items() if count > 1]
if duplicates:
    errors.append({"error": "duplicate_payload_identity", "samples": duplicates[:20]})
for index, row in enumerate(rows, start=2):
    if not clean(row.get("legacy_partner_source")) or not clean(row.get("legacy_partner_id")):
        errors.append({"line": index, "error": "missing_identity"})
    if not clean(row.get("name")):
        errors.append({"line": index, "error": "missing_name"})

existing = Partner.browse()
for source, legacy_id in keys:
    existing |= Partner.search([("legacy_partner_source", "=", source), ("legacy_partner_id", "=", legacy_id)], limit=1)
if existing:
    errors.append({"error": "target_identity_not_empty", "count": len(existing), "samples": existing[:20].mapped("id")})
if errors:
    env.cr.rollback()  # noqa: F821
    raise RuntimeError({"precheck_failed": errors[:30]})

created_rows: list[dict[str, object]] = []
try:
    for row in rows:
        vals = build_vals(row)
        rec = Partner.create({field: value for field, value in vals.items() if value not in ("", None)})
        created_rows.append(
            {
                "id": rec.id,
                "legacy_partner_source": rec.legacy_partner_source or "",
                "legacy_partner_id": rec.legacy_partner_id or "",
                "name": rec.name or "",
            }
        )
    env.cr.commit()  # noqa: F821
except Exception:
    env.cr.rollback()  # noqa: F821
    raise

post_count = 0
for source, legacy_id in keys:
    post_count += Partner.search_count([("legacy_partner_source", "=", source), ("legacy_partner_id", "=", legacy_id)])

status = "PASS" if len(created_rows) == EXPECTED_ROWS and post_count == EXPECTED_ROWS else "FAIL"
result = {
    "status": status,
    "mode": "fresh_db_partner_l4_replay_write",
    "database": env.cr.dbname,  # noqa: F821
    "target_model": "res.partner",
    "input_rows": len(rows),
    "created_rows": len(created_rows),
    "post_write_identity_count": post_count,
    "skipped_existing": 0,
    "db_writes": len(created_rows),
    "demo_targets_executed": 0,
    "write_payload": str(INPUT_CSV),
    "rollback_targets": str(ROLLBACK_CSV),
    "decision": "partner_l4_replay_write_complete" if status == "PASS" else "STOP_REVIEW_REQUIRED",
    "next_step": "replay project anchors into sc_migration_fresh",
}
write_csv(
    ROLLBACK_CSV,
    ["id", "legacy_partner_source", "legacy_partner_id", "name"],
    created_rows,
)
write_json(OUTPUT_JSON, result)
print(
    "FRESH_DB_PARTNER_L4_REPLAY_WRITE="
    + json.dumps(
        {
            "status": status,
            "input_rows": len(rows),
            "created_rows": len(created_rows),
            "post_write_identity_count": post_count,
            "db_writes": len(created_rows),
        },
        ensure_ascii=False,
        sort_keys=True,
    )
)
