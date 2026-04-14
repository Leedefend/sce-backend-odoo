#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path


INPUT_CSV = Path("artifacts/migration/contract_counterparty_strong_evidence_candidates_v1.csv")
OUTPUT_CSV = Path("artifacts/migration/partner_strong_evidence_dry_run_input_v1.csv")
OUTPUT_JSON = Path("artifacts/migration/partner_strong_evidence_dry_run_input_summary_v1.json")

FIELDS = [
    "legacy_partner_id",
    "partner_name",
    "company_credit_code",
    "company_tax_no",
    "source",
    "source_evidence",
    "linked_contract_count",
    "linked_repayment_rows",
    "sample_legacy_contract_id",
    "sample_legacy_contract_no",
    "manual_confirm_required",
    "auto_create_allowed",
    "dry_run_action",
    "review_note",
]


def main() -> int:
    with INPUT_CSV.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))

    eligible = [
        row
        for row in rows
        if row.get("legacy_contract_deleted_flag") == "0"
        and row.get("company_deleted_flag") == "0"
        and row.get("repayment_partner_id")
    ]

    grouped = defaultdict(list)
    for row in eligible:
        grouped[row["repayment_partner_id"]].append(row)

    output_rows = []
    for partner_id, items in sorted(grouped.items(), key=lambda item: (item[1][0]["company_name"], item[0])):
        first = items[0]
        repayment_rows = sum(int(item.get("repayment_rows") or 0) for item in items)
        output_rows.append(
            {
                "legacy_partner_id": partner_id,
                "partner_name": first.get("company_name", ""),
                "company_credit_code": first.get("company_credit_code", ""),
                "company_tax_no": first.get("company_tax_no", ""),
                "source": "T_Base_CooperatCompany",
                "source_evidence": "C_JFHKLR.SGHTID/WLDWID single-counterparty contracts",
                "linked_contract_count": len(items),
                "linked_repayment_rows": repayment_rows,
                "sample_legacy_contract_id": first.get("legacy_contract_id", ""),
                "sample_legacy_contract_no": first.get("legacy_contract_no", ""),
                "manual_confirm_required": "yes",
                "auto_create_allowed": "no",
                "dry_run_action": "candidate_create_or_reuse",
                "review_note": "",
            }
        )

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_CSV.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(output_rows)

    credit_code_counts = Counter("has_credit_code" if row["company_credit_code"] else "missing_credit_code" for row in output_rows)
    tax_no_counts = Counter("has_tax_no" if row["company_tax_no"] else "missing_tax_no" for row in output_rows)
    result = {
        "status": "PASS",
        "mode": "partner_strong_evidence_dry_run_input_no_db_write",
        "input_contract_candidate_rows": len(rows),
        "eligible_contract_candidate_rows": len(eligible),
        "deduplicated_partner_candidates": len(output_rows),
        "credit_code_counts": dict(sorted(credit_code_counts.items())),
        "tax_no_counts": dict(sorted(tax_no_counts.items())),
        "output_csv": str(OUTPUT_CSV),
        "decision": "NO-GO for partner creation; dry-run input prepared",
        "next_step": "manual review and implement partner dry-run importer before any real partner creation",
    }
    OUTPUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("PARTNER_STRONG_EVIDENCE_DRY_RUN_INPUT=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
