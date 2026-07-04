#!/usr/bin/env python3
"""Replay blocked partner import candidates into sc.partner.import.review."""

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
INPUT_CSV = Path(
    os.getenv(
        "FRESH_DB_PARTNER_IMPORT_REVIEW_INPUT_CSV",
        str(REPO_ROOT / "artifacts/migration/partner_business_aligned_rebuild_v1/partner_import_review_queue_v1.csv"),
    )
)
OUTPUT_JSON = ARTIFACT_ROOT / "fresh_db_partner_import_review_replay_write_result_v1.json"
EXPECTED_ROWS_RAW = os.getenv("FRESH_DB_PARTNER_IMPORT_REVIEW_EXPECTED_ROWS", "1444").strip().lower()
EXPECTED_ROWS = None if EXPECTED_ROWS_RAW == "auto" else int(EXPECTED_ROWS_RAW)
SAFE_FIELDS = [
    "import_batch",
    "legacy_partner_source",
    "legacy_partner_id",
    "partner_name",
    "company_type",
    "review_reason",
    "review_state",
    "suggested_customer_rank",
    "suggested_supplier_rank",
    "sc_supplier_type",
    "sc_region",
    "street",
    "sc_registered_capital",
    "sc_business_scope",
    "sc_default_tax_rate",
    "sc_default_tax_rate_text",
    "vat",
    "sc_account_name",
    "sc_bank_name",
    "sc_bank_account",
    "source_created_by",
    "source_created_at",
    "source_document_state",
    "source_push_result",
    "source_project_name",
    "source_files",
    "review_flags",
    "gate_reason",
    "evidence",
]


def clean(value: object) -> str:
    return "" if value is None else str(value).strip()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def to_int(value: object) -> int:
    try:
        return int(float(clean(value) or "0"))
    except ValueError:
        return 0


def to_float(value: object) -> float:
    try:
        return float(clean(value) or "0")
    except ValueError:
        return 0.0


def vals_for(row: dict[str, str]) -> dict[str, object]:
    vals: dict[str, object] = {
        "import_batch": clean(row.get("import_batch")) or "partner_business_fit_v1",
        "legacy_partner_source": clean(row.get("legacy_partner_source")),
        "legacy_partner_id": clean(row.get("legacy_partner_id")),
        "partner_name": clean(row.get("partner_name")),
        "company_type": clean(row.get("company_type")) or "company",
        "review_reason": clean(row.get("review_reason")) or "mixed_blocker",
        "review_state": clean(row.get("review_state")) or "candidate",
        "suggested_customer_rank": to_int(row.get("suggested_customer_rank")),
        "suggested_supplier_rank": to_int(row.get("suggested_supplier_rank")),
        "sc_supplier_type": clean(row.get("sc_supplier_type")),
        "sc_region": clean(row.get("sc_region")),
        "street": clean(row.get("street")),
        "sc_registered_capital": clean(row.get("sc_registered_capital")),
        "sc_business_scope": clean(row.get("sc_business_scope")),
        "sc_default_tax_rate": to_float(row.get("sc_default_tax_rate")),
        "sc_default_tax_rate_text": clean(row.get("sc_default_tax_rate_text")),
        "vat": clean(row.get("vat")),
        "sc_account_name": clean(row.get("sc_account_name")),
        "sc_bank_name": clean(row.get("sc_bank_name")),
        "sc_bank_account": clean(row.get("sc_bank_account")),
        "source_created_by": clean(row.get("source_created_by")),
        "source_created_at": clean(row.get("source_created_at")),
        "source_document_state": clean(row.get("source_document_state")),
        "source_push_result": clean(row.get("source_push_result")),
        "source_project_name": clean(row.get("source_project_name")),
        "source_files": clean(row.get("source_files")),
        "review_flags": clean(row.get("review_flags")),
        "gate_reason": clean(row.get("gate_reason")),
        "evidence": clean(row.get("evidence")),
    }
    return {field: value for field, value in vals.items() if field in SAFE_FIELDS and value not in ("", None)}


ensure_allowed_db()

Review = env["sc.partner.import.review"].sudo()  # noqa: F821
missing_fields = [field for field in SAFE_FIELDS if field not in Review._fields]
if missing_fields:
    raise RuntimeError({"missing_review_fields": missing_fields})

rows = read_csv(INPUT_CSV)
errors: list[dict[str, object]] = []
if EXPECTED_ROWS is not None and len(rows) != EXPECTED_ROWS:
    errors.append({"error": "unexpected_row_count", "actual": len(rows), "expected": EXPECTED_ROWS})

keys = [(clean(row.get("import_batch")), clean(row.get("legacy_partner_source")), clean(row.get("legacy_partner_id"))) for row in rows]
duplicates = [key for key, count in Counter(keys).items() if count > 1]
if duplicates:
    errors.append({"error": "duplicate_review_identity", "samples": duplicates[:20]})
for index, row in enumerate(rows, start=2):
    if not clean(row.get("legacy_partner_source")) or not clean(row.get("legacy_partner_id")) or not clean(row.get("partner_name")):
        errors.append({"line": index, "error": "missing_required_identity"})
if errors:
    env.cr.rollback()  # noqa: F821
    raise RuntimeError({"precheck_failed": errors[:30]})

created = 0
updated = 0
try:
    for row in rows:
        vals = vals_for(row)
        domain = [
            ("import_batch", "=", vals["import_batch"]),
            ("legacy_partner_source", "=", vals["legacy_partner_source"]),
            ("legacy_partner_id", "=", vals["legacy_partner_id"]),
        ]
        rec = Review.search(domain)
        if rec:
            rec[:1].write(vals)
            updated += 1
        else:
            Review.create(vals)
            created += 1
    env.cr.commit()  # noqa: F821
except Exception:
    env.cr.rollback()  # noqa: F821
    raise

expected_count = len(rows) if EXPECTED_ROWS is None else EXPECTED_ROWS
post_count = 0
for import_batch, source, legacy_id in keys:
    post_count += Review.search_count(
        [
            ("import_batch", "=", import_batch),
            ("legacy_partner_source", "=", source),
            ("legacy_partner_id", "=", legacy_id),
        ]
    )
status = "PASS" if created + updated == expected_count and post_count == expected_count else "FAIL"
result = {
    "status": status,
    "mode": "fresh_db_partner_import_review_replay_write",
    "database": env.cr.dbname,  # noqa: F821
    "target_model": "sc.partner.import.review",
    "input_rows": len(rows),
    "expected_rows": EXPECTED_ROWS if EXPECTED_ROWS is not None else "auto",
    "created_rows": created,
    "updated_rows": updated,
    "post_write_identity_count": post_count,
    "db_writes": created + updated,
    "write_payload": str(INPUT_CSV),
}
write_json(OUTPUT_JSON, result)
print(
    "FRESH_DB_PARTNER_IMPORT_REVIEW_REPLAY_WRITE="
    + json.dumps(
        {
            "status": status,
            "input_rows": len(rows),
            "created_rows": created,
            "updated_rows": updated,
            "post_write_identity_count": post_count,
            "db_writes": created + updated,
        },
        ensure_ascii=False,
        sort_keys=True,
    )
)
