#!/usr/bin/env python3
"""Generate no-DB review queue assets for blocked partner import candidates."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


DEFAULT_GATE = (
    "artifacts/migration/partner_business_aligned_rebuild_v1/"
    "fact_based_partner_rebuild_business_aligned_gate_v1.csv"
)
FIELDS = [
    "import_batch",
    "legacy_partner_source",
    "legacy_partner_id",
    "partner_name",
    "company_type",
    "review_reason",
    "review_state",
    "suggested_customer_rank",
    "suggested_supplier_rank",
    "sc_supplier_type",
    "sc_region",
    "street",
    "sc_registered_capital",
    "sc_business_scope",
    "sc_default_tax_rate",
    "sc_default_tax_rate_text",
    "vat",
    "legacy_credit_code",
    "sc_account_name",
    "sc_bank_name",
    "sc_bank_account",
    "source_created_by",
    "source_created_at",
    "source_document_state",
    "source_push_result",
    "source_project_name",
    "source_tax_rate",
    "source_files",
    "review_flags",
    "gate_reason",
    "evidence",
]
REASON_PRIORITY = [
    "unknown_business_role",
    "personal_fragment_review",
    "invalid_bank_account_review",
    "invalid_or_placeholder_credit",
    "multiple_current_payload_matches",
]


class PartnerReviewAssetError(Exception):
    pass


def clean(value: object) -> str:
    return "" if value is None else str(value).strip()


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise PartnerReviewAssetError(f"missing gate csv: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def review_reason(row: dict[str, str]) -> str:
    flags = {clean(item) for item in clean(row.get("gate_reason")).split(";") if clean(item)}
    for reason in REASON_PRIORITY:
        if reason in flags:
            return reason
    return "mixed_blocker"


def build_rows(gate_rows: list[dict[str, str]], import_batch: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for row in gate_rows:
        if clean(row.get("gate_action")) != "blocked_review":
            continue
        key = (import_batch, clean(row.get("legacy_partner_source")), clean(row.get("legacy_partner_id")))
        if key in seen:
            raise PartnerReviewAssetError(f"duplicate review identity: {key}")
        seen.add(key)
        rows.append(
            {
                "import_batch": import_batch,
                "legacy_partner_source": key[1],
                "legacy_partner_id": key[2],
                "partner_name": clean(row.get("name")),
                "company_type": clean(row.get("company_type")) or "company",
                "review_reason": review_reason(row),
                "review_state": "candidate",
                "suggested_customer_rank": clean(row.get("customer_rank")) or "0",
                "suggested_supplier_rank": clean(row.get("supplier_rank")) or "0",
                "sc_supplier_type": clean(row.get("sc_supplier_type")),
                "sc_region": clean(row.get("sc_region")),
                "street": clean(row.get("street")),
                "sc_registered_capital": clean(row.get("sc_registered_capital")),
                "sc_business_scope": clean(row.get("sc_business_scope")),
                "sc_default_tax_rate": clean(row.get("sc_default_tax_rate")),
                "sc_default_tax_rate_text": clean(row.get("sc_default_tax_rate_text")),
                "vat": clean(row.get("vat")),
                "legacy_credit_code": clean(row.get("legacy_credit_code")),
                "sc_account_name": clean(row.get("sc_account_name")),
                "sc_bank_name": clean(row.get("sc_bank_name")),
                "sc_bank_account": clean(row.get("sc_bank_account")),
                "source_created_by": clean(row.get("source_created_by")),
                "source_created_at": clean(row.get("source_created_at")),
                "source_document_state": clean(row.get("source_document_state")),
                "source_push_result": clean(row.get("source_push_result")),
                "source_project_name": clean(row.get("source_project_name")),
                "source_tax_rate": clean(row.get("source_tax_rate")),
                "source_files": clean(row.get("source_files")),
                "review_flags": clean(row.get("review_flags")),
                "gate_reason": clean(row.get("gate_reason")),
                "evidence": clean(row.get("legacy_source_evidence")),
            }
        )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gate", default=DEFAULT_GATE)
    parser.add_argument("--out-dir", default="artifacts/migration/partner_business_aligned_rebuild_v1")
    parser.add_argument("--import-batch", default="partner_business_fit_v1")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    try:
        rows = build_rows(read_csv(Path(args.gate)), args.import_batch)
        reason_counts = Counter(row["review_reason"] for row in rows)
        state_counts = Counter(row["review_state"] for row in rows)
        out_dir = Path(args.out_dir)
        csv_path = out_dir / "partner_import_review_queue_v1.csv"
        json_path = out_dir / "partner_import_review_queue_result_v1.json"
        write_csv(csv_path, FIELDS, rows)
        result = {
            "status": "PASS",
            "mode": "partner_import_review_asset_generator",
            "generated_at": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
            "review_rows": len(rows),
            "reason_counts": dict(sorted(reason_counts.items())),
            "state_counts": dict(sorted(state_counts.items())),
            "row_artifact": str(csv_path),
            "db_writes": 0,
            "odoo_shell": False,
        }
        write_json(json_path, result)
    except (PartnerReviewAssetError, OSError, csv.Error) as exc:
        result = {"status": "FAIL", "error": str(exc), "db_writes": 0, "odoo_shell": False}
        print("PARTNER_IMPORT_REVIEW_ASSET=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 1 if args.check else 0

    print("PARTNER_IMPORT_REVIEW_ASSET=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
