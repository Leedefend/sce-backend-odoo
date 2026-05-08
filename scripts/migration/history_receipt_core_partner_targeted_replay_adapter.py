#!/usr/bin/env python3
"""Build targeted partner anchor payload for receipt core replay dependencies."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from xml.etree import ElementTree as ET


REPO_ROOT = Path.cwd()
RECEIPT_PAYLOAD = REPO_ROOT / "artifacts/migration/fresh_db_receipt_write_design_payload_v1.csv"
PARTNER_XML = REPO_ROOT / "migration_assets/10_master/partner/partner_master_v1.xml"
OUTPUT_CSV = REPO_ROOT / "artifacts/migration/history_receipt_core_partner_targeted_replay_payload_v1.csv"
OUTPUT_JSON = REPO_ROOT / "artifacts/migration/history_receipt_core_partner_targeted_replay_adapter_result_v1.json"
FIELDS = [
    "external_id",
    "name",
    "company_type",
    "is_company",
    "legacy_partner_id",
    "legacy_partner_source",
    "legacy_partner_name",
    "legacy_credit_code",
    "legacy_tax_no",
    "legacy_source_evidence",
]


def clean(value: object) -> str:
    return "" if value is None else str(value).strip()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def field_map(record: ET.Element) -> dict[str, str]:
    values: dict[str, str] = {"external_id": clean(record.get("id"))}
    for field in record.findall("field"):
        name = clean(field.get("name"))
        if name:
            values[name] = clean(field.get("eval")) or clean(field.text)
    return values


def main() -> int:
    requested_ids = sorted(
        {
            clean(row.get("partner_ref")).removeprefix("legacy_partner_sc_")
            for row in read_csv(RECEIPT_PAYLOAD)
            if clean(row.get("partner_ref")).startswith("legacy_partner_sc_")
        }
    )
    requested_set = set(requested_ids)
    partner_rows: dict[str, dict[str, str]] = {}
    root = ET.parse(PARTNER_XML).getroot()
    for record in root.findall(".//record[@model='res.partner']"):
        values = field_map(record)
        legacy_id = clean(values.get("legacy_partner_id"))
        if legacy_id and legacy_id in requested_set:
            partner_rows[legacy_id] = {
                "external_id": clean(values.get("external_id")) or f"legacy_partner_sc_{legacy_id}",
                "name": clean(values.get("name")),
                "company_type": clean(values.get("company_type")) or "company",
                "is_company": clean(values.get("is_company")) or "1",
                "legacy_partner_id": legacy_id,
                "legacy_partner_source": clean(values.get("legacy_partner_source")),
                "legacy_partner_name": clean(values.get("legacy_partner_name")) or clean(values.get("name")),
                "legacy_credit_code": clean(values.get("legacy_credit_code")),
                "legacy_tax_no": clean(values.get("legacy_tax_no")),
                "legacy_source_evidence": clean(values.get("legacy_source_evidence"))
                or "migration_assets/10_master/partner/partner_master_v1.xml",
            }
    rows = [partner_rows[legacy_id] for legacy_id in requested_ids if legacy_id in partner_rows]
    missing_ids = [legacy_id for legacy_id in requested_ids if legacy_id not in partner_rows]
    status = "PASS" if rows and not missing_ids else "FAIL"
    write_csv(OUTPUT_CSV, rows)
    result = {
        "status": status,
        "mode": "history_receipt_core_partner_targeted_replay_adapter",
        "requested_partner_refs": len(requested_ids),
        "payload_rows": len(rows),
        "missing_partner_master_rows": len(missing_ids),
        "missing_partner_master_samples": missing_ids[:20],
        "payload_csv": str(OUTPUT_CSV),
        "db_writes": 0,
        "decision": "receipt_core_partner_targeted_payload_ready" if status == "PASS" else "STOP_REVIEW_REQUIRED",
    }
    write_json(OUTPUT_JSON, result)
    print("HISTORY_RECEIPT_CORE_PARTNER_TARGETED_REPLAY_ADAPTER=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
