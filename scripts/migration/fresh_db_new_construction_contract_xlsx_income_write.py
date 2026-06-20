#!/usr/bin/env python3
"""Replay user supplied "施工合同（新）" Excel rows as income contracts."""

from __future__ import annotations

import json
import os
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from zipfile import ZipFile


def repo_root() -> Path:
    env_root = os.getenv("MIGRATION_REPO_ROOT")
    candidates = []
    if env_root:
        candidates.append(Path(env_root))
    candidates.extend([Path("/mnt"), Path("/mnt/extra-addons"), Path.cwd()])
    for candidate in candidates:
        if (candidate / "addons/smart_construction_core").exists() or (candidate / "tmp").exists():
            return candidate
    return Path.cwd()


def ensure_allowed_db() -> None:
    allowlist = {
        item.strip()
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_migration_fresh").split(",")
        if item.strip()
    }
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_replay": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


REPO_ROOT = repo_root()
ARTIFACT_ROOT = Path(os.getenv("MIGRATION_ARTIFACT_ROOT") or str(REPO_ROOT / "artifacts/migration"))
SOURCE_XLSX = Path(
    os.getenv("CONSTRUCTION_CONTRACT_NEW_XLSX")
    or str(REPO_ROOT / "tmp/new_construction_contract_income.xlsx")
)
SOURCE_JSON_ENV = os.getenv("CONSTRUCTION_CONTRACT_NEW_XLSX_JSON") or ""
SOURCE_JSON = Path(SOURCE_JSON_ENV) if SOURCE_JSON_ENV else None
OUTPUT_JSON = ARTIFACT_ROOT / "fresh_db_new_construction_contract_xlsx_income_write_result_v1.json"
EXPECTED_ROWS = int(os.getenv("CONSTRUCTION_CONTRACT_NEW_XLSX_EXPECTED_ROWS") or "182")
LINE_NOTE = "legacy_contract_amount:construction_contract_new_xlsx"


def clean(value: object) -> str:
    if value is None or value is False:
        return ""
    return re.sub(r"\s+", " ", str(value).replace("\u3000", " ").strip())


def norm(value: object) -> str:
    text = clean(value)
    text = text.replace("（", "(").replace("）", ")")
    text = re.sub(r"[，,、；;:：\-—_·./\\（）()\s]", "", text)
    return text.lower()


def parse_amount(value: object) -> Decimal:
    text = clean(value).replace(",", "")
    if not text:
        return Decimal("0")
    try:
        return Decimal(text)
    except InvalidOperation:
        return Decimal("0")


def as_float(value: Decimal) -> float:
    return float(value.quantize(Decimal("0.01")))


def parse_date(value: object) -> str | None:
    text = clean(value)
    if not text or text in {"/", "0"}:
        return None
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(text[:10], fmt).date().isoformat()
        except ValueError:
            continue
    return None


def parse_datetime(value: object) -> str | None:
    text = clean(value)
    if not text:
        return None
    normalized = text.replace("T", " ")
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%m/%d/%Y %H:%M:%S"):
        try:
            return datetime.strptime(normalized[:19], fmt).strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue
    date_value = parse_date(text)
    return f"{date_value} 00:00:00" if date_value else None


def col_index(ref: str) -> int:
    match = re.match(r"([A-Z]+)", ref or "")
    if not match:
        return 0
    value = 0
    for char in match.group(1):
        value = value * 26 + ord(char) - 64
    return value - 1


def read_xlsx(path: Path) -> list[dict[str, str]]:
    namespace = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    with ZipFile(path) as archive:
        shared: list[str] = []
        shared_root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
        for item in shared_root.findall("m:si", namespace):
            shared.append("".join(text.text or "" for text in item.findall(".//m:t", namespace)))
        sheet = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))
        rows: list[list[str]] = []
        for row in sheet.findall(".//m:sheetData/m:row", namespace):
            values: dict[int, str] = {}
            for cell in row.findall("m:c", namespace):
                value = cell.find("m:v", namespace)
                if value is None:
                    cell_value = ""
                elif cell.attrib.get("t") == "s":
                    cell_value = shared[int(value.text or "0")]
                else:
                    cell_value = value.text or ""
                values[col_index(cell.attrib.get("r", ""))] = clean(cell_value)
            if values:
                rows.append([values.get(index, "") for index in range(max(values) + 1)])
    if not rows:
        return []
    header = rows[0]
    return [dict(zip(header, row + [""] * (len(header) - len(row)))) for row in rows[1:]]


