#!/usr/bin/env python3
"""Build targeted project-member neutral replay payload for attachment backfill."""

from __future__ import annotations

import csv
import json
import xml.etree.ElementTree as ET
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
ATTACHMENT_PAYLOAD_CSV = REPO_ROOT / "artifacts/migration/fresh_db_legacy_attachment_backfill_replay_payload_v1.csv"
PROJECT_MEMBER_XML = REPO_ROOT / "migration_assets/30_relation/project_member/project_member_neutral_v1.xml"
OUTPUT_CSV = REPO_ROOT / "artifacts/migration/history_project_member_attachment_targeted_replay_payload_v1.csv"
OUTPUT_JSON = REPO_ROOT / "artifacts/migration/history_project_member_attachment_targeted_replay_adapter_result_v1.json"


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


def legacy_user_ref_from_xml(value: str) -> str:
    text = clean(value)
    if text.startswith("legacy_user_sc_"):
        return text.removeprefix("legacy_user_sc_")
    return text


def main() -> int:
    attachment_rows = read_csv(ATTACHMENT_PAYLOAD_CSV)
    target_refs = {
        clean(row.get("res_ref")).removeprefix("legacy_project_member_sc_")
        for row in attachment_rows
        if clean(row.get("res_ref")).startswith("legacy_project_member_sc_")
    }
    target_refs = {item for item in target_refs if item}

    payload_rows: list[dict[str, object]] = []
    seen_ids: set[str] = set()
    for _, elem in ET.iterparse(PROJECT_MEMBER_XML, events=("end",)):
        if elem.tag != "record":
            continue
        external_id = clean(elem.attrib.get("id"))
        if not external_id.startswith("legacy_project_member_sc_"):
            elem.clear()
            continue
        legacy_member_id = external_id.removeprefix("legacy_project_member_sc_")
        if legacy_member_id not in target_refs or legacy_member_id in seen_ids:
            elem.clear()
            continue
        fields = {clean(field.attrib.get("name")): clean(field.attrib.get("ref")) or clean(field.text) for field in elem.findall("field")}
        payload_rows.append(
            {
                "legacy_member_id": legacy_member_id,
                "legacy_project_id": clean(fields.get("legacy_project_id")),
                "legacy_user_ref": legacy_user_ref_from_xml(fields.get("user_id", "")),
                "project_ref": clean(fields.get("project_id")),
                "user_ref": clean(fields.get("user_id")),
                "role_fact_status": clean(fields.get("role_fact_status")) or "missing",
                "import_batch": clean(fields.get("import_batch")) or "project_member_neutral_xml_v1",
                "evidence": clean(fields.get("evidence")) or external_id,
                "notes": clean(fields.get("notes")) or "neutral staging only; role fact missing",
                "active": clean(fields.get("active")) or "1",
                "replay_action": "create_if_missing",
            }
        )
        seen_ids.add(legacy_member_id)
        elem.clear()

    fieldnames = [
        "legacy_member_id",
        "legacy_project_id",
        "legacy_user_ref",
        "project_ref",
        "user_ref",
        "role_fact_status",
        "import_batch",
        "evidence",
        "notes",
        "active",
        "replay_action",
    ]
    write_csv(OUTPUT_CSV, fieldnames, sorted(payload_rows, key=lambda row: row["legacy_member_id"]))
    payload = {
        "status": "PASS" if len(payload_rows) == len(target_refs) else "FAIL",
        "mode": "history_project_member_attachment_targeted_replay_adapter",
        "requested_member_refs": len(target_refs),
        "payload_rows": len(payload_rows),
        "missing_xml_rows": len(target_refs) - len(payload_rows),
        "payload_csv": str(OUTPUT_CSV),
    }
    write_json(OUTPUT_JSON, payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
