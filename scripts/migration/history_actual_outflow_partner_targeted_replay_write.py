#!/usr/bin/env python3
"""Replay targeted actual-outflow partner anchors into allowed replay databases."""

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
        if (candidate / "artifacts/migration/history_actual_outflow_partner_targeted_replay_payload_v1.csv").exists():
            return candidate
    return Path.cwd()


def ensure_allowed_db() -> None:
    allowlist = {item.strip() for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_migration_fresh").split(",") if item.strip()}
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_replay": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


REPO_ROOT = repo_root()
ARTIFACT_ROOT = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", str(REPO_ROOT / "artifacts/migration")))
INPUT_CSV = REPO_ROOT / "artifacts/migration/history_actual_outflow_partner_targeted_replay_payload_v1.csv"
OUTPUT_JSON = ARTIFACT_ROOT / "history_actual_outflow_partner_targeted_replay_write_result_v1.json"

ensure_allowed_db()
rows = read_csv(INPUT_CSV)
Partner = env["res.partner"].sudo()  # noqa: F821

created = 0
skipped = 0
for row in rows:
    source = row.get("legacy_partner_source") or ""
    domain = [("legacy_partner_id", "=", row["legacy_partner_id"])]
    if source:
        domain.append(("legacy_partner_source", "=", source))
    existing = Partner.search(domain, limit=1)
    if existing:
        skipped += 1
        continue
    vals = {
        "name": row["name"] or row["legacy_partner_name"] or row["legacy_partner_id"],
        "company_type": row["company_type"] or "company",
        "is_company": str(row.get("is_company") or "").lower() in {"1", "true", "yes"},
        "legacy_partner_id": row["legacy_partner_id"],
        "legacy_partner_source": row["legacy_partner_source"] or False,
        "legacy_partner_name": row["legacy_partner_name"] or False,
        "legacy_credit_code": row["legacy_credit_code"] or False,
        "legacy_tax_no": row["legacy_tax_no"] or False,
        "legacy_source_evidence": row["legacy_source_evidence"] or False,
        "phone": row["phone"] or False,
        "email": row["email"] or False,
        "vat": row["vat"] or False,
    }
    Partner.create(vals)
    created += 1

env.cr.commit()  # noqa: F821
payload = {
    "status": "PASS",
    "mode": "history_actual_outflow_partner_targeted_replay_write",
    "database": env.cr.dbname,  # noqa: F821
    "input_rows": len(rows),
    "created_rows": created,
    "skipped_existing": skipped,
    "db_writes": created,
}
write_json(OUTPUT_JSON, payload)
print("HISTORY_ACTUAL_OUTFLOW_PARTNER_TARGETED_REPLAY_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
