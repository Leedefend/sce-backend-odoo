#!/usr/bin/env python3
"""Build replay payload for outflow request headers."""

from __future__ import annotations

import csv
import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path


REPO_ROOT = Path.cwd()
INPUT_XML = REPO_ROOT / "migration_assets/20_business/outflow/outflow_request_core_v1.xml"
INPUT_MANIFEST = REPO_ROOT / "migration_assets/manifest/outflow_request_asset_manifest_v1.json"
SOURCE_CSV = REPO_ROOT / "tmp/raw/payment/payment.csv"
OUTPUT_JSON = REPO_ROOT / "artifacts/migration/fresh_db_outflow_request_replay_adapter_result_v1.json"
OUTPUT_CSV = REPO_ROOT / "artifacts/migration/fresh_db_outflow_request_replay_payload_v1.csv"


def clean(value: object) -> str:
    return "" if value is None else str(value).strip()


def parse_datetime(value: object) -> str:
    raw = clean(value)
    if not raw:
        return ""
    for fmt in ("%m/%d/%Y %H:%M:%S", "%m/%d/%Y", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(raw, fmt).strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue
    return raw


def read_raw_source(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return {clean(row.get("Id")): dict(row) for row in csv.DictReader(handle) if clean(row.get("Id"))}


def extract_legacy_outflow_id(note: str) -> str:
    match = re.search(r"legacy_outflow_id=([^;\s]+)", note or "")
    return match.group(1) if match else ""


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
raw_by_id = read_raw_source(SOURCE_CSV)

payload_rows = []
for row in rows:
    note = row.get("note", "")
    legacy_record_id = extract_legacy_outflow_id(note)
    raw = raw_by_id.get(legacy_record_id, {})
    payload_rows.append(
        {
            "external_id": row["external_id"],
            "type": row.get("type", ""),
            "project_ref": row.get("project_id__ref", ""),
            "partner_ref": row.get("partner_id__ref", ""),
            "contract_ref": row.get("contract_id__ref", ""),
            "amount": row.get("amount", ""),
            "date_request": row.get("date_request", ""),
            "legacy_source_table": "C_ZFSQGL",
            "legacy_record_id": legacy_record_id,
            "creator_legacy_user_id": clean(raw.get("LRRID")),
            "creator_name": clean(raw.get("f_LRR")),
            "created_time": parse_datetime(raw.get("f_LRSJ")),
            "note": note,
            "idempotency_key": row["external_id"],
            "replay_action": "create_if_missing",
        }
    )

status = "PASS" if len(payload_rows) == expected_rows else "FAIL"
payload = {
    "status": status,
    "mode": "fresh_db_outflow_request_replay_adapter",
    "db_writes": 0,
    "asset_package_id": asset_manifest["asset_package_id"],
    "expected_rows": expected_rows,
    "replay_payload_rows": len(payload_rows),
    "row_artifact": str(OUTPUT_CSV),
    "decision": "outflow_request_replay_payload_ready" if status == "PASS" else "STOP_REVIEW_REQUIRED",
}
write_csv(
    OUTPUT_CSV,
    [
        "external_id",
        "type",
        "project_ref",
        "partner_ref",
        "contract_ref",
        "amount",
        "date_request",
        "legacy_source_table",
        "legacy_record_id",
        "creator_legacy_user_id",
        "creator_name",
        "created_time",
        "note",
        "idempotency_key",
        "replay_action",
    ],
    payload_rows,
)
write_json(OUTPUT_JSON, payload)
print(
    "FRESH_DB_OUTFLOW_REQUEST_REPLAY_ADAPTER="
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
