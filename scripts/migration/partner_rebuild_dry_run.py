#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


COMPANY_CSV = Path("tmp/raw/partner/company.csv")
SUPPLIER_CSV = Path("tmp/raw/partner/supplier.csv")
OUTPUT_JSON = Path("artifacts/migration/partner_dry_run_result_v1.json")
SAFE_SLICE_CSV = Path("artifacts/migration/partner_safe_slice_v1.csv")
FULL_AUDIT_CSV = Path("artifacts/migration/partner_l4_nodb_refresh_rows_v1.csv")
NEXT_SAFE_SLICE_500_CSV = Path("artifacts/migration/partner_l4_next_safe_slice_500_v1.csv")
NEXT_SAFE_SLICE_1000_CSV = Path("artifacts/migration/partner_l4_next_safe_slice_1000_v1.csv")
WRITTEN_TARGETS = (
    Path("artifacts/migration/partner_30_row_rollback_target_list_v1.csv"),
    Path("artifacts/migration/partner_rollback_targets_v1.csv"),
    Path("artifacts/migration/partner_l4_500_pre_write_snapshot_v1.csv"),
    Path("artifacts/migration/partner_l4_500_rollback_targets_v1.csv"),
    Path("artifacts/migration/partner_l4_1000_pre_write_snapshot_v1.csv"),
    Path("artifacts/migration/partner_l4_1000_retry_rollback_targets_v1.csv"),
    Path("artifacts/migration/partner_l4_final30_rollback_targets_v1.csv"),
    Path("artifacts/migration/partner_l4_company_supplier_pair_1713_rollback_targets_v1.csv"),
    Path("artifacts/migration/partner_l4_missing_tax_single_source_1554_rollback_targets_v1.csv"),
    Path("artifacts/migration/partner_l4_remaining_missing_tax_company_supplier_652_rollback_targets_v1.csv"),
    Path("artifacts/migration/partner_l4_missing_tax_duplicate_group_175_rollback_targets_v1.csv"),
    Path("artifacts/migration/partner_l4_same_tax_company_supplier_canonical_102_rollback_targets_v1.csv"),
    Path("artifacts/migration/partner_l4_company_supplier_duplicate_26_rollback_targets_v1.csv"),
    Path("artifacts/migration/partner_l4_company_duplicate_24_rollback_targets_v1.csv"),
    Path("artifacts/migration/partner_l4_same_tax_company_canonical_20_rollback_targets_v1.csv"),
)
DISCARD_TARGETS = (
    Path("artifacts/migration/partner_l4_unsafe_name_discard_targets_v1.csv"),
    Path("artifacts/migration/partner_l4_remaining18_discard_targets_v1.csv"),
)
EXPECTED_COMPANY_ROWS = 7864
EXPECTED_SUPPLIER_ROWS = 3041
SAFE_SLICE_LIMIT = 100
NEXT_SAFE_SLICE_LIMIT = 500
EXPANDED_SAFE_SLICE_LIMIT = 1000


def clean(value: object) -> str:
    text = "" if value is None else str(value)
    text = text.replace("\u3000", " ").strip()
    return re.sub(r"\s+", " ", text)


def source_carrier(value: object) -> str:
    text = clean(value)
    return "company_supplier" if text == "company;supplier" else text


def clean_phone(value: object) -> str:
    return re.sub(r"\D+", "", clean(value))


def valid_tax(value: object) -> str:
    text = clean(value).upper()
    if not text or text in {"0", "1", "2", "3", "NULL", "NONE", "==请选择=="}:
        return ""
    return text if len(text) >= 8 else ""


def first_nonempty(*values: object) -> str:
    for value in values:
        text = clean(value)
        if text:
            return text
    return ""


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), [dict(row) for row in reader]


def company_record(row: dict[str, str]) -> dict[str, object]:
    tax_number = first_nonempty(valid_tax(row.get("SH")), valid_tax(row.get("TYSHXYDM")))
    return {
        "legacy_partner_id": clean(row.get("Id")),
        "partner_name": clean(row.get("DWMC")),
        "tax_number": tax_number,
        "phone": clean(row.get("YWLXRHM")),
        "email": clean(row.get("YWLXRYX")),
        "supplier_flag": clean(row.get("HZLX")) == "材料" or clean(row.get("DWLX")) == "是",
        "customer_flag": True,
        "source": "company",
        "source_table": "T_Base_CooperatCompany",
        "source_code": first_nonempty(row.get("OTHER_SYSTEM_CODE"), row.get("DJBH"), row.get("DWID")),
    }


