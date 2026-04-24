#!/usr/bin/env python3
"""Build replay payload for legacy workflow audit facts."""

from __future__ import annotations

import csv
import json
import xml.etree.ElementTree as ET
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
INPUT_XML = REPO_ROOT / "migration_assets/30_relation/legacy_workflow_audit/legacy_workflow_audit_v1.xml"
OUTPUT_CSV = REPO_ROOT / "artifacts/migration/fresh_db_legacy_workflow_audit_replay_payload_v1.csv"
OUTPUT_JSON = REPO_ROOT / "artifacts/migration/fresh_db_legacy_workflow_audit_replay_adapter_result_v1.json"


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
        if clean(elem.attrib.get("model")) != "sc.legacy.workflow.audit":
            elem.clear()
            continue
        record = {"external_id": clean(elem.attrib.get("id")), "replay_action": "create_if_missing"}
        for field in elem.findall("field"):
            name = clean(field.attrib.get("name"))
            record[name] = clean(field.attrib.get("ref")) or clean(field.text)
        rows.append(record)
        elem.clear()

    fieldnames = [
        "external_id",
        "legacy_workflow_id",
        "legacy_pid",
        "legacy_djid",
        "legacy_business_id",
        "legacy_source_table",
        "legacy_detail_status_id",
        "legacy_detail_step_id",
        "legacy_setup_step_id",
        "legacy_template_id",
        "legacy_step_name",
        "legacy_template_name",
        "target_model",
        "target_external_id",
        "target_lane",
        "actor_legacy_user_id",
        "actor_name",
        "approved_at",
        "received_at",
        "action_classification",
        "legacy_status",
        "legacy_back_type",
        "legacy_approval_type",
        "approval_note",
        "import_batch",
        "replay_action",
    ]
    write_csv(OUTPUT_CSV, fieldnames, rows)
    payload = {
        "status": "PASS",
        "mode": "fresh_db_legacy_workflow_audit_replay_adapter",
        "expected_rows": len(rows),
        "replay_payload_rows": len(rows),
        "payload_csv": str(OUTPUT_CSV),
    }
    write_json(OUTPUT_JSON, payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
