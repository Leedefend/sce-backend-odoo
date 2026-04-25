#!/usr/bin/env python3
"""Build replay payload for supplier contract headers."""

from __future__ import annotations

import csv
import json
import xml.etree.ElementTree as ET
from pathlib import Path


REPO_ROOT = Path.cwd()
INPUT_XML = REPO_ROOT / "migration_assets/20_business/supplier_contract/supplier_contract_header_v1.xml"
INPUT_MANIFEST = REPO_ROOT / "migration_assets/manifest/supplier_contract_asset_manifest_v1.json"
OUTPUT_JSON = REPO_ROOT / "artifacts/migration/fresh_db_supplier_contract_replay_adapter_result_v1.json"
OUTPUT_CSV = REPO_ROOT / "artifacts/migration/fresh_db_supplier_contract_replay_payload_v1.csv"


def clean(value: object) -> str:
    return "" if value is None else str(value).strip()


def parse_xml(path: Path) -> list[dict[str, str]]:
    root = ET.parse(path).getroot()
    rows: list[dict[str, str]] = []
    for record in root.findall(".//record"):
        row = {"external_id": clean(record.attrib.get("id")), "model": clean(record.attrib.get("model"))}
        for field in record.findall("field"):
            name = clean(field.attrib.get("name"))
            row[name] = clean(field.text)
            if field.attrib.get("ref"):
                row[f"{name}__ref"] = clean(field.attrib.get("ref"))
        rows.append(row)
    return rows


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


asset_manifest = json.loads(INPUT_MANIFEST.read_text(encoding="utf-8"))
rows = parse_xml(INPUT_XML)
expected_rows = int(asset_manifest["counts"]["loadable_records"])

payload_rows = []
for row in rows:
    project_ref = clean(row.get("project_id__ref"))
    partner_ref = clean(row.get("partner_id__ref"))
    payload_rows.append(
        {
            "external_id": row["external_id"],
            "legacy_contract_id": row.get("legacy_contract_id", ""),
            "legacy_project_id": row.get("legacy_project_id", "") or project_ref.removeprefix("legacy_project_sc_"),
            "legacy_partner_id": partner_ref.removeprefix("legacy_partner_sc_"),
            "legacy_document_no": row.get("legacy_document_no", ""),
            "legacy_contract_no": row.get("legacy_contract_no", ""),
            "legacy_status": row.get("legacy_status", ""),
            "legacy_deleted_flag": row.get("legacy_deleted_flag", ""),
            "legacy_counterparty_text": row.get("legacy_counterparty_text", ""),
            "subject": row.get("subject", ""),
            "type": row.get("type", ""),
            "date_contract": row.get("date_contract", ""),
            "note": row.get("note", ""),
            "idempotency_key": row["external_id"],
            "replay_action": "create_if_missing",
        }
    )

status = "PASS" if len(payload_rows) == expected_rows else "FAIL"
payload = {
    "status": status,
    "mode": "fresh_db_supplier_contract_replay_adapter",
    "db_writes": 0,
    "asset_package_id": asset_manifest["asset_package_id"],
    "expected_rows": expected_rows,
    "replay_payload_rows": len(payload_rows),
    "row_artifact": str(OUTPUT_CSV),
    "decision": "supplier_contract_replay_payload_ready" if status == "PASS" else "STOP_REVIEW_REQUIRED",
}
write_csv(
    OUTPUT_CSV,
    [
        "external_id",
        "legacy_contract_id",
        "legacy_project_id",
        "legacy_partner_id",
        "legacy_document_no",
        "legacy_contract_no",
        "legacy_status",
        "legacy_deleted_flag",
        "legacy_counterparty_text",
        "subject",
        "type",
        "date_contract",
        "note",
        "idempotency_key",
        "replay_action",
    ],
    payload_rows,
)
write_json(OUTPUT_JSON, payload)
print(
    "FRESH_DB_SUPPLIER_CONTRACT_REPLAY_ADAPTER="
    + json.dumps(
        {
            "status": status,
            "expected_rows": expected_rows,
            "replay_payload_rows": len(payload_rows),
            "db_writes": 0,
        },
        ensure_ascii=False,
        sort_keys=True,
    )
)
