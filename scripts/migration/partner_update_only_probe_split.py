#!/usr/bin/env python3
"""Split update-only partner rows by read-only match probe result."""

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
DEFAULT_PROBE = (
    "artifacts/migration/partner_business_aligned_rebuild_v1/"
    "partner_update_only_match_probe_v1.csv"
)
DEFAULT_OUT_DIR = "artifacts/migration/partner_business_aligned_rebuild_v1"
REVIEW_FIELDS = [
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


class SplitError(Exception):
    pass


def clean(value: object) -> str:
    return "" if value is None else str(value).strip()


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise SplitError(f"missing csv: {path}")
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


def key_for(row: dict[str, str]) -> tuple[str, str]:
    return clean(row.get("legacy_partner_source")), clean(row.get("legacy_partner_id"))


def review_reason(status: str) -> str:
    if status == "not_found":
        return "update_only_not_found"
    if status == "ambiguous":
        return "update_only_ambiguous"
    return "mixed_blocker"


def review_row(gate_row: dict[str, str], probe_row: dict[str, str], import_batch: str) -> dict[str, Any]:
    status = clean(probe_row.get("match_status"))
    method = clean(probe_row.get("match_method"))
    matched_ids = clean(probe_row.get("matched_partner_ids"))
    matched_names = clean(probe_row.get("matched_partner_names"))
    return {
        "import_batch": import_batch,
        "legacy_partner_source": clean(gate_row.get("legacy_partner_source")),
        "legacy_partner_id": clean(gate_row.get("legacy_partner_id")),
        "partner_name": clean(gate_row.get("name")),
        "company_type": clean(gate_row.get("company_type")) or "company",
        "review_reason": review_reason(status),
        "review_state": "candidate",
        "suggested_customer_rank": clean(gate_row.get("customer_rank")) or "0",
        "suggested_supplier_rank": clean(gate_row.get("supplier_rank")) or "0",
        "sc_supplier_type": clean(gate_row.get("sc_supplier_type")),
        "sc_region": clean(gate_row.get("sc_region")),
        "street": clean(gate_row.get("street")),
        "sc_registered_capital": clean(gate_row.get("sc_registered_capital")),
        "sc_business_scope": clean(gate_row.get("sc_business_scope")),
        "sc_default_tax_rate": clean(gate_row.get("sc_default_tax_rate")),
        "sc_default_tax_rate_text": clean(gate_row.get("sc_default_tax_rate_text")),
        "vat": clean(gate_row.get("vat")),
        "legacy_credit_code": clean(gate_row.get("legacy_credit_code")),
        "sc_account_name": clean(gate_row.get("sc_account_name")),
        "sc_bank_name": clean(gate_row.get("sc_bank_name")),
        "sc_bank_account": clean(gate_row.get("sc_bank_account")),
        "source_created_by": clean(gate_row.get("source_created_by")),
        "source_created_at": clean(gate_row.get("source_created_at")),
        "source_document_state": clean(gate_row.get("source_document_state")),
        "source_push_result": clean(gate_row.get("source_push_result")),
        "source_project_name": clean(gate_row.get("source_project_name")),
        "source_tax_rate": clean(gate_row.get("source_tax_rate")),
        "source_files": clean(gate_row.get("source_files")),
        "review_flags": ";".join(
            item
            for item in [
                clean(gate_row.get("review_flags")),
                f"probe_status:{status}",
                f"probe_method:{method}",
            ]
            if item
        ),
        "gate_reason": ";".join(
            item
            for item in [
                clean(gate_row.get("gate_reason")),
                f"probe_status:{status}",
                f"matched_partner_ids:{matched_ids}" if matched_ids else "",
                f"matched_partner_names:{matched_names}" if matched_names else "",
            ]
            if item
        ),
        "evidence": clean(gate_row.get("legacy_source_evidence")),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gate", default=DEFAULT_GATE)
    parser.add_argument("--probe", default=DEFAULT_PROBE)
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR)
    parser.add_argument("--import-batch", default="partner_business_fit_update_only_v1")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    try:
        gate_rows = [row for row in read_csv(Path(args.gate)) if clean(row.get("gate_action")) == "update_only_candidate"]
        probe_rows = read_csv(Path(args.probe))
        gate_by_key = {key_for(row): row for row in gate_rows}
        probe_by_key = {key_for(row): row for row in probe_rows}
        missing_probe = sorted(set(gate_by_key) - set(probe_by_key))[:20]
        extra_probe = sorted(set(probe_by_key) - set(gate_by_key))[:20]
        if missing_probe or extra_probe:
            raise SplitError({"missing_probe_samples": missing_probe, "extra_probe_samples": extra_probe})
        matched_rows: list[dict[str, Any]] = []
        review_rows: list[dict[str, Any]] = []
        status_counts: Counter[str] = Counter()
        matched_fact_counts: Counter[str] = Counter()
        for key, gate_row in sorted(gate_by_key.items()):
            probe_row = probe_by_key[key]
            status = clean(probe_row.get("match_status"))
            status_counts[status] += 1
            if status == "matched_unique":
                matched_row = {**gate_row, "probe_match_method": clean(probe_row.get("match_method")), "probe_partner_id": clean(probe_row.get("matched_partner_ids"))}
                matched_rows.append(matched_row)
                if clean(gate_row.get("sc_bank_account")):
                    matched_fact_counts["bank_account"] += 1
                if clean(gate_row.get("sc_default_tax_rate")):
                    matched_fact_counts["tax_rate"] += 1
                if clean(gate_row.get("sc_region")):
                    matched_fact_counts["region"] += 1
            else:
                review_rows.append(review_row(gate_row, probe_row, args.import_batch))
        out_dir = Path(args.out_dir)
        matched_csv = out_dir / "partner_update_only_matched_updates_v1.csv"
        review_csv = out_dir / "partner_update_only_probe_review_queue_v1.csv"
        result_json = out_dir / "partner_update_only_probe_split_result_v1.json"
        matched_fields = list(matched_rows[0].keys()) if matched_rows else list(gate_rows[0].keys()) + ["probe_match_method", "probe_partner_id"]
        write_csv(matched_csv, matched_fields, matched_rows)
        write_csv(review_csv, REVIEW_FIELDS, review_rows)
        result = {
            "status": "PASS",
            "mode": "partner_update_only_probe_split",
            "generated_at": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
            "input_update_only_rows": len(gate_rows),
            "probe_rows": len(probe_rows),
            "match_status_counts": dict(sorted(status_counts.items())),
            "matched_update_rows": len(matched_rows),
            "review_rows": len(review_rows),
            "matched_fact_counts": dict(sorted(matched_fact_counts.items())),
            "matched_csv": str(matched_csv),
            "review_csv": str(review_csv),
            "db_writes": 0,
            "odoo_shell": False,
        }
        write_json(result_json, result)
    except (SplitError, OSError, csv.Error) as exc:
        result = {"status": "FAIL", "error": str(exc), "db_writes": 0, "odoo_shell": False}
        print("PARTNER_UPDATE_ONLY_PROBE_SPLIT=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 1 if args.check else 0

    print("PARTNER_UPDATE_ONLY_PROBE_SPLIT=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
