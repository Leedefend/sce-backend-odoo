#!/usr/bin/env python3
"""Materialize missing contract counterparty partner anchors."""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path


REPO_ROOT = Path("/mnt")
PAYLOADS = [
    REPO_ROOT / "artifacts/migration/contract_header_slice200_authorization_payload_v1.csv",
    REPO_ROOT / "artifacts/migration/contract_header_next200_authorization_payload_v1.csv",
    REPO_ROOT / "artifacts/migration/contract_header_post400_next200_authorization_payload_v1.csv",
    REPO_ROOT / "artifacts/migration/contract_header_post600_next200_authorization_payload_v1.csv",
    REPO_ROOT / "artifacts/migration/contract_header_post800_next200_authorization_payload_v1.csv",
    REPO_ROOT / "artifacts/migration/contract_header_post1000_next200_authorization_payload_v1.csv",
    REPO_ROOT / "artifacts/migration/contract_header_final132_authorization_payload_v1.csv",
]
FRESH_CONTRACT_57_ROLLBACK = REPO_ROOT / "artifacts/migration/fresh_db_contract_57_retry_rollback_targets_v1.csv"
OUTPUT_JSON = REPO_ROOT / "artifacts/migration/fresh_db_contract_missing_partner_anchor_write_result_v1.json"
ROLLBACK_CSV = REPO_ROOT / "artifacts/migration/fresh_db_contract_missing_partner_anchor_rollback_targets_v1.csv"
RESOLUTION_CSV = REPO_ROOT / "artifacts/migration/fresh_db_contract_missing_partner_anchor_resolution_v1.csv"
OUTPUT_REPORT = REPO_ROOT / "docs/migration_alignment/fresh_db_contract_missing_partner_anchor_write_report_v1.md"

EXPECTED_MISSING_NAMES = 95
EXPECTED_DEPENDENT_CONTRACT_ROWS = 557
SAFE_FIELDS = ["name", "company_type", "legacy_partner_name", "legacy_source_evidence"]
ROLLBACK_FIELDS = ["id", "name"]
RESOLUTION_FIELDS = [
    "anchor_name",
    "partner_id",
    "resolution",
    "dependent_contract_rows",
    "legacy_partner_source",
    "legacy_partner_id",
    "legacy_deleted_flag",
    "legacy_source_evidence",
]


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


def load_source_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in PAYLOADS:
        rows.extend(read_csv(path))
    return rows


def existing_fresh_contract_ids() -> set[str]:
    return {
        clean(row.get("legacy_contract_id"))
        for row in read_csv(FRESH_CONTRACT_57_ROLLBACK)
        if clean(row.get("legacy_contract_id"))
    }


def read_existing_rollback_rows() -> list[dict[str, object]]:
    if not ROLLBACK_CSV.exists():
        return []
    return [
        {"id": clean(row.get("id")), "name": clean(row.get("name"))}
        for row in read_csv(ROLLBACK_CSV)
        if clean(row.get("id"))
    ]


def read_existing_resolution_names() -> set[str]:
    if not RESOLUTION_CSV.exists():
        return set()
    return {
        clean(row.get("anchor_name"))
        for row in read_csv(RESOLUTION_CSV)
        if clean(row.get("anchor_name"))
    }


def write_report(payload: dict[str, object]) -> None:
    text = f"""# Fresh DB Contract Missing Partner Anchor Write Report V1

Status: {payload["status"]}

Task: `ITER-2026-04-15-FRESH-DB-CONTRACT-MISSING-PARTNER-ANCHOR-WRITE`

## Scope

Materialize minimal company partner anchors for contract counterparties that are
required by remaining contract headers but absent from the fresh database.

## Result

- missing names: `{payload["missing_names"]}`
- dependent contract rows: `{payload["dependent_contract_rows"]}`
- created rows: `{payload["created_rows"]}`
- reused existing rows: `{payload["reused_existing_rows"]}`
- resolved anchors: `{payload["resolved_anchor_count"]}`
- DB writes: `{payload["db_writes"]}`
- demo targets executed: `0`

## Decision

`{payload["decision"]}`

## Next

{payload["next_step"]}
"""
    OUTPUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_REPORT.write_text(text, encoding="utf-8")


def build_vals(name: str, dependent_rows: int) -> dict[str, object]:
    return {
        "name": name,
        "company_type": "company",
        "legacy_partner_name": name,
        "legacy_source_evidence": (
            "fresh_db_contract_missing_partner_anchor_write;"
            f" dependent_contract_rows={dependent_rows}"
        ),
    }


if env.cr.dbname != "sc_migration_fresh":  # noqa: F821
    raise RuntimeError({"db_name_not_sc_migration_fresh": env.cr.dbname})  # noqa: F821

Partner = env["res.partner"].sudo()  # noqa: F821
missing_fields = [field for field in SAFE_FIELDS if field not in Partner._fields]
if missing_fields:
    raise RuntimeError({"missing_partner_fields": missing_fields})

source_rows = load_source_rows()
existing_contract_ids = existing_fresh_contract_ids()
existing_resolution_names = read_existing_resolution_names()
candidate_rows = [
    row
    for row in source_rows
    if clean(row.get("legacy_contract_id")) and clean(row.get("legacy_contract_id")) not in existing_contract_ids
]

