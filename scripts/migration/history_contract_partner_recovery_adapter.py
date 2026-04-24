#!/usr/bin/env python3
"""Build recovery payload for non-direction-defer contract headers blocked only by partner resolution."""

from __future__ import annotations

import csv
import json
import xml.etree.ElementTree as ET
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_CONTRACT_CSV = REPO_ROOT / "tmp/raw/contract/contract.csv"
GAP_ROWS_CSV = REPO_ROOT / "artifacts/migration/history_contract_partner_gap_rows_v1.csv"
BACKTRACE_CSV = REPO_ROOT / "artifacts/migration/history_contract_strong_evidence_backtrace_rows_v1.csv"
RECEIPT_EXCLUDED_CSV = REPO_ROOT / "artifacts/migration/fresh_db_receipt_excluded_policy_rows_v1.csv"
PARTNER_XML = REPO_ROOT / "migration_assets/10_master/partner/partner_master_v1.xml"
OUTPUT_CSV = REPO_ROOT / "artifacts/migration/history_contract_partner_recovery_payload_v1.csv"
OUTPUT_JSON = REPO_ROOT / "artifacts/migration/history_contract_partner_recovery_adapter_result_v1.json"
EXPECTED_ROWS = 23
OWN_COMPANY_NAMES = {"四川保盛建设集团有限公司", "四川保感建设集团有限公司", "My Company"}


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


def infer_direction(raw: dict[str, str]) -> str:
    fbf = clean(raw.get("FBF"))
    cbf = clean(raw.get("CBF"))
    if cbf in OWN_COMPANY_NAMES and fbf not in OWN_COMPANY_NAMES:
        return "out"
    if fbf in OWN_COMPANY_NAMES and cbf not in OWN_COMPANY_NAMES:
        return "in"
    raise RuntimeError({"cannot_infer_direction": clean(raw.get("Id")), "fbf": fbf, "cbf": cbf})


def load_partner_xml_records() -> dict[str, dict[str, str]]:
    fields_keep = {
        "name",
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
        values = {"external_id": clean(elem.attrib.get("id"))}
        for field in elem.findall("field"):
            name = clean(field.attrib.get("name"))
            if name in fields_keep:
                values[name] = clean(field.text)
        name = clean(values.get("name"))
        if name:
            found[name] = values
        elem.clear()
    return found


def main() -> int:
    raw_by_id = {clean(row.get("Id")): row for row in read_csv(RAW_CONTRACT_CSV)}
    gap_rows = read_csv(GAP_ROWS_CSV)
    backtrace_rows = {clean(row.get("legacy_contract_id")): row for row in read_csv(BACKTRACE_CSV)}
    receipt_rows = read_csv(RECEIPT_EXCLUDED_CSV)
    partner_by_name = load_partner_xml_records()

    direct_contract_ids = {
        clean(row.get("legacy_contract_id"))
        for row in gap_rows
        if clean(row.get("partner_source_bucket")) == "partner_master_recoverable"
    }
    strong_contract_ids = {
        clean(row.get("legacy_contract_id"))
        for row in gap_rows
        if clean(row.get("partner_source_bucket")) == "no_asset_source_in_current_packages" and clean(row.get("counterparty_text"))
    }

    receipt_partner_map: dict[str, dict[str, str]] = {}
    for row in receipt_rows:
        contract_id = clean(row.get("legacy_contract_id"))
        if contract_id not in direct_contract_ids:
            continue
        candidate = {
            "partner_name": clean(row.get("partner_name")),
            "legacy_partner_id": clean(row.get("legacy_partner_id")),
        }
        existing = receipt_partner_map.get(contract_id)
        if existing and existing != candidate:
            raise RuntimeError({"conflicting_receipt_partner_mapping": contract_id, "existing": existing, "candidate": candidate})
        receipt_partner_map[contract_id] = candidate

    if set(receipt_partner_map) != direct_contract_ids:
        raise RuntimeError({"missing_receipt_partner_mapping": sorted(direct_contract_ids - set(receipt_partner_map))})

    rows_out: list[dict[str, object]] = []

    def append_row(legacy_contract_id: str, partner_name: str, recovery_family: str) -> None:
        raw = raw_by_id.get(legacy_contract_id)
        if not raw:
            raise RuntimeError({"missing_raw_contract": legacy_contract_id})
        partner_record = partner_by_name.get(partner_name)
        if not partner_record:
            raise RuntimeError({"missing_partner_master_record": legacy_contract_id, "partner_name": partner_name})
        rows_out.append(
            {
                "legacy_contract_id": legacy_contract_id,
                "legacy_project_id": clean(raw.get("XMID")),
                "subject": clean(raw.get("HTBT")) or clean(raw.get("DJBH")) or clean(raw.get("HTBH")),
                "type": infer_direction(raw),
                "legacy_contract_no": clean(raw.get("HTBH")),
                "legacy_document_no": clean(raw.get("DJBH")),
                "legacy_external_contract_no": clean(raw.get("f_WBHTBH")) or clean(raw.get("WBHTBH")) or clean(raw.get("PID")),
                "legacy_status": clean(raw.get("DJZT")),
                "legacy_deleted_flag": clean(raw.get("DEL")),
                "legacy_counterparty_text": clean(raw.get("FBF")),
                "partner_name": clean(partner_record.get("name")),
                "partner_legacy_source": clean(partner_record.get("legacy_partner_source")),
                "partner_legacy_id": clean(partner_record.get("legacy_partner_id")),
                "recovery_family": recovery_family,
            }
        )

    for legacy_contract_id in sorted(direct_contract_ids):
        append_row(legacy_contract_id, receipt_partner_map[legacy_contract_id]["partner_name"], "partner_master_replay_gap_4")

    for legacy_contract_id in sorted(strong_contract_ids):
        backtrace = backtrace_rows.get(legacy_contract_id)
        if not backtrace:
            raise RuntimeError({"missing_backtrace_row": legacy_contract_id})
        append_row(legacy_contract_id, clean(backtrace.get("repayment_partner_name")), "strong_evidence_promotion_gap_19")

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
        "recovery_family",
    ]
    write_csv(OUTPUT_CSV, fieldnames, rows_out)
    payload = {
        "status": "PASS",
        "mode": "history_contract_partner_recovery_adapter",
        "payload_rows": len(rows_out),
        "recovery_family_counts": {
            "partner_master_replay_gap_4": sum(1 for row in rows_out if row["recovery_family"] == "partner_master_replay_gap_4"),
            "strong_evidence_promotion_gap_19": sum(1 for row in rows_out if row["recovery_family"] == "strong_evidence_promotion_gap_19"),
        },
        "payload_csv": str(OUTPUT_CSV),
    }
    write_json(OUTPUT_JSON, payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
