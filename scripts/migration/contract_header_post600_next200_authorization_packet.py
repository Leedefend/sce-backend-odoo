#!/usr/bin/env python3
"""Build a no-DB authorization packet for the post600 next 200-row contract header design."""

from __future__ import annotations

import csv
import json
from pathlib import Path


REPO_ROOT = Path.cwd()
DESIGN_JSON = REPO_ROOT / "artifacts/migration/contract_header_post600_next200_write_design_result_v1.json"
DESIGN_CSV = REPO_ROOT / "artifacts/migration/contract_header_post600_next200_write_design_rows_v1.csv"
OUTPUT_CSV = REPO_ROOT / "artifacts/migration/contract_header_post600_next200_authorization_payload_v1.csv"
OUTPUT_JSON = REPO_ROOT / "artifacts/migration/contract_header_post600_next200_authorization_packet_v1.json"

PAYLOAD_FIELDS = [
    "legacy_contract_id",
    "legacy_project_id",
    "project_id",
    "partner_id",
    "subject",
    "type",
    "legacy_contract_no",
    "legacy_document_no",
    "legacy_external_contract_no",
    "legacy_status",
    "legacy_deleted_flag",
    "legacy_counterparty_text",
]


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(path, fieldnames, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def clean(value):
    return "" if value is None else str(value).strip()


def main():
    design = json.loads(DESIGN_JSON.read_text(encoding="utf-8"))
    design_rows = read_csv(DESIGN_CSV)
    blockers = []
    if design.get("status") != "PASS":
        blockers.append({"reason": "design_not_pass", "status": design.get("status")})
    if design.get("write_design_rows") != len(design_rows):
        blockers.append({"reason": "design_row_count_mismatch", "json": design.get("write_design_rows"), "csv": len(design_rows)})
    if len(design_rows) != 200:
        blockers.append({"reason": "payload_not_200_rows", "count": len(design_rows)})

    payload_rows = []
    for row in design_rows:
        row_blockers = []
        if clean(row.get("target_model")) != "construction.contract":
            row_blockers.append("target_model_not_construction_contract")
        if clean(row.get("operation")) != "create_only":
            row_blockers.append("operation_not_create_only")
        if clean(row.get("db_write")) != "no":
            row_blockers.append("db_write_not_no")
        for field in ("legacy_contract_id", "project_id", "partner_id", "subject", "type"):
            if not clean(row.get(field)):
                row_blockers.append(f"missing_{field}")
        if row_blockers:
            blockers.append({"legacy_contract_id": clean(row.get("legacy_contract_id")), "reasons": row_blockers})
            continue
        payload_rows.append({field: clean(row.get(field)) for field in PAYLOAD_FIELDS})

    write_csv(OUTPUT_CSV, PAYLOAD_FIELDS, payload_rows)
    packet = {
        "status": "PASS" if len(payload_rows) == 200 and not blockers else "PASS_WITH_BLOCKERS",
        "mode": "contract_header_post600_next200_authorization_packet_no_db",
        "database": "sc_demo",
        "db_writes": 0,
        "input_design": str(DESIGN_JSON),
        "input_design_rows": str(DESIGN_CSV),
        "payload_csv": str(OUTPUT_CSV),
        "payload_rows": len(payload_rows),
        "blocked_rows": len(blockers),
        "blockers": blockers[:50],
        "write_authorization": "packet_ready_write_not_executed",
        "write_scope": {
            "model": "construction.contract",
            "operation": "create_only",
            "row_count": len(payload_rows),
            "allowed_fields": PAYLOAD_FIELDS,
            "rollback_key": "legacy_contract_id",
            "forbidden_operations": [
                "update",
                "unlink",
                "workflow_replay",
                "line_creation",
                "payment_linkage",
                "settlement_linkage",
                "accounting_semantics",
            ],
        },
        "next_step": "open dedicated DB write batch for the post600 next 200-row payload" if len(payload_rows) == 200 and not blockers else "resolve packet blockers",
    }
    write_json(OUTPUT_JSON, packet)
    print(
        "CONTRACT_HEADER_POST600_NEXT200_AUTH_PACKET="
        + json.dumps(
            {
                "status": packet["status"],
                "payload_rows": packet["payload_rows"],
                "blocked_rows": packet["blocked_rows"],
                "write_authorization": packet["write_authorization"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


main()
