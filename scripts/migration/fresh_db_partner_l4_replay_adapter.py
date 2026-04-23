#!/usr/bin/env python3
"""Build a no-DB fresh-db replay payload for completed partner L4 writes."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


REPO_ROOT = Path.cwd()
COMPANY_CSV = REPO_ROOT / "tmp/raw/partner/company.csv"
SUPPLIER_CSV = REPO_ROOT / "tmp/raw/partner/supplier.csv"
OUTPUT_JSON = REPO_ROOT / "artifacts/migration/fresh_db_partner_l4_replay_adapter_result_v1.json"
OUTPUT_CSV = REPO_ROOT / "artifacts/migration/fresh_db_partner_l4_replay_payload_v1.csv"
OUTPUT_REPORT = REPO_ROOT / "docs/migration_alignment/fresh_db_partner_l4_replay_adapter_report_v1.md"

WRITE_RESULTS = [
    "artifacts/migration/partner_l4_500_write_result_v1.json",
    "artifacts/migration/partner_l4_1000_retry_write_result_v1.json",
    "artifacts/migration/partner_l4_company_supplier_pair_1713_write_result_v1.json",
    "artifacts/migration/partner_l4_missing_tax_single_source_1554_write_result_v1.json",
    "artifacts/migration/partner_l4_remaining_missing_tax_company_supplier_652_write_result_v1.json",
    "artifacts/migration/partner_l4_missing_tax_duplicate_group_175_write_result_v1.json",
    "artifacts/migration/partner_l4_same_tax_company_supplier_canonical_102_write_result_v1.json",
    "artifacts/migration/partner_l4_company_supplier_duplicate_26_write_result_v1.json",
    "artifacts/migration/partner_l4_company_duplicate_24_write_result_v1.json",
    "artifacts/migration/partner_l4_same_tax_company_canonical_20_write_result_v1.json",
    "artifacts/migration/partner_l4_final30_write_result_v1.json",
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
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def source_indexes() -> dict[tuple[str, str], dict[str, str]]:
    index: dict[tuple[str, str], dict[str, str]] = {}
    for row in read_csv(COMPANY_CSV):
        legacy_id = clean(row.get("Id"))
        if legacy_id:
            index[("cooperat_company", legacy_id)] = {
                "source_type": "company",
                "legacy_partner_id": legacy_id,
                "name": clean(row.get("DWMC")),
                "tax_no": clean(row.get("TYSHXYDM")) or clean(row.get("SH")),
                "deleted_flag": clean(row.get("DEL")),
                "source_status": clean(row.get("DJZT")),
                "source_code": clean(row.get("DJBH")),
            }
    for row in read_csv(SUPPLIER_CSV):
        legacy_id = clean(row.get("ID"))
        if legacy_id:
            index[("supplier", legacy_id)] = {
                "source_type": "supplier",
                "legacy_partner_id": legacy_id,
                "name": clean(row.get("f_SupplierName")),
                "tax_no": clean(row.get("SHXYDM")) or clean(row.get("NSRSBH")),
                "deleted_flag": clean(row.get("f_del")),
                "source_status": clean(row.get("DJZT")) or clean(row.get("f_AuditState")),
                "source_code": clean(row.get("f_SupplierCode")) or clean(row.get("DJBH")),
            }
    return index


def load_created_rows() -> tuple[list[dict[str, object]], list[str]]:
    rows: list[dict[str, object]] = []
    missing_files: list[str] = []
    for rel_path in WRITE_RESULTS:
        path = REPO_ROOT / rel_path
        if not path.exists():
            missing_files.append(rel_path)
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        for row in payload.get("created_rows", []):
            rows.append(
                {
                    "source_file": rel_path,
                    "legacy_partner_source": clean(row.get("legacy_partner_source")),
                    "legacy_partner_id": clean(row.get("legacy_partner_id")),
                    "name": clean(row.get("name")),
                    "current_db_partner_id": clean(row.get("id")),
                }
            )
    return rows, missing_files


def write_report(payload: dict[str, object]) -> None:
    text = f"""# Fresh DB Partner L4 Replay Adapter Report v1

Status: {payload["status"]}

Task: `ITER-2026-04-15-FRESH-DB-REPLAY-PARTNER-L4-ADAPTER`

## Scope

Build a no-DB consolidated replay payload for completed partner L4 create-only
writes. This batch does not execute partner write scripts and does not touch a
database.

