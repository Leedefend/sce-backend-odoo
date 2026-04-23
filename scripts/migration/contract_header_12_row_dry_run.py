"""Build a no-DB dry-run payload for the 12 safe contract header candidates.

Run from the repository root:

    python3 scripts/migration/contract_header_12_row_dry_run.py

The script reads only local CSV/JSON artifacts and does not access Odoo.
"""

from __future__ import annotations

import csv
import json
import re
from collections import Counter
from pathlib import Path


RAW_CONTRACT_CSV = Path("tmp/raw/contract/contract.csv")
SAFE_CANDIDATE_CSV = Path("artifacts/migration/contract_anchor_safe_candidates_v1.csv")
READINESS_JSON = Path("artifacts/migration/contract_anchor_readiness_recheck_v1.json")
PROJECT_SAMPLE_30_CSV = Path("data/migration_samples/project_sample_v1.csv")
PROJECT_SAMPLE_30_POST_WRITE_CSV = Path("artifacts/migration/project_create_only_post_write_snapshot_v1.csv")
PROJECT_SAMPLE_100_CSV = Path("artifacts/migration/project_create_only_expand_post_write_snapshot_v1.csv")
OUTPUT_ROWS_CSV = Path("artifacts/migration/contract_header_12_row_dry_run_rows_v1.csv")
OUTPUT_JSON = Path("artifacts/migration/contract_header_12_row_dry_run_result_v1.json")


def clean_text(value):
    text = "" if value is None else str(value)
    text = text.replace("\u3000", " ").strip()
    return re.sub(r"\s+", " ", text)


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


def project_index():
    index = {}
    duplicate_legacy_ids = set()
    for path in (PROJECT_SAMPLE_30_POST_WRITE_CSV, PROJECT_SAMPLE_100_CSV, PROJECT_SAMPLE_30_CSV):
        if not path.exists():
            continue
        for row in read_csv(path):
            legacy_project_id = clean_text(row.get("legacy_project_id"))
            project_id = clean_text(row.get("id"))
            if not legacy_project_id or not project_id:
                continue
            item = {
                "project_id": project_id,
                "project_name": clean_text(row.get("name")),
                "project_source": str(path),
            }
            if legacy_project_id in index and index[legacy_project_id]["project_id"] != project_id:
                duplicate_legacy_ids.add(legacy_project_id)
            index.setdefault(legacy_project_id, item)
    return index, duplicate_legacy_ids


