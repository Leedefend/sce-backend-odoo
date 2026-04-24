#!/usr/bin/env python3
"""Audit contract header replay coverage against contract_sc_v1 assets."""

from __future__ import annotations

import csv
import json
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
ASSET_XML = REPO_ROOT / "migration_assets/20_business/contract/contract_header_v1.xml"
HISTORICAL_PAYLOADS = [
    REPO_ROOT / "artifacts/migration/contract_header_slice200_authorization_payload_v1.csv",
    REPO_ROOT / "artifacts/migration/contract_header_next200_authorization_payload_v1.csv",
    REPO_ROOT / "artifacts/migration/contract_header_post400_next200_authorization_payload_v1.csv",
    REPO_ROOT / "artifacts/migration/contract_header_post600_next200_authorization_payload_v1.csv",
    REPO_ROOT / "artifacts/migration/contract_header_post800_next200_authorization_payload_v1.csv",
    REPO_ROOT / "artifacts/migration/contract_header_post1000_next200_authorization_payload_v1.csv",
    REPO_ROOT / "artifacts/migration/contract_header_final132_authorization_payload_v1.csv",
]
SPECIAL_12_PAYLOAD = REPO_ROOT / "artifacts/migration/contract_12_row_write_authorization_payload_v1.csv"
RETRY_57_ROLLBACK = REPO_ROOT / "artifacts/migration/fresh_db_contract_57_retry_rollback_targets_v1.csv"
OUTPUT_JSON = REPO_ROOT / "artifacts/migration/history_contract_core_gap_audit_v1.json"
OUTPUT_MD = REPO_ROOT / "docs/migration_alignment/history_contract_core_gap_report_v1.md"
UNREACHED_CSV = REPO_ROOT / "artifacts/migration/ur_a_contract_unreached_asset_rows_v1.csv"


def clean(value: object) -> str:
    return "" if value is None else str(value).strip()


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def payload_ids(path: Path) -> list[str]:
    rows = read_csv_rows(path)
    ids = []
    for row in rows:
        value = clean(row.get("legacy_contract_id") or row.get("\ufefflegacy_contract_id"))
        if value:
            ids.append(value)
    return ids


def asset_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    tree = ET.parse(ASSET_XML)
    for record in tree.findall(".//record"):
        fields = {}
        project_ref = ""
        partner_ref = ""
        for field in record.findall("field"):
            name = field.get("name")
            if not name:
                continue
            if name == "project_id":
                project_ref = clean(field.get("ref"))
            elif name == "partner_id":
                partner_ref = clean(field.get("ref"))
            else:
                fields[name] = clean(field.text)
        legacy_contract_id = clean(fields.get("legacy_contract_id"))
        if not legacy_contract_id:
            continue
        rows.append(
            {
                "legacy_contract_id": legacy_contract_id,
                "subject": clean(fields.get("subject")),
                "type": clean(fields.get("type")),
                "legacy_status": clean(fields.get("legacy_status")),
                "legacy_deleted_flag": clean(fields.get("legacy_deleted_flag")),
                "project_ref": project_ref,
                "partner_ref": partner_ref,
            }
        )
    return rows


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def render_report(payload: dict[str, object]) -> str:
    return f"""# History Contract Core Gap Report v1

Status: ACTIVE

Task: `ITER-2026-04-25-HISTORY-CONTRACT-CORE-GAP-AUDIT-001`

## Scope

Read-only audit of `contract_sc_v1` coverage against the original contract
header asset package.

This audit freezes:

- how many contract headers exist in the asset package;
- how many entered bounded historical payloads;
- how many entered retry/special slices;
- how many never entered any replay payload at all.

## Coverage Snapshot

- asset rows: `{payload["asset_rows"]}`
- historical bounded payload rows: `{payload["historical_bounded_rows"]}`
- special 12-row payload: `{payload["special_12_rows"]}`
- bounded payload union: `{payload["bounded_union_rows"]}`
- retry 57 rows: `{payload["retry_57_rows"]}`
- bounded + retry coverage: `{payload["bounded_plus_retry_rows"]}`
- never-reached asset rows: `{payload["never_reached_rows"]}`

## Key Findings

1. The current historical bounded chain is not the full `contract_sc_v1` asset.
   It covers `{payload["bounded_union_rows"]}` rows, not `{payload["asset_rows"]}`.
2. Even after adding the dedicated `57 retry` lane, total historical/retry
   coverage reaches `{payload["bounded_plus_retry_rows"]}`, still leaving
   `{payload["never_reached_rows"]}` asset rows never entering any replay lane.
3. The unreached rows are not structurally blank:
   - project refs present: `{payload["unreached_shape"]["project_ref_present"]}`
   - partner refs present: `{payload["unreached_shape"]["partner_ref_present"]}`
   - master partner refs: `{payload["unreached_shape"]["partner_master"]}`
   - contract counterparty refs: `{payload["unreached_shape"]["partner_contract_counterparty"]}`

## Decision

`Batch-UR-A` is now frozen into three concrete sub-gaps:

1. `special_slice_gap_12`
2. `retry_lane_gap_57`
3. `never_reached_asset_gap_91`

`Group B` downstream replay must stay blocked until these are resolved in order.

## Artifacts

- JSON audit: `{payload["artifacts"]["json"]}`
- unreached CSV: `{payload["artifacts"]["unreached_csv"]}`
"""