def supplier_record(row: dict[str, str]) -> dict[str, object]:
    tax_number = first_nonempty(valid_tax(row.get("SH")), valid_tax(row.get("SHXYDM")), valid_tax(row.get("NSRSBH")), valid_tax(row.get("TISHXYDM")))
    return {
        "legacy_partner_id": clean(row.get("ID")),
        "partner_name": clean(row.get("f_SupplierName")),
        "tax_number": tax_number,
        "phone": clean(row.get("f_Phone")),
        "email": clean(row.get("f_Email")),
        "supplier_flag": True,
        "customer_flag": False,
        "source": "supplier",
        "source_table": "T_Base_SupplierInfo",
        "source_code": first_nonempty(row.get("f_SupplierCode"), row.get("GYSBM"), row.get("DJBH")),
    }


def dedup_key(record: dict[str, object]) -> tuple[str, str]:
    tax_number = clean(record.get("tax_number"))
    name = clean(record.get("partner_name"))
    phone = clean_phone(record.get("phone"))
    if tax_number:
        return ("tax_number", tax_number)
    if name and phone:
        return ("name_phone", f"{name}|{phone}")
    if name:
        return ("exact_name", name)
    return ("missing_identity", clean(record.get("legacy_partner_id")))


def safe_name(value: object) -> bool:
    text = clean(value)
    if len(text) < 4:
        return False
    if text.isdigit():
        return False
    if text in {"==请选择==", "请选择", "无", "测试"}:
        return False
    return True


def merged_row(key_type: str, key: str, rows: list[dict[str, object]]) -> dict[str, object]:
    first = rows[0]
    names = sorted({clean(row.get("partner_name")) for row in rows if clean(row.get("partner_name"))})
    tax_numbers = sorted({clean(row.get("tax_number")) for row in rows if clean(row.get("tax_number"))})
    phones = sorted({clean_phone(row.get("phone")) for row in rows if clean_phone(row.get("phone"))})
    emails = sorted({clean(row.get("email")).lower() for row in rows if clean(row.get("email"))})
    sources = sorted({clean(row.get("source")) for row in rows if clean(row.get("source"))})
    legacy_ids = sorted({clean(row.get("legacy_partner_id")) for row in rows if clean(row.get("legacy_partner_id"))})
    source_codes = sorted({clean(row.get("source_code")) for row in rows if clean(row.get("source_code"))})
    conflicts = []
    if key_type == "tax_number" and len(names) > 1:
        conflicts.append("same_tax_multiple_names")
    if len(tax_numbers) > 1:
        conflicts.append("multiple_tax_numbers")
    if not names:
        conflicts.append("missing_partner_name")
    if not legacy_ids:
        conflicts.append("missing_legacy_partner_id")
    return {
        "dedup_key_type": key_type,
        "dedup_key": key,
        "legacy_partner_id": clean(first.get("legacy_partner_id")),
        "legacy_partner_ids": legacy_ids,
        "partner_name": names[0] if names else "",
        "tax_number": tax_numbers[0] if tax_numbers else "",
        "phone": phones[0] if phones else "",
        "email": emails[0] if emails else "",
        "supplier_flag": any(bool(row.get("supplier_flag")) for row in rows),
        "customer_flag": any(bool(row.get("customer_flag")) for row in rows),
        "sources": sources,
        "source_codes": source_codes,
        "source_row_count": len(rows),
        "merge_strategy": "merge_by_" + key_type if len(rows) > 1 else "create_single",
        "conflicts": conflicts,
    }


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def read_partner_keys(paths: tuple[Path, ...]) -> set[tuple[str, str]]:
    keys: set[tuple[str, str]] = set()
    for path in paths:
        if not path.exists():
            continue
        _, rows = read_csv(path)
        for row in rows:
            source = source_carrier(row.get("legacy_partner_source"))
            legacy_id = clean(row.get("legacy_partner_id"))
            if source and legacy_id:
                keys.add((source, legacy_id))
    return keys


def serialize(value: object) -> str:
    if isinstance(value, list):
        return ";".join(clean(item) for item in value)
    return clean(value)


def is_primary_company_row(row: dict[str, object]) -> bool:
    return row.get("sources") == ["company"]


def audit_legacy_source(row: dict[str, object]) -> str:
    return "cooperat_company" if is_primary_company_row(row) else source_carrier(serialize(row["sources"]))


def audit_identity_key(row: dict[str, object]) -> tuple[str, str]:
    return (audit_legacy_source(row), clean(row["legacy_partner_id"]))


