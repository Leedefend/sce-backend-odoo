"""Readonly DB precheck for the 12 contract header dry-run rows.

Run through Odoo shell from the repository root:

    DB_NAME=sc_demo make odoo.shell.exec < scripts/migration/contract_header_12_row_readonly_db_precheck.py

The script performs searches only. It does not call create(), write(), unlink(),
default_get(), or model helpers that may self-heal missing master data.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


INPUT_CSV = Path("/mnt/artifacts/migration/contract_header_12_row_dry_run_rows_v1.csv")
OUTPUT_JSON = Path("/mnt/artifacts/migration/contract_header_12_row_readonly_db_precheck_v1.json")


def clean_text(value):
    return "" if value is None else str(value).strip()


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def readonly_tax_candidates(contract_type):
    type_tax_use = "sale" if contract_type == "out" else "purchase"
    name = "销项VAT 9%" if contract_type == "out" else "进项VAT 13%"
    amount = 9.0 if contract_type == "out" else 13.0
    domain = [
        ("company_id", "=", env.company.id),
        ("type_tax_use", "in", [type_tax_use, "all"]),
        ("amount_type", "=", "percent"),
        ("price_include", "=", False),
        ("amount", "=", amount),
    ]
    candidates = env["account.tax"].sudo().with_context(active_test=False).search(domain)
    exact = candidates.filtered(lambda tax: tax.name == name)
    picked = (exact or candidates[:1])[:1]
    return {
        "type_tax_use": type_tax_use,
        "expected_name": name,
        "expected_amount": amount,
        "candidate_count": len(candidates),
        "exact_name_count": len(exact),
        "picked_tax_id": picked.id if picked else False,
        "picked_tax_active": bool(picked.active) if picked else False,
    }


rows = read_csv(INPUT_CSV)
Contract = env["construction.contract"].sudo()
Project = env["project.project"].sudo()
Partner = env["res.partner"].sudo()
Sequence = env["ir.sequence"].sudo()

row_results = []
blockers = Counter()
type_counts = Counter()

for row in rows:
    legacy_contract_id = clean_text(row.get("legacy_contract_id"))
    project_id = clean_text(row.get("project_id"))
    partner_id = clean_text(row.get("partner_id"))
    contract_type = clean_text(row.get("type"))
    type_counts[contract_type or "blank"] += 1

    existing_contract_count = Contract.search_count([("legacy_contract_id", "=", legacy_contract_id)])
    project_exists = bool(project_id and Project.browse(int(project_id)).exists())
    partner_exists = bool(partner_id and Partner.browse(int(partner_id)).exists())
    tax_info = readonly_tax_candidates(contract_type)
    seq_code = "construction.contract.income" if contract_type == "out" else "construction.contract.expense"
    seq_count = Sequence.search_count([("code", "=", seq_code)])

    row_blockers = []
    if existing_contract_count:
        row_blockers.append("legacy_contract_already_exists")
    if not project_exists:
        row_blockers.append("project_missing")
    if not partner_exists:
        row_blockers.append("partner_missing")
    if not tax_info["picked_tax_id"]:
        row_blockers.append("default_tax_missing")
    elif not tax_info["picked_tax_active"]:
        row_blockers.append("default_tax_inactive")
    if not seq_count:
        row_blockers.append("sequence_missing")

    for blocker in row_blockers:
        blockers[blocker] += 1

    row_results.append(
        {
            "legacy_contract_id": legacy_contract_id,
            "project_id": project_id,
            "partner_id": partner_id,
            "type": contract_type,
            "existing_contract_count": existing_contract_count,
            "project_exists": project_exists,
            "partner_exists": partner_exists,
            "tax": tax_info,
            "sequence_code": seq_code,
            "sequence_count": seq_count,
            "status": "READY_FOR_WRITE_AUTHORIZATION_GATE" if not row_blockers else "BLOCKED",
            "blockers": row_blockers,
        }
    )

ready_rows = sum(1 for item in row_results if item["status"] == "READY_FOR_WRITE_AUTHORIZATION_GATE")
payload = {
    "status": "PASS" if ready_rows == len(row_results) and len(row_results) == 12 else "PASS_WITH_BLOCKERS",
    "mode": "contract_header_12_row_readonly_db_precheck",
    "database": env.cr.dbname,
    "input": str(INPUT_CSV),
    "row_count": len(row_results),
    "ready_for_write_authorization_gate_rows": ready_rows,
    "blocked_rows": len(row_results) - ready_rows,
    "type_counts": dict(sorted(type_counts.items())),
    "blocker_counts": dict(sorted(blockers.items())),
    "write_authorization": "not_granted",
    "contract_write_decision": "NO-GO until separate explicit contract write authorization",
    "rows": row_results,
    "next_step": "if PASS, open a dedicated contract write authorization packet; otherwise fix blockers first",
}
write_json(OUTPUT_JSON, payload)
print(
    "CONTRACT_HEADER_12_READONLY_DB_PRECHECK="
    + json.dumps(
        {
            "status": payload["status"],
            "row_count": payload["row_count"],
            "ready_for_write_authorization_gate_rows": payload["ready_for_write_authorization_gate_rows"],
            "blocked_rows": payload["blocked_rows"],
            "contract_write_decision": payload["contract_write_decision"],
        },
        ensure_ascii=False,
        sort_keys=True,
    )
)