def read_source_rows() -> list[dict[str, str]]:
    if SOURCE_JSON and SOURCE_JSON.exists():
        return json.loads(SOURCE_JSON.read_text(encoding="utf-8"))
    if not SOURCE_XLSX.exists():
        if os.getenv("CONSTRUCTION_CONTRACT_NEW_XLSX") or os.getenv("CONSTRUCTION_CONTRACT_NEW_XLSX_JSON"):
            raise RuntimeError({"missing_source_xlsx": str(SOURCE_XLSX)})
        return []
    return read_xlsx(SOURCE_XLSX)


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def source_subject(row: dict[str, str]) -> str:
    return clean(row.get("合同标题")) or clean(row.get("合同编号")) or clean(row.get("单据编号")) or clean(row.get("项目名称"))


def legacy_state(row: dict[str, str]) -> str:
    return "confirmed" if clean(row.get("单据状态")) == "审核通过" else "draft"


ensure_allowed_db()

Contract = env["construction.contract"].sudo()  # noqa: F821
ContractLine = env["construction.contract.line"].sudo()  # noqa: F821
Project = env["project.project"].sudo()  # noqa: F821
Partner = env["res.partner"].sudo()  # noqa: F821


def resolve_project(row: dict[str, str]):
    names = [clean(row.get("项目名称")), clean(row.get("合同标题"))]
    for name in names:
        if not name:
            continue
        exact = Project.search([("name", "=", name)], limit=2)
        if len(exact) == 1:
            return exact[0]
    normalized_candidates = [(name, norm(name)) for name in names if name]
    for name, normalized in normalized_candidates:
        if not normalized:
            continue
        candidates = Project.search([("name", "ilike", name[:12])], limit=20)
        for project in candidates:
            project_name = norm(project.display_name)
            if normalized == project_name or normalized in project_name or project_name in normalized:
                return project
    project_name = clean(row.get("项目名称")) or source_subject(row) or "施工合同（新）项目"
    vals = {"name": project_name}
    if "company_id" in Project._fields:
        vals["company_id"] = env.company.id  # noqa: F821
    return Project.create(vals)


def resolve_project_for_contract(existing_contract, row: dict[str, str]):
    if existing_contract:
        legacy_project_id = clean(existing_contract.legacy_project_id)
        if legacy_project_id:
            matches = Project.search([("legacy_project_id", "=", legacy_project_id)], limit=2)
            if len(matches) == 1:
                return matches[0]
        if existing_contract.project_id:
            return existing_contract.project_id
    return resolve_project(row)


def resolve_partner(row: dict[str, str]):
    name = clean(row.get("发包人")) or "施工合同（新）发包人"
    matches = Partner.search([("name", "=", name)], order="id")
    if matches:
        ranked = matches.filtered(lambda item: item.customer_rank > 0)
        return (ranked or matches)[0]
    vals = {
        "name": name,
        "company_type": "company",
        "legacy_partner_id": f"new_construction_contract_xlsx:{clean(row.get('单据编号'))}",
        "legacy_partner_source": "new_construction_contract_xlsx",
        "legacy_partner_name": name,
    }
    if "is_company" in Partner._fields:
        vals["is_company"] = True
    if "customer_rank" in Partner._fields:
        vals["customer_rank"] = 1
    return Partner.create(vals)