def row_blockers(
    row: dict[str, object],
    written_keys: set[tuple[str, str]],
    discard_keys: set[tuple[str, str]],
) -> list[str]:
    blockers = [clean(item) for item in row["conflicts"]]
    if not clean(row["legacy_partner_id"]):
        blockers.append("missing_legacy_partner_id")
    if not safe_name(row["partner_name"]):
        blockers.append("unsafe_partner_name")
    if not clean(row["tax_number"]):
        blockers.append("missing_tax_number")
    if row["dedup_key_type"] == "missing_identity":
        blockers.append("missing_identity_key")
    if row["source_row_count"] != 1:
        blockers.append("deduplicated_group_not_create_only")
    if not is_primary_company_row(row):
        blockers.append("non_primary_partner_source")
    if ("cooperat_company", clean(row["legacy_partner_id"])) in written_keys or audit_identity_key(row) in written_keys:
        blockers.append("already_written_validation")
    if audit_identity_key(row) in discard_keys:
        blockers.append("discarded_by_policy_validation")
    return blockers


def action_for_row(row: dict[str, object], blockers: list[str]) -> str:
    if "discarded_by_policy_validation" in blockers:
        return "discarded_validation"
    if "already_written_validation" in blockers:
        return "skip_existing_validation"
    if blockers:
        return "blocked"
    return "create_candidate"


