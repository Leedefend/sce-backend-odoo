#!/usr/bin/env python3
"""Readonly full-source contract coverage screen after header migration closure.

Run from the repository root:

    DB_NAME=sc_demo python3 scripts/migration/contract_source_coverage_nodb_screen.py

The script reads legacy contract source rows, the approved contract header safe
candidate CSV, and current target contract legacy IDs. It performs SELECT/COPY
only against PostgreSQL and writes local evidence artifacts.
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
SAFE_CANDIDATE_CSV = REPO_ROOT / "artifacts/migration/contract_readiness_nodb_screen_safe_candidates_v1.csv"
OUTPUT_JSON = REPO_ROOT / "artifacts/migration/contract_source_coverage_nodb_screen_result_v1.json"
OUTPUT_CSV = REPO_ROOT / "artifacts/migration/contract_source_coverage_nodb_screen_rows_v1.csv"
OUTPUT_REPORT = REPO_ROOT / "docs/migration_alignment/contract_source_coverage_nodb_screen_report_v1.md"

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


def partner_indexes() -> tuple[dict[str, list[dict[str, str]]], dict[str, list[dict[str, str]]]]:
    partners = psql_copy(
        """
        select
          id::text as id,
          coalesce(name, '')::text as name
        from res_partner
        """
    )
    exact: dict[str, list[dict[str, str]]] = {}
    normalized: dict[str, list[dict[str, str]]] = {}
    for partner in partners:
        name = clean(partner.get("name"))
        if not name:
            continue
        exact.setdefault(name, []).append(partner)
        normalized.setdefault(norm_name(name), []).append(partner)
    return exact, normalized


def project_index() -> dict[str, list[dict[str, str]]]:
    projects = psql_copy(
        """
        select
          id::text as id,
          coalesce(legacy_project_id, '')::text as legacy_project_id
        from project_project
        where legacy_project_id is not null and legacy_project_id != ''
        """
    )
    by_legacy: dict[str, list[dict[str, str]]] = {}
    for project in projects:
        by_legacy.setdefault(clean(project.get("legacy_project_id")), []).append(project)
    return by_legacy


def target_contracts() -> dict[str, dict[str, str]]:
    rows = psql_copy(
        """
        select
          id::text as id,
          coalesce(legacy_contract_id, '')::text as legacy_contract_id,
          coalesce(name, '')::text as name
        from construction_contract
        where legacy_contract_id is not null and legacy_contract_id != ''
        """
    )
    return {clean(row.get("legacy_contract_id")): row for row in rows if clean(row.get("legacy_contract_id"))}


def row_blockers(
    row: dict[str, str],
    exact_partner: dict[str, list[dict[str, str]]],
    normalized_partner: dict[str, list[dict[str, str]]],
    project_by_legacy: dict[str, list[dict[str, str]]],
) -> list[str]:
    blockers: list[str] = []
    legacy_project_id = clean(row.get("XMID"))
    subject = clean(row.get("HTBT")) or clean(row.get("DJBH")) or clean(row.get("HTBH"))
    direction, counterparty = infer_direction(row)
    exact_matches = exact_partner.get(counterparty, []) if counterparty else []
    normalized_matches = normalized_partner.get(norm_name(counterparty), []) if counterparty else []
    partner_matches = exact_matches or normalized_matches
    project_matches = project_by_legacy.get(legacy_project_id, [])
    if clean(row.get("DEL")) == "1":
        blockers.append("deleted_flag")
    if direction not in {"out", "in"}:
        blockers.append("direction_defer")
    if len(partner_matches) != 1:
        blockers.append("partner_unresolved" if not partner_matches else "partner_ambiguous")
    if len(project_matches) != 1:
        blockers.append("project_unresolved" if not project_matches else "project_ambiguous")
    if not subject:
        blockers.append("missing_subject")
    return blockers


def route_for_blockers(blockers: list[str]) -> str:
    if "deleted_flag" in blockers:
        return "discard_deleted_source"
    if "project_unresolved" in blockers or "project_ambiguous" in blockers:
        return "project_anchor_blocked"
    if "partner_unresolved" in blockers or "partner_ambiguous" in blockers:
        return "partner_anchor_blocked"
    if "direction_defer" in blockers:
        return "direction_policy_blocked"
    if blockers:
        return "other_blocked"
    return "unexpected_ready_missing_target"


def write_report(payload: dict[str, object]) -> None:
    blocker_counts = payload["blocker_counts"]
    route_counts = payload["route_counts"]
    text = f"""# Contract Source Coverage No-DB Screen v1

Status: {payload["status"]}

Task: `ITER-2026-04-15-CONTRACT-SOURCE-COVERAGE-NODB-SCREEN`

## Scope

Reconcile the full legacy contract source population after the 1332-row
contract header migration closure. This batch performs no database writes.

## Result

