"""Readonly contract anchor readiness recheck.

Run from the repository root:

    python3 scripts/migration/contract_anchor_readiness_recheck.py

This script reads the locked partner rollback target list plus raw
contract/project sample files. It does not access Odoo or write any database.
"""

from __future__ import annotations

import csv
import json
import re
from collections import Counter
from pathlib import Path


CONTRACT_CSV = Path("tmp/raw/contract/contract.csv")
PROJECT_SAMPLE_30_CSV = Path("data/migration_samples/project_sample_v1.csv")
PROJECT_SAMPLE_100_CSV = Path("artifacts/migration/project_create_only_expand_post_write_snapshot_v1.csv")
PARTNER_ROLLBACK_TARGET_CSV = Path("artifacts/migration/partner_30_row_rollback_target_list_v1.csv")
OUTPUT_JSON = Path("artifacts/migration/contract_anchor_readiness_recheck_v1.json")
OUTPUT_CSV = Path("artifacts/migration/contract_anchor_safe_candidates_v1.csv")

OWN_COMPANY_NAMES = {"四川保盛建设集团有限公司", "My Company"}
ORG_SUFFIXES = ("有限责任公司", "股份有限公司", "集团有限公司", "有限公司", "公司")


def clean_text(value):
    text = "" if value is None else str(value)
    text = text.replace("\u3000", " ").strip()
    return re.sub(r"\s+", " ", text)


def norm_name(value):
    text = clean_text(value)
    text = re.sub(r"[（）()·,，.。/、\s\\-]", "", text)
    for suffix in ORG_SUFFIXES:
        if text.endswith(suffix):
            text = text[: -len(suffix)]
            break
    return text


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


def written_project_ids():
    ids = set()
    for path in (PROJECT_SAMPLE_30_CSV, PROJECT_SAMPLE_100_CSV):
        if not path.exists():
            continue
        for row in read_csv(path):
            value = clean_text(row.get("legacy_project_id"))
            if value:
                ids.add(value)
    return ids


def infer_direction(row):
    fbf = clean_text(row.get("FBF"))
    cbf = clean_text(row.get("CBF"))
    if cbf in OWN_COMPANY_NAMES and fbf not in OWN_COMPANY_NAMES:
        return "out", fbf
    if fbf in OWN_COMPANY_NAMES and cbf not in OWN_COMPANY_NAMES:
        return "in", cbf
    return "defer", ""


def partner_index():
    partners = read_csv(PARTNER_ROLLBACK_TARGET_CSV)
    exact = {}
    normalized = {}
    rows = []
    for partner in partners:
        info = {
            "id": clean_text(partner.get("partner_id")),
            "name": clean_text(partner.get("partner_name")),
            "display_name": clean_text(partner.get("partner_name")),
            "legacy_partner_id": clean_text(partner.get("legacy_partner_id")),
            "legacy_partner_source": clean_text(partner.get("legacy_partner_source")),
        }
        rows.append(info)
        for name in {info["name"], info["display_name"]}:
            name = clean_text(name)
            if not name:
                continue
            exact.setdefault(name, []).append(info)
            normalized.setdefault(norm_name(name), []).append(info)
    return rows, exact, normalized


def main():
    contracts = read_csv(CONTRACT_CSV)
    project_ids = written_project_ids()
    partners, exact, normalized = partner_index()

    direction_counts = Counter()
    match_counts = Counter()
    blocker_counts = Counter()
    project_scope_counts = Counter()
    deleted_counts = Counter()
    safe_rows = []

    for row in contracts:
        legacy_contract_id = clean_text(row.get("Id"))
        legacy_project_id = clean_text(row.get("XMID"))
        direction, counterparty = infer_direction(row)
        direction_counts[direction] += 1
        exact_matches = exact.get(counterparty, []) if counterparty else []
        norm_matches = normalized.get(norm_name(counterparty), []) if counterparty else []
        partner_matches = exact_matches or norm_matches
        match_type = "exact" if exact_matches else "normalized" if norm_matches else "defer"
        match_counts[match_type] += 1

        deleted = clean_text(row.get("DEL")) == "1"
        subject = clean_text(row.get("HTBT")) or clean_text(row.get("DJBH")) or clean_text(row.get("HTBH"))
        project_in_scope = legacy_project_id in project_ids
        direction_ok = direction in {"out", "in"}
        partner_ok = len(partner_matches) == 1
        subject_ok = bool(subject)
        project_scope_counts["written_project_match" if project_in_scope else "project_not_written_scope"] += 1
        deleted_counts["deleted" if deleted else "active_or_blank"] += 1
        if not project_in_scope:
            blocker_counts["project_not_written_scope"] += 1
        if not direction_ok:
            blocker_counts["direction_defer"] += 1
        if not partner_ok:
            blocker_counts["partner_unresolved"] += 1
        if not subject_ok:
            blocker_counts["missing_subject"] += 1
        if deleted:
            blocker_counts["deleted_flag"] += 1

        if legacy_contract_id and project_in_scope and direction_ok and partner_ok and subject_ok and not deleted:
            partner = partner_matches[0]
            safe_rows.append(
                {
                    "legacy_contract_id": legacy_contract_id,
                    "legacy_project_id": legacy_project_id,
                    "subject": subject,
                    "contract_no": clean_text(row.get("HTBH")),
                    "direction": direction,
                    "counterparty_text": counterparty,
                    "partner_id": partner["id"],
                    "legacy_partner_source": partner["legacy_partner_source"],
                    "legacy_partner_id": partner["legacy_partner_id"],
                    "match_type": match_type,
                    "legacy_status": clean_text(row.get("DJZT")),
                    "legacy_deleted": clean_text(row.get("DEL")),
                }
            )

    write_csv(
        OUTPUT_CSV,
        [
            "legacy_contract_id",
            "legacy_project_id",
            "subject",
            "contract_no",
            "direction",
            "counterparty_text",
            "partner_id",
            "legacy_partner_source",
            "legacy_partner_id",
            "match_type",
            "legacy_status",
            "legacy_deleted",
        ],
        safe_rows,
    )
    payload = {
        "status": "PASS",
        "mode": "contract_anchor_readiness_recheck_readonly",
        "database": "sc_demo",
        "partner_anchor_input": str(PARTNER_ROLLBACK_TARGET_CSV),
        "contract_rows": len(contracts),
        "partner_anchor_count": len(partners),
        "written_project_anchor_count": len(project_ids),
        "direction_counts": dict(sorted(direction_counts.items())),
        "partner_match_counts": dict(sorted(match_counts.items())),
        "project_scope_counts": dict(sorted(project_scope_counts.items())),
        "deleted_counts": dict(sorted(deleted_counts.items())),
        "safe_candidate_rows": len(safe_rows),
        "safe_candidate_csv": str(OUTPUT_CSV),
        "blocker_counts": dict(sorted(blocker_counts.items())),
        "decision": "candidate dry-run allowed" if safe_rows else "NO-GO for contract write",
        "next_step": "prepare bounded contract header dry-run" if safe_rows else "continue partner/project anchor expansion before contract write",
    }
    write_json(OUTPUT_JSON, payload)
    print(
        "CONTRACT_ANCHOR_RECHECK="
        + json.dumps(
            {
                "status": payload["status"],
                "contract_rows": payload["contract_rows"],
                "partner_anchor_count": payload["partner_anchor_count"],
                "written_project_anchor_count": payload["written_project_anchor_count"],
                "safe_candidate_rows": payload["safe_candidate_rows"],
                "decision": payload["decision"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


main()