def main() -> int:
    company_columns, company_rows = read_csv(COMPANY_CSV)
    supplier_columns, supplier_rows = read_csv(SUPPLIER_CSV)
    written_keys = read_partner_keys(WRITTEN_TARGETS)
    discard_keys = read_partner_keys(DISCARD_TARGETS)
    missing_fields = []
    for field in ["Id", "DWMC"]:
        if field not in company_columns:
            missing_fields.append(f"company.{field}")
    for field in ["ID", "f_SupplierName"]:
        if field not in supplier_columns:
            missing_fields.append(f"supplier.{field}")

    records = [company_record(row) for row in company_rows] + [supplier_record(row) for row in supplier_rows]
    groups: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for record in records:
        groups[dedup_key(record)].append(record)

    merged = [merged_row(key_type, key, rows) for (key_type, key), rows in sorted(groups.items())]
    conflict_rows = [row for row in merged if row["conflicts"]]
    duplicate_groups = [row for row in merged if row["source_row_count"] > 1]
    create_ready_rows = [row for row in merged if not row["conflicts"]]
    audit_rows = []
    next_safe_candidates = []
    for row_no, row in enumerate(merged, start=1):
        blockers = row_blockers(row, written_keys, discard_keys)
        action = action_for_row(row, blockers)
        audit_row = {
            "row_no": row_no,
            "legacy_partner_source": audit_legacy_source(row),
            "legacy_partner_id": clean(row["legacy_partner_id"]),
            "partner_name": clean(row["partner_name"]),
            "tax_number": clean(row["tax_number"]),
            "phone": clean(row["phone"]),
            "email": clean(row["email"]),
            "supplier_flag": serialize(row["supplier_flag"]),
            "customer_flag": serialize(row["customer_flag"]),
            "dedup_key_type": clean(row["dedup_key_type"]),
            "dedup_key": clean(row["dedup_key"]),
            "sources": serialize(row["sources"]),
            "source_codes": serialize(row["source_codes"]),
            "source_row_count": clean(row["source_row_count"]),
            "merge_strategy": clean(row["merge_strategy"]),
            "dry_run_action": action,
            "blockers": ";".join(blockers),
        }
        audit_rows.append(audit_row)
        if action == "create_candidate":
            next_safe_candidates.append(row)

    safe_slice = next_safe_candidates[:SAFE_SLICE_LIMIT]
    next_safe_slice_500 = next_safe_candidates[:NEXT_SAFE_SLICE_LIMIT]
    next_safe_slice_1000 = next_safe_candidates[:EXPANDED_SAFE_SLICE_LIMIT]

    fieldnames = [
        "legacy_partner_source",
        "legacy_partner_id",
        "partner_name",
        "tax_number",
        "phone",
        "email",
        "supplier_flag",
        "customer_flag",
        "dedup_key_type",
        "dedup_key",
        "sources",
        "source_codes",
        "merge_strategy",
        "dry_run_action",
        "blockers",
    ]

    audit_fieldnames = [
        "row_no",
        "legacy_partner_source",
        "legacy_partner_id",
        "partner_name",
        "tax_number",
        "phone",
        "email",
        "supplier_flag",
        "customer_flag",
        "dedup_key_type",
        "dedup_key",
        "sources",
        "source_codes",
        "source_row_count",
        "merge_strategy",
        "dry_run_action",
        "blockers",
    ]
    write_csv(FULL_AUDIT_CSV, audit_fieldnames, audit_rows)

    def output_slice_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
        output = []
        for row in rows:
            output.append(
                {
                    "legacy_partner_source": "cooperat_company",
                    "legacy_partner_id": clean(row["legacy_partner_id"]),
                    "partner_name": clean(row["partner_name"]),
                    "tax_number": clean(row["tax_number"]),
                    "phone": clean(row["phone"]),
                    "email": clean(row["email"]),
                    "supplier_flag": serialize(row["supplier_flag"]),
                    "customer_flag": serialize(row["customer_flag"]),
                    "dedup_key_type": clean(row["dedup_key_type"]),
                    "dedup_key": clean(row["dedup_key"]),
                    "sources": serialize(row["sources"]),
                    "source_codes": serialize(row["source_codes"]),
                    "merge_strategy": clean(row["merge_strategy"]),
                    "dry_run_action": "create_candidate",
                    "blockers": "",
                }
            )
        return output

    write_csv(
        SAFE_SLICE_CSV,
        fieldnames,
        output_slice_rows(safe_slice),
    )
    write_csv(NEXT_SAFE_SLICE_500_CSV, fieldnames, output_slice_rows(next_safe_slice_500))
    write_csv(NEXT_SAFE_SLICE_1000_CSV, fieldnames, output_slice_rows(next_safe_slice_1000))

    key_counts = Counter(row["dedup_key_type"] for row in merged)
    merge_counts = Counter(row["merge_strategy"] for row in merged)
    action_counts = Counter(row["dry_run_action"] for row in audit_rows)
    blocker_counts = Counter(
        blocker
        for row in audit_rows
        for blocker in str(row["blockers"]).split(";")
        if blocker
    )
    result = {
        "status": "PASS" if not missing_fields else "FAIL",
        "mode": "partner_l4_nodb_refresh",
        "inputs": {
            "company": str(COMPANY_CSV),
            "supplier": str(SUPPLIER_CSV),
        },
        "total": len(company_rows),
        "source_rows": {
            "company": len(company_rows),
            "supplier": len(supplier_rows),
            "combined": len(records),
        },
        "deduplicated": len(merged),
        "to_create": len(create_ready_rows),
        "to_merge": len(duplicate_groups),
        "written_validation_identity_count": len(written_keys),
        "discard_validation_identity_count": len(discard_keys),
        "action_counts": dict(sorted(action_counts.items())),
        "blocker_counts": dict(sorted(blocker_counts.items())),
        "missing_fields": missing_fields,
        "conflicts": conflict_rows[:200],
        "conflict_count": len(conflict_rows),
        "duplicate_groups": duplicate_groups[:200],
        "duplicate_group_count": len(duplicate_groups),
        "dedup_key_counts": dict(sorted(key_counts.items())),
        "merge_strategy": {
            "priority": ["tax_number", "name_phone", "exact_name"],
            "counts": dict(sorted(merge_counts.items())),
        },
        "safe_slice": {
            "path": str(SAFE_SLICE_CSV),
            "rows": len(safe_slice),
            "requirements": ["company source only", "not already written", "no duplicate group", "no conflicts", "legacy_partner_id present", "partner_name present", "tax_number present"],
        },
        "full_audit": {
            "path": str(FULL_AUDIT_CSV),
            "rows": len(audit_rows),
        },
        "next_safe_slice": {
            "path": str(NEXT_SAFE_SLICE_500_CSV),
            "rows": len(next_safe_slice_500),
            "limit": NEXT_SAFE_SLICE_LIMIT,
        },
        "expanded_next_safe_slice": {
            "path": str(NEXT_SAFE_SLICE_1000_CSV),
            "rows": len(next_safe_slice_1000),
            "limit": EXPANDED_SAFE_SLICE_LIMIT,
        },
        "promotion_level": "L4 candidate no-DB refresh",
        "next_gate": "L3 expanded create-only write gate; no DB write authorized by this result",
    }
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("PARTNER_REBUILD_DRY_RUN=" + json.dumps({
        "status": result["status"],
        "total": result["total"],
        "deduplicated": result["deduplicated"],
        "to_create": result["to_create"],
        "to_merge": result["to_merge"],
        "conflict_count": result["conflict_count"],
        "skip_existing_validation": result["action_counts"].get("skip_existing_validation", 0),
        "discarded_validation": result["action_counts"].get("discarded_validation", 0),
        "safe_slice_rows": result["safe_slice"]["rows"],
        "next_safe_slice_rows": result["next_safe_slice"]["rows"],
        "expanded_next_safe_slice_rows": result["expanded_next_safe_slice"]["rows"],
    }, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