def amount_values(row: dict[str, str]) -> dict[str, object]:
    contract_amount = parse_amount(row.get("合同金额"))
    invoice_amount = parse_amount(row.get("累计开票"))
    received_amount = parse_amount(row.get("累计收款"))
    unreceived_amount = parse_amount(row.get("未收款"))
    if not unreceived_amount and contract_amount and received_amount:
        unreceived_amount = max(contract_amount - received_amount, Decimal("0"))
    return {
        "legacy_contract_amount": as_float(contract_amount),
        "legacy_contract_amount_source": "施工合同（新）.合同金额",
        "visible_invoice_amount": as_float(invoice_amount),
        "visible_invoice_amount_source": "施工合同（新）.累计开票",
        "visible_received_amount": as_float(received_amount),
        "visible_received_amount_source": "施工合同（新）.累计收款",
        "visible_unreceived_amount": as_float(unreceived_amount),
        "visible_unreceived_amount_source": "施工合同（新）.未收款",
        "visible_unreceived_rate": clean(row.get("未收款比例")),
    }


def contract_vals(row: dict[str, str], project, partner) -> dict[str, object]:
    vals: dict[str, object] = {
        "legacy_contract_id": f"new_construction_contract_xlsx:{clean(row.get('单据编号'))}",
        "legacy_document_no": clean(row.get("单据编号")),
        "legacy_contract_no": clean(row.get("合同编号")),
        "legacy_status": clean(row.get("单据状态")),
        "legacy_deleted_flag": "0",
        "legacy_counterparty_text": clean(row.get("发包人")),
        "legacy_income_surface_visible": True,
        "subject": source_subject(row),
        "type": "out",
        "state": legacy_state(row),
        "project_id": project.id,
        "partner_id": partner.id,
        "date_contract": parse_date(row.get("合同订立日期")),
        "engineering_address": clean(row.get("工程地址")),
        "engineering_content": clean(row.get("工程内容")),
        "contract_duration_text": clean(row.get("合同工期天数")),
        "entry_user_text": clean(row.get("录入人")),
        "entry_time": parse_datetime(row.get("录入时间")),
    }
    vals.update(amount_values(row))
    sale_tax = Contract._get_default_tax("out")
    if sale_tax:
        vals["tax_id"] = sale_tax.id
    return {key: value for key, value in vals.items() if value not in ("", None)}


def sync_amount_line(contract, row: dict[str, str]) -> str:
    amount = parse_amount(row.get("合同金额"))
    if not amount:
        return ""
    vals = {
        "contract_id": contract.id,
        "sequence": 1,
        "qty_contract": 1.0,
        "price_contract": as_float(amount),
        "note": LINE_NOTE,
    }
    lines = contract.line_ids.filtered(lambda line: (line.note or "") == LINE_NOTE)
    if lines:
        lines[:1].write(vals)
        return "line_updated"
    if not contract.line_ids:
        ContractLine.create(vals)
        return "line_created"
    return ""


