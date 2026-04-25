#!/usr/bin/env python3
"""Build replay payload for contract summary lines."""

from __future__ import annotations

import csv
import json
import xml.etree.ElementTree as ET
from pathlib import Path


REPO_ROOT = Path.cwd()
INPUT_XML = REPO_ROOT / "migration_assets/20_business/contract_line/contract_line_summary_v1.xml"
INPUT_MANIFEST = REPO_ROOT / "migration_assets/manifest/contract_line_asset_manifest_v1.json"
OUTPUT_JSON = REPO_ROOT / "artifacts/migration/fresh_db_contract_line_replay_adapter_result_v1.json"
OUTPUT_CSV = REPO_ROOT / "artifacts/migration/fresh_db_contract_line_replay_payload_v1.csv"


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
    contract_ref = clean(row.get("contract_id__ref"))
    payload_rows.append(
        {
            "external_id": row["external_id"],
            "legacy_contract_id": contract_ref.removeprefix("legacy_contract_sc_"),
            "sequence": row.get("sequence", ""),
            "qty_contract": row.get("qty_contract", ""),
            "price_contract": row.get("price_contract", ""),
            "note": row.get("note", ""),
            "idempotency_key": row["external_id"],
            "replay_action": "create_if_missing",
        }
    )

status = "PASS" if len(payload_rows) == expected_rows else "FAIL"
payload = {
    "status": status,
    "mode": "fresh_db_contract_line_replay_adapter",
    "db_writes": 0,
    "asset_package_id": asset_manifest["asset_package_id"],
    "expected_rows": expected_rows,
    "replay_payload_rows": len(payload_rows),
    "row_artifact": str(OUTPUT_CSV),
    "decision": "contract_line_replay_payload_ready" if status == "PASS" else "STOP_REVIEW_REQUIRED",
}
write_csv(
    OUTPUT_CSV,
    ["external_id", "legacy_contract_id", "sequence", "qty_contract", "price_contract", "note", "idempotency_key", "replay_action"],
    payload_rows,
)
write_json(OUTPUT_JSON, payload)
print(
    "FRESH_DB_CONTRACT_LINE_REPLAY_ADAPTER="
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
