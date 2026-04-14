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
EXPECTED_COMPANY_ROWS = 7864
EXPECTED_SUPPLIER_ROWS = 3041
SAFE_SLICE_LIMIT = 100


def clean(value: object) -> str:
    text = "" if value is None else str(value)
    text = text.replace("\u3000", " ").strip()
    return re.sub(r"\s+", " ", text)


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


def main() -> int:
    company_columns, company_rows = read_csv(COMPANY_CSV)
    supplier_columns, supplier_rows = read_csv(SUPPLIER_CSV)
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
    safe_slice = [
        row for row in merged
        if not row["conflicts"]
        and row["source_row_count"] == 1
        and row["legacy_partner_id"]
        and safe_name(row["partner_name"])
        and row["tax_number"]
        and row["dedup_key_type"] != "missing_identity"
    ][:SAFE_SLICE_LIMIT]

    fieldnames = [
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
    ]
    write_csv(
        SAFE_SLICE_CSV,
        fieldnames,
        [
            {key: ";".join(value) if isinstance(value, list) else value for key, value in row.items() if key in fieldnames}
            for row in safe_slice
        ],
    )

    key_counts = Counter(row["dedup_key_type"] for row in merged)
    merge_counts = Counter(row["merge_strategy"] for row in merged)
    result = {
        "status": "PASS" if not missing_fields else "FAIL",
        "mode": "partner_rebuild_l1_no_db_dry_run",
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
            "requirements": ["no duplicate group", "no conflicts", "legacy_partner_id present", "partner_name present", "tax_number present"],
        },
        "promotion_level": "L1 dry-run",
        "next_gate": "L2 safe-slice review; no DB write authorized by this result",
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
        "safe_slice_rows": result["safe_slice"]["rows"],
    }, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
