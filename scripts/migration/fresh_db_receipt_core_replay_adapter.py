#!/usr/bin/env python3
"""Build fresh DB receipt core replay payload from the baseline XML asset."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from xml.etree import ElementTree as ET


REPO_ROOT = Path.cwd()
ASSET_XML = REPO_ROOT / "migration_assets/20_business/receipt/receipt_core_v1.xml"
OUTPUT_CSV = REPO_ROOT / "artifacts/migration/fresh_db_receipt_write_design_payload_v1.csv"
OUTPUT_JSON = REPO_ROOT / "artifacts/migration/fresh_db_receipt_core_replay_adapter_result_v1.json"
EXPECTED_ROWS = 5355
FIELDS = [
    "legacy_receipt_id",
    "legacy_project_id",
    "legacy_contract_id",
    "legacy_partner_id",
    "project_ref",
    "contract_ref",
    "partner_ref",
    "amount",
    "date_request",
    "type",
    "note",
    "source_mode",
]


def clean(value: object) -> str:
    return "" if value is None else str(value).strip()


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


def extract_legacy_receipt_id(note: str) -> str:
    token = "legacy_receipt_id="
    if token not in note:
        return ""
    return note.split(token, 1)[1].split(";", 1)[0].split()[0].strip()


def main() -> int:
    rows: list[dict[str, str]] = []
    root = ET.parse(ASSET_XML).getroot()
    for record in root.findall(".//record[@model='payment.request']"):
        values = field_map(record)
        refs = ref_map(record)
        note = clean(values.get("note"))
        legacy_receipt_id = extract_legacy_receipt_id(note)
        if not legacy_receipt_id:
            continue
        rows.append(
            {
                "legacy_receipt_id": legacy_receipt_id,
                "legacy_project_id": refs.get("project_id", "").removeprefix("legacy_project_sc_"),
                "legacy_contract_id": refs.get("contract_id", "").removeprefix("legacy_contract_sc_"),
                "legacy_partner_id": refs.get("partner_id", "").removeprefix("legacy_partner_sc_"),
                "project_ref": clean(refs.get("project_id")),
                "contract_ref": clean(refs.get("contract_id")),
                "partner_ref": clean(refs.get("partner_id")),
                "amount": clean(values.get("amount")),
                "date_request": clean(values.get("date_request")),
                "type": clean(values.get("type")) or "receive",
                "note": note,
                "source_mode": "asset_xml",
            }
        )

    status = "PASS" if len(rows) == EXPECTED_ROWS else "FAIL"
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_CSV.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    result = {
        "status": status,
        "mode": "fresh_db_receipt_core_replay_adapter",
        "source_mode": "asset_xml",
        "replay_payload_rows": len(rows),
        "expected_rows": EXPECTED_ROWS,
        "db_writes": 0,
    }
    OUTPUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("FRESH_DB_RECEIPT_CORE_REPLAY_ADAPTER=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
