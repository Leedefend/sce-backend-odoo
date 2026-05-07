#!/usr/bin/env python3
"""Build a business-alignment overlay for the existing partner rebuild payload.

This script does not replace the rebuild package. It compares the current
partner rebuild payload with the user-provided mixed partner Excel source and
emits reviewable deltas for the next rebuild iteration.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path

from partner_import_source_audit import (
    build_entity_rows,
    clean,
    identity_for,
    load_source_records,
    norm_name,
    norm_tax,
    parse_amount,
    write_csv,
    write_json,
)


DEFAULT_CURRENT_PAYLOAD = (
    "artifacts/migration/fact_based_partner_rebuild_2_fact_only_20260506T2055/"
    "fact_based_partner_rebuild_payload_v1.csv"
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def first_value(rows: list[dict[str, str]], field: str) -> str:
    values = [clean(row.get(field)) for row in rows if clean(row.get(field))]
    return Counter(values).most_common(1)[0][0] if values else ""


def join_values(rows: list[dict[str, str]], field: str, limit: int = 20) -> str:
    return ";".join(sorted({clean(row.get(field)) for row in rows if clean(row.get(field))})[:limit])


def current_keys(row: dict[str, str]) -> set[str]:
    keys: set[str] = set()
    vat = norm_tax(row.get("vat") or row.get("legacy_credit_code"))
    name = norm_name(row.get("name"))
    partner_key = clean(row.get("partner_key"))
    legacy_partner_id = clean(row.get("legacy_partner_id"))
    if vat:
        keys.add(f"tax:{vat}")
    if name:
        keys.add(f"name:{name}")
    if partner_key:
        keys.add(partner_key)
    if legacy_partner_id:
        keys.add(legacy_partner_id)
    return keys


def role_from_current(row: dict[str, str]) -> str:
    customer = clean(row.get("customer_rank")) not in {"", "0", "0.0", "False", "false"}
    supplier = clean(row.get("supplier_rank")) not in {"", "0", "0.0", "False", "false"}
    if customer and supplier:
        return "customer_and_supplier"
    if customer:
        return "customer"
    if supplier:
        return "supplier"
    return "none"


def target_role(entity: dict[str, object]) -> str:
    return clean(entity.get("target_role"))


def source_groups(source_records: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for record in source_records:
        grouped[identity_for(record)].append(record)
    return grouped


def build_overlay(source_records: list[dict[str, str]], current_rows: list[dict[str, str]]) -> list[dict[str, object]]:
    grouped = source_groups(source_records)
    entity_by_key = {clean(row["identity_key"]): row for row in build_entity_rows(source_records)}
    current_by_key: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in current_rows:
        for key in current_keys(row):
            current_by_key[key].append(row)

    overlay_rows: list[dict[str, object]] = []
    for identity_key, rows in sorted(grouped.items()):
        entity = entity_by_key[identity_key]
        matches = current_by_key.get(identity_key, [])
        if not matches and identity_key.startswith("tax:"):
            name_key = "name:" + norm_name(entity.get("canonical_name"))
            matches = current_by_key.get(name_key, [])
        current = matches[0] if matches else {}
        current_role = role_from_current(current) if current else "missing"
        expected_role = target_role(entity)

        missing_basic_fields = []
        field_pairs = [
            ("bank_name", "sc_bank_name"),
            ("bank_account", "sc_bank_account"),
            ("tax_rate", "source_tax_rate"),
            ("project_name", "source_project_name"),
        ]
        for source_field, current_field in field_pairs:
            if first_value(rows, source_field) and not clean(current.get(current_field)):
                missing_basic_fields.append(current_field)

        if not matches:
            action = "add_missing_partner_candidate"
        elif expected_role != "unknown" and current_role != expected_role:
            action = "adjust_business_role"
        elif missing_basic_fields:
            action = "fill_basic_info"
        else:
            action = "aligned"

        overlay_rows.append(
            {
                "identity_key": identity_key,
                "action": action,
                "source_name": entity["canonical_name"],
                "source_tax_no": entity["tax_no"],
                "expected_role": expected_role,
                "current_role": current_role,
                "current_partner_key": clean(current.get("partner_key")),
                "current_legacy_partner_source": clean(current.get("legacy_partner_source")),
                "current_legacy_partner_id": clean(current.get("legacy_partner_id")),
                "source_row_count": entity["row_count"],
                "source_kinds": entity["source_kinds"],
                "source_files": join_values(rows, "source_file", limit=20),
                "source_project_names": join_values(rows, "project_name", limit=50),
                "source_bank_name": first_value(rows, "bank_name"),
                "source_bank_account": first_value(rows, "bank_account"),
                "source_bank_account_name": first_value(rows, "bank_account_name") or entity["canonical_name"],
                "source_tax_rate": first_value(rows, "tax_rate"),
                "source_cooperation_types": join_values(rows, "cooperation_type"),
                "source_main_supply_types": join_values(rows, "main_supply_type"),
                "receipt_amount": entity["receipt_amount"],
                "payment_amount": entity["payment_amount"],
                "missing_basic_fields": ";".join(missing_basic_fields),
                "current_review_flags": clean(current.get("review_flags")),
            }
        )
    return overlay_rows


def summarize(overlay_rows: list[dict[str, object]], current_rows: list[dict[str, str]]) -> dict[str, object]:
    action_counts = Counter(clean(row["action"]) for row in overlay_rows)
    role_counts = Counter(clean(row["expected_role"]) for row in overlay_rows)
    return {
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "current_payload_rows": len(current_rows),
        "source_entity_rows": len(overlay_rows),
        "action_counts": dict(sorted(action_counts.items())),
        "expected_role_counts": dict(sorted(role_counts.items())),
        "missing_partner_candidates": action_counts.get("add_missing_partner_candidate", 0),
        "role_adjustment_candidates": action_counts.get("adjust_business_role", 0),
        "basic_info_fill_candidates": action_counts.get("fill_basic_info", 0),
        "aligned_rows": action_counts.get("aligned", 0),
        "db_write": False,
        "decision": "business_alignment_overlay_ready",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", default="/home/odoo/workspace/partner_import_source")
    parser.add_argument("--current-payload", default=DEFAULT_CURRENT_PAYLOAD)
    parser.add_argument("--out-dir", default="artifacts/migration/partner_business_alignment_overlay_v1")
    args = parser.parse_args()

    source_records = load_source_records(Path(args.source_root))
    current_rows = read_csv(Path(args.current_payload))
    overlay_rows = build_overlay(source_records, current_rows)
    out_dir = Path(args.out_dir)
    fieldnames = list(overlay_rows[0].keys()) if overlay_rows else []
    write_csv(out_dir / "partner_business_alignment_overlay_v1.csv", fieldnames, overlay_rows)
    write_csv(
        out_dir / "partner_business_alignment_action_queue_v1.csv",
        fieldnames,
        [row for row in overlay_rows if clean(row["action"]) != "aligned"],
    )
    summary = summarize(overlay_rows, current_rows)
    write_json(out_dir / "partner_business_alignment_summary_v1.json", summary)
    print("PARTNER_BUSINESS_ALIGNMENT_OVERLAY=" + json.dumps(summary, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