def main() -> int:
    asset = asset_rows()
    asset_ids = {row["legacy_contract_id"] for row in asset}

    historical_rows = sum(len(payload_ids(path)) for path in HISTORICAL_PAYLOADS)
    historical_union: set[str] = set()
    for path in HISTORICAL_PAYLOADS:
        historical_union.update(payload_ids(path))

    special_12 = set(payload_ids(SPECIAL_12_PAYLOAD))
    bounded_union = historical_union | special_12
    retry_57 = set(payload_ids(RETRY_57_ROLLBACK))
    bounded_plus_retry = bounded_union | retry_57

    unreached = [row for row in asset if row["legacy_contract_id"] not in bounded_plus_retry]

    type_counter = Counter(row["type"] for row in unreached)
    status_counter = Counter(row["legacy_status"] for row in unreached)
    partner_ref_counter = Counter(
        "contract_counterparty"
        if row["partner_ref"].startswith("legacy_contract_counterparty_sc_")
        else "partner_master"
        if row["partner_ref"].startswith("legacy_partner_sc_")
        else "other"
        for row in unreached
    )

    write_csv(
        UNREACHED_CSV,
        [
            "legacy_contract_id",
            "subject",
            "type",
            "legacy_status",
            "legacy_deleted_flag",
            "project_ref",
            "partner_ref",
        ],
        unreached,
    )

    payload = {
        "status": "PASS",
        "mode": "history_contract_core_gap_audit",
        "asset_rows": len(asset),
        "historical_bounded_rows": historical_rows,
        "historical_bounded_union_rows": len(historical_union),
        "special_12_rows": len(special_12),
        "bounded_union_rows": len(bounded_union),
        "retry_57_rows": len(retry_57),
        "bounded_plus_retry_rows": len(bounded_plus_retry),
        "never_reached_rows": len(unreached),
        "never_reached_ids_sample": sorted(row["legacy_contract_id"] for row in unreached)[:30],
        "unreached_shape": {
            "project_ref_present": sum(1 for row in unreached if row["project_ref"]),
            "partner_ref_present": sum(1 for row in unreached if row["partner_ref"]),
            "partner_master": partner_ref_counter["partner_master"],
            "partner_contract_counterparty": partner_ref_counter["contract_counterparty"],
            "partner_other": partner_ref_counter["other"],
        },
        "unreached_distributions": {
            "type": dict(type_counter),
            "legacy_status": dict(status_counter),
        },
        "decision": {
            "special_slice_gap": len(special_12),
            "retry_lane_gap": len(retry_57),
            "never_reached_asset_gap": len(unreached),
        },
        "artifacts": {
            "json": str(OUTPUT_JSON.relative_to(REPO_ROOT)),
            "report": str(OUTPUT_MD.relative_to(REPO_ROOT)),
            "unreached_csv": str(UNREACHED_CSV.relative_to(REPO_ROOT)),
        },
    }
    write_json(OUTPUT_JSON, payload)
    OUTPUT_MD.write_text(render_report(payload), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
