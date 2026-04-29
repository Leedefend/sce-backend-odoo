#!/usr/bin/env python3
"""Build a fresh DB replay payload for remaining contract headers."""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from xml.etree import ElementTree as ET


REPO_ROOT = Path.cwd()
PAYLOADS = [
    REPO_ROOT / "artifacts/migration/contract_header_slice200_authorization_payload_v1.csv",
    REPO_ROOT / "artifacts/migration/contract_header_next200_authorization_payload_v1.csv",
    REPO_ROOT / "artifacts/migration/contract_header_post400_next200_authorization_payload_v1.csv",
    REPO_ROOT / "artifacts/migration/contract_header_post600_next200_authorization_payload_v1.csv",
    REPO_ROOT / "artifacts/migration/contract_header_post800_next200_authorization_payload_v1.csv",
    REPO_ROOT / "artifacts/migration/contract_header_post1000_next200_authorization_payload_v1.csv",
    REPO_ROOT / "artifacts/migration/contract_header_final132_authorization_payload_v1.csv",
]
FRESH_PROJECT_ROLLBACK = REPO_ROOT / "artifacts/migration/fresh_db_project_anchor_replay_rollback_targets_v1.csv"
FRESH_PARTNER_ROLLBACK = REPO_ROOT / "artifacts/migration/fresh_db_partner_l4_replay_rollback_targets_v1.csv"
FRESH_CONTRACT_57_ROLLBACK = REPO_ROOT / "artifacts/migration/fresh_db_contract_57_retry_rollback_targets_v1.csv"
CONTRACT_PARTNER_RESOLUTION = (
    REPO_ROOT / "artifacts/migration/fresh_db_contract_partner_12_anchor_replay_resolution_v1.csv"
)
CONTRACT_MISSING_PARTNER_RESOLUTION = (
    REPO_ROOT / "artifacts/migration/fresh_db_contract_missing_partner_anchor_resolution_v1.csv"
)
OUTPUT_CSV = REPO_ROOT / "artifacts/migration/fresh_db_contract_remaining_replay_payload_v1.csv"
OUTPUT_JSON = REPO_ROOT / "artifacts/migration/fresh_db_contract_remaining_adapter_result_v1.json"
OUTPUT_REPORT = REPO_ROOT / "docs/migration_alignment/fresh_db_contract_remaining_adapter_report_v1.md"
ASSET_XML = REPO_ROOT / "migration_assets/20_business/contract/contract_header_v1.xml"

EXPECTED_SOURCE_ROWS = 1332
EXPECTED_EXCLUDED_ROWS = 57
EXPECTED_REPLAY_ROWS = 1332
ASSET_EXPECTED_REPLAY_ROWS = 1492
OUTPUT_FIELDS = [
    "legacy_contract_id",
    "legacy_project_id",
    "project_id",
    "partner_id",
    "subject",
    "type",
    "legacy_contract_no",
    "legacy_document_no",
    "legacy_external_contract_no",
    "legacy_status",
    "legacy_deleted_flag",
    "legacy_counterparty_text",
    "partner_ref",
    "source_payload",
]


def clean(value: object) -> str:
    return "" if value is None else str(value).replace("\r\n", "\n").replace("\r", "\n").strip()


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


def indexed_project_ids() -> dict[str, int]:
    mapping: dict[str, int] = {}
    duplicates: set[str] = set()
    for row in read_csv(FRESH_PROJECT_ROLLBACK):
        legacy_project_id = clean(row.get("legacy_project_id"))
        fresh_id = clean(row.get("id"))
        if not legacy_project_id or not fresh_id:
            continue
        if legacy_project_id in mapping:
            duplicates.add(legacy_project_id)
        mapping[legacy_project_id] = int(fresh_id)
    if duplicates:
        raise RuntimeError({"duplicate_fresh_project_anchors": sorted(duplicates)[:20]})
    return mapping


def indexed_partner_ids() -> tuple[dict[str, int], dict[str, list[int]]]:
    ids_by_name: dict[str, list[int]] = defaultdict(list)
    for row in read_csv(FRESH_PARTNER_ROLLBACK):
        name = clean(row.get("name"))
        fresh_id = clean(row.get("id"))
        if name and fresh_id:
            ids_by_name[name].append(int(fresh_id))

    canonical: dict[str, int] = {
        name: ids[0] for name, ids in ids_by_name.items() if len(set(ids)) == 1
    }
    duplicates = {name: sorted(set(ids)) for name, ids in ids_by_name.items() if len(set(ids)) > 1}

    for resolution_path in (CONTRACT_PARTNER_RESOLUTION, CONTRACT_MISSING_PARTNER_RESOLUTION):
        if not resolution_path.exists():
            continue
        for row in read_csv(resolution_path):
            name = clean(row.get("anchor_name"))
            fresh_id = clean(row.get("partner_id"))
            if name and fresh_id:
                canonical[name] = int(fresh_id)
                duplicates.pop(name, None)

    return canonical, duplicates


