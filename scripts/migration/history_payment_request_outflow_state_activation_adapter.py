#!/usr/bin/env python3
"""Build payload for safe historical outflow-request state activation."""

from __future__ import annotations

import csv
import json
import re
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
OUTFLOW_XML = REPO_ROOT / "migration_assets/20_business/outflow/outflow_request_core_v1.xml"
WORKFLOW_XML = REPO_ROOT / "migration_assets/30_relation/legacy_workflow_audit/legacy_workflow_audit_v1.xml"
OUTPUT_CSV = REPO_ROOT / "artifacts/migration/history_payment_request_outflow_state_activation_payload_v1.csv"
OUTPUT_JSON = REPO_ROOT / "artifacts/migration/history_payment_request_outflow_state_activation_adapter_result_v1.json"

LEGACY_OUTFLOW_RE = re.compile(r"legacy_outflow_id=([^;]+)")
DOCUMENT_NO_RE = re.compile(r"document_no=([^;]+)")


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


def parse_note_token(pattern: re.Pattern[str], note: str) -> str:
    matched = pattern.search(clean(note))
    return clean(matched.group(1)) if matched else ""


def load_workflow_targets() -> Counter[str]:
    counter: Counter[str] = Counter()
    for _, elem in ET.iterparse(WORKFLOW_XML, events=("end",)):
        if elem.tag != "record":
            continue
        target_lane = ""
        target_external_id = ""
        for field in elem.findall("field"):
            name = clean(field.attrib.get("name"))
            value = clean(field.attrib.get("ref")) or clean(field.text)
            if name == "target_lane":
                target_lane = value
            elif name == "target_external_id":
                target_external_id = value
        if target_lane == "outflow_request" and target_external_id:
            counter[target_external_id] += 1
        elem.clear()
    if not counter:
        raise RuntimeError({"missing_workflow_targets": str(WORKFLOW_XML)})
    return counter


def load_outflow_requests() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for _, elem in ET.iterparse(OUTFLOW_XML, events=("end",)):
        if elem.tag != "record":
            continue
        external_id = clean(elem.attrib.get("id"))
        if not external_id.startswith("legacy_outflow_sc_"):
            elem.clear()
            continue
        note = ""
        for field in elem.findall("field"):
            if clean(field.attrib.get("name")) == "note":
                note = clean(field.text)
                break
        rows.append(
            {
                "external_id": external_id,
                "legacy_outflow_id": parse_note_token(LEGACY_OUTFLOW_RE, note),
                "document_no": parse_note_token(DOCUMENT_NO_RE, note),
                "note": note,
            }
        )
        elem.clear()
    if not rows:
        raise RuntimeError({"missing_outflow_asset_rows": str(OUTFLOW_XML)})
    return rows


def main() -> int:
    workflow_targets = load_workflow_targets()
    outflow_rows = load_outflow_requests()

    rows_out: list[dict[str, object]] = []
    for row in outflow_rows:
        external_id = clean(row["external_id"])
        workflow_row_count = int(workflow_targets.get(external_id) or 0)
        if workflow_row_count <= 0:
            continue
        rows_out.append(
            {
                "external_id": external_id,
                "legacy_outflow_id": clean(row["legacy_outflow_id"]),
                "document_no": clean(row["document_no"]),
                "workflow_row_count": workflow_row_count,
                "activation_target_state": "submit",
            }
        )

    if not rows_out:
        raise RuntimeError({"no_activation_candidates": True})

    missing_legacy_ids = [row["external_id"] for row in rows_out if not clean(row["legacy_outflow_id"])]
    if missing_legacy_ids:
        raise RuntimeError({"missing_legacy_outflow_id_in_note": missing_legacy_ids[:20], "count": len(missing_legacy_ids)})

    fieldnames = [
        "external_id",
        "legacy_outflow_id",
        "document_no",
        "workflow_row_count",
        "activation_target_state",
    ]
    write_csv(OUTPUT_CSV, fieldnames, rows_out)
    payload = {
        "status": "PASS",
        "mode": "history_payment_request_outflow_state_activation_adapter",
        "outflow_asset_rows": len(outflow_rows),
        "workflow_covered_rows": len(rows_out),
        "workflow_uncovered_rows": len(outflow_rows) - len(rows_out),
        "workflow_row_total": sum(int(row["workflow_row_count"]) for row in rows_out),
        "payload_csv": str(OUTPUT_CSV),
    }
    write_json(OUTPUT_JSON, payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
