#!/usr/bin/env python3
"""Build targeted partner-master replay payload for direction-defer strong-evidence partners."""

from __future__ import annotations

import csv
import json
import xml.etree.ElementTree as ET
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
STRONG_EVIDENCE_CSV = REPO_ROOT / "artifacts/migration/contract_counterparty_strong_evidence_candidates_v1.csv"
DIRECTION_DEFER_CSV = REPO_ROOT / "artifacts/migration/history_contract_direction_defer_rows_v1.csv"
PARTNER_XML = REPO_ROOT / "migration_assets/10_master/partner/partner_master_v1.xml"
OUTPUT_CSV = REPO_ROOT / "artifacts/migration/history_partner_master_direction_defer_replay_payload_v1.csv"
OUTPUT_JSON = REPO_ROOT / "artifacts/migration/history_partner_master_direction_defer_replay_adapter_result_v1.json"
EXPECTED_ROWS = 12


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


def load_partner_records() -> dict[str, dict[str, str]]:
    fields_keep = {
        "name",
        "company_type",
        "is_company",
        "vat",
        "phone",
        "email",
        "legacy_partner_id",
        "legacy_partner_source",
        "legacy_partner_name",
        "legacy_credit_code",
        "legacy_tax_no",
        "legacy_source_evidence",
    }
    found: dict[str, dict[str, str]] = {}
    for _, elem in ET.iterparse(PARTNER_XML, events=("end",)):
        if elem.tag != "record":
            continue
        values: dict[str, str] = {"external_id": clean(elem.attrib.get("id"))}
        for field in elem.findall("field"):
            name = clean(field.attrib.get("name"))
            if name in fields_keep:
                values[name] = clean(field.text)
        legacy_partner_id = clean(values.get("legacy_partner_id"))
        if legacy_partner_id:
            found[legacy_partner_id] = values
        elem.clear()
    return found


def main() -> int:
    direction_ids = {clean(row.get("legacy_contract_id")) for row in read_csv(DIRECTION_DEFER_CSV)}
    partner_ids = []
    for row in read_csv(STRONG_EVIDENCE_CSV):
        if clean(row.get("legacy_contract_id")) in direction_ids:
            partner_ids.append(clean(row.get("repayment_partner_id")))

    unique_partner_ids = sorted({pid for pid in partner_ids if pid})
    if len(unique_partner_ids) != EXPECTED_ROWS:
        raise RuntimeError({"unexpected_partner_ids": len(unique_partner_ids), "expected": EXPECTED_ROWS, "ids": unique_partner_ids})

    records = load_partner_records()
    missing = sorted(pid for pid in unique_partner_ids if pid not in records)
    if missing:
        raise RuntimeError({"missing_partner_master_records": missing})

    rows = [records[pid] for pid in unique_partner_ids]
    fieldnames = [
        "external_id",
        "name",
        "company_type",
        "is_company",
        "vat",
        "phone",
        "email",
        "legacy_partner_id",
        "legacy_partner_source",
        "legacy_partner_name",
        "legacy_credit_code",
        "legacy_tax_no",
        "legacy_source_evidence",
    ]
    write_csv(OUTPUT_CSV, fieldnames, rows)
    payload = {
        "status": "PASS",
        "mode": "history_partner_master_direction_defer_replay_adapter",
        "target_rows": len(rows),
        "payload_csv": str(OUTPUT_CSV),
    }
    write_json(OUTPUT_JSON, payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