## Result

- source write result files: `{payload["write_result_files"]}`
- created evidence rows: `{payload["created_evidence_rows"]}`
- replay payload rows: `{payload["replay_payload_rows"]}`
- duplicate replay identities: `{payload["duplicate_replay_identities"]}`
- raw source misses: `{payload["raw_source_misses"]}`
- DB writes: `0`

## Source Type Counts

```json
{json.dumps(payload["source_type_counts"], ensure_ascii=False, indent=2)}
```

## Decision

`{payload["decision"]}`

## Next

{payload["next_step"]}
"""
    OUTPUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_REPORT.write_text(text, encoding="utf-8")


def main() -> int:
    source_index = source_indexes()
    created_rows, missing_files = load_created_rows()
    seen: dict[tuple[str, str], dict[str, object]] = {}
    duplicates: list[dict[str, object]] = []
    raw_misses: list[dict[str, str]] = []
    source_type_counts: Counter[str] = Counter()

    for row in created_rows:
        key = (clean(row["legacy_partner_source"]), clean(row["legacy_partner_id"]))
        if not key[0] or not key[1]:
            raw_misses.append({"legacy_partner_source": key[0], "legacy_partner_id": key[1], "reason": "missing_identity"})
            continue
        if key in seen:
            duplicates.append({"legacy_partner_source": key[0], "legacy_partner_id": key[1]})
            continue
        source = source_index.get(key)
        if not source:
            raw_misses.append({"legacy_partner_source": key[0], "legacy_partner_id": key[1], "reason": "missing_raw_source"})
            source = {
                "source_type": "unknown",
                "name": clean(row["name"]),
                "tax_no": "",
                "deleted_flag": "",
                "source_status": "",
                "source_code": "",
            }
        source_type_counts[source["source_type"]] += 1
        seen[key] = {
            "legacy_partner_source": key[0],
            "legacy_partner_id": key[1],
            "name": source["name"] or clean(row["name"]),
            "tax_no": source["tax_no"],
            "source_type": source["source_type"],
            "deleted_flag": source["deleted_flag"],
            "source_status": source["source_status"],
            "source_code": source["source_code"],
            "idempotency_key": f"{key[0]}::{key[1]}",
            "replay_action": "create_if_missing",
            "current_db_partner_id": row["current_db_partner_id"],
            "evidence_file": row["source_file"],
        }

    payload_rows = sorted(seen.values(), key=lambda item: (item["legacy_partner_source"], item["legacy_partner_id"]))
    status = "PASS" if not missing_files and not duplicates else "FAIL"
    payload = {
        "status": status,
        "mode": "fresh_db_partner_l4_replay_adapter",
        "db_writes": 0,
        "database_operations": 0,
        "write_scripts_executed": 0,
        "write_result_files": len(WRITE_RESULTS),
        "missing_write_result_files": missing_files,
        "created_evidence_rows": len(created_rows),
        "replay_payload_rows": len(payload_rows),
        "duplicate_replay_identities": len(duplicates),
        "duplicate_samples": duplicates[:20],
        "raw_source_misses": len(raw_misses),
        "raw_source_miss_samples": raw_misses[:20],
        "source_type_counts": dict(sorted(source_type_counts.items())),
        "row_artifact": str(OUTPUT_CSV),
        "decision": "partner_l4_replay_payload_ready" if status == "PASS" else "STOP_REVIEW_REQUIRED",
        "next_step": "open partner L4 replay adapter write-dry-run against a fresh database after fresh database operation contract exists",
    }
    write_csv(
        OUTPUT_CSV,
        [
            "legacy_partner_source",
            "legacy_partner_id",
            "name",
            "tax_no",
            "source_type",
            "deleted_flag",
            "source_status",
            "source_code",
            "idempotency_key",
            "replay_action",
            "current_db_partner_id",
            "evidence_file",
        ],
        payload_rows,
    )
    write_json(OUTPUT_JSON, payload)
    write_report(payload)
    print(
        "FRESH_DB_PARTNER_L4_REPLAY_ADAPTER="
        + json.dumps(
            {
                "status": status,
                "created_evidence_rows": len(created_rows),
                "replay_payload_rows": len(payload_rows),
                "duplicates": len(duplicates),
                "raw_source_misses": len(raw_misses),
                "db_writes": 0,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
