#!/usr/bin/env python3
"""Build targeted replay payload for missing legacy receipt-income partner anchors."""

from __future__ import annotations

import csv
import json
import xml.etree.ElementTree as ET
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
RECEIPT_INCOME_PAYLOAD_CSV = REPO_ROOT / "artifacts/migration/fresh_db_legacy_receipt_income_replay_payload_v1.csv"
PARTNER_XML = REPO_ROOT / "migration_assets/10_master/partner/partner_master_v1.xml"
RECEIPT_COUNTERPARTY_CSV = REPO_ROOT / "artifacts/migration/fresh_db_receipt_counterparty_partner_replay_payload_v1.csv"
CONTRACT_COUNTERPARTY_CSV = REPO_ROOT / "artifacts/migration/fresh_db_contract_counterparty_partner_replay_payload_v1.csv"
OUTPUT_CSV = REPO_ROOT / "artifacts/migration/history_receipt_income_partner_targeted_replay_payload_v1.csv"
OUTPUT_JSON = REPO_ROOT / "artifacts/migration/history_receipt_income_partner_targeted_replay_adapter_result_v1.json"


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


def load_partner_master_records() -> dict[str, dict[str, str]]:
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
    rows = read_csv(RECEIPT_INCOME_PAYLOAD_CSV)
    partner_refs = sorted({clean(row.get("partner_ref")) for row in rows if clean(row.get("partner_ref"))})
    partner_master = load_partner_master_records()
    receipt_counterparty = {
        clean(row.get("legacy_partner_id")): row
        for row in read_csv(RECEIPT_COUNTERPARTY_CSV)
        if clean(row.get("legacy_partner_id"))
    }
    contract_counterparty = {
        clean(row.get("legacy_partner_id")): row
        for row in read_csv(CONTRACT_COUNTERPARTY_CSV)
        if clean(row.get("legacy_partner_id"))
    }

    rows_out: list[dict[str, object]] = []
    source_counts = {"partner_master": 0, "receipt_counterparty": 0, "contract_counterparty": 0}
    unresolved: list[dict[str, str]] = []

    for partner_ref in partner_refs:
        record = None
        source_bucket = ""
        normalized_partner_id = ""
        if partner_ref.startswith("legacy_partner_sc_"):
            normalized_partner_id = partner_ref.removeprefix("legacy_partner_sc_").replace("_", "-")
            record = partner_master.get(normalized_partner_id)
            source_bucket = "partner_master" if record else ""
        elif partner_ref.startswith("legacy_receipt_counterparty_sc_"):
            normalized_partner_id = partner_ref.removeprefix("legacy_receipt_counterparty_sc_").replace("_", "-")
            record = receipt_counterparty.get(normalized_partner_id)
            source_bucket = "receipt_counterparty" if record else ""
        elif partner_ref.startswith("legacy_contract_counterparty_sc_"):
            normalized_partner_id = partner_ref.removeprefix("legacy_contract_counterparty_sc_").replace("_", "-")
            record = contract_counterparty.get(normalized_partner_id)
            source_bucket = "contract_counterparty" if record else ""
        if not record:
            unresolved.append({"partner_ref": partner_ref})
            continue
        source_counts[source_bucket] += 1
        rows_out.append(
            {
                "external_id": clean(record.get("external_id")),
                "name": clean(record.get("name")),
                "company_type": clean(record.get("company_type")),
                "is_company": clean(record.get("is_company")),
                "vat": clean(record.get("vat")),
                "phone": clean(record.get("phone")),
                "email": clean(record.get("email")),
                "legacy_partner_id": clean(record.get("legacy_partner_id")) or normalized_partner_id,
                "legacy_partner_source": clean(record.get("legacy_partner_source")),
                "legacy_partner_name": clean(record.get("legacy_partner_name")) or clean(record.get("name")),
                "legacy_credit_code": clean(record.get("legacy_credit_code")),
                "legacy_tax_no": clean(record.get("legacy_tax_no")),
                "legacy_source_evidence": clean(record.get("legacy_source_evidence")),
                "source_bucket": source_bucket,
                "requested_partner_ref": partner_ref,
            }
        )

    if unresolved:
        raise RuntimeError({"unresolved_partner_refs": unresolved[:50], "unresolved_count": len(unresolved)})

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
        "source_bucket",
        "requested_partner_ref",
    ]
    write_csv(OUTPUT_CSV, fieldnames, rows_out)
    payload = {
        "status": "PASS",
        "mode": "history_receipt_income_partner_targeted_replay_adapter",
        "requested_partner_refs": len(partner_refs),
        "payload_rows": len(rows_out),
        "source_bucket_counts": source_counts,
        "payload_csv": str(OUTPUT_CSV),
    }
    write_json(OUTPUT_JSON, payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
