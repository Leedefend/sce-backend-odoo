#!/usr/bin/env python3
"""Replay visible construction contract approval and attachment trace assets."""

from __future__ import annotations

import csv
import json
import os
import re
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from xml.etree import ElementTree as ET


DEFAULT_XLSX = "/home/odoo/workspace/partner_import_source/施工合同（新）639137606365482500.xlsx"
OUTPUT_JSON = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", "/mnt/artifacts/migration")) / "fresh_db_construction_contract_visible_trace_write_result_v1.json"
FILE_INDEX_CSV = Path(os.getenv("MIGRATION_FILE_INDEX_CSV", "/mnt/artifacts/migration/fresh_db_legacy_file_index_replay_payload_v1.csv"))
SOURCE_MODEL = "construction_contract_visible_surface"
APPROVAL_FACT_TYPE = "construction_contract_visible_approval"
ATTACHMENT_MARKER = "[migration:construction_contract_visible_attachment]"
WRITE_VISIBLE_ATTACHMENTS = os.getenv("CONSTRUCTION_CONTRACT_VISIBLE_TRACE_ATTACHMENTS", "0") == "1"
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
        values.append("".join(node.text or "" for node in item.findall(".//x:t", ns)))
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


def attachment_hits_for(row: dict[str, object], file_rows: list[dict[str, str]]) -> list[dict[str, object]]:
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
    result: list[dict[str, object]] = []
    seen: set[str] = set()
    for score, filename, file_path in sorted(hits, key=lambda item: (-item[0], item[1]))[:8]:
        if filename in seen:
            continue
        seen.add(filename)
        result.append({"score": score, "name": filename, "path": file_path})
    return result


ensure_allowed_db()

Contract = env["construction.contract"].sudo()  # noqa: F821
ContractEvent = env["sc.contract.event"].sudo()  # noqa: F821
Attachment = env["ir.attachment"].sudo()  # noqa: F821

xlsx_path = Path(os.getenv("CONSTRUCTION_CONTRACT_VISIBLE_XLSX", DEFAULT_XLSX))
rows = rows_from_xlsx(xlsx_path)
file_rows = read_file_index(FILE_INDEX_CSV)

approval_created = approval_updated = attachment_created = attachment_removed = 0
missing: list[dict[str, object]] = []
duplicates: list[dict[str, object]] = []
attachment_rows: list[dict[str, object]] = []

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

    approval_info = clean(row.get("审批信息"))
    if approval_info:
        domain = [
            ("legacy_fact_model", "=", SOURCE_MODEL),
            ("legacy_fact_key", "=", document_no),
            ("legacy_fact_type", "=", APPROVAL_FACT_TYPE),
        ]
        event = ContractEvent.search(domain, limit=1)
        vals = {
            "name": f"{document_no} 历史审批",
            "event_type": "legacy_approval",
            "project_id": contract.project_id.id,
            "contract_id": contract.id,
            "partner_id": contract.partner_id.id,
            "event_no": document_no,
            "source_channel": "import",
            "event_date": parse_date(row.get("录入时间")) or contract.date_contract or False,
            "amount_impact": 0.0,
            "tax_excluded_amount": 0.0,
            "tax_amount": 0.0,
            "settlement_included": False,
            "state": "done",
            "legacy_fact_model": SOURCE_MODEL,
            "legacy_fact_key": document_no,
            "legacy_fact_type": APPROVAL_FACT_TYPE,
            "description": approval_info,
            "basis": "施工合同（新）.审批信息",
        }
        if event:
            event.write(vals)
            approval_updated += 1
        else:
            ContractEvent.create(vals)
            approval_created += 1

    old_attachments = Attachment.search(
        [
            ("res_model", "=", "construction.contract"),
            ("res_id", "=", contract.id),
            ("description", "ilike", ATTACHMENT_MARKER),
        ]
    )
    attachment_removed += len(old_attachments)
    old_attachments.unlink()

    hits = attachment_hits_for(row, file_rows) if WRITE_VISIBLE_ATTACHMENTS else []
    for hit in hits:
        Attachment.create(
            {
                "name": hit["name"],
                "type": "url",
                "url": hit["path"] or hit["name"],
                "res_model": "construction.contract",
                "res_id": contract.id,
                "description": (
                    f"{ATTACHMENT_MARKER} document_no={document_no}; "
                    f"contract_no={contract_no}; score={hit['score']}; source_path={hit['path']}"
                ),
            }
        )
        attachment_created += 1
    if hits:
        attachment_rows.append(
            {
                "document_no": document_no,
                "contract_no": contract_no,
                "contract_id": contract.id,
                "attachment_count": len(hits),
                "attachments": [hit["name"] for hit in hits],
            }
        )

env.cr.commit()  # noqa: F821

post_approval_count = ContractEvent.search_count(
    [
        ("legacy_fact_model", "=", SOURCE_MODEL),
        ("legacy_fact_type", "=", APPROVAL_FACT_TYPE),
    ]
)
post_attachment_count = Attachment.search_count(
    [
        ("res_model", "=", "construction.contract"),
        ("description", "ilike", ATTACHMENT_MARKER),
    ]
)
post_errors = []
if missing:
    post_errors.append({"error": "missing_contracts", "count": len(missing)})
if duplicates:
    post_errors.append({"error": "duplicate_contracts", "count": len(duplicates)})
if post_approval_count < approval_created + approval_updated:
    post_errors.append({"error": "approval_event_count_below_processed", "actual": post_approval_count})
if post_attachment_count != attachment_created:
    post_errors.append({"error": "attachment_count_not_expected", "actual": post_attachment_count, "expected": attachment_created})

status = "PASS" if not post_errors else "FAIL"
payload = {
    "status": status,
    "mode": "fresh_db_construction_contract_visible_trace_write",
    "database": env.cr.dbname,  # noqa: F821
    "xlsx": str(xlsx_path),
    "file_index_csv": str(FILE_INDEX_CSV),
    "input_rows": len(rows),
    "approval_event_created_rows": approval_created,
    "approval_event_updated_rows": approval_updated,
    "approval_event_count": post_approval_count,
    "write_visible_attachments": WRITE_VISIBLE_ATTACHMENTS,
    "attachment_removed_rows": attachment_removed,
    "attachment_created_rows": attachment_created,
    "attachment_count": post_attachment_count,
    "attachment_contract_rows": len(attachment_rows),
    "attachment_rows": attachment_rows,
    "missing_rows": missing,
    "duplicate_rows": duplicates,
    "post_errors": post_errors,
}
OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
OUTPUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("FRESH_DB_CONSTRUCTION_CONTRACT_VISIBLE_TRACE_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
if status != "PASS":
    raise RuntimeError({"visible_trace_write_failed": post_errors})
