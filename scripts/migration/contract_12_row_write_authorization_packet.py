"""Build the no-DB authorization packet for 12 contract header rows."""

from __future__ import annotations

import csv
import json
from pathlib import Path


DRY_RUN_CSV = Path("artifacts/migration/contract_header_12_row_dry_run_rows_v1.csv")
PRECHECK_JSON = Path("artifacts/migration/contract_header_12_row_readonly_db_precheck_v1.json")
OUTPUT_CSV = Path("artifacts/migration/contract_12_row_write_authorization_payload_v1.csv")
OUTPUT_JSON = Path("artifacts/migration/contract_12_row_write_authorization_packet_v1.json")


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(path, fieldnames, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


precheck = json.loads(PRECHECK_JSON.read_text(encoding="utf-8"))
dry_rows = read_csv(DRY_RUN_CSV)
precheck_by_legacy = {row["legacy_contract_id"]: row for row in precheck.get("rows", [])}

payload_rows = []
blockers = []

for row in dry_rows:
    legacy_contract_id = row["legacy_contract_id"]
    precheck_row = precheck_by_legacy.get(legacy_contract_id)
    if not precheck_row:
        blockers.append({"legacy_contract_id": legacy_contract_id, "reason": "missing_precheck_row"})
        continue
    if precheck_row.get("status") != "READY_FOR_WRITE_AUTHORIZATION_GATE":
        blockers.append(
            {
                "legacy_contract_id": legacy_contract_id,
                "reason": "precheck_not_ready",
                "blockers": precheck_row.get("blockers", []),
            }
        )
        continue
    payload_rows.append(
        {
            "legacy_contract_id": legacy_contract_id,
            "legacy_project_id": row["legacy_project_id"],
            "project_id": row["project_id"],
            "partner_id": row["partner_id"],
            "subject": row["subject"],
            "type": row["type"],
            "legacy_contract_no": row["legacy_contract_no"],
            "legacy_document_no": row["legacy_document_no"],
            "legacy_external_contract_no": row["legacy_external_contract_no"],
            "legacy_status": row["legacy_status"],
            "legacy_deleted_flag": row["legacy_deleted_flag"],
            "legacy_counterparty_text": row["legacy_counterparty_text"],
            "tax_policy": row["tax_id_policy"],
            "name_policy": row["name_policy"],
            "state_policy": row["state_policy"],
        }
    )

fieldnames = [
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
    "tax_policy",
    "name_policy",
    "state_policy",
]
write_csv(OUTPUT_CSV, fieldnames, payload_rows)

packet = {
    "status": "PASS" if len(payload_rows) == 12 and not blockers else "PASS_WITH_BLOCKERS",
    "mode": "contract_12_row_write_authorization_packet_no_db",
    "database": "sc_demo",
    "input_dry_run": str(DRY_RUN_CSV),
    "input_precheck": str(PRECHECK_JSON),
    "payload_csv": str(OUTPUT_CSV),
    "payload_rows": len(payload_rows),
    "blocked_rows": len(blockers),
    "blockers": blockers,
    "write_authorization": "not_granted",
    "write_scope": {
        "model": "construction.contract",
        "operation": "create_only",
        "row_count": len(payload_rows),
        "allowed_fields": fieldnames,
        "forbidden_operations": ["update", "unlink", "workflow replay", "line creation", "payment linkage", "settlement linkage"],
    },
    "precheck_summary": {
        "row_count": precheck.get("row_count"),
        "ready_for_write_authorization_gate_rows": precheck.get("ready_for_write_authorization_gate_rows"),
        "blocked_rows": precheck.get("blocked_rows"),
        "blocker_counts": precheck.get("blocker_counts", {}),
    },
    "authorization_boundary": "real contract write requires separate explicit authorization after this packet",
    "next_step": "stop for explicit contract write authorization, or continue no-DB rollback/post-write review design",
}
write_json(OUTPUT_JSON, packet)
print(
    "CONTRACT_12_ROW_WRITE_AUTH_PACKET="
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