def existing_fresh_contract_ids() -> set[str]:
    return {
        clean(row.get("legacy_contract_id"))
        for row in read_csv(FRESH_CONTRACT_57_ROLLBACK)
        if clean(row.get("legacy_contract_id"))
    }


def load_source_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in PAYLOADS:
        for row in read_csv(path):
            row["source_payload"] = str(path.relative_to(REPO_ROOT))
            rows.append(row)
    return rows


def field_map(record: ET.Element) -> dict[str, str]:
    values: dict[str, str] = {}
    for field in record.findall("field"):
        name = clean(field.get("name"))
        if name:
            values[name] = clean(field.text)
    return values


def ref_map(record: ET.Element) -> dict[str, str]:
    values: dict[str, str] = {}
    for field in record.findall("field"):
        name = clean(field.get("name"))
        ref = clean(field.get("ref"))
        if name and ref:
            values[name] = ref
    return values


def load_asset_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    root = ET.parse(ASSET_XML).getroot()
    for record in root.findall(".//record[@model='construction.contract']"):
        values = field_map(record)
        refs = ref_map(record)
        legacy_contract_id = clean(values.get("legacy_contract_id"))
        if not legacy_contract_id:
            continue
        rows.append(
            {
                "legacy_contract_id": legacy_contract_id,
                "legacy_project_id": clean(values.get("legacy_project_id")),
                "project_id": "",
                "partner_id": "",
                "subject": clean(values.get("subject")),
                "type": clean(values.get("type")),
                "legacy_contract_no": clean(values.get("legacy_contract_no")),
                "legacy_document_no": clean(values.get("legacy_document_no")),
                "legacy_external_contract_no": clean(values.get("legacy_external_contract_no")),
                "legacy_status": clean(values.get("legacy_status")),
                "legacy_deleted_flag": clean(values.get("legacy_deleted_flag")),
                "legacy_counterparty_text": clean(values.get("legacy_counterparty_text")),
                "partner_ref": clean(refs.get("partner_id")),
                "source_payload": str(ASSET_XML.relative_to(REPO_ROOT)),
            }
        )
    return rows


def write_report(payload: dict[str, object]) -> None:
    text = f"""# Fresh DB Contract Remaining Adapter Report V1

Status: {payload["status"]}

Task: `ITER-2026-04-15-FRESH-DB-CONTRACT-REMAINING-ADAPTER`

## Scope

Build a no-DB-write replay payload for remaining contract headers by remapping
legacy project ids and counterparty names to fresh database anchors.

## Result

- source rows: `{payload["source_rows"]}`
- existing fresh reference rows: `{payload["existing_fresh_reference_rows"]}`
- excluded existing fresh rows: `{payload["excluded_existing_fresh_rows"]}`
- replay payload rows: `{payload["replay_payload_rows"]}`
- missing project anchors: `{payload["missing_project_anchor_count"]}`
- missing partner anchors: `{payload["missing_partner_anchor_count"]}`
- ambiguous partner anchors: `{payload["ambiguous_partner_anchor_count"]}`
- DB writes: `0`

## Decision

`{payload["decision"]}`

## Next

{payload["next_step"]}
"""
    OUTPUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_REPORT.write_text(text, encoding="utf-8")


