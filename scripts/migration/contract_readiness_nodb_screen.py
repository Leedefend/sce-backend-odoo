#!/usr/bin/env python3
"""Readonly contract readiness screen against current DB anchors.

Run from the repository root:

    DB_NAME=sc_demo python3 scripts/migration/contract_readiness_nodb_screen.py

The script reads source CSV data from the host workspace and queries PostgreSQL
through psql. It issues SELECT/COPY only and writes local artifact files.
"""

from __future__ import annotations

import csv
import io
import json
import os
import re
import subprocess
from collections import Counter
from pathlib import Path


REPO_ROOT = Path.cwd()
CONTRACT_CSV = REPO_ROOT / "tmp/raw/contract/contract.csv"
OUTPUT_JSON = REPO_ROOT / "artifacts/migration/contract_readiness_nodb_screen_result_v1.json"
OUTPUT_CSV = REPO_ROOT / "artifacts/migration/contract_readiness_nodb_screen_safe_candidates_v1.csv"

DB_CONTAINER = os.environ.get("DB_CONTAINER", "sc-backend-odoo-dev-db-1")
DB_USER = os.environ.get("DB_USER", "odoo")
DB_NAME = os.environ.get("DB_NAME", "sc_demo")

OWN_COMPANY_NAMES = {"四川保盛建设集团有限公司", "My Company"}
ORG_SUFFIXES = ("有限责任公司", "股份有限公司", "集团有限公司", "有限公司", "公司")


def clean(value: object) -> str:
    text = "" if value is None else str(value)
    text = text.replace("\u3000", " ").strip()
    return re.sub(r"\s+", " ", text)


def norm_name(value: object) -> str:
    text = clean(value)
    text = re.sub(r"[（）()·,，.。/、\s\\-]", "", text)
    for suffix in ORG_SUFFIXES:
        if text.endswith(suffix):
            text = text[: -len(suffix)]
            break
    return text


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


def psql_copy(sql: str) -> list[dict[str, str]]:
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


def infer_direction(row: dict[str, str]) -> tuple[str, str]:
    fbf = clean(row.get("FBF"))
    cbf = clean(row.get("CBF"))
    if cbf in OWN_COMPANY_NAMES and fbf not in OWN_COMPANY_NAMES:
        return "out", fbf
    if fbf in OWN_COMPANY_NAMES and cbf not in OWN_COMPANY_NAMES:
        return "in", cbf
    return "defer", ""


def partner_indexes() -> tuple[
    list[dict[str, str]],
    dict[str, list[dict[str, str]]],
    dict[str, list[dict[str, str]]],
    Counter[tuple[str, str]],
]:
    partners = psql_copy(
        """
        select
          id::text as id,
          coalesce(name, '')::text as name,
          coalesce(legacy_partner_source, '')::text as legacy_partner_source,
          coalesce(legacy_partner_id, '')::text as legacy_partner_id,
          coalesce(active, false)::text as active
        from res_partner
        """
    )
    exact: dict[str, list[dict[str, str]]] = {}
    normalized: dict[str, list[dict[str, str]]] = {}
    legacy_seen: Counter[tuple[str, str]] = Counter()
    for partner in partners:
        source = clean(partner.get("legacy_partner_source"))
        legacy_id = clean(partner.get("legacy_partner_id"))
        if source or legacy_id:
            legacy_seen[(source, legacy_id)] += 1
        name = clean(partner.get("name"))
        if not name:
            continue
        exact.setdefault(name, []).append(partner)
        normalized.setdefault(norm_name(name), []).append(partner)
    duplicate_legacy = Counter({key: count for key, count in legacy_seen.items() if count > 1})
    return partners, exact, normalized, duplicate_legacy


def project_index() -> tuple[dict[str, list[dict[str, str]]], Counter[str]]:
    projects = psql_copy(
        """
        select
          id::text as id,
          coalesce(name::text, '') as name,
          coalesce(legacy_project_id, '')::text as legacy_project_id,
          coalesce(active, false)::text as active
        from project_project
        where legacy_project_id is not null and legacy_project_id != ''
        """
    )
    by_legacy: dict[str, list[dict[str, str]]] = {}
    for project in projects:
        by_legacy.setdefault(clean(project.get("legacy_project_id")), []).append(project)
    duplicates = Counter({key: len(rows) for key, rows in by_legacy.items() if len(rows) > 1})
    return by_legacy, duplicates


def existing_contract_legacy_ids() -> set[str]:
    contracts = psql_copy(
        """
        select coalesce(legacy_contract_id, '')::text as legacy_contract_id
        from construction_contract
        where legacy_contract_id is not null and legacy_contract_id != ''
        """
    )
    return {clean(row.get("legacy_contract_id")) for row in contracts if clean(row.get("legacy_contract_id"))}


