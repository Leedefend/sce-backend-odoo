#!/usr/bin/env python3
"""Replay business-fit partner bank accounts into sc_migration_fresh."""

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
        "FRESH_DB_PARTNER_BANK_INPUT_CSV",
        str(REPO_ROOT / ".runtime_artifacts/migration_assets/partner_bank_business_fit_v1/10_master/partner_bank/partner_bank_master_v1.csv"),
    )
)
OUTPUT_JSON = ARTIFACT_ROOT / "fresh_db_partner_bank_replay_write_result_v1.json"
ROLLBACK_CSV = ARTIFACT_ROOT / "fresh_db_partner_bank_replay_rollback_targets_v1.csv"
EXPECTED_ROWS_RAW = os.getenv("FRESH_DB_PARTNER_BANK_EXPECTED_ROWS", "5574").strip().lower()
EXPECTED_ROWS = None if EXPECTED_ROWS_RAW == "auto" else int(EXPECTED_ROWS_RAW)
REQUIRED_BANK_FIELDS = [
    "partner_id",
    "acc_number",
    "sc_legacy_external_id",
    "sc_legacy_partner_source",
    "sc_legacy_partner_id",
    "sc_legacy_partner_name",
    "sc_account_holder_name",
    "sc_bank_name",
    "sc_source_evidence",
    "sc_import_batch",
]
OPTIONAL_BANK_FIELDS = ["acc_holder_name"]


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


def build_vals(row: dict[str, str], partner_id: int, optional_fields: set[str]) -> dict[str, object]:
    vals: dict[str, object] = {
        "partner_id": partner_id,
        "acc_number": clean(row.get("acc_number")),
        "sc_legacy_external_id": clean(row.get("sc_legacy_external_id")) or clean(row.get("external_id")),
        "sc_legacy_partner_source": clean(row.get("sc_legacy_partner_source")) or clean(row.get("partner_legacy_partner_source")),
        "sc_legacy_partner_id": clean(row.get("sc_legacy_partner_id")) or clean(row.get("partner_legacy_partner_id")),
        "sc_legacy_partner_name": clean(row.get("sc_legacy_partner_name")) or clean(row.get("partner_name")),
        "sc_account_holder_name": clean(row.get("sc_account_holder_name")) or clean(row.get("acc_holder_name")),
        "sc_bank_name": clean(row.get("sc_bank_name")) or clean(row.get("bank_name")),
        "sc_source_evidence": clean(row.get("sc_source_evidence")) or clean(row.get("source_evidence")),
        "sc_import_batch": clean(row.get("sc_import_batch")) or "partner_bank_business_fit_v1",
    }
    if "acc_holder_name" in optional_fields:
        vals["acc_holder_name"] = vals["sc_account_holder_name"]
    return vals


ensure_allowed_db()

Partner = env["res.partner"].sudo()  # noqa: F821
PartnerBank = env["res.partner.bank"].sudo()  # noqa: F821
missing_partner_fields = [field for field in ["legacy_partner_source", "legacy_partner_id"] if field not in Partner._fields]
missing_bank_fields = [field for field in REQUIRED_BANK_FIELDS if field not in PartnerBank._fields]
if missing_partner_fields or missing_bank_fields:
    raise RuntimeError({"missing_partner_fields": missing_partner_fields, "missing_bank_fields": missing_bank_fields})
optional_fields = {field for field in OPTIONAL_BANK_FIELDS if field in PartnerBank._fields}

rows = read_csv(INPUT_CSV)
errors: list[dict[str, object]] = []
if EXPECTED_ROWS is not None and len(rows) != EXPECTED_ROWS:
    errors.append({"error": "unexpected_row_count", "actual": len(rows), "expected": EXPECTED_ROWS})

external_ids = [clean(row.get("sc_legacy_external_id")) or clean(row.get("external_id")) for row in rows]
external_counts = Counter(external_ids)
duplicate_external_ids = [value for value, count in external_counts.items() if value and count > 1]
if duplicate_external_ids:
    errors.append({"error": "duplicate_bank_external_id", "samples": duplicate_external_ids[:20]})

