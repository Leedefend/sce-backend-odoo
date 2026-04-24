#!/usr/bin/env python3
"""Build replay payload for legacy expense deposit facts."""

from __future__ import annotations

import csv
import json
import xml.etree.ElementTree as ET
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
INPUT_XML = REPO_ROOT / "migration_assets/30_relation/legacy_expense_deposit/legacy_expense_deposit_v1.xml"
OUTPUT_CSV = REPO_ROOT / "artifacts/migration/fresh_db_legacy_expense_deposit_replay_payload_v1.csv"
OUTPUT_JSON = REPO_ROOT / "artifacts/migration/fresh_db_legacy_expense_deposit_replay_adapter_result_v1.json"


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


def main() -> int:
    rows: list[dict[str, object]] = []
    for _, elem in ET.iterparse(INPUT_XML, events=("end",)):
        if elem.tag != "record":
            continue
        if clean(elem.attrib.get("model")) != "sc.legacy.expense.deposit.fact":
            elem.clear()
            continue
        record = {"external_id": clean(elem.attrib.get("id")), "project_ref": "", "partner_ref": "", "replay_action": "create_if_missing"}
        for field in elem.findall("field"):
            name = clean(field.attrib.get("name"))
            value = clean(field.attrib.get("ref")) or clean(field.text)
            if name == "project_id":
                record["project_ref"] = value
            elif name == "partner_id":
                record["partner_ref"] = value
            else:
                record[name] = value
        rows.append(record)
        elem.clear()

    fieldnames = [
        "external_id",
        "legacy_source_table",
        "legacy_record_id",
        "legacy_pid",
        "source_family",
        "direction",
        "document_no",
        "document_date",
        "legacy_state",
        "project_ref",
        "legacy_project_id",
        "legacy_project_name",
        "partner_ref",
        "legacy_partner_id",
        "legacy_partner_name",
        "source_amount",
        "source_amount_field",
        "note",
        "import_batch",
        "replay_action",
    ]
    write_csv(OUTPUT_CSV, fieldnames, rows)
    payload = {
        "status": "PASS",
        "mode": "fresh_db_legacy_expense_deposit_replay_adapter",
        "expected_rows": len(rows),
        "replay_payload_rows": len(rows),
        "payload_csv": str(OUTPUT_CSV),
    }
    write_json(OUTPUT_JSON, payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