def main() -> int:
    if not CONTRACT_CSV.exists():
        raise RuntimeError({"missing_contract_csv": str(CONTRACT_CSV)})

    rows = read_csv(CONTRACT_CSV)
    partners, exact_partner, normalized_partner, duplicate_partner_legacy = partner_indexes()
    project_by_legacy, duplicate_projects = project_index()
    existing_contract_ids = existing_contract_legacy_ids()

    blockers = Counter()
    direction_counts = Counter()
    partner_match_counts = Counter()
    project_match_counts = Counter()
    deleted_counts = Counter()
    existing_counts = Counter()
    counterparty_counts = Counter()
    safe_rows: list[dict[str, object]] = []

    for row in rows:
        legacy_contract_id = clean(row.get("Id"))
        legacy_project_id = clean(row.get("XMID"))
        subject = clean(row.get("HTBT")) or clean(row.get("DJBH")) or clean(row.get("HTBH"))
        deleted = clean(row.get("DEL")) == "1"
        direction, counterparty = infer_direction(row)
        direction_counts[direction] += 1
        deleted_counts["deleted" if deleted else "active_or_blank"] += 1
        if counterparty:
            counterparty_counts[counterparty] += 1

        exact_matches = exact_partner.get(counterparty, []) if counterparty else []
        normalized_matches = normalized_partner.get(norm_name(counterparty), []) if counterparty else []
        partner_matches = exact_matches or normalized_matches
        partner_match_type = "exact" if exact_matches else "normalized" if normalized_matches else "unresolved"
        if len(partner_matches) > 1:
            partner_match_type = "ambiguous_" + partner_match_type
        partner_match_counts[partner_match_type] += 1

        project_matches = project_by_legacy.get(legacy_project_id, [])
        project_match_type = "exact" if len(project_matches) == 1 else "missing" if not project_matches else "ambiguous"
        project_match_counts[project_match_type] += 1

        existing_contract = legacy_contract_id in existing_contract_ids
        existing_counts["existing_contract" if existing_contract else "not_existing_contract"] += 1

        row_blockers = []
        if deleted:
            row_blockers.append("deleted_flag")
        if direction not in {"out", "in"}:
            row_blockers.append("direction_defer")
        if len(partner_matches) != 1:
            row_blockers.append("partner_unresolved" if not partner_matches else "partner_ambiguous")
        if len(project_matches) != 1:
            row_blockers.append("project_unresolved" if not project_matches else "project_ambiguous")
        if not subject:
            row_blockers.append("missing_subject")
        if existing_contract:
            row_blockers.append("legacy_contract_already_exists")
        for blocker in row_blockers:
            blockers[blocker] += 1

        if not row_blockers:
            partner = partner_matches[0]
            project = project_matches[0]
            safe_rows.append(
                {
                    "legacy_contract_id": legacy_contract_id,
                    "legacy_project_id": legacy_project_id,
                    "project_id": project["id"],
                    "project_name": project["name"],
                    "subject": subject,
                    "contract_no": clean(row.get("HTBH")),
                    "direction": direction,
                    "counterparty_text": counterparty,
                    "partner_id": partner["id"],
                    "partner_name": partner["name"],
                    "partner_match_type": partner_match_type,
                    "legacy_status": clean(row.get("DJZT")),
                    "legacy_deleted": clean(row.get("DEL")),
                }
            )

    write_csv(
        OUTPUT_CSV,
        [
            "legacy_contract_id",
            "legacy_project_id",
            "project_id",
            "project_name",
            "subject",
            "contract_no",
            "direction",
            "counterparty_text",
            "partner_id",
            "partner_name",
            "partner_match_type",
            "legacy_status",
            "legacy_deleted",
        ],
        safe_rows,
    )

    payload = {
        "status": "PASS",
        "mode": "contract_readiness_nodb_screen",
        "database": DB_NAME,
        "db_container": DB_CONTAINER,
        "db_writes": 0,
        "source_file": str(CONTRACT_CSV),
        "contract_rows": len(rows),
        "partner_baseline_count": len(partners),
        "project_legacy_anchor_count": len(project_by_legacy),
        "existing_contract_legacy_id_count": len(existing_contract_ids),
        "direction_counts": dict(sorted(direction_counts.items())),
        "partner_match_counts": dict(sorted(partner_match_counts.items())),
        "project_match_counts": dict(sorted(project_match_counts.items())),
        "deleted_counts": dict(sorted(deleted_counts.items())),
        "existing_contract_counts": dict(sorted(existing_counts.items())),
        "safe_candidate_rows": len(safe_rows),
        "safe_candidate_csv": str(OUTPUT_CSV),
        "blocker_counts": dict(sorted(blockers.items())),
        "top_counterparty_texts": [
            {"text": text, "rows": count}
            for text, count in counterparty_counts.most_common(30)
        ],
        "integrity_warnings": {
            "duplicate_partner_legacy_keys": len(duplicate_partner_legacy),
            "duplicate_project_legacy_ids": len(duplicate_projects),
        },
        "decision": "candidate_dry_run_allowed" if safe_rows else "NO_GO_FOR_CONTRACT_WRITE",
        "write_authorization": "not_granted",
        "next_step": "open bounded contract header dry-run" if safe_rows else "continue reference anchor preparation before contract write",
    }
    write_json(OUTPUT_JSON, payload)
    print(
        "CONTRACT_READINESS_NODB_SCREEN="
        + json.dumps(
            {
                "status": payload["status"],
                "contract_rows": payload["contract_rows"],
                "partner_baseline_count": payload["partner_baseline_count"],
                "project_legacy_anchor_count": payload["project_legacy_anchor_count"],
                "safe_candidate_rows": payload["safe_candidate_rows"],
                "decision": payload["decision"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
