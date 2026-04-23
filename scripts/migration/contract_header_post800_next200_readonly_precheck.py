#!/usr/bin/env python3
"""Readonly DB precheck for the post800 next 200-row contract header slice."""

from __future__ import annotations

import csv
import io
import json
import os
import subprocess
from collections import Counter
from pathlib import Path


REPO_ROOT = Path.cwd()
INPUT_CSV = REPO_ROOT / "artifacts/migration/contract_header_next_slice200_after_800_v1.csv"
OUTPUT_JSON = REPO_ROOT / "artifacts/migration/contract_header_post800_next200_readonly_precheck_result_v1.json"

DB_CONTAINER = os.environ.get("DB_CONTAINER", "sc-backend-odoo-dev-db-1")
DB_USER = os.environ.get("DB_USER", "odoo")
DB_NAME = os.environ.get("DB_NAME", "sc_demo")
EXPECTED_ROWS = 200


def clean(value):
    return "" if value is None else str(value).strip()


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def psql_copy(sql):
    command = [
        "docker",
        "exec",
        "-i",
        DB_CONTAINER,
        "psql",
        "-U",
        DB_USER,
        "-d",
        DB_NAME,
        "-c",
        f"\\copy ({sql}) TO STDOUT WITH CSV HEADER",
    ]
    proc = subprocess.run(command, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return [dict(row) for row in csv.DictReader(io.StringIO(proc.stdout))]


def sql_list(values):
    cleaned = sorted({clean(value) for value in values if clean(value)})
    if not cleaned:
        return "''"
    return ",".join("'" + value.replace("'", "''") + "'" for value in cleaned)


def main():
    rows = read_csv(INPUT_CSV)
    legacy_contract_ids = [row.get("legacy_contract_id") for row in rows]
    project_ids = [row.get("project_id") for row in rows]
    partner_ids = [row.get("partner_id") for row in rows]

    existing_contract_rows = psql_copy(
        f"""
        select legacy_contract_id::text as legacy_contract_id, count(*)::text as count
        from construction_contract
        where legacy_contract_id in ({sql_list(legacy_contract_ids)})
        group by legacy_contract_id
        """
    )
    existing_contract_counts = {clean(row["legacy_contract_id"]): int(row["count"]) for row in existing_contract_rows}

    project_rows = psql_copy(
        f"""
        select id::text as id, count(*)::text as count
        from project_project
        where id::text in ({sql_list(project_ids)})
        group by id
        """
    )
    project_counts = {clean(row["id"]): int(row["count"]) for row in project_rows}

    partner_rows = psql_copy(
        f"""
        select id::text as id, count(*)::text as count
        from res_partner
        where id::text in ({sql_list(partner_ids)})
        group by id
        """
    )
    partner_counts = {clean(row["id"]): int(row["count"]) for row in partner_rows}

    blockers = Counter()
    row_results = []
    input_legacy_counter = Counter(clean(row.get("legacy_contract_id")) for row in rows if clean(row.get("legacy_contract_id")))
    duplicate_input_legacy_ids = sorted([key for key, count in input_legacy_counter.items() if count > 1])

    for row in rows:
        legacy_contract_id = clean(row.get("legacy_contract_id"))
        project_id = clean(row.get("project_id"))
        partner_id = clean(row.get("partner_id"))
        row_blockers = []
        if existing_contract_counts.get(legacy_contract_id, 0):
            row_blockers.append("legacy_contract_already_exists")
        if project_counts.get(project_id, 0) != 1:
            row_blockers.append("project_missing_or_duplicate")
        if partner_counts.get(partner_id, 0) != 1:
            row_blockers.append("partner_missing_or_duplicate")
        if input_legacy_counter.get(legacy_contract_id, 0) > 1:
            row_blockers.append("duplicate_input_legacy_contract_id")
        for blocker in row_blockers:
            blockers[blocker] += 1
        row_results.append(
            {
                "legacy_contract_id": legacy_contract_id,
                "project_id": project_id,
                "partner_id": partner_id,
                "status": "READY_FOR_WRITE_DESIGN" if not row_blockers else "BLOCKED",
                "blockers": row_blockers,
            }
        )

    ready_rows = sum(1 for row in row_results if row["status"] == "READY_FOR_WRITE_DESIGN")
    if len(rows) != EXPECTED_ROWS:
        blockers["unexpected_input_row_count"] += 1

    payload = {
        "status": "PASS" if ready_rows == len(row_results) and len(rows) == EXPECTED_ROWS else "PASS_WITH_BLOCKERS",
        "mode": "contract_header_post800_next200_readonly_precheck",
        "database": DB_NAME,
        "db_container": DB_CONTAINER,
        "db_writes": 0,
        "input": str(INPUT_CSV),
        "row_count": len(row_results),
        "ready_for_write_design_rows": ready_rows,
        "blocked_rows": len(row_results) - ready_rows,
        "existing_contract_rows": sum(existing_contract_counts.values()),
        "project_match_rows": sum(project_counts.values()),
        "partner_match_rows": sum(partner_counts.values()),
        "duplicate_input_legacy_ids": duplicate_input_legacy_ids[:30],
        "blocker_counts": dict(sorted(blockers.items())),
        "write_authorization": "not_granted",
        "contract_write_decision": "NO-GO until separate write design and explicit write authorization",
        "rows": row_results[:30],
        "next_step": "open no-DB write design for the next 200-row slice" if ready_rows == len(row_results) else "resolve precheck blockers before write design",
    }
    write_json(OUTPUT_JSON, payload)
    print(
        "CONTRACT_HEADER_POST800_NEXT200_READONLY_PRECHECK="
        + json.dumps(
            {
                "status": payload["status"],
                "row_count": payload["row_count"],
                "ready_for_write_design_rows": payload["ready_for_write_design_rows"],
                "blocked_rows": payload["blocked_rows"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


main()
