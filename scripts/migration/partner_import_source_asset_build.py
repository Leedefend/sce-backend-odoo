#!/usr/bin/env python3
"""Build a no-DB normalized partner asset from the user Excel source."""

from __future__ import annotations

import argparse
import csv
import hashlib
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


def stable_external_id(identity_key: str) -> str:
    digest = hashlib.sha1(identity_key.encode("utf-8")).hexdigest()[:16]
    return f"legacy_partner_import_source_{digest}"


def first_value(rows: list[dict[str, str]], field: str) -> str:
    values = [clean(row.get(field)) for row in rows if clean(row.get(field))]
    if not values:
        return ""
    return Counter(values).most_common(1)[0][0]


def joined_values(rows: list[dict[str, str]], field: str, limit: int = 20) -> str:
    values = sorted({clean(row.get(field)) for row in rows if clean(row.get(field))})
    return ";".join(values[:limit])


def role_status(entity: dict[str, object]) -> str:
    role = clean(entity.get("target_role"))
    if role == "customer_and_supplier":
        return "mixed_role_review"
    if role == "unknown":
        return "unknown_role_review"
    if int(entity.get("personal_fragment") or 0):
        return "personal_fragment_review"
    if not clean(entity.get("tax_no")):
        return "missing_tax_review"
    return "loadable"


def build_asset_rows(source_records: list[dict[str, str]]) -> list[dict[str, object]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for record in source_records:
        grouped[identity_for(record)].append(record)

    entity_by_key = {clean(row["identity_key"]): row for row in build_entity_rows(source_records)}
    rows: list[dict[str, object]] = []
    for identity_key, records in sorted(grouped.items()):
        entity = entity_by_key[identity_key]
        role = clean(entity["target_role"])
        supplier_rank = 1 if role in {"supplier", "customer_and_supplier"} else 0
        customer_rank = 1 if role in {"customer", "customer_and_supplier"} else 0
        tax_no = norm_tax(entity.get("tax_no"))
        name = norm_name(entity.get("canonical_name"))
        rows.append(
            {
                "external_id": stable_external_id(identity_key),
                "legacy_identity_key": identity_key,
                "legacy_partner_source": "partner_import_source",
                "legacy_partner_key": identity_key.split(":", 1)[1] if ":" in identity_key else identity_key,
                "asset_status": role_status(entity),
                "target_role": role,
                "name": name,
                "is_company": 0 if int(entity.get("personal_fragment") or 0) else 1,
                "vat": tax_no,
                "customer_rank": customer_rank,
                "supplier_rank": supplier_rank,
                "bank_name": first_value(records, "bank_name"),
                "bank_account": first_value(records, "bank_account"),
                "bank_account_name": first_value(records, "bank_account_name") or name,
                "tax_rate": first_value(records, "tax_rate"),
                "region": first_value(records, "region"),
                "address": first_value(records, "address"),
                "cooperation_types": joined_values(records, "cooperation_type"),
                "main_supply_types": joined_values(records, "main_supply_type"),
                "category_labels": joined_values(records, "category_label"),
                "project_names": joined_values(records, "project_name", limit=50),
                "source_kinds": entity["source_kinds"],
                "source_row_count": entity["row_count"],
                "source_files": joined_values(records, "source_file", limit=20),
                "receipt_amount": entity["receipt_amount"],
                "payment_amount": entity["payment_amount"],
                "has_tax_no": 1 if tax_no else 0,
                "has_bank_account": entity["has_bank_account"],
                "has_region": entity["has_region"],
                "has_address": entity["has_address"],
            }
        )
    return rows


def summarize(rows: list[dict[str, object]]) -> dict[str, object]:
    status_counts = Counter(clean(row["asset_status"]) for row in rows)
    role_counts = Counter(clean(row["target_role"]) for row in rows)
    return {
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "asset_rows": len(rows),
        "asset_status_counts": dict(sorted(status_counts.items())),
        "target_role_counts": dict(sorted(role_counts.items())),
        "loadable_rows": status_counts.get("loadable", 0),
        "review_rows": len(rows) - status_counts.get("loadable", 0),
        "rows_with_bank_account": sum(1 for row in rows if clean(row["bank_account"])),
        "rows_with_bank_name": sum(1 for row in rows if clean(row["bank_name"])),
        "rows_with_tax_no": sum(1 for row in rows if clean(row["vat"])),
        "rows_without_tax_no": sum(1 for row in rows if not clean(row["vat"])),
        "db_write": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", default="/home/odoo/workspace/partner_import_source")
    parser.add_argument("--out-dir", default="artifacts/migration/partner_import_source_asset_v1")
    args = parser.parse_args()

    source_records = load_source_records(Path(args.source_root))
    asset_rows = build_asset_rows(source_records)
    out_dir = Path(args.out_dir)
    fieldnames = list(asset_rows[0].keys()) if asset_rows else []
    write_csv(out_dir / "partner_master_source_v1.csv", fieldnames, asset_rows)
    write_json(out_dir / "partner_master_source_summary_v1.json", summarize(asset_rows))
    write_csv(
        out_dir / "partner_master_review_queue_v1.csv",
        fieldnames,
        [row for row in asset_rows if clean(row["asset_status"]) != "loadable"],
    )
    print("PARTNER_IMPORT_SOURCE_ASSET=" + json.dumps(summarize(asset_rows), ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
