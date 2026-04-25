#!/usr/bin/env python3
"""Replay receipt counterparty partner anchors into allowed replay databases."""

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
    allowlist = {
        item.strip()
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_migration_fresh").split(",")
        if item.strip()
    }
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_replay": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def clean(value: object) -> str:
    return "" if value is None else str(value).strip()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


REPO_ROOT = repo_root()
ARTIFACT_ROOT = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", str(REPO_ROOT / "artifacts/migration")))
INPUT_CSV = REPO_ROOT / "artifacts/migration/fresh_db_receipt_counterparty_partner_replay_payload_v1.csv"
INPUT_MANIFEST = REPO_ROOT / "artifacts/migration/fresh_db_receipt_counterparty_partner_replay_adapter_result_v1.json"
OUTPUT_JSON = ARTIFACT_ROOT / "fresh_db_receipt_counterparty_partner_replay_write_result_v1.json"
ROLLBACK_CSV = ARTIFACT_ROOT / "fresh_db_receipt_counterparty_partner_replay_rollback_targets_v1.csv"

ensure_allowed_db()

asset_manifest = json.loads(INPUT_MANIFEST.read_text(encoding="utf-8"))
expected_rows = int(asset_manifest["expected_rows"])
rows = read_csv(INPUT_CSV)

Partner = env["res.partner"].sudo()  # noqa: F821
required_fields = [
    "name",
    "company_type",
    "legacy_partner_id",
    "legacy_partner_source",
    "legacy_partner_name",
    "legacy_source_evidence",
]
missing_fields = [field for field in required_fields if field not in Partner._fields]
if missing_fields:
    raise RuntimeError({"missing_partner_fields": missing_fields})

errors: list[dict[str, object]] = []
if len(rows) != expected_rows:
    errors.append({"error": "unexpected_row_count", "actual": len(rows), "expected": expected_rows})

identities = [(row["legacy_partner_source"], row["legacy_partner_id"]) for row in rows]
identity_counts = Counter(identities)
duplicates = [identity for identity, count in identity_counts.items() if count > 1]
if duplicates:
    errors.append({"error": "duplicate_payload_identity", "samples": duplicates[:20]})

for index, row in enumerate(rows, start=1):
    if row.get("legacy_partner_source") != "receipt_counterparty":
        errors.append({"line": index, "error": "unexpected_source", "value": row.get("legacy_partner_source")})
    if row.get("company_type") not in {"person", "company"}:
        errors.append({"line": index, "error": "unexpected_company_type", "value": row.get("company_type")})
    if not row.get("legacy_partner_id") or not row.get("name"):
        errors.append({"line": index, "error": "missing_identity_or_name"})

if errors:
    env.cr.rollback()  # noqa: F821
    raise RuntimeError({"precheck_failed": errors[:30]})

created_rows: list[dict[str, object]] = []
skipped_rows: list[dict[str, object]] = []

try:
    for row in rows:
        domain = [
            ("legacy_partner_source", "=", row["legacy_partner_source"]),
            ("legacy_partner_id", "=", row["legacy_partner_id"]),
        ]
        existing = Partner.search(domain, limit=1)
        if existing:
            skipped_rows.append(
                {
                    "id": existing.id,
                    "external_id": row["external_id"],
                    "legacy_partner_source": row["legacy_partner_source"],
                    "legacy_partner_id": row["legacy_partner_id"],
                    "name": existing.name or "",
                    "reason": "already_exists_by_legacy_identity",
                }
            )
            continue
        vals = {
            "name": row["name"],
            "company_type": row["company_type"],
            "legacy_partner_id": row["legacy_partner_id"],
            "legacy_partner_source": row["legacy_partner_source"],
            "legacy_partner_name": row["legacy_partner_name"],
            "legacy_source_evidence": row["legacy_source_evidence"],
        }
        if "is_company" in Partner._fields:
            vals["is_company"] = row.get("is_company") == "1"
        rec = Partner.create(vals)
        created_rows.append(
            {
                "id": rec.id,
                "external_id": row["external_id"],
                "legacy_partner_source": row["legacy_partner_source"],
                "legacy_partner_id": row["legacy_partner_id"],
                "name": rec.name or "",
            }
        )
    env.cr.commit()  # noqa: F821
except Exception:
    env.cr.rollback()  # noqa: F821
    raise

post_count = 0
for source, legacy_id in identities:
    post_count += Partner.search_count([("legacy_partner_source", "=", source), ("legacy_partner_id", "=", legacy_id)])

status = "PASS" if len(created_rows) + len(skipped_rows) == expected_rows and post_count == expected_rows else "FAIL"
result = {
    "status": status,
    "mode": "fresh_db_receipt_counterparty_partner_replay_write",
    "database": env.cr.dbname,  # noqa: F821
    "target_model": "res.partner",
    "asset_package_id": asset_manifest["asset_package_id"],
    "input_rows": len(rows),
    "created_rows": len(created_rows),
    "skipped_existing": len(skipped_rows),
    "post_write_identity_count": post_count,
    "db_writes": len(created_rows),
    "write_payload": str(INPUT_CSV),
    "rollback_targets": str(ROLLBACK_CSV),
    "decision": "receipt_counterparty_partner_replay_write_complete" if status == "PASS" else "STOP_REVIEW_REQUIRED",
    "next_step": "continue full-package continuity replay",
}
write_csv(
    ROLLBACK_CSV,
    ["id", "external_id", "legacy_partner_source", "legacy_partner_id", "name"],
    created_rows,
)
write_json(OUTPUT_JSON, result)
print(
    "FRESH_DB_RECEIPT_COUNTERPARTY_PARTNER_REPLAY_WRITE="
    + json.dumps(
        {
            "status": status,
            "input_rows": len(rows),
            "created_rows": len(created_rows),
            "skipped_existing": len(skipped_rows),
            "post_write_identity_count": post_count,
            "db_writes": len(created_rows),
        },
        ensure_ascii=False,
        sort_keys=True,
    )
)
