#!/usr/bin/env python3
"""Backtrace blocked contract partner rows to original strong-evidence analysis assets."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
GAP_ROWS_CSV = REPO_ROOT / "artifacts/migration/history_contract_partner_gap_rows_v1.csv"
STRONG_EVIDENCE_CSV = REPO_ROOT / "artifacts/migration/contract_counterparty_strong_evidence_candidates_v1.csv"
OUTPUT_JSON = REPO_ROOT / "artifacts/migration/history_contract_strong_evidence_backtrace_audit_v1.json"
OUTPUT_CSV = REPO_ROOT / "artifacts/migration/history_contract_strong_evidence_backtrace_rows_v1.csv"


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


def main() -> int:
    gap_rows = [
        row
        for row in read_csv(GAP_ROWS_CSV)
        if clean(row.get("partner_source_bucket")) == "no_asset_source_in_current_packages"
        and clean(row.get("counterparty_text"))
    ]
    strong_rows = {clean(row.get("legacy_contract_id")): row for row in read_csv(STRONG_EVIDENCE_CSV)}

    evidence_type_counts = Counter()
    evidence_strength_counts = Counter()
    confirm_required_counts = Counter()
    action_counts = Counter()
    missing_contracts: list[str] = []
    rows_out: list[dict[str, object]] = []

    for row in gap_rows:
        legacy_contract_id = clean(row.get("legacy_contract_id"))
        strong = strong_rows.get(legacy_contract_id)
        if not strong:
            missing_contracts.append(legacy_contract_id)
            rows_out.append(
                {
                    "legacy_contract_id": legacy_contract_id,
                    "counterparty_text": clean(row.get("counterparty_text")),
                    "backtrace_status": "missing_in_strong_evidence_candidates",
                    "evidence_type": "",
                    "evidence_strength": "",
                    "manual_confirm_required": "",
                    "confirmed_partner_action": "",
                    "repayment_partner_name": "",
                    "company_name": "",
                    "review_note": "",
                }
            )
            continue

        evidence_type = clean(strong.get("evidence_type"))
        evidence_strength = clean(strong.get("evidence_strength"))
        manual_confirm_required = clean(strong.get("manual_confirm_required"))
        confirmed_partner_action = clean(strong.get("confirmed_partner_action"))
        repayment_partner_name = clean(strong.get("repayment_partner_name"))
        company_name = clean(strong.get("company_name"))
        review_note = clean(strong.get("review_note"))

        evidence_type_counts[evidence_type] += 1
        evidence_strength_counts[evidence_strength] += 1
        confirm_required_counts[manual_confirm_required] += 1
        action_counts[confirmed_partner_action or "<empty>"] += 1

        rows_out.append(
            {
                "legacy_contract_id": legacy_contract_id,
                "counterparty_text": clean(row.get("counterparty_text")),
                "backtrace_status": "matched_in_strong_evidence_candidates",
                "evidence_type": evidence_type,
                "evidence_strength": evidence_strength,
                "manual_confirm_required": manual_confirm_required,
                "confirmed_partner_action": confirmed_partner_action,
                "repayment_partner_name": repayment_partner_name,
                "company_name": company_name,
                "review_note": review_note,
            }
        )

    payload = {
        "status": "PASS",
        "mode": "history_contract_strong_evidence_backtrace_audit",
        "gap_rows": len(gap_rows),
        "matched_rows": len(gap_rows) - len(missing_contracts),
        "missing_rows": len(missing_contracts),
        "evidence_type_counts": dict(sorted(evidence_type_counts.items())),
        "evidence_strength_counts": dict(sorted(evidence_strength_counts.items())),
        "manual_confirm_required_counts": dict(sorted(confirm_required_counts.items())),
        "confirmed_partner_action_counts": dict(sorted(action_counts.items())),
        "row_artifact": str(OUTPUT_CSV.relative_to(REPO_ROOT)),
        "missing_contract_ids": missing_contracts[:50],
        "sample_rows": rows_out[:20],
    }

    write_csv(
        OUTPUT_CSV,
        [
            "legacy_contract_id",
            "counterparty_text",
            "backtrace_status",
            "evidence_type",
            "evidence_strength",
            "manual_confirm_required",
            "confirmed_partner_action",
            "repayment_partner_name",
            "company_name",
            "review_note",
        ],
        rows_out,
    )
    write_json(OUTPUT_JSON, payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
