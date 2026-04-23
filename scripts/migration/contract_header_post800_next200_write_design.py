#!/usr/bin/env python3
"""Build a no-DB create-only design for the post800 next 200-row contract header slice."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


REPO_ROOT = Path.cwd()
INPUT_CSV = REPO_ROOT / "artifacts/migration/contract_header_next_slice200_after_800_v1.csv"
PRECHECK_JSON = REPO_ROOT / "artifacts/migration/contract_header_post800_next200_readonly_precheck_result_v1.json"
OUTPUT_CSV = REPO_ROOT / "artifacts/migration/contract_header_post800_next200_write_design_rows_v1.csv"
OUTPUT_JSON = REPO_ROOT / "artifacts/migration/contract_header_post800_next200_write_design_result_v1.json"

ALLOWED_FIELDS = [
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


def clean(value):
    return "" if value is None else str(value).strip()


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


def as_int(value, default=-1):
    if value is None or value == "":
        return default
    return int(value)


def main():
    precheck = json.loads(PRECHECK_JSON.read_text(encoding="utf-8"))
    if precheck.get("status") != "PASS":
        raise RuntimeError({"precheck_not_pass": precheck.get("status")})
    precheck_rows = {clean(row.get("legacy_contract_id")): row for row in precheck.get("rows", [])}
    precheck_summary_ready = (
        precheck.get("status") == "PASS"
        and as_int(precheck.get("row_count")) == as_int(precheck.get("ready_for_write_design_rows"))
        and as_int(precheck.get("blocked_rows")) == 0
    )
    rows = read_csv(INPUT_CSV)

    blockers = []
    duplicate_input_ids = [
        key for key, count in Counter(clean(row.get("legacy_contract_id")) for row in rows).items() if key and count > 1
    ]
    if duplicate_input_ids:
        blockers.append({"reason": "duplicate_input_legacy_contract_id", "ids": duplicate_input_ids})

    design_rows = []
    type_counts = Counter()
    status_counts = Counter()
    for index, row in enumerate(rows, start=1):
        legacy_contract_id = clean(row.get("legacy_contract_id"))
        precheck_row = precheck_rows.get(legacy_contract_id)
        row_blockers = []
        if not precheck_row and not precheck_summary_ready:
            row_blockers.append("missing_precheck_row")
        elif precheck_row and precheck_row.get("status") != "READY_FOR_WRITE_DESIGN":
            row_blockers.append("precheck_not_ready")
        if clean(row.get("dry_run_status")) != "READY_FOR_READONLY_PRECHECK":
            row_blockers.append("dry_run_not_ready")
        if clean(row.get("type")) not in {"out", "in"}:
            row_blockers.append("invalid_contract_type")
        if clean(row.get("legacy_deleted_flag")) == "1":
            row_blockers.append("deleted_flag")
        for field in ("legacy_contract_id", "legacy_project_id", "project_id", "partner_id", "subject"):
            if not clean(row.get(field)):
                row_blockers.append(f"missing_{field}")

        type_counts[clean(row.get("type")) or "blank"] += 1
        status_counts[clean(row.get("legacy_status")) or "blank"] += 1
        if row_blockers:
            blockers.append({"legacy_contract_id": legacy_contract_id, "reasons": row_blockers})
            continue

        design = {field: clean(row.get(field)) for field in ALLOWED_FIELDS}
        design.update(
            {
                "write_design_id": f"contract_header_post800_next200:{index:04d}",
                "target_model": "construction.contract",
                "operation": "create_only",
                "rollback_key": "legacy_contract_id",
                "rollback_key_value": legacy_contract_id,
                "name_policy": "use_model_sequence_only_after_write_authorization",
                "tax_policy": "defer_to_model_defaults_or_later_tax_precheck",
                "state_policy": "create_as_draft_do_not_replay_legacy_workflow",
                "line_policy": "do_not_create_lines",
                "db_write": "no",
            }
        )
        design_rows.append(design)

    fieldnames = [
        "write_design_id",
        "target_model",
        "operation",
        *ALLOWED_FIELDS,
        "rollback_key",
        "rollback_key_value",
        "name_policy",
        "tax_policy",
        "state_policy",
        "line_policy",
        "db_write",
    ]
    write_csv(OUTPUT_CSV, fieldnames, design_rows)

    payload = {
        "status": "PASS" if len(design_rows) == len(rows) and not blockers else "PASS_WITH_BLOCKERS",
        "mode": "contract_header_post800_next200_write_design_no_db",
        "database": "no_db_access",
        "db_writes": 0,
        "input": str(INPUT_CSV),
        "input_precheck": str(PRECHECK_JSON),
        "input_rows": len(rows),
        "write_design_rows": len(design_rows),
        "blocked_rows": len(blockers),
        "blockers": blockers[:50],
        "type_counts": dict(sorted(type_counts.items())),
        "legacy_status_counts": dict(sorted(status_counts.items())),
        "output_rows": str(OUTPUT_CSV),
        "write_authorization": "not_granted",
        "write_scope": {
            "model": "construction.contract",
            "operation": "create_only",
            "allowed_fields": ALLOWED_FIELDS,
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
        "next_step": "open no-DB authorization packet for the post800 next 200-row design" if len(design_rows) == len(rows) and not blockers else "resolve design blockers",
    }
    write_json(OUTPUT_JSON, payload)
    print(
        "CONTRACT_HEADER_POST800_NEXT200_WRITE_DESIGN="
        + json.dumps(
            {
                "status": payload["status"],
                "input_rows": payload["input_rows"],
                "write_design_rows": payload["write_design_rows"],
                "blocked_rows": payload["blocked_rows"],
                "write_authorization": payload["write_authorization"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


main()