name_to_contract_ids: dict[str, set[str]] = defaultdict(set)
errors: list[dict[str, object]] = []
for index, row in enumerate(candidate_rows, start=2):
    name = clean(row.get("legacy_counterparty_text"))
    legacy_contract_id = clean(row.get("legacy_contract_id"))
    if not name:
        errors.append({"line": index, "legacy_contract_id": legacy_contract_id, "error": "missing_counterparty_name"})
        continue
    matches = Partner.search([("name", "=", name)], order="id")
    if len(matches) == 0 or name in existing_resolution_names:
        name_to_contract_ids[name].add(legacy_contract_id)
    elif len(matches) > 1:
        errors.append(
            {
                "line": index,
                "legacy_contract_id": legacy_contract_id,
                "error": "ambiguous_existing_partner_anchor",
                "name": name,
                "candidate_partner_ids": matches[:20].mapped("id"),
            }
        )

missing_names = sorted(name_to_contract_ids)
dependent_contract_rows = sum(len(ids) for ids in name_to_contract_ids.values())
if len(missing_names) != EXPECTED_MISSING_NAMES:
    errors.append({"error": "unexpected_missing_name_count", "actual": len(missing_names), "expected": EXPECTED_MISSING_NAMES})
if dependent_contract_rows != EXPECTED_DEPENDENT_CONTRACT_ROWS:
    errors.append(
        {
            "error": "unexpected_dependent_contract_rows",
            "actual": dependent_contract_rows,
            "expected": EXPECTED_DEPENDENT_CONTRACT_ROWS,
        }
    )

if errors:
    env.cr.rollback()  # noqa: F821
    raise RuntimeError({"precheck_failed": errors[:40]})

created_rows: list[dict[str, object]] = []
resolution_rows: list[dict[str, object]] = []
existing_rollback_rows = read_existing_rollback_rows()
existing_rollback_ids = {clean(row.get("id")) for row in existing_rollback_rows}
try:
    for name in missing_names:
        dependent_rows = len(name_to_contract_ids[name])
        matches = Partner.search([("name", "=", name)], order="id")
        if len(matches) == 1:
            rec = matches[0]
            resolution = "reuse_existing"
        elif len(matches) == 0:
            rec = Partner.create(build_vals(name, dependent_rows))
            created_rows.append({"id": rec.id, "name": rec.name or ""})
            resolution = "created_missing_anchor"
        else:
            raise RuntimeError({"ambiguous_existing_partner_anchor": name, "candidate_partner_ids": matches.mapped("id")})
        resolution_rows.append(
            {
                "anchor_name": name,
                "partner_id": rec.id,
                "resolution": resolution,
                "dependent_contract_rows": dependent_rows,
                "legacy_partner_source": rec.legacy_partner_source or "",
                "legacy_partner_id": rec.legacy_partner_id or "",
                "legacy_deleted_flag": rec.legacy_deleted_flag or "",
                "legacy_source_evidence": rec.legacy_source_evidence or "",
            }
        )
    env.cr.commit()  # noqa: F821
except Exception:
    env.cr.rollback()  # noqa: F821
    raise

rollback_rows = list(existing_rollback_rows)
for row in created_rows:
    if clean(row.get("id")) not in existing_rollback_ids:
        rollback_rows.append(row)

resolved_anchor_count = len(resolution_rows)
reused_existing_rows = resolved_anchor_count - len(created_rows)
status = "PASS" if resolved_anchor_count == EXPECTED_MISSING_NAMES else "FAIL"
result = {
    "status": status,
    "mode": "fresh_db_contract_missing_partner_anchor_write",
    "database": env.cr.dbname,  # noqa: F821
    "target_model": "res.partner",
    "missing_names": len(missing_names),
    "dependent_contract_rows": dependent_contract_rows,
    "created_rows": len(created_rows),
    "cumulative_created_rows": len(rollback_rows),
    "reused_existing_rows": reused_existing_rows,
    "resolved_anchor_count": resolved_anchor_count,
    "db_writes": len(created_rows),
    "demo_targets_executed": 0,
    "rollback_targets": str(ROLLBACK_CSV),
    "resolution_artifact": str(RESOLUTION_CSV),
    "decision": "contract_missing_partner_anchors_materialized" if status == "PASS" else "STOP_REVIEW_REQUIRED",
    "next_step": "rerun remaining contract header adapter",
}
write_csv(ROLLBACK_CSV, ROLLBACK_FIELDS, rollback_rows)
write_csv(RESOLUTION_CSV, RESOLUTION_FIELDS, resolution_rows)
write_json(OUTPUT_JSON, result)
try:
    write_report(result)
except OSError:
    pass
print(
    "FRESH_DB_CONTRACT_MISSING_PARTNER_ANCHOR_WRITE="
    + json.dumps(
        {
            "status": status,
            "missing_names": len(missing_names),
            "dependent_contract_rows": dependent_contract_rows,
            "created_rows": len(created_rows),
            "resolved_anchor_count": resolved_anchor_count,
            "db_writes": len(created_rows),
        },
        ensure_ascii=False,
        sort_keys=True,
    )
)
if status != "PASS":
    raise RuntimeError({"contract_missing_partner_anchor_write_failed": result})