def main():
    readiness = json.loads(READINESS_JSON.read_text(encoding="utf-8"))
    candidates = read_csv(SAFE_CANDIDATE_CSV)
    raw_contracts = {clean_text(row.get("Id")): row for row in read_csv(RAW_CONTRACT_CSV)}
    projects, duplicate_project_legacy_ids = project_index()

    rows = []
    blockers = Counter()
    type_counts = Counter()
    status_counts = Counter()

    for candidate in candidates:
        legacy_contract_id = clean_text(candidate.get("legacy_contract_id"))
        legacy_project_id = clean_text(candidate.get("legacy_project_id"))
        raw = raw_contracts.get(legacy_contract_id, {})
        project = projects.get(legacy_project_id, {})

        subject = clean_text(candidate.get("subject"))
        contract_type = clean_text(candidate.get("direction"))
        project_id = clean_text(project.get("project_id"))
        partner_id = clean_text(candidate.get("partner_id"))
        legacy_document_no = clean_text(raw.get("DJBH"))
        legacy_contract_no = clean_text(candidate.get("contract_no")) or clean_text(raw.get("HTBH"))
        legacy_external_contract_no = clean_text(raw.get("f_WBHTBH")) or clean_text(raw.get("WBHTBH")) or clean_text(raw.get("PID"))
        legacy_status = clean_text(candidate.get("legacy_status")) or clean_text(raw.get("DJZT"))
        legacy_deleted_flag = clean_text(candidate.get("legacy_deleted")) or clean_text(raw.get("DEL"))
        counterparty_text = clean_text(candidate.get("counterparty_text"))

        row_blockers = []
        if not legacy_contract_id:
            row_blockers.append("missing_legacy_contract_id")
        if not subject:
            row_blockers.append("missing_subject")
        if contract_type not in {"out", "in"}:
            row_blockers.append("invalid_contract_type")
        if not project_id:
            row_blockers.append("project_id_not_resolved")
        if legacy_project_id in duplicate_project_legacy_ids:
            row_blockers.append("duplicate_project_anchor")
        if not partner_id:
            row_blockers.append("missing_partner_id")
        if legacy_deleted_flag == "1":
            row_blockers.append("deleted_flag")

        for blocker in row_blockers:
            blockers[blocker] += 1
        type_counts[contract_type or "blank"] += 1
        status_counts[legacy_status or "blank"] += 1

        rows.append(
            {
                "legacy_contract_id": legacy_contract_id,
                "legacy_project_id": legacy_project_id,
                "project_id": project_id,
                "project_name": clean_text(project.get("project_name")),
                "partner_id": partner_id,
                "subject": subject,
                "type": contract_type,
                "legacy_contract_no": legacy_contract_no,
                "legacy_document_no": legacy_document_no,
                "legacy_external_contract_no": legacy_external_contract_no,
                "legacy_status": legacy_status,
                "legacy_deleted_flag": legacy_deleted_flag,
                "legacy_counterparty_text": counterparty_text,
                "tax_id_policy": "use_model_default_tax_for_type_after_db_precheck",
                "name_policy": "use_model_sequence_on_create_after_write_authorization",
                "state_policy": "create_as_draft_do_not_replay_legacy_workflow",
                "dry_run_status": "READY_FOR_DB_PRECHECK" if not row_blockers else "BLOCKED",
                "dry_run_blockers": "|".join(row_blockers),
            }
        )

    fieldnames = [
        "legacy_contract_id",
        "legacy_project_id",
        "project_id",
        "project_name",
        "partner_id",
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
    write_csv(OUTPUT_ROWS_CSV, fieldnames, rows)

    ready_rows = sum(1 for row in rows if row["dry_run_status"] == "READY_FOR_DB_PRECHECK")
    payload = {
        "status": "PASS" if ready_rows == len(rows) and len(rows) == 12 else "PASS_WITH_BLOCKERS",
        "mode": "contract_header_12_row_no_db_dry_run",
        "database": "no_db_access",
        "upstream_readiness": str(READINESS_JSON),
        "upstream_safe_candidate_rows": readiness.get("safe_candidate_rows"),
        "input_candidate_rows": len(candidates),
        "dry_run_rows": len(rows),
        "ready_for_db_precheck_rows": ready_rows,
        "blocked_rows": len(rows) - ready_rows,
        "type_counts": dict(sorted(type_counts.items())),
        "legacy_status_counts": dict(sorted(status_counts.items())),
        "blocker_counts": dict(sorted(blockers.items())),
        "dry_run_rows_csv": str(OUTPUT_ROWS_CSV),
        "write_authorization": "not_granted",
        "contract_write_decision": "NO-GO until explicit contract write authorization plus DB precheck",
        "db_precheck_required": [
            "resolve default tax_id for each contract type",
            "confirm construction.contract sequence availability",
            "confirm legacy_contract_id uniqueness in target DB",
            "confirm project_id and partner_id still exist in target DB",
        ],
        "next_step": "open readonly DB precheck for the 12 dry-run rows or request explicit contract write authorization after precheck",
    }
    write_json(OUTPUT_JSON, payload)
    print(
        "CONTRACT_HEADER_12_DRY_RUN="
        + json.dumps(
            {
                "status": payload["status"],
                "dry_run_rows": payload["dry_run_rows"],
                "ready_for_db_precheck_rows": payload["ready_for_db_precheck_rows"],
                "blocked_rows": payload["blocked_rows"],
                "contract_write_decision": payload["contract_write_decision"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


main()
