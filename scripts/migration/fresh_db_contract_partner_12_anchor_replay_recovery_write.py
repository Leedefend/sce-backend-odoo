#!/usr/bin/env python3
"""Recover contract-dependent partner anchor replay in sc_migration_fresh."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


REPO_ROOT = Path("/mnt")
INPUT_CSV = REPO_ROOT / "artifacts/migration/fresh_db_contract_partner_12_anchor_replay_payload_v1.csv"
OUTPUT_JSON = REPO_ROOT / "artifacts/migration/fresh_db_contract_partner_12_anchor_replay_recovery_write_result_v1.json"
ROLLBACK_CSV = REPO_ROOT / "artifacts/migration/fresh_db_contract_partner_12_anchor_replay_recovery_rollback_targets_v1.csv"
RESOLUTION_CSV = REPO_ROOT / "artifacts/migration/fresh_db_contract_partner_12_anchor_replay_resolution_v1.csv"
EXPECTED_ROWS = 12
EXPECTED_DEPENDENT_CONTRACT_ROWS = 57
SAFE_FIELDS = ["name", "company_type", "legacy_partner_name", "legacy_source_evidence"]
ROLLBACK_FIELDS = ["id", "name"]


def clean(value: object) -> str:
    return "" if value is None else str(value).strip()


def is_deleted_flag(value: object) -> bool:
    normalized = clean(value).lower()
    return bool(normalized) and normalized not in {"0", "false", "no", "n"}


def has_tax_evidence(partner) -> bool:
    return bool(clean(partner.legacy_credit_code) or clean(partner.legacy_tax_no))


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


def read_existing_rollback_rows() -> list[dict[str, object]]:
    if not ROLLBACK_CSV.exists():
        return []
    return [
        {"id": clean(row.get("id")), "name": clean(row.get("name"))}
        for row in read_csv(ROLLBACK_CSV)
        if clean(row.get("id"))
    ]


def build_vals(row: dict[str, str]) -> dict[str, object]:
    name = clean(row.get("name")) or clean(row.get("counterparty_text"))
    evidence = clean(row.get("evidence_file")) or "fresh_db_contract_partner_12_anchor_replay_payload_v1.csv"
    sample_contract_id = clean(row.get("sample_legacy_contract_id"))
    return {
        "name": name,
        "company_type": "company",
        "legacy_partner_name": name,
        "legacy_source_evidence": f"{evidence}; sample_contract={sample_contract_id}" if sample_contract_id else evidence,
    }


def choose_canonical(matches):
    if len(matches) == 0:
        return matches
    if len(matches) == 1:
        return matches if not is_deleted_flag(matches.legacy_deleted_flag) else matches.browse()
    active = matches.filtered(lambda partner: not is_deleted_flag(partner.legacy_deleted_flag))
    if len(active) == 1:
        return active
    active_with_tax = active.filtered(has_tax_evidence)
    if len(active_with_tax) == 1:
        return active_with_tax
    with_tax = matches.filtered(has_tax_evidence)
    if len(with_tax) == 1:
        return with_tax
    return matches.browse()


if env.cr.dbname != "sc_migration_fresh":  # noqa: F821
    raise RuntimeError({"db_name_not_sc_migration_fresh": env.cr.dbname})  # noqa: F821

Partner = env["res.partner"].sudo()  # noqa: F821
missing_fields = [field for field in SAFE_FIELDS if field not in Partner._fields]
if missing_fields:
    raise RuntimeError({"missing_partner_fields": missing_fields})

rows = read_csv(INPUT_CSV)
errors: list[dict[str, object]] = []
if len(rows) != EXPECTED_ROWS:
    errors.append({"error": "unexpected_row_count", "actual": len(rows), "expected": EXPECTED_ROWS})

names = [clean(row.get("name")) or clean(row.get("counterparty_text")) for row in rows]
name_counts = Counter(names)
duplicates = [name for name, count in name_counts.items() if name and count > 1]
if duplicates:
    errors.append({"error": "duplicate_payload_name", "samples": duplicates[:20]})

dependent_contract_rows = 0
for index, row in enumerate(rows, start=2):
    name = clean(row.get("name")) or clean(row.get("counterparty_text"))
    if not name:
        errors.append({"line": index, "error": "missing_name"})
    if clean(row.get("partner_kind")) != "company":
        errors.append({"line": index, "error": "non_company_anchor", "value": clean(row.get("partner_kind"))})
    if clean(row.get("replay_action")) != "create_if_missing_for_contract_retry":
        errors.append({"line": index, "error": "unexpected_replay_action", "value": clean(row.get("replay_action"))})
    dependent_contract_rows += int(clean(row.get("dependent_contract_rows")) or "0")
if dependent_contract_rows != EXPECTED_DEPENDENT_CONTRACT_ROWS:
    errors.append(
        {
            "error": "unexpected_dependent_contract_rows",
            "actual": dependent_contract_rows,
            "expected": EXPECTED_DEPENDENT_CONTRACT_ROWS,
        }
    )

existing_by_name: dict[str, object] = {}
for name in names:
    matches = Partner.search([("name", "=", name)], order="id")
    canonical = choose_canonical(matches)
    if len(matches) > 1 and len(canonical) != 1:
        errors.append({"error": "non_unique_canonical_partner", "name": name, "count": len(matches), "samples": matches[:20].mapped("id")})
    elif len(canonical) == 1:
        existing_by_name[name] = canonical
if errors:
    env.cr.rollback()  # noqa: F821
    raise RuntimeError({"precheck_failed": errors[:30]})

created_rows: list[dict[str, object]] = []
resolution_rows: list[dict[str, object]] = []
existing_rollback_rows = read_existing_rollback_rows()
existing_rollback_ids = {clean(row.get("id")) for row in existing_rollback_rows}
try:
    for row in rows:
        name = clean(row.get("name")) or clean(row.get("counterparty_text"))
        existing = existing_by_name.get(name)
        if existing:
            resolution_rows.append(
                {
                    "anchor_name": name,
                    "partner_id": existing.id,
                    "resolution": "reuse_existing_canonical",
                    "legacy_partner_source": existing.legacy_partner_source or "",
                    "legacy_partner_id": existing.legacy_partner_id or "",
                    "legacy_deleted_flag": existing.legacy_deleted_flag or "",
                    "legacy_credit_code": existing.legacy_credit_code or "",
                    "dependent_contract_rows": clean(row.get("dependent_contract_rows")),
                }
            )
            continue
        rec = Partner.create(build_vals(row))
        created_rows.append({"id": rec.id, "name": rec.name or ""})
        resolution_rows.append(
            {
                "anchor_name": name,
                "partner_id": rec.id,
                "resolution": "created_missing_anchor",
                "legacy_partner_source": rec.legacy_partner_source or "",
                "legacy_partner_id": rec.legacy_partner_id or "",
                "legacy_deleted_flag": rec.legacy_deleted_flag or "",
                "legacy_credit_code": rec.legacy_credit_code or "",
                "dependent_contract_rows": clean(row.get("dependent_contract_rows")),
            }
        )
    env.cr.commit()  # noqa: F821
except Exception:
    env.cr.rollback()  # noqa: F821
    raise

post_resolved_count = len(resolution_rows)
created_count = len(created_rows)
reused_count = post_resolved_count - created_count
rollback_rows = list(existing_rollback_rows)
for row in created_rows:
    if clean(row.get("id")) not in existing_rollback_ids:
        rollback_rows.append(row)
status = "PASS" if post_resolved_count == EXPECTED_ROWS and created_count + reused_count == EXPECTED_ROWS else "FAIL"
result = {
    "status": status,
    "mode": "fresh_db_contract_partner_12_anchor_replay_recovery_write",
    "database": env.cr.dbname,  # noqa: F821
    "target_model": "res.partner",
    "input_rows": len(rows),
    "created_rows": created_count,
    "cumulative_created_rows": len(rollback_rows),
    "reused_existing_canonical": reused_count,
    "resolved_anchor_count": post_resolved_count,
    "dependent_contract_rows": dependent_contract_rows,
    "db_writes": created_count,
    "demo_targets_executed": 0,
    "write_payload": str(INPUT_CSV),
    "rollback_targets": str(ROLLBACK_CSV),
    "resolution_artifact": str(RESOLUTION_CSV),
    "decision": "contract_partner_12_anchor_recovery_write_complete" if status == "PASS" else "STOP_REVIEW_REQUIRED",
    "next_step": "retry the 57 dependent contract rows in sc_migration_fresh",
}
write_csv(ROLLBACK_CSV, ROLLBACK_FIELDS, rollback_rows)
write_csv(
    RESOLUTION_CSV,
    [
        "anchor_name",
        "partner_id",
        "resolution",
        "legacy_partner_source",
        "legacy_partner_id",
        "legacy_deleted_flag",
        "legacy_credit_code",
        "dependent_contract_rows",
    ],
    resolution_rows,
)
write_json(OUTPUT_JSON, result)
print(
    "FRESH_DB_CONTRACT_PARTNER_12_ANCHOR_RECOVERY_WRITE="
    + json.dumps(
        {
            "status": status,
            "input_rows": len(rows),
            "created_rows": created_count,
            "cumulative_created_rows": len(rollback_rows),
            "reused_existing_canonical": reused_count,
            "resolved_anchor_count": post_resolved_count,
            "dependent_contract_rows": dependent_contract_rows,
            "db_writes": created_count,
        },
        ensure_ascii=False,
        sort_keys=True,
    )
)
