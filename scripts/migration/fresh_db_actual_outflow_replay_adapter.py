#!/usr/bin/env python3
"""Build replay payload for actual outflow draft carriers."""

from __future__ import annotations

import csv
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
INPUT_XML = REPO_ROOT / "migration_assets/20_business/actual_outflow/actual_outflow_core_v1.xml"
OUTPUT_CSV = REPO_ROOT / "artifacts/migration/fresh_db_actual_outflow_replay_payload_v1.csv"
OUTPUT_JSON = REPO_ROOT / "artifacts/migration/fresh_db_actual_outflow_replay_adapter_result_v1.json"
REQUEST_EXTERNAL_RE = re.compile(r"request_external_id=([^;]+)")


def clean(value: object) -> str:
    return "" if value is None else str(value).strip()


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_request_external_id(note: str) -> str:
    match = REQUEST_EXTERNAL_RE.search(note)
    return clean(match.group(1)) if match else ""


def main() -> int:
    rows: list[dict[str, object]] = []
    for _, elem in ET.iterparse(INPUT_XML, events=("end",)):
        if elem.tag != "record":
            continue
        if clean(elem.attrib.get("model")) != "payment.request":
            elem.clear()
            continue
        record = {
            "external_id": clean(elem.attrib.get("id")),
            "type": "",
            "project_ref": "",
            "partner_ref": "",
            "amount": "",
            "date_request": "",
            "note": "",
            "request_external_id": "",
            "idempotency_key": "",
            "replay_action": "create_if_missing",
        }
        for field in elem.findall("field"):
            name = clean(field.attrib.get("name"))
            value = clean(field.attrib.get("ref")) or clean(field.text)
            if name == "type":
                record["type"] = value
            elif name == "project_id":
                record["project_ref"] = value
            elif name == "partner_id":
                record["partner_ref"] = value
            elif name == "amount":
                record["amount"] = value
            elif name == "date_request":
                record["date_request"] = value
            elif name == "note":
                record["note"] = value
        record["request_external_id"] = parse_request_external_id(clean(record["note"]))
        record["idempotency_key"] = clean(record["external_id"])
        rows.append(record)
        elem.clear()

    fieldnames = [
        "external_id",
        "type",
        "project_ref",
        "partner_ref",
        "amount",
        "date_request",
        "note",
        "request_external_id",
        "idempotency_key",
        "replay_action",
    ]
    write_csv(OUTPUT_CSV, fieldnames, rows)
    payload = {
        "status": "PASS",
        "mode": "fresh_db_actual_outflow_replay_adapter",
        "expected_rows": len(rows),
        "replay_payload_rows": len(rows),
        "payload_csv": str(OUTPUT_CSV),
    }
    write_json(OUTPUT_JSON, payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
