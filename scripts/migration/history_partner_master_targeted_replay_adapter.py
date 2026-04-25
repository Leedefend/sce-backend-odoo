#!/usr/bin/env python3
"""Build targeted replay payload for missing partner-master anchors required by UR-B."""

from __future__ import annotations

import csv
import json
import xml.etree.ElementTree as ET
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
BACKTRACE_CSV = REPO_ROOT / "artifacts/migration/history_contract_strong_evidence_backtrace_rows_v1.csv"
PARTNER_XML = REPO_ROOT / "migration_assets/10_master/partner/partner_master_v1.xml"
OUTPUT_CSV = REPO_ROOT / "artifacts/migration/history_partner_master_targeted_replay_payload_v1.csv"
OUTPUT_JSON = REPO_ROOT / "artifacts/migration/history_partner_master_targeted_replay_adapter_result_v1.json"

TARGET_NAMES = {
    "中国人民解放军32038部队",
    "重庆市璧山区青杠街道产业发展服务中心",
    "德阳开放大学",
    "中国电信股份有限公司泸州分公司",
}


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
        name = clean(values.get("name"))
        if name in TARGET_NAMES:
            found[name] = values
        elem.clear()
    return found


def main() -> int:
    backtrace_rows = read_csv(BACKTRACE_CSV)
    required = {clean(row.get("repayment_partner_name")) for row in backtrace_rows if clean(row.get("repayment_partner_name")) in TARGET_NAMES}
    if required != TARGET_NAMES:
        raise RuntimeError({"error": "unexpected_target_names", "required": sorted(required), "expected": sorted(TARGET_NAMES)})

    records = load_partner_records()
    missing = sorted(name for name in TARGET_NAMES if name not in records)
    if missing:
        raise RuntimeError({"missing_partner_master_records": missing})

    rows = [records[name] for name in sorted(TARGET_NAMES)]
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
        "mode": "history_partner_master_targeted_replay_adapter",
        "target_rows": len(rows),
        "target_names": sorted(TARGET_NAMES),
        "payload_csv": str(OUTPUT_CSV),
    }
    write_json(OUTPUT_JSON, payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
