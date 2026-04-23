#!/usr/bin/env python3
"""Screen duplicate partner names blocking contract partner anchor replay."""

from __future__ import annotations

import csv
import json
from pathlib import Path


REPO_ROOT = Path("/mnt")
INPUT_CSV = REPO_ROOT / "artifacts/migration/fresh_db_contract_partner_12_anchor_replay_payload_v1.csv"
OUTPUT_JSON = REPO_ROOT / "artifacts/migration/fresh_db_contract_partner_dupname_screen_result_v1.json"
OUTPUT_CSV = REPO_ROOT / "artifacts/migration/fresh_db_contract_partner_dupname_screen_rows_v1.csv"
EXPECTED_DUP_NAMES = {
    "四川宝烨金属制品有限公司",
    "四川高竹工程建设有限公司",
    "德阳泰诚硕商贸有限公司",
}
ROW_FIELDS = [
    "blocked_name",
    "partner_id",
    "partner_name",
    "legacy_partner_source",
    "legacy_partner_id",
    "legacy_partner_name",
    "legacy_credit_code",
    "legacy_tax_no",
    "legacy_deleted_flag",
    "legacy_source_evidence",
    "dependent_contract_rows",
    "sample_legacy_contract_id",
    "sample_contract_subject",
    "candidate_role",
]


def clean(value: object) -> str:
    return "" if value is None else str(value).strip()


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


def classify_candidate(partner) -> str:
    source = clean(partner.legacy_partner_source)
    evidence = clean(partner.legacy_source_evidence)
    if source == "company_supplier":
        return "prefer_strong_combined_identity"
    if source == "cooperat_company":
        return "company_identity_candidate"
    if source == "supplier":
        return "supplier_identity_candidate"
    if evidence:
        return "evidence_only_candidate"
    return "plain_partner_candidate"


if env.cr.dbname != "sc_migration_fresh":  # noqa: F821
    raise RuntimeError({"db_name_not_sc_migration_fresh": env.cr.dbname})  # noqa: F821

Partner = env["res.partner"].sudo()  # noqa: F821
payload_rows = read_csv(INPUT_CSV)
payload_by_name = {clean(row.get("name")) or clean(row.get("counterparty_text")): row for row in payload_rows}

screen_rows: list[dict[str, object]] = []
summary: dict[str, object] = {}
for name in sorted(EXPECTED_DUP_NAMES):
    payload = payload_by_name.get(name, {})
    matches = Partner.search([("name", "=", name)], order="id")
    roles = []
    for partner in matches:
        role = classify_candidate(partner)
        roles.append(role)
        screen_rows.append(
            {
                "blocked_name": name,
                "partner_id": partner.id,
                "partner_name": partner.name or "",
                "legacy_partner_source": partner.legacy_partner_source or "",
                "legacy_partner_id": partner.legacy_partner_id or "",
                "legacy_partner_name": partner.legacy_partner_name or "",
                "legacy_credit_code": partner.legacy_credit_code or "",
                "legacy_tax_no": partner.legacy_tax_no or "",
                "legacy_deleted_flag": partner.legacy_deleted_flag or "",
                "legacy_source_evidence": partner.legacy_source_evidence or "",
                "dependent_contract_rows": clean(payload.get("dependent_contract_rows")),
                "sample_legacy_contract_id": clean(payload.get("sample_legacy_contract_id")),
                "sample_contract_subject": clean(payload.get("sample_contract_subject")),
                "candidate_role": role,
            }
        )
    summary[name] = {
        "target_match_count": len(matches),
        "candidate_roles": sorted(set(roles)),
        "dependent_contract_rows": int(clean(payload.get("dependent_contract_rows")) or "0"),
        "sample_legacy_contract_id": clean(payload.get("sample_legacy_contract_id")),
    }

all_blocking_names_present = set(summary) == EXPECTED_DUP_NAMES
all_have_duplicates = all(item["target_match_count"] > 1 for item in summary.values())
result = {
    "status": "PASS" if all_blocking_names_present and all_have_duplicates else "FAIL",
    "mode": "fresh_db_contract_partner_dupname_screen",
    "database": env.cr.dbname,  # noqa: F821
    "db_writes": 0,
    "input_payload_rows": len(payload_rows),
    "blocked_duplicate_names": len(summary),
    "screen_rows": len(screen_rows),
    "summary": summary,
    "row_artifact": str(OUTPUT_CSV),
    "decision": "duplicate_name_evidence_screen_complete" if all_blocking_names_present and all_have_duplicates else "STOP_REVIEW_REQUIRED",
    "next_step": "classify retry policy for contract partner anchors",
}
write_csv(OUTPUT_CSV, ROW_FIELDS, screen_rows)
write_json(OUTPUT_JSON, result)
env.cr.rollback()  # noqa: F821
print(
    "FRESH_DB_CONTRACT_PARTNER_DUPNAME_SCREEN="
    + json.dumps(
        {
            "status": result["status"],
            "blocked_duplicate_names": len(summary),
            "screen_rows": len(screen_rows),
            "db_writes": 0,
        },
        ensure_ascii=False,
        sort_keys=True,
    )
)
