#!/usr/bin/env python3
"""Replay targeted supplier-contract partner anchors into allowed DBs."""

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
        if (candidate / "artifacts/migration/history_supplier_partner_targeted_replay_payload_v1.csv").exists():
            return candidate
    return Path.cwd()


def ensure_allowed_db() -> None:
    allowlist = {item.strip() for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_demo").split(",") if item.strip()}
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
INPUT_CSV = REPO_ROOT / "artifacts/migration/history_supplier_partner_targeted_replay_payload_v1.csv"
OUTPUT_JSON = ARTIFACT_ROOT / "history_supplier_partner_targeted_replay_write_result_v1.json"
ROLLBACK_CSV = ARTIFACT_ROOT / "history_supplier_partner_targeted_replay_rollback_targets_v1.csv"

ensure_allowed_db()

Partner = env["res.partner"].sudo()  # noqa: F821
rows = read_csv(INPUT_CSV)
identities = [(clean(r.get("legacy_partner_source")), clean(r.get("legacy_partner_id"))) for r in rows]
duplicates = [identity for identity, count in Counter(identities).items() if identity[0] and identity[1] and count > 1]
errors: list[dict[str, object]] = []
if duplicates:
    errors.append({"error": "duplicate_payload_identity", "samples": duplicates[:30]})
for index, row in enumerate(rows, start=1):
    if not clean(row.get("name")) or not clean(row.get("legacy_partner_id")) or not clean(row.get("legacy_partner_source")):
        errors.append({"line": index, "error": "missing_required_fields"})
if errors:
    env.cr.rollback()  # noqa: F821
    raise RuntimeError({"precheck_failed": errors[:50]})

created_rows: list[dict[str, object]] = []
skipped_rows: list[dict[str, object]] = []
try:
    for row in rows:
        domain = [
            ("legacy_partner_source", "=", clean(row.get("legacy_partner_source"))),
            ("legacy_partner_id", "=", clean(row.get("legacy_partner_id"))),
        ]
        existing = Partner.search(domain, limit=1)
        if existing:
            skipped_rows.append(
                {
                    "id": existing.id,
                    "legacy_partner_source": existing.legacy_partner_source or "",
                    "legacy_partner_id": existing.legacy_partner_id or "",
                    "name": existing.name or "",
                    "source_bucket": clean(row.get("source_bucket")),
                    "reason": "already_exists_by_legacy_identity",
                }
            )
            continue
        vals = {
            "name": clean(row.get("name")),
            "company_type": clean(row.get("company_type")) or "company",
            "legacy_partner_id": clean(row.get("legacy_partner_id")),
            "legacy_partner_source": clean(row.get("legacy_partner_source")),
            "legacy_partner_name": clean(row.get("legacy_partner_name")),
            "legacy_credit_code": clean(row.get("legacy_credit_code")),
            "legacy_tax_no": clean(row.get("legacy_tax_no")),
            "legacy_source_evidence": clean(row.get("legacy_source_evidence")),
            "vat": clean(row.get("vat")),
            "phone": clean(row.get("phone")),
            "email": clean(row.get("email")),
        }
        if "is_company" in Partner._fields:
            vals["is_company"] = clean(row.get("is_company")) == "1"
        rec = Partner.create({k: v for k, v in vals.items() if v not in ("", None)})
        created_rows.append(
            {
                "id": rec.id,
                "legacy_partner_source": rec.legacy_partner_source or "",
                "legacy_partner_id": rec.legacy_partner_id or "",
                "name": rec.name or "",
                "source_bucket": clean(row.get("source_bucket")),
            }
        )
    env.cr.commit()  # noqa: F821
except Exception:
    env.cr.rollback()  # noqa: F821
    raise

write_csv(ROLLBACK_CSV, ["id", "legacy_partner_source", "legacy_partner_id", "name", "source_bucket"], created_rows)
result = {
    "status": "PASS",
    "mode": "history_supplier_partner_targeted_replay_write",
    "database": env.cr.dbname,  # noqa: F821
    "input_rows": len(rows),
    "created_rows": len(created_rows),
    "skipped_existing": len(skipped_rows),
    "rollback_csv": str(ROLLBACK_CSV),
}
write_json(OUTPUT_JSON, result)
print(json.dumps(result, ensure_ascii=False, indent=2))
