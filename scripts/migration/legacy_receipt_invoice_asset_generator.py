#!/usr/bin/env python3
"""Generate XML assets for legacy receipt invoice line facts."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import xml.etree.ElementTree as ET
from collections import Counter
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any


REPO_ASSET_ROOT = Path("migration_assets")
RUNTIME_ROOT = Path(".runtime_artifacts/migration_assets/receipt_invoice_line_sc_v1")
XML_REL_PATH = Path("20_business/receipt_invoice_line/receipt_invoice_line_v1.xml")
EXTERNAL_REL_PATH = Path("manifest/receipt_invoice_line_external_id_manifest_v1.json")
VALIDATION_REL_PATH = Path("manifest/receipt_invoice_line_validation_manifest_v1.json")
ASSET_MANIFEST_REL_PATH = Path("manifest/receipt_invoice_line_asset_manifest_v1.json")
CATALOG_REL_PATH = Path("manifest/migration_asset_catalog_v1.json")
ASSET_PACKAGE_ID = "receipt_invoice_line_sc_v1"
GENERATED_AT = "2026-04-15T15:20:00+00:00"
EXPECTED_RAW_ROWS = 4491

SQL = r"""
SET NOCOUNT ON;
DECLARE @sep varchar(1) = '|';
WITH src AS (
SELECT
  CONVERT(nvarchar(max), Id) AS Id,
  CONVERT(nvarchar(max), ZBID) AS ZBID,
  CONVERT(nvarchar(max), FPHM) AS FPHM,
  CONVERT(nvarchar(max), SPFMC) AS SPFMC,
  CONVERT(nvarchar(max), KPJE) AS KPJE,
  CONVERT(nvarchar(max), CCSKJE) AS CCSKJE,
  CONVERT(nvarchar(max), YKPJE) AS YKPJE,
  CONVERT(nvarchar(max), FPID) AS FPID,
  CONVERT(nvarchar(max), DJBH) AS DJBH,
  CONVERT(nvarchar(max), KPDW) AS KPDW,
  CONVERT(nvarchar(max), FP_CB_Id) AS FP_CB_Id,
  CONVERT(nvarchar(max), pid) AS pid
FROM dbo.C_JFHKLR_CB
)
SELECT CONCAT(
  ISNULL(REPLACE(REPLACE(REPLACE(Id, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(ZBID, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(FPHM, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(SPFMC, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(KPJE, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(CCSKJE, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(YKPJE, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(FPID, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(DJBH, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(KPDW, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(FP_CB_Id, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(pid, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), '')
) AS rowdata
FROM src
ORDER BY Id;
"""

SQL_COLUMNS = ["Id", "ZBID", "FPHM", "SPFMC", "KPJE", "CCSKJE", "YKPJE", "FPID", "DJBH", "KPDW", "FP_CB_Id", "pid"]


class ReceiptInvoiceAssetError(Exception):
    pass


def clean(value: object) -> str:
    text = "" if value is None else str(value).strip()
    return "" if text.upper() == "NULL" else text


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ReceiptInvoiceAssetError(message)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    require(path.exists(), f"missing json file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def run_sql() -> str:
    cmd = [
        "docker",
        "exec",
        "-i",
        "legacy-sqlserver",
        "bash",
        "-lc",
        "/opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P \"$SA_PASSWORD\" -C -d LegacyDb -W -s '|'",
    ]
    completed = subprocess.run(cmd, input=SQL, text=True, capture_output=True, check=False)
    require(completed.returncode == 0, completed.stderr.strip() or completed.stdout.strip())
    return completed.stdout


def parse_sql_rows(output: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in output.splitlines():
        text = line.strip()
        if not text or text == "rowdata" or set(text) <= {"-"}:
            continue
        parts = [part.strip() for part in text.split("|")]
        if len(parts) != len(SQL_COLUMNS):
            continue
        rows.append(dict(zip(SQL_COLUMNS, parts)))
    require(len(rows) == EXPECTED_RAW_ROWS, f"raw row count drifted: {len(rows)} != {EXPECTED_RAW_ROWS}")
    return rows


def load_receipt_map(asset_root: Path) -> dict[str, str]:
    manifest = load_json(asset_root / "manifest/receipt_external_id_manifest_v1.json")
    result: dict[str, str] = {}
    for row in manifest.get("records", []):
        legacy_id = clean(row.get("legacy_receipt_id"))
        external_id = clean(row.get("external_id"))
        if legacy_id and external_id and row.get("status") == "loadable":
            result[legacy_id] = external_id
    require(result, "receipt anchor map is empty")
    return result


def parse_amount(value: object) -> Decimal:
    try:
        return Decimal(clean(value) or "0")
    except InvalidOperation:
        return Decimal("0")


def best_amount(row: dict[str, str]) -> tuple[str, Decimal]:
    for field in ("KPJE", "CCSKJE", "YKPJE"):
        amount = parse_amount(row.get(field))
        if amount > 0:
            return field, amount
    return "", Decimal("0")


def safe_external_suffix(value: str) -> str:
    suffix = re.sub(r"[^0-9A-Za-z_]+", "_", value).strip("_").lower()
    require(bool(suffix), "cannot build external id from blank legacy receipt invoice line id")
    return suffix


def add_text_field(record: ET.Element, name: str, value: object, *, required: bool = False) -> None:
    text = clean(value)
    if not text and not required:
        return
    field = ET.SubElement(record, "field", {"name": name})
    field.text = text


def add_ref_field(record: ET.Element, name: str, external_id: str) -> None:
    ET.SubElement(record, "field", {"name": name, "ref": external_id})


def write_xml(path: Path, records: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    root = ET.Element("odoo")
    data = ET.SubElement(root, "data", {"noupdate": "1"})
    for row in records:
        record = ET.SubElement(data, "record", {"id": row["external_id"], "model": "sc.receipt.invoice.line"})
        add_ref_field(record, "request_id", row["receipt_external_id"])
        add_text_field(record, "sequence", row["sequence"], required=True)
        add_text_field(record, "legacy_invoice_line_id", row["legacy_invoice_line_id"], required=True)
        add_text_field(record, "legacy_receipt_id", row["legacy_receipt_id"], required=True)
        add_text_field(record, "legacy_invoice_id", row["legacy_invoice_id"])
        add_text_field(record, "legacy_invoice_child_id", row["legacy_invoice_child_id"])
        add_text_field(record, "legacy_pid", row["legacy_pid"])
        add_text_field(record, "invoice_no", row["invoice_no"])
        add_text_field(record, "invoice_party_name", row["invoice_party_name"])
        add_text_field(record, "invoice_issue_company", row["invoice_issue_company"])
        add_text_field(record, "source_document_no", row["source_document_no"])
        add_text_field(record, "source_table_name", "C_JFHKLR_CB", required=True)
        add_text_field(record, "amount_source", row["amount_source"], required=True)
        add_text_field(record, "invoice_amount", row["invoice_amount"], required=True)
        add_text_field(record, "current_receipt_amount", row["current_receipt_amount"])
        add_text_field(record, "invoiced_before_amount", row["invoiced_before_amount"])
        add_text_field(record, "note", row["note"], required=True)
    ET.indent(root, space="  ")
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)


def update_catalog(asset_root: Path, manifest_hash: str) -> None:
    catalog_path = asset_root / CATALOG_REL_PATH
    catalog = load_json(catalog_path)
    package = {
        "asset_manifest_path": str(ASSET_MANIFEST_REL_PATH),
        "asset_manifest_sha256": manifest_hash,
        "asset_package_id": ASSET_PACKAGE_ID,
        "baseline_package": True,
        "business_priority": "receipt_invoice_line_fact",
        "dependencies": ["receipt_sc_v1"],
        "layer": "20_business",
        "load_phase": 20,
        "package_type": "receipt_invoice_line_fact",
        "required": True,
        "risk_class": "auxiliary_invoice_line_fact",
        "target_model": "sc.receipt.invoice.line",
        "verification_command": "python3 scripts/migration/legacy_receipt_invoice_asset_verify.py --asset-root migration_assets --lane receipt_invoice_line --check",
    }
    catalog["package_order"] = [item for item in catalog.get("package_order", []) if item != ASSET_PACKAGE_ID]
    catalog["package_order"].append(ASSET_PACKAGE_ID)
    catalog["packages"] = [item for item in catalog.get("packages", []) if item.get("asset_package_id") != ASSET_PACKAGE_ID]
    catalog["packages"].append(package)
    catalog["generated_at"] = GENERATED_AT
    write_json(catalog_path, catalog)


def generate(asset_root: Path, runtime_root: Path, expected_ready: int) -> dict[str, Any]:
    source_rows = parse_sql_rows(run_sql())
    receipt_by_legacy = load_receipt_map(asset_root)
    loadable: list[dict[str, str]] = []
    blocked: list[dict[str, str]] = []
    counters: Counter[str] = Counter()
    amount_source_counts: Counter[str] = Counter()
    invoice_no_counts: Counter[str] = Counter()
    external_ids: Counter[str] = Counter()

    for line_no, row in enumerate(source_rows, start=2):
        legacy_line_id = clean(row.get("Id"))
        legacy_receipt_id = clean(row.get("ZBID"))
        receipt_external_id = receipt_by_legacy.get(legacy_receipt_id, "")
        amount_source, invoice_amount = best_amount(row)
        errors: list[str] = []
        if not legacy_line_id:
            errors.append("missing_legacy_receipt_invoice_line_id")
        if not legacy_receipt_id:
            errors.append("missing_parent_receipt_id")
        elif not receipt_external_id:
            errors.append("receipt_anchor_missing")
        if invoice_amount <= 0:
            errors.append("amount_not_positive")

        if clean(row.get("FPHM")):
            invoice_no_counts["invoice_no_present"] += 1
        else:
            invoice_no_counts["invoice_no_empty"] += 1

        if errors:
            for error in errors:
                counters[error] += 1
            blocked.append(
                {
                    "line_no": str(line_no),
                    "legacy_receipt_invoice_line_id": legacy_line_id,
                    "legacy_receipt_id": legacy_receipt_id,
                    "errors": ",".join(errors),
                }
            )
            continue

        external_id = f"legacy_receipt_invoice_line_sc_{safe_external_suffix(legacy_line_id)}"
        external_ids[external_id] += 1
        amount_source_counts[amount_source] += 1
        loadable.append(
            {
                "external_id": external_id,
                "receipt_external_id": receipt_external_id,
                "sequence": str(line_no * 10),
                "legacy_receipt_invoice_line_id": legacy_line_id,
                "legacy_invoice_line_id": legacy_line_id,
                "legacy_receipt_id": legacy_receipt_id,
                "legacy_invoice_id": clean(row.get("FPID")),
                "legacy_invoice_child_id": clean(row.get("FP_CB_Id")),
                "legacy_pid": clean(row.get("pid")),
                "invoice_no": clean(row.get("FPHM")),
                "invoice_party_name": clean(row.get("SPFMC")),
                "invoice_issue_company": clean(row.get("KPDW")),
                "source_document_no": clean(row.get("DJBH")),
                "amount_source": amount_source,
                "invoice_amount": str(invoice_amount),
                "current_receipt_amount": str(parse_amount(row.get("CCSKJE"))) if parse_amount(row.get("CCSKJE")) > 0 else "",
                "invoiced_before_amount": str(parse_amount(row.get("YKPJE"))) if parse_amount(row.get("YKPJE")) > 0 else "",
                "attachment_candidate_keys": {
                    "Id": legacy_line_id,
                    "ZBID": legacy_receipt_id,
                    "FPID": clean(row.get("FPID")),
                    "FP_CB_Id": clean(row.get("FP_CB_Id")),
                    "pid": clean(row.get("pid")),
                },
                "note": (
                    "[migration:receipt_invoice_line] "
                    f"legacy_receipt_invoice_line_id={legacy_line_id}; "
                    f"legacy_receipt_id={legacy_receipt_id}; "
                    f"invoice_fact=true; not_account_move=true; not_settlement=true; attachment_binary=false"
                ),
            }
        )

    duplicate_external_ids = sorted(key for key, count in external_ids.items() if count > 1)
    require(not duplicate_external_ids, f"duplicate XML external ids: {duplicate_external_ids[:10]}")
    require(len(loadable) == expected_ready, f"ready receipt invoice line count drifted: {len(loadable)} != {expected_ready}")

    xml_path = asset_root / XML_REL_PATH
    external_path = asset_root / EXTERNAL_REL_PATH
    validation_path = asset_root / VALIDATION_REL_PATH
    asset_manifest_path = asset_root / ASSET_MANIFEST_REL_PATH
    write_xml(xml_path, loadable)

    external_manifest = {
        "manifest_version": "1.0",
        "asset_package_id": ASSET_PACKAGE_ID,
        "generated_at": GENERATED_AT,
        "records": [
            {
                "external_id": row["external_id"],
                "legacy_receipt_invoice_line_id": row["legacy_receipt_invoice_line_id"],
                "legacy_receipt_id": row["legacy_receipt_id"],
                "receipt_external_id": row["receipt_external_id"],
                "target_model": "sc.receipt.invoice.line",
                "status": "loadable",
                "attachment_candidate_keys": row["attachment_candidate_keys"],
            }
            for row in loadable
        ],
        "summary": {"loadable": len(loadable), "blocked": len(blocked), "raw_rows": len(source_rows)},
        "db_writes": 0,
        "odoo_shell": False,
    }
    validation_manifest = {
        "manifest_version": "1.0",
        "asset_package_id": ASSET_PACKAGE_ID,
        "generated_at": GENERATED_AT,
        "validation_gates": {
            "generate_time": [
                "legacy_receipt_invoice_line_id_unique",
                "receipt_external_id_resolves",
                "invoice_amount_positive",
                "source_table_preserved",
                "account_move_not_written",
                "settlement_not_written",
                "attachment_binary_not_imported",
            ]
        },
        "business_boundary": {
            "receipt_invoice_line_fact": "included",
            "parent_receipt_anchor": "required",
            "accounting": "excluded",
            "posted_invoice": "excluded",
            "settlement": "excluded",
            "attachment_binary": "excluded_later_lane",
        },
        "blocked": blocked,
        "db_writes": 0,
        "odoo_shell": False,
    }
    write_json(external_path, external_manifest)
    write_json(validation_path, validation_manifest)

    asset_manifest = {
        "asset_manifest_version": "1.0",
        "asset_package_id": ASSET_PACKAGE_ID,
        "generated_at": GENERATED_AT,
        "baseline_package": True,
        "db_writes": 0,
        "odoo_shell": False,
        "dependencies": ["receipt_sc_v1"],
        "lane": {"layer": "20_business", "lane_id": "receipt_invoice_line"},
        "target": {"model": "sc.receipt.invoice.line", "source_table": "C_JFHKLR_CB"},
        "counts": {
            "raw_rows": len(source_rows),
            "loadable_records": len(loadable),
            "blocked_records": len(blocked),
        },
        "source_counts": {
            "amount_source_counts": dict(sorted(amount_source_counts.items())),
            "invoice_no_counts": dict(sorted(invoice_no_counts.items())),
            "blocked_reason_counts": dict(sorted(counters.items())),
        },
        "assets": [
            {"path": str(XML_REL_PATH), "sha256": sha256_file(xml_path)},
            {"path": str(EXTERNAL_REL_PATH), "sha256": sha256_file(external_path)},
            {"path": str(VALIDATION_REL_PATH), "sha256": sha256_file(validation_path)},
        ],
    }
    write_json(asset_manifest_path, asset_manifest)
    manifest_hash = sha256_file(asset_manifest_path)
    update_catalog(asset_root, manifest_hash)

    runtime_root.mkdir(parents=True, exist_ok=True)
    write_json(runtime_root / "generation_result_v1.json", asset_manifest)
    return {
        "status": "PASS",
        "asset_package_id": ASSET_PACKAGE_ID,
        "xml_path": str(xml_path),
        "asset_manifest": str(asset_manifest_path),
        "raw_rows": len(source_rows),
        "loadable_records": len(loadable),
        "blocked_records": len(blocked),
        "db_writes": 0,
        "odoo_shell": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate receipt invoice line XML migration assets.")
    parser.add_argument("--asset-root", default=str(REPO_ASSET_ROOT))
    parser.add_argument("--runtime-root", default=str(RUNTIME_ROOT))
    parser.add_argument("--expected-ready", type=int, default=4454)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    try:
        result = generate(Path(args.asset_root), Path(args.runtime_root), args.expected_ready)
    except (ReceiptInvoiceAssetError, json.JSONDecodeError, OSError) as exc:
        payload = {"status": "FAIL", "error": str(exc), "db_writes": 0, "odoo_shell": False}
        print("RECEIPT_INVOICE_ASSET_GENERATOR=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 1 if args.check else 0
    print("RECEIPT_INVOICE_ASSET_GENERATOR=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
