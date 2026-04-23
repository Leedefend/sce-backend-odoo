#!/usr/bin/env python3
"""Build a no-DB contract header dry-run payload from readiness candidates."""

from __future__ import annotations

import csv
import json
import os
import re
from collections import Counter
from pathlib import Path


REPO_ROOT = Path.cwd()
RAW_CONTRACT_CSV = REPO_ROOT / "tmp/raw/contract/contract.csv"
READINESS_JSON = REPO_ROOT / "artifacts/migration/contract_readiness_nodb_screen_result_v1.json"
SAFE_CANDIDATE_CSV = REPO_ROOT / "artifacts/migration/contract_readiness_nodb_screen_safe_candidates_v1.csv"
OUTPUT_ROWS_CSV = REPO_ROOT / "artifacts/migration/contract_header_bounded_dry_run_rows_v1.csv"
OUTPUT_SLICE_CSV = REPO_ROOT / "artifacts/migration/contract_header_bounded_dry_run_slice200_v1.csv"
OUTPUT_JSON = REPO_ROOT / "artifacts/migration/contract_header_bounded_dry_run_result_v1.json"
SLICE_LIMIT = int(os.environ.get("CONTRACT_HEADER_DRY_RUN_SLICE_LIMIT", "200"))


def clean(value):
    text = "" if value is None else str(value)
    text = text.replace("\u3000", " ").strip()
    return re.sub(r"\s+", " ", text)


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


def main():
    readiness = json.loads(READINESS_JSON.read_text(encoding="utf-8"))
    if readiness.get("status") != "PASS":
        raise RuntimeError({"readiness_not_pass": readiness.get("status")})
    if readiness.get("safe_candidate_rows", 0) <= 0:
        raise RuntimeError({"no_safe_candidates": readiness.get("safe_candidate_rows")})

    candidates = read_csv(SAFE_CANDIDATE_CSV)
    raw_contracts = {clean(row.get("Id")): row for row in read_csv(RAW_CONTRACT_CSV)}

    rows = []
    blockers = Counter()
    type_counts = Counter()
    status_counts = Counter()
    project_counts = Counter()
    partner_counts = Counter()

    for candidate in candidates:
        legacy_contract_id = clean(candidate.get("legacy_contract_id"))
        raw = raw_contracts.get(legacy_contract_id, {})
        legacy_project_id = clean(candidate.get("legacy_project_id"))
        project_id = clean(candidate.get("project_id"))
        partner_id = clean(candidate.get("partner_id"))
        subject = clean(candidate.get("subject"))
        contract_type = clean(candidate.get("direction"))
        legacy_status = clean(candidate.get("legacy_status")) or clean(raw.get("DJZT"))
        legacy_deleted_flag = clean(candidate.get("legacy_deleted")) or clean(raw.get("DEL"))

        row_blockers = []
        if not legacy_contract_id:
            row_blockers.append("missing_legacy_contract_id")
        if legacy_contract_id not in raw_contracts:
            row_blockers.append("missing_raw_contract_row")
        if not legacy_project_id or not project_id:
            row_blockers.append("missing_project_anchor")
        if not partner_id:
            row_blockers.append("missing_partner_anchor")
        if not subject:
            row_blockers.append("missing_subject")
        if contract_type not in {"out", "in"}:
            row_blockers.append("invalid_contract_type")
        if legacy_deleted_flag == "1":
            row_blockers.append("deleted_flag")

        for blocker in row_blockers:
            blockers[blocker] += 1
        type_counts[contract_type or "blank"] += 1
        status_counts[legacy_status or "blank"] += 1
        project_counts[project_id or "blank"] += 1
        partner_counts[partner_id or "blank"] += 1

        rows.append(
            {
                "legacy_contract_id": legacy_contract_id,
                "legacy_project_id": legacy_project_id,
                "project_id": project_id,
                "project_name": clean(candidate.get("project_name")),
                "partner_id": partner_id,
                "partner_name": clean(candidate.get("partner_name")),
                "subject": subject,
                "type": contract_type,
                "legacy_contract_no": clean(candidate.get("contract_no")) or clean(raw.get("HTBH")),
                "legacy_document_no": clean(raw.get("DJBH")),
                "legacy_external_contract_no": clean(raw.get("f_WBHTBH")) or clean(raw.get("WBHTBH")) or clean(raw.get("PID")),
                "legacy_status": legacy_status,
                "legacy_deleted_flag": legacy_deleted_flag,
                "legacy_counterparty_text": clean(candidate.get("counterparty_text")),
                "tax_id_policy": "defer_to_separate_readonly_precheck",
                "name_policy": "use_model_sequence_only_after_write_authorization",
                "state_policy": "create_as_draft_do_not_replay_legacy_workflow",
                "dry_run_status": "READY_FOR_READONLY_PRECHECK" if not row_blockers else "BLOCKED",
                "dry_run_blockers": "|".join(row_blockers),
            }
        )

    fieldnames = [
        "legacy_contract_id",
        "legacy_project_id",
        "project_id",
        "project_name",
        "partner_id",
        "partner_name",
        "subject",
        "type",
        "legacy_contract_no",
        "legacy_document_no",
        "legacy_external_contract_no",
        "legacy_status",
        "legacy_deleted_flag",
        "legacy_counterparty_text",
        "tax_id_policy",
        "name_policy",
        "state_policy",
        "dry_run_status",
        "dry_run_blockers",
    ]
    ready_rows = [row for row in rows if row["dry_run_status"] == "READY_FOR_READONLY_PRECHECK"]
    write_csv(OUTPUT_ROWS_CSV, fieldnames, rows)
    write_csv(OUTPUT_SLICE_CSV, fieldnames, ready_rows[:SLICE_LIMIT])

    payload = {
        "status": "PASS" if len(ready_rows) == len(rows) else "PASS_WITH_BLOCKERS",
        "mode": "contract_header_bounded_no_db_dry_run",
        "database": "no_db_access",
        "db_writes": 0,
        "upstream_readiness": str(READINESS_JSON),
        "upstream_safe_candidate_rows": readiness.get("safe_candidate_rows"),
        "input_candidate_rows": len(candidates),
        "dry_run_rows": len(rows),
        "ready_for_readonly_precheck_rows": len(ready_rows),
        "blocked_rows": len(rows) - len(ready_rows),
        "slice_limit": SLICE_LIMIT,
        "slice_rows": min(len(ready_rows), SLICE_LIMIT),
        "type_counts": dict(sorted(type_counts.items())),
        "legacy_status_counts": dict(sorted(status_counts.items())),
        "distinct_project_ids": len(project_counts),
        "distinct_partner_ids": len(partner_counts),
        "blocker_counts": dict(sorted(blockers.items())),
        "dry_run_rows_csv": str(OUTPUT_ROWS_CSV),
        "dry_run_slice_csv": str(OUTPUT_SLICE_CSV),
        "write_authorization": "not_granted",
        "contract_write_decision": "NO-GO until separate readonly DB precheck and explicit write authorization",
        "next_step": "open readonly DB precheck for the 200-row dry-run slice",
    }
    write_json(OUTPUT_JSON, payload)
    print(
        "CONTRACT_HEADER_BOUNDED_DRY_RUN="
        + json.dumps(
            {
                "status": payload["status"],
                "dry_run_rows": payload["dry_run_rows"],
                "ready_for_readonly_precheck_rows": payload["ready_for_readonly_precheck_rows"],
                "blocked_rows": payload["blocked_rows"],
                "slice_rows": payload["slice_rows"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


main()
