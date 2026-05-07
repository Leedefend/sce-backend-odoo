#!/usr/bin/env python3
"""Audit partner Excel sources against the current partner replay payload."""

from __future__ import annotations

import argparse
import csv
import json
import re
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from zipfile import ZipFile


SHEET_NS = {
    "a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}

ENTERPRISE_HINTS = (
    "公司",
    "有限",
    "集团",
    "合作社",
    "经营部",
    "商贸",
    "建材",
    "工程",
    "中心",
    "厂",
    "店",
    "银行",
    "局",
    "院",
    "学校",
)
INVALID_TAX_VALUES = {"", "/", "0", "1", "无", "null", "NULL", "None"}


def clean(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def norm_space(value: object) -> str:
    return re.sub(r"\s+", "", clean(value))


def norm_name(value: object) -> str:
    text = norm_space(value)
    text = re.sub(r"^(称|名称|单位名称)[:：]+", "", text)
    return text


def norm_tax(value: object) -> str:
    text = norm_space(value).upper()
    return "" if text in INVALID_TAX_VALUES else text


def parse_amount(value: object) -> float:
    text = clean(value).replace(",", "")
    if not text:
        return 0.0
    try:
        return float(text)
    except ValueError:
        return 0.0


def classify_file(path: Path) -> str:
    name = path.name
    if "供应商_合作单位" in name:
        return "supplier_registry"
    if "费用单位" in name:
        return "expense_unit_registry"
    if "往来单位" in name:
        return "counterparty_flow"
    return "unknown"


def column_index(cell_ref: str) -> int:
    match = re.match(r"([A-Z]+)", cell_ref or "")
    letters = match.group(1) if match else ""
    result = 0
    for letter in letters:
        result = result * 26 + ord(letter) - ord("A") + 1
    return result - 1


def read_shared_strings(book: ZipFile) -> list[str]:
    try:
        data = book.read("xl/sharedStrings.xml")
    except KeyError:
        return []
    root = ET.fromstring(data)
    values: list[str] = []
    for item in root.findall("a:si", SHEET_NS):
        values.append("".join(part.text or "" for part in item.findall(".//a:t", SHEET_NS)))
    return values


def cell_value(cell: ET.Element, shared_strings: list[str]) -> str:
    cell_type = cell.attrib.get("t")
    if cell_type == "inlineStr":
        return clean("".join(part.text or "" for part in cell.findall(".//a:t", SHEET_NS)))
    value = cell.find("a:v", SHEET_NS)
    if value is None:
        return ""
    raw = value.text or ""
    if cell_type == "s":
        try:
            return clean(shared_strings[int(raw)])
        except (IndexError, ValueError):
            return clean(raw)
    return clean(raw)


def read_xlsx_rows(path: Path) -> list[dict[str, str]]:
    with ZipFile(path) as book:
        shared_strings = read_shared_strings(book)
        sheet = ET.fromstring(book.read("xl/worksheets/sheet1.xml"))
        raw_rows: list[list[str]] = []
        for row in sheet.findall(".//a:sheetData/a:row", SHEET_NS):
            values: list[str] = []
            for cell in row.findall("a:c", SHEET_NS):
                index = column_index(cell.attrib.get("r", ""))
                while len(values) <= index:
                    values.append("")
                values[index] = cell_value(cell, shared_strings)
            if any(values):
                raw_rows.append(values)
    if not raw_rows:
        return []
    headers = [clean(item) for item in raw_rows[0]]
    rows: list[dict[str, str]] = []
    for raw in raw_rows[1:]:
        row = {}
        for index, header in enumerate(headers):
            if header:
                row[header] = raw[index] if index < len(raw) else ""
        if any(clean(value) for value in row.values()):
            rows.append(row)
    return rows


def pick(row: dict[str, str], *headers: str) -> str:
    for header in headers:
        value = clean(row.get(header))
        if value:
            return value
    return ""


def identity_for(row: dict[str, str]) -> str:
    tax = norm_tax(row.get("tax_no"))
    name = norm_name(row.get("name"))
    if tax:
        return f"tax:{tax}"
    return f"name:{name}"


def looks_personal(name: str, tax_no: str) -> bool:
    if tax_no:
        return False
    if any(hint in name for hint in ENTERPRISE_HINTS):
        return False
    return 1 <= len(name) <= 4


def source_record(path: Path, source_root: Path, row: dict[str, str], row_number: int) -> dict[str, str]:
    file_kind = classify_file(path)
    receipt_amount = parse_amount(row.get("收款金额"))
    payment_amount = parse_amount(row.get("付款金额"))
    category = pick(row, "合作类型", "分类标签", "主供类型", "信息来源")
    name = norm_name(pick(row, "单位名称", "开户姓名"))
    tax_no = norm_tax(pick(row, "统一社会信用代码", "税号", "纳税人识别号"))
    supplier_hint = file_kind == "supplier_registry" or payment_amount > 0 or bool(pick(row, "单位编号"))
    customer_hint = receipt_amount > 0 or "甲方" in category
    return {
        "source_file": str(path.relative_to(source_root)),
        "source_kind": file_kind,
        "row_number": str(row_number),
        "document_state": pick(row, "单据状态"),
        "push_result": pick(row, "推送结果"),
        "project_name": pick(row, "项目名称"),
        "partner_code": pick(row, "单位编号"),
        "name": name,
        "short_name": pick(row, "单位简称"),
        "tax_no": tax_no,
        "cooperation_type": pick(row, "合作类型"),
        "main_supply_type": pick(row, "主供类型"),
        "category_label": pick(row, "分类标签"),
        "bank_name": pick(row, "开户银行"),
        "bank_account": pick(row, "账号", "开户账号", "银行账号"),
        "bank_account_name": pick(row, "开户姓名"),
        "receipt_amount": f"{receipt_amount:.2f}" if receipt_amount else "",
        "payment_amount": f"{payment_amount:.2f}" if payment_amount else "",
        "tax_rate": pick(row, "主税率"),
        "region": pick(row, "地区名称"),
        "address": pick(row, "详细地址"),
        "register_capital": pick(row, "注册资本"),
        "business_scope": pick(row, "经营范围"),
        "source_operator": pick(row, "录入人", "登记人"),
        "source_time": pick(row, "录入时间", "登记日期"),
        "supplier_hint": "1" if supplier_hint else "0",
        "customer_hint": "1" if customer_hint else "0",
        "personal_fragment": "1" if looks_personal(name, tax_no) else "0",
    }


def load_source_records(source_root: Path) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    for path in sorted(source_root.rglob("*.xlsx")):
        for index, row in enumerate(read_xlsx_rows(path), start=2):
            record = source_record(path, source_root, row, index)
            if record["name"]:
                records.append(record)
    return records


def load_payload_records(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
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
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_entity_rows(records: list[dict[str, str]]) -> list[dict[str, object]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for record in records:
        grouped[identity_for(record)].append(record)
    rows: list[dict[str, object]] = []
    for key, items in sorted(grouped.items()):
        names = sorted({item["name"] for item in items if item["name"]})
        tax_values = sorted({item["tax_no"] for item in items if item["tax_no"]})
        source_kinds = sorted({item["source_kind"] for item in items})
        supplier_hint = any(item["supplier_hint"] == "1" for item in items)
        customer_hint = any(item["customer_hint"] == "1" for item in items)
        if supplier_hint and customer_hint:
            target_role = "customer_and_supplier"
        elif customer_hint:
            target_role = "customer"
        elif supplier_hint:
            target_role = "supplier"
        else:
            target_role = "unknown"
        rows.append(
            {
                "identity_key": key,
                "canonical_name": names[0] if names else "",
                "name_count": len(names),
                "tax_no": tax_values[0] if tax_values else "",
                "row_count": len(items),
                "source_kinds": ";".join(source_kinds),
                "project_count": len({item["project_name"] for item in items if item["project_name"]}),
                "has_bank_name": int(any(item["bank_name"] for item in items)),
                "has_bank_account": int(any(item["bank_account"] for item in items)),
                "has_tax_rate": int(any(item["tax_rate"] for item in items)),
                "has_region": int(any(item["region"] for item in items)),
                "has_address": int(any(item["address"] for item in items)),
                "has_business_scope": int(any(item["business_scope"] for item in items)),
                "receipt_amount": round(sum(parse_amount(item["receipt_amount"]) for item in items), 2),
                "payment_amount": round(sum(parse_amount(item["payment_amount"]) for item in items), 2),
                "supplier_hint": int(supplier_hint),
                "customer_hint": int(customer_hint),
                "target_role": target_role,
                "personal_fragment": int(any(item["personal_fragment"] == "1" for item in items)),
                "sample_files": ";".join(sorted({item["source_file"] for item in items})[:5]),
            }
        )
    return rows


def summarize(records: list[dict[str, str]], entity_rows: list[dict[str, object]], payload_rows: list[dict[str, str]]) -> dict[str, object]:
    payload_names = {norm_name(row.get("name")) for row in payload_rows if norm_name(row.get("name"))}
    payload_tax = {norm_tax(row.get("tax_no")) for row in payload_rows if norm_tax(row.get("tax_no"))}
    source_names = {norm_name(row.get("name")) for row in records if norm_name(row.get("name"))}
    source_tax = {norm_tax(row.get("tax_no")) for row in records if norm_tax(row.get("tax_no"))}
    source_by_kind = Counter(row["source_kind"] for row in records)
    entity_role_counts = Counter(clean(row["target_role"]) for row in entity_rows)
    payload_source_counts = Counter(clean(row.get("legacy_partner_source")) for row in payload_rows)
    return {
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "source_rows": len(records),
        "source_rows_by_kind": dict(sorted(source_by_kind.items())),
        "source_entity_count": len(entity_rows),
        "source_entity_roles": dict(sorted(entity_role_counts.items())),
        "source_entities_with_tax": sum(1 for row in entity_rows if row["tax_no"]),
        "source_entities_without_tax": sum(1 for row in entity_rows if not row["tax_no"]),
        "source_personal_fragments": sum(int(row["personal_fragment"]) for row in entity_rows),
        "source_entities_with_bank_account": sum(int(row["has_bank_account"]) for row in entity_rows),
        "source_entities_with_bank_name": sum(int(row["has_bank_name"]) for row in entity_rows),
        "source_entities_with_region": sum(int(row["has_region"]) for row in entity_rows),
        "source_entities_with_address": sum(int(row["has_address"]) for row in entity_rows),
        "source_entities_with_business_scope": sum(int(row["has_business_scope"]) for row in entity_rows),
        "current_payload_rows": len(payload_rows),
        "current_payload_sources": dict(sorted(payload_source_counts.items())),
        "current_payload_columns": sorted(payload_rows[0].keys()) if payload_rows else [],
        "source_names_missing_in_payload": len(source_names - payload_names),
        "payload_names_missing_in_source": len(payload_names - source_names),
        "source_tax_missing_in_payload": len(source_tax - payload_tax),
        "payload_tax_missing_in_source": len(payload_tax - source_tax),
        "source_payload_name_overlap": len(source_names & payload_names),
        "source_payload_tax_overlap": len(source_tax & payload_tax),
        "schema_gap": {
            "payload_has_bank_fields": any("bank" in column.lower() or "account" in column.lower() for column in (payload_rows[0].keys() if payload_rows else [])),
            "payload_has_project_source": "project_name" in (payload_rows[0].keys() if payload_rows else []),
            "payload_has_cooperation_type": "cooperation_type" in (payload_rows[0].keys() if payload_rows else []),
            "payload_has_region_or_address": any(column in (payload_rows[0].keys() if payload_rows else []) for column in ("region", "address")),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", default="/home/odoo/workspace/partner_import_source")
    parser.add_argument("--payload", default="artifacts/migration/fresh_db_partner_l4_replay_payload_v1.csv")
    parser.add_argument("--out-dir", default="artifacts/migration/partner_import_source_audit_v1")
    args = parser.parse_args()

    source_root = Path(args.source_root)
    payload_path = Path(args.payload)
    out_dir = Path(args.out_dir)
    source_records = load_source_records(source_root)
    payload_records = load_payload_records(payload_path)
    payload_record_names = {norm_name(item.get("name")) for item in payload_records}
    entity_rows = build_entity_rows(source_records)
    summary = summarize(source_records, entity_rows, payload_records)

    record_fields = [
        "source_file",
        "source_kind",
        "row_number",
        "document_state",
        "push_result",
        "project_name",
        "partner_code",
        "name",
        "short_name",
        "tax_no",
        "cooperation_type",
        "main_supply_type",
        "category_label",
        "bank_name",
        "bank_account",
        "bank_account_name",
        "receipt_amount",
        "payment_amount",
        "tax_rate",
        "region",
        "address",
        "register_capital",
        "business_scope",
        "source_operator",
        "source_time",
        "supplier_hint",
        "customer_hint",
        "personal_fragment",
    ]
    entity_fields = list(entity_rows[0].keys()) if entity_rows else []
    write_csv(out_dir / "source_rows_v1.csv", record_fields, source_records)
    write_csv(out_dir / "source_entities_v1.csv", entity_fields, entity_rows)
    write_csv(
        out_dir / "source_payload_gap_samples_v1.csv",
        ["gap_type", "identity_key", "name", "tax_no", "target_role", "source_kinds", "sample_files"],
        [
            {
                "gap_type": "source_entity_missing_by_name",
                "identity_key": row["identity_key"],
                "name": row["canonical_name"],
                "tax_no": row["tax_no"],
                "target_role": row["target_role"],
                "source_kinds": row["source_kinds"],
                "sample_files": row["sample_files"],
            }
            for row in entity_rows
            if norm_name(row["canonical_name"])
            and norm_name(row["canonical_name"]) not in payload_record_names
        ][:300],
    )
    write_json(out_dir / "summary_v1.json", summary)
    print("PARTNER_IMPORT_SOURCE_AUDIT=" + json.dumps(summary, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
