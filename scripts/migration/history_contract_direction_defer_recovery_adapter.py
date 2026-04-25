#!/usr/bin/env python3
"""Build recovery payload for direction-defer contract headers backed by repayment strong evidence."""

from __future__ import annotations

import csv
import json
import xml.etree.ElementTree as ET
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_CONTRACT_CSV = REPO_ROOT / "tmp/raw/contract/contract.csv"
DIRECTION_DEFER_CSV = REPO_ROOT / "artifacts/migration/history_contract_direction_defer_rows_v1.csv"
STRONG_EVIDENCE_CSV = REPO_ROOT / "artifacts/migration/contract_counterparty_strong_evidence_candidates_v1.csv"
PARTNER_XML = REPO_ROOT / "migration_assets/10_master/partner/partner_master_v1.xml"
OUTPUT_CSV = REPO_ROOT / "artifacts/migration/history_contract_direction_defer_recovery_payload_v1.csv"
OUTPUT_JSON = REPO_ROOT / "artifacts/migration/history_contract_direction_defer_recovery_adapter_result_v1.json"
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


def load_partner_xml_records() -> tuple[dict[str, dict[str, str]], dict[str, dict[str, str]]]:
    fields_keep = {
        "name",
        "legacy_partner_id",
        "legacy_partner_source",
        "legacy_partner_name",
        "legacy_credit_code",
        "legacy_tax_no",
        "legacy_source_evidence",
    }
    found_by_name: dict[str, dict[str, str]] = {}
    found_by_legacy_id: dict[str, dict[str, str]] = {}
    for _, elem in ET.iterparse(PARTNER_XML, events=("end",)):
        if elem.tag != "record":
            continue
        values = {"external_id": clean(elem.attrib.get("id"))}
        for field in elem.findall("field"):
            name = clean(field.attrib.get("name"))
            if name in fields_keep:
                values[name] = clean(field.text)
        partner_name = clean(values.get("name"))
        legacy_partner_id = clean(values.get("legacy_partner_id"))
        if partner_name and partner_name not in found_by_name:
            found_by_name[partner_name] = values
        if legacy_partner_id:
            found_by_legacy_id[legacy_partner_id] = values
        elem.clear()
    return found_by_name, found_by_legacy_id


def main() -> int:
    direction_rows = read_csv(DIRECTION_DEFER_CSV)
    raw_by_id = {clean(row.get("Id")): row for row in read_csv(RAW_CONTRACT_CSV)}
    strong_by_contract = {clean(row.get("legacy_contract_id")): row for row in read_csv(STRONG_EVIDENCE_CSV)}
    partner_by_name, partner_by_legacy_id = load_partner_xml_records()

    rows_out: list[dict[str, object]] = []
    missing_strong: list[str] = []

    for row in direction_rows:
        legacy_contract_id = clean(row.get("legacy_contract_id"))
        raw = raw_by_id.get(legacy_contract_id)
        if not raw:
            raise RuntimeError({"missing_raw_contract": legacy_contract_id})
        strong = strong_by_contract.get(legacy_contract_id)
        if not strong:
            missing_strong.append(legacy_contract_id)
            continue
        partner_name = clean(strong.get("repayment_partner_name"))
        repayment_partner_id = clean(strong.get("repayment_partner_id"))
        partner_record = partner_by_legacy_id.get(repayment_partner_id) or partner_by_name.get(partner_name)
        if not partner_record:
            raise RuntimeError({"missing_partner_master_record": legacy_contract_id, "partner_name": partner_name, "repayment_partner_id": repayment_partner_id})
        rows_out.append(
            {
                "legacy_contract_id": legacy_contract_id,
                "legacy_project_id": clean(raw.get("XMID")),
                "subject": clean(raw.get("HTBT")) or clean(raw.get("DJBH")) or clean(raw.get("HTBH")),
                # Direction-defer rows lack usable own-company side markers.
                # The original full rebuild already froze them under repayment-based
                # strong evidence, so continuity promotion follows receipt-side
                # customer direction.
                "type": "in",
                "legacy_contract_no": clean(raw.get("HTBH")),
                "legacy_document_no": clean(raw.get("DJBH")),
                "legacy_external_contract_no": clean(raw.get("f_WBHTBH")) or clean(raw.get("WBHTBH")) or clean(raw.get("PID")),
                "legacy_status": clean(raw.get("DJZT")),
                "legacy_deleted_flag": clean(raw.get("DEL")),
                "legacy_counterparty_text": clean(raw.get("FBF")) or clean(raw.get("CBF")),
                "partner_name": clean(partner_record.get("name")),
                "partner_legacy_source": clean(partner_record.get("legacy_partner_source")),
                "partner_legacy_id": clean(partner_record.get("legacy_partner_id")),
                "evidence_type": clean(strong.get("evidence_type")),
                "evidence_strength": clean(strong.get("evidence_strength")),
                "manual_confirm_required": clean(strong.get("manual_confirm_required")),
                "recovery_family": "direction_defer_strong_evidence_12",
            }
        )

    if missing_strong:
        raise RuntimeError({"missing_strong_evidence_rows": sorted(missing_strong)})
    if len(rows_out) != EXPECTED_ROWS:
        raise RuntimeError({"unexpected_payload_rows": len(rows_out), "expected": EXPECTED_ROWS})

    fieldnames = [
        "legacy_contract_id",
        "legacy_project_id",
        "subject",
        "type",
        "legacy_contract_no",
        "legacy_document_no",
        "legacy_external_contract_no",
        "legacy_status",
        "legacy_deleted_flag",
        "legacy_counterparty_text",
        "partner_name",
        "partner_legacy_source",
        "partner_legacy_id",
        "evidence_type",
        "evidence_strength",
        "manual_confirm_required",
        "recovery_family",
    ]
    write_csv(OUTPUT_CSV, fieldnames, rows_out)
    payload = {
        "status": "PASS",
        "mode": "history_contract_direction_defer_recovery_adapter",
        "payload_rows": len(rows_out),
        "payload_csv": str(OUTPUT_CSV),
        "evidence_type_counts": {
            "repayment_single_counterparty": sum(1 for row in rows_out if row["evidence_type"] == "repayment_single_counterparty"),
        },
    }
    write_json(OUTPUT_JSON, payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
