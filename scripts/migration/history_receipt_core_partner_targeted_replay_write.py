#!/usr/bin/env python3
"""Replay targeted partner anchors required by receipt core facts."""

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
        if (candidate / "artifacts/migration/history_receipt_core_partner_targeted_replay_payload_v1.csv").exists():
            return candidate
    return Path.cwd()


def ensure_allowed_db() -> None:
    allowlist = {item.strip() for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_migration_fresh").split(",") if item.strip()}
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_replay": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


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


REPO_ROOT = repo_root()
ARTIFACT_ROOT = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", str(REPO_ROOT / "artifacts/migration")))
INPUT_CSV = REPO_ROOT / "artifacts/migration/history_receipt_core_partner_targeted_replay_payload_v1.csv"
INPUT_MANIFEST = REPO_ROOT / "artifacts/migration/history_receipt_core_partner_targeted_replay_adapter_result_v1.json"
OUTPUT_JSON = ARTIFACT_ROOT / "history_receipt_core_partner_targeted_replay_write_result_v1.json"
ROLLBACK_CSV = ARTIFACT_ROOT / "history_receipt_core_partner_targeted_replay_rollback_targets_v1.csv"

ensure_allowed_db()
manifest = json.loads(INPUT_MANIFEST.read_text(encoding="utf-8"))
rows = read_csv(INPUT_CSV)
expected_rows = int(manifest["payload_rows"])

Partner = env["res.partner"].sudo()  # noqa: F821
required_fields = [
    "name",
    "company_type",
    "legacy_partner_id",
    "legacy_partner_source",
    "legacy_partner_name",
    "legacy_credit_code",
    "legacy_tax_no",
    "legacy_source_evidence",
]
missing_fields = [field for field in required_fields if field not in Partner._fields]
if missing_fields:
    raise RuntimeError({"missing_partner_fields": missing_fields})

errors: list[dict[str, object]] = []
if len(rows) != expected_rows:
    errors.append({"error": "unexpected_row_count", "actual": len(rows), "expected": expected_rows})
id_counts = Counter(clean(row.get("legacy_partner_id")) for row in rows)
duplicates = [legacy_id for legacy_id, count in id_counts.items() if count > 1]
if duplicates:
    errors.append({"error": "duplicate_payload_legacy_partner_id", "samples": duplicates[:20]})
for index, row in enumerate(rows, start=2):
    if not clean(row.get("legacy_partner_id")) or not clean(row.get("name")):
        errors.append({"line": index, "error": "missing_identity_or_name"})
if errors:
    env.cr.rollback()  # noqa: F821
    raise RuntimeError({"precheck_failed": errors[:30]})

created_rows: list[dict[str, object]] = []
skipped_rows = 0
try:
    for row in rows:
        legacy_id = clean(row.get("legacy_partner_id"))
        existing = Partner.search([("legacy_partner_id", "=", legacy_id)], limit=1)
        if existing:
            skipped_rows += 1
            continue
        vals = {
            "name": clean(row.get("name")),
            "company_type": clean(row.get("company_type")) or "company",
            "legacy_partner_id": legacy_id,
            "legacy_partner_source": clean(row.get("legacy_partner_source")) or "cooperat_company",
            "legacy_partner_name": clean(row.get("legacy_partner_name")) or clean(row.get("name")),
            "legacy_credit_code": clean(row.get("legacy_credit_code")),
            "legacy_tax_no": clean(row.get("legacy_tax_no")),
            "legacy_source_evidence": clean(row.get("legacy_source_evidence"))
            or "history_receipt_core_partner_targeted_replay",
        }
        if "is_company" in Partner._fields:
            vals["is_company"] = clean(row.get("is_company")) != "0"
        rec = Partner.create(vals)
        created_rows.append(
            {
                "id": rec.id,
                "external_id": clean(row.get("external_id")),
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
for legacy_id in id_counts:
    post_count += Partner.search_count([("legacy_partner_id", "=", legacy_id)])

status = "PASS" if len(created_rows) + skipped_rows == expected_rows and post_count >= expected_rows else "FAIL"
result = {
    "status": status,
    "mode": "history_receipt_core_partner_targeted_replay_write",
    "database": env.cr.dbname,  # noqa: F821
    "target_model": "res.partner",
    "input_rows": len(rows),
    "created_rows": len(created_rows),
    "skipped_existing": skipped_rows,
    "post_write_identity_count": post_count,
    "db_writes": len(created_rows),
    "rollback_targets": str(ROLLBACK_CSV),
    "decision": "receipt_core_partner_targeted_replay_complete" if status == "PASS" else "STOP_REVIEW_REQUIRED",
}
write_csv(
    ROLLBACK_CSV,
    ["id", "external_id", "legacy_partner_source", "legacy_partner_id", "name"],
    created_rows,
)
write_json(OUTPUT_JSON, result)
print("HISTORY_RECEIPT_CORE_PARTNER_TARGETED_REPLAY_WRITE=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
