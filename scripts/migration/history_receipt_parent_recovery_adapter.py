#!/usr/bin/env python3
"""Build recovery payload for missing receipt parents required by receipt invoice line replay."""

from __future__ import annotations

import csv
import json
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
INVOICE_LINE_PAYLOAD = REPO_ROOT / "artifacts/migration/fresh_db_receipt_invoice_line_replay_payload_v1.csv"
RECEIPT_CORE_SNAPSHOT = REPO_ROOT / "artifacts/migration/fresh_db_receipt_core_post_write_snapshot_v1.csv"
RECEIPT_EXCLUDED_CSV = REPO_ROOT / "artifacts/migration/fresh_db_receipt_excluded_policy_rows_v1.csv"
RECEIPT_XML = REPO_ROOT / "migration_assets/20_business/receipt/receipt_core_v1.xml"
OUTPUT_CSV = REPO_ROOT / "artifacts/migration/history_receipt_parent_recovery_payload_v1.csv"
OUTPUT_JSON = REPO_ROOT / "artifacts/migration/history_receipt_parent_recovery_adapter_result_v1.json"


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


def parse_receipt_xml(target_ids: set[str]) -> dict[str, dict[str, str]]:
    found: dict[str, dict[str, str]] = {}
    for _, elem in ET.iterparse(RECEIPT_XML, events=("end",)):
        if elem.tag != "record":
            continue
        external_id = clean(elem.attrib.get("id"))
        if not external_id.startswith("legacy_receipt_sc_"):
            elem.clear()
            continue
        legacy_receipt_id = external_id.removeprefix("legacy_receipt_sc_")
        if legacy_receipt_id not in target_ids:
            elem.clear()
            continue
        row = {
            "external_id": external_id,
            "legacy_receipt_id": legacy_receipt_id,
            "type": "",
            "project_ref": "",
            "partner_ref": "",
            "amount": "",
            "date_request": "",
            "note": "",
            "legacy_contract_id": "",
        }
        for field in elem.findall("field"):
            name = clean(field.attrib.get("name"))
            value = clean(field.attrib.get("ref")) or clean(field.text)
            if name == "project_id":
                row["project_ref"] = value
            elif name == "partner_id":
                row["partner_ref"] = value
            elif name in row:
                row[name] = value
        note = row["note"]
        token = "legacy_contract_id="
        if token in note:
            contract_part = note.split(token, 1)[1].split(";", 1)[0].strip()
            row["legacy_contract_id"] = contract_part.split()[0].strip() if contract_part else ""
        found[legacy_receipt_id] = row
        elem.clear()
    return found


def main() -> int:
    existing_receipt_ids = {
        clean(row.get("legacy_receipt_id"))
        for row in read_csv(RECEIPT_CORE_SNAPSHOT)
        if clean(row.get("legacy_receipt_id"))
    }
    invoice_line_counts: Counter[str] = Counter()
    for row in read_csv(INVOICE_LINE_PAYLOAD):
        legacy_receipt_id = clean(row.get("legacy_receipt_id"))
        if legacy_receipt_id and legacy_receipt_id not in existing_receipt_ids:
            invoice_line_counts[legacy_receipt_id] += 1

    target_ids = set(invoice_line_counts)
    receipt_rows = parse_receipt_xml(target_ids)
    excluded_rows = {
        clean(row.get("legacy_receipt_id")): row
        for row in read_csv(RECEIPT_EXCLUDED_CSV)
        if clean(row.get("legacy_receipt_id")) in target_ids
    }

    missing_xml = sorted(target_ids - set(receipt_rows))
    if missing_xml:
        raise RuntimeError({"missing_receipt_xml_rows": missing_xml[:30], "missing_count": len(missing_xml)})
    missing_excluded = sorted(target_ids - set(excluded_rows))
    if missing_excluded:
        raise RuntimeError({"missing_excluded_policy_rows": missing_excluded[:30], "missing_count": len(missing_excluded)})

    rows_out: list[dict[str, object]] = []
    for legacy_receipt_id in sorted(target_ids):
        xml_row = receipt_rows[legacy_receipt_id]
        excluded = excluded_rows[legacy_receipt_id]
        rows_out.append(
            {
                "legacy_receipt_id": legacy_receipt_id,
                "external_id": xml_row["external_id"],
                "type": clean(xml_row.get("type")) or "receive",
                "project_ref": clean(xml_row.get("project_ref")),
                "partner_ref": clean(xml_row.get("partner_ref")),
                "legacy_contract_id": clean(xml_row.get("legacy_contract_id")),
                "amount": clean(xml_row.get("amount")),
                "date_request": clean(xml_row.get("date_request")),
                "note": clean(xml_row.get("note")),
                "policy_action": clean(excluded.get("policy_action")),
                "bucket": clean(excluded.get("bucket")),
                "partner_name": clean(excluded.get("partner_name")),
                "document_no": clean(excluded.get("document_no")),
                "invoice_line_count": invoice_line_counts[legacy_receipt_id],
            }
        )

    fieldnames = [
        "legacy_receipt_id",
        "external_id",
        "type",
        "project_ref",
        "partner_ref",
        "legacy_contract_id",
        "amount",
        "date_request",
        "note",
        "policy_action",
        "bucket",
        "partner_name",
        "document_no",
        "invoice_line_count",
    ]
    write_csv(OUTPUT_CSV, fieldnames, rows_out)
    payload = {
        "status": "PASS",
        "mode": "history_receipt_parent_recovery_adapter",
        "payload_rows": len(rows_out),
        "invoice_line_rows_covered": sum(invoice_line_counts.values()),
        "policy_action_counts": dict(Counter(clean(row["policy_action"]) for row in rows_out)),
        "payload_csv": str(OUTPUT_CSV),
    }
    write_json(OUTPUT_JSON, payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
