#!/usr/bin/env python3
"""Generate the business-aligned partner rebuild payload.

The existing rebuild flow already has a payload contract. This adapter keeps
that contract and refreshes the rows from the user's full mixed partner source.
It performs no database writes.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
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

PAYLOAD_FIELDS = [
    "partner_key",
    "legacy_partner_source",
    "legacy_partner_id",
    "legacy_partner_ids",
    "name",
    "company_type",
    "customer_rank",
    "supplier_rank",
    "sc_supplier_type",
    "sc_account_name",
    "sc_bank_name",
    "sc_bank_account",
    "vat",
    "legacy_credit_code",
    "source_created_by",
    "source_created_at",
    "source_project_name",
    "source_document_state",
    "source_push_result",
    "source_tax_rate",
    "source_files",
    "legacy_source_evidence",
    "review_flags",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


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


def first_value(rows: list[dict[str, str]], field: str) -> str:
    values = [clean(row.get(field)) for row in rows if clean(row.get(field))]
    return Counter(values).most_common(1)[0][0] if values else ""


def join_values(rows: list[dict[str, str]], field: str, limit: int = 50) -> str:
    return ";".join(sorted({clean(row.get(field)) for row in rows if clean(row.get(field))})[:limit])


def supplier_type(rows: list[dict[str, str]]) -> str:
    text = ";".join(
        clean(row.get("cooperation_type") or row.get("main_supply_type") or row.get("category_label"))
        for row in rows
    )
    if "劳务" in text:
        return "labor"
    if "分包" in text:
        return "subcontract"
    if "设备" in text:
        return "equipment"
    if "材料" in text:
        return "material"
    return "other"


def partner_key_for(identity_key: str) -> str:
    if identity_key.startswith("tax:"):
        return "credit:" + identity_key.split(":", 1)[1]
    return identity_key


def is_valid_bank_account(value: object) -> bool:
    text = re.sub(r"\s+", "", clean(value))
    if not text or text in {"0", "1", ".", "/", "无", "无开户行"}:
        return False
    return bool(re.search(r"\d{6,}", text))


def build_payload_rows(source_records: list[dict[str, str]], current_rows: list[dict[str, str]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for record in source_records:
        grouped[identity_for(record)].append(record)
    entity_by_key = {clean(row["identity_key"]): row for row in build_entity_rows(source_records)}

    current_by_key: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in current_rows:
        for key in current_keys(row):
            current_by_key[key].append(row)

    payload_rows: list[dict[str, object]] = []
    matched_current_row_ids: set[int] = set()
    for identity_key, rows in sorted(grouped.items()):
        entity = entity_by_key[identity_key]
        matches = current_by_key.get(identity_key, [])
        if not matches and identity_key.startswith("tax:"):
            matches = current_by_key.get("name:" + norm_name(entity.get("canonical_name")), [])
        if matches:
            matched_current_row_ids.add(id(matches[0]))

        role = clean(entity.get("target_role"))
        customer_rank = 1 if role in {"customer", "customer_and_supplier"} else 0
        supplier_rank = 1 if role in {"supplier", "customer_and_supplier"} else 0
        name = norm_name(entity.get("canonical_name"))
        tax_no = norm_tax(entity.get("tax_no"))
        bank_account = first_value(rows, "bank_account")
        review_flags = set()
        if role == "unknown":
            review_flags.add("unknown_business_role")
        if not tax_no:
            review_flags.add("missing_credit_code")
        if clean(entity.get("personal_fragment")) == "1":
            review_flags.add("personal_fragment_review")
        if bank_account and not is_valid_bank_account(bank_account):
            review_flags.add("invalid_bank_account_review")
        if len(matches) > 1:
            review_flags.add("multiple_current_payload_matches")
        for match in matches[:1]:
            for flag in clean(match.get("review_flags")).split(";"):
                if flag:
                    review_flags.add(flag)

        payload_rows.append(
            {
                "partner_key": partner_key_for(identity_key),
                "legacy_partner_source": "xlsx_business_aligned_partner",
                "legacy_partner_id": identity_key,
                "legacy_partner_ids": "",
                "name": name,
                "company_type": "person" if clean(entity.get("personal_fragment")) == "1" else "company",
                "customer_rank": customer_rank,
                "supplier_rank": supplier_rank,
                "sc_supplier_type": supplier_type(rows),
                "sc_account_name": first_value(rows, "bank_account_name") or name,
                "sc_bank_name": first_value(rows, "bank_name"),
                "sc_bank_account": bank_account,
                "vat": tax_no,
                "legacy_credit_code": tax_no,
                "source_created_by": first_value(rows, "source_operator"),
                "source_created_at": first_value(rows, "source_time"),
                "source_project_name": join_values(rows, "project_name"),
                "source_document_state": join_values(rows, "document_state"),
                "source_push_result": join_values(rows, "push_result"),
                "source_tax_rate": first_value(rows, "tax_rate"),
                "source_files": join_values(rows, "source_file"),
                "legacy_source_evidence": "partner_import_source_business_aligned:" + identity_key,
                "review_flags": ";".join(sorted(review_flags)),
            }
        )

    current_only_rows: list[dict[str, object]] = []
    source_identity_keys = set(grouped)
    source_name_keys = {"name:" + norm_name(row.get("canonical_name")) for row in entity_by_key.values()}
    source_tax_keys = {"tax:" + norm_tax(row.get("tax_no")) for row in entity_by_key.values() if norm_tax(row.get("tax_no"))}
    source_keys = source_identity_keys | source_name_keys | source_tax_keys
    for row in current_rows:
        if current_keys(row) & source_keys:
            continue
        current_only_rows.append({**row, "review_reason": "current_payload_row_not_found_in_business_source"})
    return payload_rows, current_only_rows


def summarize(payload_rows: list[dict[str, object]], current_rows: list[dict[str, str]], current_only_rows: list[dict[str, object]]) -> dict[str, object]:
    role_counts = Counter()
    review_counts = Counter()
    for row in payload_rows:
        customer = clean(row["customer_rank"]) == "1"
        supplier = clean(row["supplier_rank"]) == "1"
        if customer and supplier:
            role_counts["customer_and_supplier"] += 1
        elif customer:
            role_counts["customer"] += 1
        elif supplier:
            role_counts["supplier"] += 1
        else:
            role_counts["unknown"] += 1
        for flag in clean(row["review_flags"]).split(";"):
            if flag:
                review_counts[flag] += 1
    return {
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "mode": "partner_business_aligned_rebuild_adapter",
        "source": "/home/odoo/workspace/partner_import_source",
        "current_payload_rows": len(current_rows),
        "business_aligned_payload_rows": len(payload_rows),
        "current_only_review_rows": len(current_only_rows),
        "role_counts": dict(sorted(role_counts.items())),
        "review_flag_counts": dict(sorted(review_counts.items())),
        "rows_with_bank_account": sum(1 for row in payload_rows if clean(row["sc_bank_account"])),
        "rows_with_bank_name": sum(1 for row in payload_rows if clean(row["sc_bank_name"])),
        "rows_with_credit_code": sum(1 for row in payload_rows if clean(row["vat"])),
        "db_write": False,
        "decision": "business_aligned_partner_payload_ready",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", default="/home/odoo/workspace/partner_import_source")
    parser.add_argument("--current-payload", default=DEFAULT_CURRENT_PAYLOAD)
    parser.add_argument("--out-dir", default="artifacts/migration/partner_business_aligned_rebuild_v1")
    args = parser.parse_args()

    source_records = load_source_records(Path(args.source_root))
    current_rows = read_csv(Path(args.current_payload))
    payload_rows, current_only_rows = build_payload_rows(source_records, current_rows)
    out_dir = Path(args.out_dir)
    write_csv(out_dir / "fact_based_partner_rebuild_payload_business_aligned_v1.csv", PAYLOAD_FIELDS, payload_rows)
    write_csv(
        out_dir / "fact_based_partner_rebuild_current_only_review_v1.csv",
        list(current_only_rows[0].keys()) if current_only_rows else PAYLOAD_FIELDS + ["review_reason"],
        current_only_rows,
    )
    summary = summarize(payload_rows, current_rows, current_only_rows)
    write_json(out_dir / "fact_based_partner_rebuild_business_aligned_result_v1.json", summary)
    print("PARTNER_BUSINESS_ALIGNED_REBUILD=" + json.dumps(summary, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