- source rows: `{payload["source_rows"]}`
- safe candidate rows from readiness screen: `{payload["safe_candidate_rows"]}`
- target contract legacy ids: `{payload["target_contract_legacy_ids"]}`
- header-lane migrated rows: `{payload["header_lane_migrated_rows"]}`
- pre-existing target rows: `{payload["pre_existing_target_rows"]}`
- remaining blocked rows: `{payload["remaining_blocked_rows"]}`
- unexpected safe candidates missing target: `{payload["safe_candidate_missing_target_rows"]}`
- DB writes: `0`

## Route Counts

```json
{json.dumps(route_counts, ensure_ascii=False, indent=2)}
```

## Blocker Counts

```json
{json.dumps(blocker_counts, ensure_ascii=False, indent=2)}
```

## Decision

`{payload["decision"]}`

## Next

{payload["next_step"]}
"""
    OUTPUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_REPORT.write_text(text, encoding="utf-8")


def main() -> int:
    if not CONTRACT_CSV.exists():
        raise RuntimeError({"missing_contract_csv": str(CONTRACT_CSV)})
    if not SAFE_CANDIDATE_CSV.exists():
        raise RuntimeError({"missing_safe_candidate_csv": str(SAFE_CANDIDATE_CSV)})

    source_rows = read_csv(CONTRACT_CSV)
    safe_ids = {clean(row.get("legacy_contract_id")) for row in read_csv(SAFE_CANDIDATE_CSV)}
    safe_ids.discard("")
    exact_partner, normalized_partner = partner_indexes()
    project_by_legacy = project_index()
    target_by_legacy = target_contracts()

    rows: list[dict[str, object]] = []
    route_counts: Counter[str] = Counter()
    blocker_counts: Counter[str] = Counter()
    safe_missing: list[str] = []

    for row in source_rows:
        legacy_contract_id = clean(row.get("Id"))
        target = target_by_legacy.get(legacy_contract_id)
        in_safe_set = legacy_contract_id in safe_ids
        blockers = [] if target else row_blockers(row, exact_partner, normalized_partner, project_by_legacy)

        if target and in_safe_set:
            route = "header_lane_migrated"
        elif target:
            route = "pre_existing_target"
        elif in_safe_set:
            route = "safe_candidate_missing_target"
            safe_missing.append(legacy_contract_id)
        else:
            route = route_for_blockers(blockers)

        route_counts[route] += 1
        for blocker in blockers:
            blocker_counts[blocker] += 1

        rows.append(
            {
                "legacy_contract_id": legacy_contract_id,
                "legacy_project_id": clean(row.get("XMID")),
                "subject": clean(row.get("HTBT")) or clean(row.get("DJBH")) or clean(row.get("HTBH")),
                "in_safe_candidate_set": "1" if in_safe_set else "0",
                "target_contract_id": target["id"] if target else "",
                "coverage_route": route,
                "blockers": "|".join(blockers),
            }
        )

    status = "PASS" if len(source_rows) == 1694 and not safe_missing else "FAIL"
    remaining_blocked = len(source_rows) - route_counts["header_lane_migrated"] - route_counts["pre_existing_target"]
    payload = {
        "status": status,
        "mode": "contract_source_coverage_nodb_screen",
        "database": DB_NAME,
        "db_container": DB_CONTAINER,
        "db_writes": 0,
        "source_file": str(CONTRACT_CSV),
        "source_rows": len(source_rows),
        "safe_candidate_rows": len(safe_ids),
        "target_contract_legacy_ids": len(target_by_legacy),
        "header_lane_migrated_rows": route_counts["header_lane_migrated"],
        "pre_existing_target_rows": route_counts["pre_existing_target"],
        "remaining_blocked_rows": remaining_blocked,
        "safe_candidate_missing_target_rows": len(safe_missing),
        "route_counts": dict(sorted(route_counts.items())),
        "blocker_counts": dict(sorted(blocker_counts.items())),
        "row_artifact": str(OUTPUT_CSV),
        "decision": "remaining_contract_source_screened" if status == "PASS" else "STOP_REVIEW_REQUIRED",
        "write_authorization": "not_granted",
        "next_step": "open no-DB contract remaining-blocker policy screen; do not open payment, settlement, accounting, or line writes",
        "errors": [] if status == "PASS" else [{"safe_candidate_missing_target_ids": safe_missing[:20]}],
    }

    write_csv(
        OUTPUT_CSV,
        [
            "legacy_contract_id",
            "legacy_project_id",
            "subject",
            "in_safe_candidate_set",
            "target_contract_id",
            "coverage_route",
            "blockers",
        ],
        rows,
    )
    write_json(OUTPUT_JSON, payload)
    write_report(payload)

    print(
        "CONTRACT_SOURCE_COVERAGE_NODB_SCREEN="
        + json.dumps(
            {
                "status": status,
                "source_rows": payload["source_rows"],
                "header_lane_migrated_rows": payload["header_lane_migrated_rows"],
                "pre_existing_target_rows": payload["pre_existing_target_rows"],
                "remaining_blocked_rows": payload["remaining_blocked_rows"],
                "db_writes": 0,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