rows = read_source_rows()
if not rows:
    payload = {
        "status": "SKIP",
        "mode": "fresh_db_new_construction_contract_xlsx_income_write",
        "database": env.cr.dbname,  # noqa: F821
        "decision": "source_not_configured_or_missing",
        "source_xlsx": str(SOURCE_XLSX),
        "source_json": str(SOURCE_JSON) if SOURCE_JSON else "",
        "db_writes": 0,
    }
    write_json(OUTPUT_JSON, payload)
    print("FRESH_DB_NEW_CONSTRUCTION_CONTRACT_XLSX_INCOME_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
    raise SystemExit(0)

docs = [clean(row.get("单据编号")) for row in rows if clean(row.get("单据编号"))]
source_legacy_ids = {
    f"new_construction_contract_xlsx:{doc}"
    for doc in docs
}
if len(rows) != EXPECTED_ROWS:
    raise RuntimeError({"unexpected_xlsx_rows": len(rows), "expected": EXPECTED_ROWS})
if len(set(docs)) != len(docs):
    raise RuntimeError({"duplicate_document_no": [doc for doc in docs if docs.count(doc) > 1][:20]})

existing = Contract.search(
    [
        "|",
        ("legacy_contract_id", "in", sorted(source_legacy_ids)),
        ("legacy_document_no", "in", docs),
    ],
    order="legacy_document_no,id",
)
existing_by_doc: dict[str, object] = {}
existing_by_source_legacy: dict[str, object] = {}
duplicates: list[dict[str, object]] = []
for rec in existing:
    source_legacy_id = clean(rec.legacy_contract_id)
    if source_legacy_id in source_legacy_ids:
        document_no = source_legacy_id.removeprefix("new_construction_contract_xlsx:")
        if source_legacy_id in existing_by_source_legacy:
            duplicates.append(
                {
                    "legacy_contract_id": source_legacy_id,
                    "ids": [existing_by_source_legacy[source_legacy_id].id, rec.id],
                }
            )
        else:
            existing_by_source_legacy[source_legacy_id] = rec
            existing_by_doc[document_no] = rec
        continue
    document_no = clean(rec.legacy_document_no)
    if document_no in existing_by_doc:
        # Different historical sources can legitimately reuse a document number.
        # Prefer the xlsx-owned record above and only treat duplicates inside the
        # xlsx source identity as blocking.
        continue
    else:
        existing_by_doc[document_no] = rec
if duplicates:
    raise RuntimeError({"duplicate_existing_source_contract": duplicates[:20]})

created = updated = type_corrected = visible_corrected = line_created = line_updated = 0
for row in rows:
    document_no = clean(row.get("单据编号"))
    source_legacy_id = f"new_construction_contract_xlsx:{document_no}"
    existing_contract = existing_by_source_legacy.get(source_legacy_id) or existing_by_doc.get(document_no)
    project = resolve_project_for_contract(existing_contract, row)
    partner = resolve_partner(row)
    vals = contract_vals(row, project, partner)
    if existing_contract:
        before_type = existing_contract.type
        before_visible = bool(existing_contract.legacy_income_surface_visible)
        target_state = vals.pop("state", "")
        existing_contract.with_context(skip_validation_check=True).write(vals)
        if target_state and existing_contract.state != target_state:
            env.cr.execute(  # noqa: F821
                "UPDATE construction_contract SET state = %s, write_date = NOW(), write_uid = 1 WHERE id = %s",
                [target_state, existing_contract.id],
            )
            existing_contract.invalidate_recordset(["state"])
        if before_type != "out":
            type_corrected += 1
        if not before_visible:
            visible_corrected += 1
        action = sync_amount_line(existing_contract, row)
        updated += 1
    else:
        contract = Contract.create(vals)
        action = sync_amount_line(contract, row)
        created += 1
    if action == "line_created":
        line_created += 1
    elif action == "line_updated":
        line_updated += 1

env.cr.commit()  # noqa: F821

visible_count = Contract.search_count(
    [
        ("legacy_contract_id", "in", sorted(source_legacy_ids)),
        ("type", "=", "out"),
        ("legacy_income_surface_visible", "=", True),
    ]
)
income_wrapper_count = env["construction.contract.income"].sudo().search_count(  # noqa: F821
    [("legacy_contract_id", "in", sorted(source_legacy_ids))]
)
result = {
    "status": "PASS" if visible_count == len(docs) and income_wrapper_count == len(docs) else "FAIL",
    "mode": "fresh_db_new_construction_contract_xlsx_income_write",
    "database": env.cr.dbname,  # noqa: F821
    "source_xlsx": str(SOURCE_XLSX),
    "source_json": str(SOURCE_JSON) if SOURCE_JSON else "",
    "input_rows": len(rows),
    "created_rows": created,
    "updated_rows": updated,
    "type_corrected_rows": type_corrected,
    "visible_corrected_rows": visible_corrected,
    "amount_line_created_rows": line_created,
    "amount_line_updated_rows": line_updated,
    "visible_income_rows_after": visible_count,
    "income_wrapper_rows_after": income_wrapper_count,
}
write_json(OUTPUT_JSON, result)
print("FRESH_DB_NEW_CONSTRUCTION_CONTRACT_XLSX_INCOME_WRITE=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
if result["status"] != "PASS":
    raise RuntimeError({"xlsx_income_write_failed": result})
