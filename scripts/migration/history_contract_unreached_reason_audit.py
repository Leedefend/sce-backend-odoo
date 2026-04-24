#!/usr/bin/env python3
"""Classify why the 91 unreached contract headers never entered bounded replay payloads."""

from __future__ import annotations

import csv
import io
import json
import os
import re
import subprocess
from collections import Counter
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
UNREACHED_CSV = REPO_ROOT / "artifacts/migration/ur_a_contract_unreached_asset_rows_v1.csv"
RAW_CONTRACT_CSV = REPO_ROOT / "tmp/raw/contract/contract.csv"
OUTPUT_JSON = REPO_ROOT / "artifacts/migration/history_contract_unreached_reason_audit_v1.json"
OUTPUT_CSV = REPO_ROOT / "artifacts/migration/history_contract_unreached_reason_rows_v1.csv"

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
    text = re.sub(r"[（）()·,，.。/、\s\\-]", "", clean(value))
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
    with path.open("w", encoding="utf-8", newline="") as handle:
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


def partner_indexes():
    partners = psql_copy(
        """
        select
          id::text as id,
          coalesce(name, '')::text as name,
          coalesce(legacy_partner_source, '')::text as legacy_partner_source,
          coalesce(legacy_partner_id, '')::text as legacy_partner_id
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


def project_index():
    projects = psql_copy(
        """
        select
          id::text as id,
          coalesce(name::text, '') as name,
          coalesce(legacy_project_id, '')::text as legacy_project_id
        from project_project
        where legacy_project_id is not null and legacy_project_id != ''
        """
    )
    by_legacy: dict[str, list[dict[str, str]]] = {}
    for project in projects:
        by_legacy.setdefault(clean(project.get("legacy_project_id")), []).append(project)
    return by_legacy


def existing_contract_ids() -> set[str]:
    rows = psql_copy(
        """
        select coalesce(legacy_contract_id, '')::text as legacy_contract_id
        from construction_contract
        where legacy_contract_id is not null and legacy_contract_id != ''
        """
    )
    return {clean(row.get("legacy_contract_id")) for row in rows if clean(row.get("legacy_contract_id"))}


def main() -> int:
    unreached = read_csv(UNREACHED_CSV)
    raw_contracts = {clean(row.get("Id")): row for row in read_csv(RAW_CONTRACT_CSV)}
    exact_partner, normalized_partner = partner_indexes()
    projects_by_legacy = project_index()
    existing_contract = existing_contract_ids()

    blocker_counts = Counter()
    blocker_combo_counts = Counter()
    partner_match_counts = Counter()
    project_match_counts = Counter()
    rows_out: list[dict[str, object]] = []

    for row in unreached:
        legacy_contract_id = clean(row.get("legacy_contract_id"))
        raw = raw_contracts.get(legacy_contract_id, {})
        legacy_project_id = clean(raw.get("XMID"))
        subject = clean(raw.get("HTBT")) or clean(raw.get("DJBH")) or clean(raw.get("HTBH"))
        deleted = clean(raw.get("DEL")) == "1"
        direction, counterparty = infer_direction(raw)

        exact_matches = exact_partner.get(counterparty, []) if counterparty else []
        normalized_matches = normalized_partner.get(norm_name(counterparty), []) if counterparty else []
        partner_matches = exact_matches or normalized_matches
        partner_match_type = "exact" if exact_matches else "normalized" if normalized_matches else "unresolved"
        if len(partner_matches) > 1:
            partner_match_type = "ambiguous_" + partner_match_type
        partner_match_counts[partner_match_type] += 1

        project_matches = projects_by_legacy.get(legacy_project_id, [])
        project_match_type = "exact" if len(project_matches) == 1 else "missing" if not project_matches else "ambiguous"
        project_match_counts[project_match_type] += 1

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
        if legacy_contract_id in existing_contract:
            row_blockers.append("legacy_contract_already_exists")
        for blocker in row_blockers:
            blocker_counts[blocker] += 1
        blocker_combo_counts["|".join(row_blockers) if row_blockers else "READY_FOR_RECOVERY"] += 1

        rows_out.append(
            {
                "legacy_contract_id": legacy_contract_id,
                "counterparty_text": counterparty,
                "direction": direction,
                "legacy_project_id": legacy_project_id,
                "partner_match_type": partner_match_type,
                "project_match_type": project_match_type,
                "blockers": "|".join(row_blockers),
                "subject": subject,
            }
        )

    write_csv(
        OUTPUT_CSV,
        [
            "legacy_contract_id",
            "counterparty_text",
            "direction",
            "legacy_project_id",
            "partner_match_type",
            "project_match_type",
            "blockers",
            "subject",
        ],
        rows_out,
    )

    payload = {
        "status": "PASS",
        "mode": "history_contract_unreached_reason_audit",
        "database": DB_NAME,
        "unreached_rows": len(rows_out),
        "ready_rows": sum(1 for row in rows_out if not row["blockers"]),
        "blocked_rows": sum(1 for row in rows_out if row["blockers"]),
        "blocker_counts": dict(sorted(blocker_counts.items())),
        "blocker_combo_counts": dict(sorted(blocker_combo_counts.items())),
        "partner_match_counts": dict(sorted(partner_match_counts.items())),
        "project_match_counts": dict(sorted(project_match_counts.items())),
        "rows_artifact": str(OUTPUT_CSV.relative_to(REPO_ROOT)),
        "sample_rows": rows_out[:20],
    }
    write_json(OUTPUT_JSON, payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
