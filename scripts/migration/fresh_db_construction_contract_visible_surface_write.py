#!/usr/bin/env python3
"""Replay user-visible construction contract fields from the acceptance Excel."""

from __future__ import annotations

import json
import os
import re
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from xml.etree import ElementTree as ET


DEFAULT_XLSX = "/home/odoo/workspace/partner_import_source/施工合同（新）639137606365482500.xlsx"
OUTPUT_JSON = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", "/mnt/artifacts/migration")) / "fresh_db_construction_contract_visible_surface_write_result_v1.json"
FILE_INDEX_CSV = Path(os.getenv("MIGRATION_FILE_INDEX_CSV", "/mnt/artifacts/migration/fresh_db_legacy_file_index_replay_payload_v1.csv"))
EXPECTED_HEADERS = [
    "序号",
    "单据状态",
    "单据编号",
    "合同订立日期",
    "原件是否归档",
    "发包人",
    "项目名称",
    "工程类别",
    "合同标题",
    "合同编号",
    "合同金额",
    "结算金额",
    "累计开票",
    "累计收款",
    "未收款",
    "未收款比例",
    "挂靠人",
    "工程地址",
    "工程内容",
    "录入人",
    "录入时间",
    "审批信息",
]


def ensure_allowed_db() -> None:
    allowlist = {item.strip() for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_migration_fresh").split(",") if item.strip()}
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_replay": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def clean(value: object) -> str:
    return "" if value is None else str(value).replace("\r\n", "\n").replace("\r", "\n").strip()


def normalize_match_text(value: object) -> str:
    text = clean(value).lower()
    return re.sub(r"[\s\-_（）()、，,。\.·:：/\\]+", "", text)


def decimal_value(value: object) -> float:
    text = clean(value)
    if not text:
        return 0.0
    return float(text.replace(",", "").replace("%", ""))


def parse_bool(value: object) -> bool:
    text = clean(value)
    return text in {"是", "true", "True", "1", "已归档", "归档"}


def parse_datetime(value: object):
    text = clean(value)
    if not text:
        return False
    if re.fullmatch(r"\d+(\.\d+)?", text):
        base = datetime(1899, 12, 30)
        return base + timedelta(days=float(text))
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return False


def parse_date(value: object):
    parsed = parse_datetime(value)
    return parsed.date() if parsed else False


def read_shared_strings(package: zipfile.ZipFile) -> list[str]:
    try:
        xml = package.read("xl/sharedStrings.xml")
    except KeyError:
        return []
    root = ET.fromstring(xml)
    ns = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    values = []
    for item in root.findall("x:si", ns):
        parts = [node.text or "" for node in item.findall(".//x:t", ns)]
        values.append("".join(parts))
    return values


def read_sheet_rows(path: Path) -> list[list[object]]:
    ns = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    with zipfile.ZipFile(path) as package:
        shared = read_shared_strings(package)
        root = ET.fromstring(package.read("xl/worksheets/sheet1.xml"))
    rows: list[list[object]] = []
    for row in root.findall(".//x:sheetData/x:row", ns):
        cells: dict[int, object] = {}
        for cell in row.findall("x:c", ns):
            ref = cell.attrib.get("r", "")
            col_letters = "".join(ch for ch in ref if ch.isalpha())
            col_index = 0
            for ch in col_letters:
                col_index = col_index * 26 + ord(ch.upper()) - ord("A") + 1
            value_node = cell.find("x:v", ns)
            value = value_node.text if value_node is not None else ""
            if cell.attrib.get("t") == "s" and value != "":
                value = shared[int(value)]
            elif cell.attrib.get("t") == "inlineStr":
                value = "".join(node.text or "" for node in cell.findall(".//x:t", ns))
            cells[col_index] = value
        if cells:
            rows.append([cells.get(index, "") for index in range(1, max(cells) + 1)])
    return rows


def rows_from_xlsx(path: Path) -> list[dict[str, object]]:
    raw_rows = read_sheet_rows(path)
    if not raw_rows:
        return []
    headers = [clean(item) for item in raw_rows[0]]
    if headers[: len(EXPECTED_HEADERS)] != EXPECTED_HEADERS:
        raise RuntimeError({"unexpected_headers": headers, "expected": EXPECTED_HEADERS})
    result = []
    for row in raw_rows[1:]:
        padded = row + [""] * (len(headers) - len(row))
        values = dict(zip(headers, padded))
        if clean(values.get("单据编号")):
            result.append(values)
    return result


def read_file_index(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    import csv

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [
            row
            for row in csv.DictReader(handle)
            if clean(row.get("active")) == "1" and clean(row.get("file_name"))
        ]


def title_fragment_score(title: str, filename: str) -> int:
    if len(title) < 8:
        return 0
    for length in (24, 20, 18, 14, 10, 8):
        if len(title) < length:
            continue
        for start in range(0, len(title) - length + 1):
            if title[start : start + length] in filename:
                return length
    return 0


def attachment_text_for(row: dict[str, object], file_rows: list[dict[str, str]]) -> tuple[str, int]:
    contract_no = normalize_match_text(row.get("合同编号"))
    title = normalize_match_text(row.get("合同标题"))
    project = normalize_match_text(row.get("项目名称"))
    hits: list[tuple[int, str, str]] = []
    for file_row in file_rows:
        filename = clean(file_row.get("file_name"))
        normalized_filename = normalize_match_text(filename)
        score = 0
        if contract_no and contract_no in normalized_filename:
            score += 60
        if title and (title in normalized_filename or normalized_filename in title):
            score += 40
        if project and (project in normalized_filename or normalized_filename in project):
            score += 30
        if not score:
            score = title_fragment_score(title, normalized_filename)
        if score >= 18:
            hits.append((score, filename, clean(file_row.get("file_path"))))
    if not hits:
        return "", 0
    # Keep the highest-confidence unique file names visible; paths remain in the source payload.
    names: list[str] = []
    seen: set[str] = set()
    for _score, filename, _path in sorted(hits, key=lambda item: (-item[0], item[1]))[:8]:
        if filename in seen:
            continue
        seen.add(filename)
        names.append(filename)
    return "\n".join(names), len(names)


def amount_close(left: float, right: float) -> bool:
    return abs((left or 0.0) - (right or 0.0)) <= 0.01


ensure_allowed_db()

xlsx_path = Path(os.getenv("CONSTRUCTION_CONTRACT_VISIBLE_XLSX", DEFAULT_XLSX))
rows = rows_from_xlsx(xlsx_path)
file_rows = read_file_index(FILE_INDEX_CSV)
Contract = env["construction.contract"].sudo()  # noqa: F821

updated = 0
missing: list[dict[str, object]] = []
duplicates: list[dict[str, object]] = []
amount_mismatches: list[dict[str, object]] = []
attachment_matched_rows = 0
for row in rows:
    document_no = clean(row.get("单据编号"))
    contract_no = clean(row.get("合同编号"))
    matches = Contract.search([("legacy_document_no", "=", document_no)])
    if not matches and contract_no:
        matches = Contract.search([("legacy_contract_no", "=", contract_no)])
    if not matches:
        missing.append({"单据编号": document_no, "合同编号": contract_no, "合同标题": clean(row.get("合同标题"))})
        continue
    if len(matches) > 1:
        duplicates.append({"单据编号": document_no, "合同编号": contract_no, "ids": matches.ids})
        continue
    contract = matches[0]
    attachment_text, attachment_count = attachment_text_for(row, file_rows)
    if attachment_count:
        attachment_matched_rows += 1
    vals = {
        "legacy_status": clean(row.get("单据状态")),
        "date_contract": parse_date(row.get("合同订立日期")),
        "archived": parse_bool(row.get("原件是否归档")),
        "engineering_category_text": clean(row.get("工程类别")),
        "affiliated_person": clean(row.get("挂靠人")),
        "engineering_address": clean(row.get("工程地址")),
        "engineering_content": clean(row.get("工程内容")),
        "entry_user_text": clean(row.get("录入人")),
        "entry_time": parse_datetime(row.get("录入时间")),
        "approval_info": clean(row.get("审批信息")),
        "attachment_text": attachment_text,
        "visible_invoice_amount": decimal_value(row.get("累计开票")),
        "visible_received_amount": decimal_value(row.get("累计收款")),
        "visible_unreceived_amount": decimal_value(row.get("未收款")),
        "visible_unreceived_rate": clean(row.get("未收款比例")),
    }
    contract.write({field: value for field, value in vals.items() if value not in ("", False)})
    updated += 1

    checks = {
        "合同金额": (contract.visible_contract_amount, decimal_value(row.get("合同金额"))),
        "结算金额": (contract.settlement_amount, decimal_value(row.get("结算金额"))),
        "累计开票": (contract.visible_invoice_amount, decimal_value(row.get("累计开票"))),
        "累计收款": (contract.visible_received_amount, decimal_value(row.get("累计收款"))),
        "未收款": (contract.visible_unreceived_amount, decimal_value(row.get("未收款"))),
    }
    bad = {name: {"system": system, "excel": excel} for name, (system, excel) in checks.items() if not amount_close(system, excel)}
    if bad:
        amount_mismatches.append({"单据编号": document_no, "合同编号": contract_no, "mismatches": bad})

env.cr.commit()  # noqa: F821
status = "PASS" if not missing and not duplicates else "FAIL"
payload = {
    "status": status,
    "mode": "fresh_db_construction_contract_visible_surface_write",
    "database": env.cr.dbname,  # noqa: F821
    "xlsx": str(xlsx_path),
    "input_rows": len(rows),
    "updated_rows": updated,
    "file_index_csv": str(FILE_INDEX_CSV),
    "file_index_rows": len(file_rows),
    "attachment_matched_rows": attachment_matched_rows,
    "missing_rows": missing,
    "duplicate_rows": duplicates,
    "visible_surface_mismatches": amount_mismatches,
    "visible_surface_mismatch_count": len(amount_mismatches),
}
OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
OUTPUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("FRESH_DB_CONSTRUCTION_CONTRACT_VISIBLE_SURFACE_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
