#!/usr/bin/env python3
"""Read-only match probe for business-fit update-only partner rows."""

from __future__ import annotations

import csv
import json
import os
from collections import Counter
from datetime import UTC, datetime
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
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_prod_sim,sc_migration_fresh").split(",")
        if item.strip()
    }
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_probe": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


REPO_ROOT = repo_root()
ARTIFACT_ROOT = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", str(REPO_ROOT / "artifacts/migration")))
INPUT_CSV = Path(
    os.getenv(
        "PARTNER_UPDATE_ONLY_GATE_CSV",
        str(
            REPO_ROOT
            / "artifacts/migration/partner_business_aligned_rebuild_v1/"
            "fact_based_partner_rebuild_business_aligned_gate_v1.csv"
        ),
    )
)
OUTPUT_DIR = ARTIFACT_ROOT / "partner_business_aligned_rebuild_v1"
OUTPUT_CSV = OUTPUT_DIR / "partner_update_only_match_probe_v1.csv"
OUTPUT_JSON = OUTPUT_DIR / "partner_update_only_match_probe_result_v1.json"
ROW_FIELDS = [
    "partner_key",
    "name",
    "legacy_partner_source",
    "legacy_partner_id",
    "vat",
    "gate_reason",
    "match_status",
    "match_method",
    "matched_partner_ids",
    "matched_partner_names",
    "has_bank_account",
    "has_tax_rate",
    "has_region",
]


def clean(value: object) -> str:
    return "" if value is None else str(value).strip()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def find_partner(Partner, row: dict[str, str]):
    legacy_source = clean(row.get("legacy_partner_source"))
    legacy_id = clean(row.get("legacy_partner_id"))
    if legacy_source and legacy_id:
        matches = Partner.search([("legacy_partner_source", "=", legacy_source), ("legacy_partner_id", "=", legacy_id)])
        if len(matches) == 1:
            return matches, "legacy_identity"
        if len(matches) > 1:
            return matches, "ambiguous_legacy_identity"
    vat = clean(row.get("vat"))
    if vat:
        matches = Partner.search([("vat", "=", vat)])
        if len(matches) == 1:
            return matches, "vat"
        if len(matches) > 1:
            return matches, "ambiguous_vat"
    name = clean(row.get("name"))
    if name:
        matches = Partner.search([("name", "=", name)])
        if len(matches) == 1:
            return matches, "exact_name"
        if len(matches) > 1:
            return matches, "ambiguous_exact_name"
    return Partner.browse(), "not_found"


ensure_allowed_db()
Partner = env["res.partner"].sudo().with_context(active_test=False)  # noqa: F821
missing_fields = [field for field in ["legacy_partner_source", "legacy_partner_id"] if field not in Partner._fields]
if missing_fields:
    raise RuntimeError({"missing_partner_fields": missing_fields})

gate_rows = [row for row in read_csv(INPUT_CSV) if clean(row.get("gate_action")) == "update_only_candidate"]
probe_rows: list[dict[str, object]] = []
status_counts: Counter[str] = Counter()
method_counts: Counter[str] = Counter()
reason_counts: Counter[str] = Counter()
for row in gate_rows:
    matches, method = find_partner(Partner, row)
    if len(matches) == 1:
        status = "matched_unique"
    elif len(matches) > 1:
        status = "ambiguous"
    else:
        status = "not_found"
    status_counts[status] += 1
    method_counts[method] += 1
    reason_counts[clean(row.get("gate_reason"))] += 1
    probe_rows.append(
        {
            "partner_key": clean(row.get("partner_key")),
            "name": clean(row.get("name")),
            "legacy_partner_source": clean(row.get("legacy_partner_source")),
            "legacy_partner_id": clean(row.get("legacy_partner_id")),
            "vat": clean(row.get("vat")),
            "gate_reason": clean(row.get("gate_reason")),
            "match_status": status,
            "match_method": method,
            "matched_partner_ids": ";".join(str(item) for item in matches.ids),
            "matched_partner_names": ";".join(clean(name) for name in matches.mapped("name")),
            "has_bank_account": int(bool(clean(row.get("sc_bank_account")))),
            "has_tax_rate": int(bool(clean(row.get("sc_default_tax_rate")))),
            "has_region": int(bool(clean(row.get("sc_region")))),
        }
    )
summary = {
    "status": "PASS",
    "mode": "fresh_db_partner_update_only_match_probe",
    "generated_at": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
    "database": env.cr.dbname,  # noqa: F821
    "input_rows": len(gate_rows),
    "match_status_counts": dict(sorted(status_counts.items())),
    "match_method_counts": dict(sorted(method_counts.items())),
    "gate_reason_counts": dict(sorted(reason_counts.items())),
    "rows_with_bank_account": sum(int(row["has_bank_account"]) for row in probe_rows),
    "rows_with_tax_rate": sum(int(row["has_tax_rate"]) for row in probe_rows),
    "rows_with_region": sum(int(row["has_region"]) for row in probe_rows),
    "db_writes": 0,
    "row_artifact": str(OUTPUT_CSV),
}
write_csv(OUTPUT_CSV, ROW_FIELDS, probe_rows)
write_json(OUTPUT_JSON, summary)
env.cr.rollback()  # noqa: F821
print("PARTNER_UPDATE_ONLY_MATCH_PROBE=" + json.dumps(summary, ensure_ascii=False, sort_keys=True))
