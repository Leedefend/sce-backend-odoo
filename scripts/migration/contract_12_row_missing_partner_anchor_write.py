#!/usr/bin/env python3
"""Materialize missing partner anchors required only by the special 12-row contract slice."""

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
        if (candidate / "artifacts/migration/contract_12_row_write_authorization_payload_v1.csv").exists():
            return candidate
    return Path.cwd()


def ensure_allowed_db() -> None:
    allowlist = {
        item.strip()
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_demo").split(",")
        if item.strip()
    }
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_replay": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


REPO_ROOT = repo_root()
ARTIFACT_ROOT = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", str(REPO_ROOT / "artifacts/migration")))
PAYLOAD_CSV = REPO_ROOT / "artifacts/migration/contract_12_row_write_authorization_payload_v1.csv"
OUTPUT_JSON = ARTIFACT_ROOT / "contract_12_row_missing_partner_anchor_write_result_v1.json"
ROLLBACK_CSV = ARTIFACT_ROOT / "contract_12_row_missing_partner_anchor_rollback_targets_v1.csv"
RESOLUTION_CSV = ARTIFACT_ROOT / "contract_12_row_missing_partner_anchor_resolution_v1.csv"
def clean(value: object) -> str:
    return "" if value is None else str(value).replace("\r\n", "\n").replace("\r", "\n").strip()


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


ensure_allowed_db()

Partner = env["res.partner"].sudo()  # noqa: F821

rows = read_csv(PAYLOAD_CSV)
names = sorted({clean(row.get("legacy_counterparty_text")) for row in rows if clean(row.get("legacy_counterparty_text"))})
missing_names: list[str] = []
resolution_rows: list[dict[str, object]] = []
created_rows: list[dict[str, object]] = []
rollback_rows: list[dict[str, object]] = []
ambiguous_existing_names: list[str] = []

for name in names:
    matches = Partner.search([("name", "=", name)], order="id")
    if len(matches) == 1:
        rec = matches[0]
        resolution_rows.append({"anchor_name": name, "partner_id": rec.id, "resolution": "reuse_existing"})
        continue
    if len(matches) > 1:
        migration_matches = matches.filtered(
            lambda rec: "contract_12_row_missing_partner_anchor_write" in (rec.legacy_source_evidence or "")
        )
        rec = (migration_matches or matches)[0]
        ambiguous_existing_names.append(name)
        resolution_rows.append({"anchor_name": name, "partner_id": rec.id, "resolution": "reuse_existing_ambiguous_name"})
        continue
    missing_names.append(name)

try:
    for name in missing_names:
        rec = Partner.create(
            {
                "name": name,
                "company_type": "company",
                "legacy_partner_name": name,
                "legacy_source_evidence": "contract_12_row_missing_partner_anchor_write",
            }
        )
        created_rows.append({"id": rec.id, "name": rec.name or ""})
        rollback_rows.append({"id": rec.id, "name": rec.name or ""})
        resolution_rows.append({"anchor_name": name, "partner_id": rec.id, "resolution": "created_missing_anchor"})
    env.cr.commit()  # noqa: F821
except Exception:
    env.cr.rollback()  # noqa: F821
    raise

write_csv(ROLLBACK_CSV, ["id", "name"], rollback_rows)
write_csv(RESOLUTION_CSV, ["anchor_name", "partner_id", "resolution"], resolution_rows)

payload = {
    "status": "PASS",
    "mode": "contract_12_row_missing_partner_anchor_write",
    "database": env.cr.dbname,  # noqa: F821
    "missing_names": len(missing_names),
    "created_rows": len(created_rows),
    "rollback_rows": len(rollback_rows),
    "ambiguous_existing_names": len(ambiguous_existing_names),
    "artifacts": {
        "rollback_csv": str(ROLLBACK_CSV),
        "resolution_csv": str(RESOLUTION_CSV),
    },
}
write_json(OUTPUT_JSON, payload)
print("CONTRACT_12_ROW_MISSING_PARTNER_ANCHOR_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