def main() -> int:
    use_asset_source = not all(path.exists() for path in PAYLOADS)
    project_by_legacy = {} if use_asset_source else indexed_project_ids()
    partner_by_name, duplicate_partner_names = ({}, {}) if use_asset_source else indexed_partner_ids()
    existing_contract_ids = set() if use_asset_source else existing_fresh_contract_ids()
    source_rows = load_asset_rows() if use_asset_source else load_source_rows()
    expected_source_rows = ASSET_EXPECTED_REPLAY_ROWS if use_asset_source else EXPECTED_SOURCE_ROWS
    expected_excluded_rows = 0 if use_asset_source else EXPECTED_EXCLUDED_ROWS
    expected_replay_rows = ASSET_EXPECTED_REPLAY_ROWS if use_asset_source else EXPECTED_REPLAY_ROWS
    ids = [clean(row.get("legacy_contract_id")) for row in source_rows]
    duplicate_input_ids = sorted(identity for identity, count in Counter(ids).items() if identity and count > 1)

    output_rows: list[dict[str, object]] = []
    excluded_existing_rows = 0
    errors: list[dict[str, object]] = []
    missing_projects: set[str] = set()
    missing_partners: set[str] = set()
    ambiguous_partners: set[str] = set()

    for index, row in enumerate(source_rows, start=2):
        legacy_contract_id = clean(row.get("legacy_contract_id"))
        if legacy_contract_id in existing_contract_ids:
            excluded_existing_rows += 1
            continue

        legacy_project_id = clean(row.get("legacy_project_id"))
        counterparty = clean(row.get("legacy_counterparty_text"))
        project_id = "" if use_asset_source else project_by_legacy.get(legacy_project_id)
        partner_id = "" if use_asset_source else partner_by_name.get(counterparty)

        if not use_asset_source and not project_id:
            missing_projects.add(legacy_project_id)
            errors.append(
                {
                    "line": index,
                    "legacy_contract_id": legacy_contract_id,
                    "error": "missing_fresh_project_anchor",
                    "legacy_project_id": legacy_project_id,
                }
            )
            continue
        if not use_asset_source and counterparty in duplicate_partner_names:
            ambiguous_partners.add(counterparty)
            errors.append(
                {
                    "line": index,
                    "legacy_contract_id": legacy_contract_id,
                    "error": "ambiguous_fresh_partner_anchor",
                    "counterparty": counterparty,
                    "candidate_partner_ids": duplicate_partner_names[counterparty][:10],
                }
            )
            continue
        if not use_asset_source and not partner_id:
            missing_partners.add(counterparty)
            errors.append(
                {
                    "line": index,
                    "legacy_contract_id": legacy_contract_id,
                    "error": "missing_fresh_partner_anchor",
                    "counterparty": counterparty,
                }
            )
            continue

        output_rows.append(
            {
                "legacy_contract_id": legacy_contract_id,
                "legacy_project_id": legacy_project_id,
                "project_id": project_id,
                "partner_id": partner_id,
                "subject": clean(row.get("subject")),
                "type": clean(row.get("type")),
                "legacy_contract_no": clean(row.get("legacy_contract_no")),
                "legacy_document_no": clean(row.get("legacy_document_no")),
                "legacy_external_contract_no": clean(row.get("legacy_external_contract_no")),
                "legacy_status": clean(row.get("legacy_status")),
                "legacy_deleted_flag": clean(row.get("legacy_deleted_flag")),
                "legacy_counterparty_text": counterparty,
                "partner_ref": clean(row.get("partner_ref")),
                "source_payload": clean(row.get("source_payload")),
            }
        )

    if len(source_rows) != expected_source_rows:
        errors.append({"error": "unexpected_source_rows", "actual": len(source_rows), "expected": expected_source_rows})
    if len(existing_contract_ids) != expected_excluded_rows:
        errors.append(
            {
                "error": "unexpected_existing_fresh_contract_rows",
                "actual": len(existing_contract_ids),
                "expected": expected_excluded_rows,
            }
        )
    if duplicate_input_ids:
        errors.append({"error": "duplicate_input_legacy_contract_id", "ids": duplicate_input_ids[:20]})
    if len(output_rows) != expected_replay_rows:
        errors.append({"error": "unexpected_replay_rows", "actual": len(output_rows), "expected": expected_replay_rows})

    status = "PASS" if not errors else "FAIL"
    if status == "PASS":
        write_csv(OUTPUT_CSV, OUTPUT_FIELDS, output_rows)

    result = {
        "status": status,
        "mode": "fresh_db_contract_remaining_adapter",
        "db_writes": 0,
        "source_mode": "asset_xml" if use_asset_source else "legacy_authorization_payloads",
        "source_rows": len(source_rows),
        "existing_fresh_reference_rows": len(existing_contract_ids),
        "excluded_existing_fresh_rows": excluded_existing_rows,
        "replay_payload_rows": len(output_rows),
        "expected_replay_rows": expected_replay_rows,
        "missing_project_anchor_count": len(missing_projects),
        "missing_partner_anchor_count": len(missing_partners),
        "ambiguous_partner_anchor_count": len(ambiguous_partners),
        "duplicate_input_legacy_contract_ids": len(duplicate_input_ids),
        "errors": errors[:80],
        "artifacts": {
            "replay_payload": str(OUTPUT_CSV),
            "report": str(OUTPUT_REPORT),
        },
        "decision": "fresh_db_contract_remaining_adapter_ready" if status == "PASS" else "STOP_REVIEW_REQUIRED",
        "next_step": "write remaining contract headers into sc_migration_fresh" if status == "PASS" else "screen missing or ambiguous anchors",
    }
    write_json(OUTPUT_JSON, result)
    write_report(result)
    print(
        "FRESH_DB_CONTRACT_REMAINING_ADAPTER="
        + json.dumps(
            {
                "status": status,
                "source_mode": "asset_xml" if use_asset_source else "legacy_authorization_payloads",
                "source_rows": len(source_rows),
                "existing_fresh_reference_rows": len(existing_contract_ids),
                "excluded_existing_fresh_rows": excluded_existing_rows,
                "replay_payload_rows": len(output_rows),
                "missing_project_anchor_count": len(missing_projects),
                "missing_partner_anchor_count": len(missing_partners),
                "ambiguous_partner_anchor_count": len(ambiguous_partners),
                "db_writes": 0,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