partner_by_identity: dict[tuple[str, str], object] = {}
existing_by_external: dict[str, object] = {}
for index, row in enumerate(rows, start=2):
    external_id = clean(row.get("sc_legacy_external_id")) or clean(row.get("external_id"))
    source = clean(row.get("sc_legacy_partner_source")) or clean(row.get("partner_legacy_partner_source"))
    legacy_id = clean(row.get("sc_legacy_partner_id")) or clean(row.get("partner_legacy_partner_id"))
    acc_number = clean(row.get("acc_number"))
    if not external_id:
        errors.append({"line": index, "error": "missing_bank_external_id"})
    if not source or not legacy_id:
        errors.append({"line": index, "error": "missing_partner_identity"})
        continue
    if not acc_number:
        errors.append({"line": index, "error": "missing_acc_number"})
    key = (source, legacy_id)
    if key not in partner_by_identity:
        partner = Partner.search([("legacy_partner_source", "=", source), ("legacy_partner_id", "=", legacy_id)])
        if len(partner) != 1:
            errors.append({"line": index, "error": "partner_identity_not_unique", "legacy_partner_source": source, "legacy_partner_id": legacy_id, "matches": len(partner)})
        else:
            partner_by_identity[key] = partner
    if external_id:
        matches = PartnerBank.search([("sc_legacy_external_id", "=", external_id)])
        if len(matches) > 1:
            errors.append({"line": index, "error": "duplicate_target_bank_external_id", "external_id": external_id, "matches": matches[:20].mapped("id")})
        elif matches:
            existing_by_external[external_id] = matches

if errors:
    env.cr.rollback()  # noqa: F821
    raise RuntimeError({"precheck_failed": errors[:30]})

created_rows: list[dict[str, object]] = []
updated_rows: list[dict[str, object]] = []
try:
    for row in rows:
        external_id = clean(row.get("sc_legacy_external_id")) or clean(row.get("external_id"))
        source = clean(row.get("sc_legacy_partner_source")) or clean(row.get("partner_legacy_partner_source"))
        legacy_id = clean(row.get("sc_legacy_partner_id")) or clean(row.get("partner_legacy_partner_id"))
        partner = partner_by_identity[(source, legacy_id)]
        vals = build_vals(row, partner.id, optional_fields)
        write_vals = {field: value for field, value in vals.items() if value not in ("", None)}
        rec = existing_by_external.get(external_id)
        if rec:
            rec.write(write_vals)
            target_rows = updated_rows
        else:
            rec = PartnerBank.create(write_vals)
            target_rows = created_rows
        target_rows.append(
            {
                "id": rec.id,
                "sc_legacy_external_id": rec.sc_legacy_external_id or "",
                "partner_id": rec.partner_id.id,
                "partner_name": rec.partner_id.name or "",
                "acc_number": rec.acc_number or "",
                "sc_bank_name": rec.sc_bank_name or "",
            }
        )
    env.cr.commit()  # noqa: F821
except Exception:
    env.cr.rollback()  # noqa: F821
    raise

post_count = 0
for external_id in external_ids:
    post_count += PartnerBank.search_count([("sc_legacy_external_id", "=", external_id)])
expected_count = len(rows) if EXPECTED_ROWS is None else EXPECTED_ROWS
status = "PASS" if len(created_rows) + len(updated_rows) == expected_count and post_count == expected_count else "FAIL"
result = {
    "status": status,
    "mode": "fresh_db_partner_bank_replay_write",
    "database": env.cr.dbname,  # noqa: F821
    "target_model": "res.partner.bank",
    "input_rows": len(rows),
    "expected_rows": EXPECTED_ROWS if EXPECTED_ROWS is not None else "auto",
    "created_rows": len(created_rows),
    "updated_rows": len(updated_rows),
    "post_write_identity_count": post_count,
    "db_writes": len(created_rows) + len(updated_rows),
    "write_payload": str(INPUT_CSV),
    "rollback_targets": str(ROLLBACK_CSV),
    "decision": "partner_bank_replay_write_complete" if status == "PASS" else "STOP_REVIEW_REQUIRED",
    "next_step": "replay downstream documents that reference partner bank accounts",
}
write_csv(
    ROLLBACK_CSV,
    ["id", "sc_legacy_external_id", "partner_id", "partner_name", "acc_number", "sc_bank_name"],
    created_rows,
)
write_json(OUTPUT_JSON, result)
print(
    "FRESH_DB_PARTNER_BANK_REPLAY_WRITE="
    + json.dumps(
        {
            "status": status,
            "input_rows": len(rows),
            "created_rows": len(created_rows),
            "updated_rows": len(updated_rows),
            "post_write_identity_count": post_count,
            "db_writes": len(created_rows) + len(updated_rows),
        },
        ensure_ascii=False,
        sort_keys=True,
    )
)
