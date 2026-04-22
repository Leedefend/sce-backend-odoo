#!/usr/bin/env python3
"""Generate URL-type ir.attachment XML assets for receipt invoice lines."""

from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import re
import subprocess
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


REPO_ASSET_ROOT = Path("migration_assets")
RUNTIME_ROOT = Path(".runtime_artifacts/migration_assets/receipt_invoice_attachment_sc_v1")
XML_REL_PATH = Path("30_relation/receipt_invoice_attachment/receipt_invoice_attachment_v1.xml")
EXTERNAL_REL_PATH = Path("manifest/receipt_invoice_attachment_external_id_manifest_v1.json")
VALIDATION_REL_PATH = Path("manifest/receipt_invoice_attachment_validation_manifest_v1.json")
ASSET_MANIFEST_REL_PATH = Path("manifest/receipt_invoice_attachment_asset_manifest_v1.json")
CATALOG_REL_PATH = Path("manifest/migration_asset_catalog_v1.json")
ASSET_PACKAGE_ID = "receipt_invoice_attachment_sc_v1"
GENERATED_AT = "2026-04-15T15:50:00+00:00"
EXPECTED_FILE_ROWS = 126967

SQL = r"""
SET NOCOUNT ON;
DECLARE @sep varchar(1) = '|';
WITH src AS (
SELECT
  CONVERT(nvarchar(max), ID) AS ID,
  CONVERT(nvarchar(max), PID) AS PID,
  CONVERT(nvarchar(max), BILLID) AS BILLID,
  CONVERT(nvarchar(max), BUSINESSID) AS BUSINESSID,
  CONVERT(nvarchar(max), ATTR_NAME) AS ATTR_NAME,
  CONVERT(nvarchar(max), ATTR_PATH) AS ATTR_PATH,
  CONVERT(nvarchar(max), FILEMD5) AS FILEMD5,
  CONVERT(nvarchar(max), FILESIZE) AS FILESIZE,
  CONVERT(nvarchar(max), SOURCE) AS SOURCE,
  CONVERT(nvarchar(max), DEL) AS DEL
FROM dbo.BASE_SYSTEM_FILE
)
SELECT CONCAT(
  ISNULL(REPLACE(REPLACE(REPLACE(ID, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(PID, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(BILLID, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(BUSINESSID, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(ATTR_NAME, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(ATTR_PATH, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(FILEMD5, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(FILESIZE, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(SOURCE, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(DEL, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), '')
) AS rowdata
FROM src
ORDER BY ID;
"""

SQL_COLUMNS = ["ID", "PID", "BILLID", "BUSINESSID", "ATTR_NAME", "ATTR_PATH", "FILEMD5", "FILESIZE", "SOURCE", "DEL"]


class ReceiptInvoiceAttachmentAssetError(Exception):
    pass


def clean(value: object) -> str:
    text = "" if value is None else str(value).strip()
    return "" if text.upper() == "NULL" else text


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ReceiptInvoiceAttachmentAssetError(message)


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
        "/opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P \"$SA_PASSWORD\" -C -d LegacyDb -s '|' -y 0 -Y 0",
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
    require(len(rows) == EXPECTED_FILE_ROWS, f"file row count drifted: {len(rows)} != {EXPECTED_FILE_ROWS}")
    return rows


def load_pid_index(asset_root: Path) -> dict[str, str]:
    manifest = load_json(asset_root / "manifest/receipt_invoice_line_external_id_manifest_v1.json")
    result: dict[str, str] = {}
    for row in manifest.get("records", []):
        external_id = clean(row.get("external_id"))
        keys = row.get("attachment_candidate_keys") or {}
        pid = clean(keys.get("pid")) if isinstance(keys, dict) else ""
        if pid and external_id:
            result[pid] = external_id
    require(result, "receipt invoice pid index is empty")
    return result


def is_deleted(value: object) -> bool:
    normalized = clean(value).lower()
    return bool(normalized) and normalized not in {"0", "false", "no", "n", "否"}


def safe_external_suffix(value: str) -> str:
    suffix = re.sub(r"[^0-9A-Za-z_]+", "_", value).strip("_").lower()
    require(bool(suffix), "cannot build external id from blank legacy file id")
    return suffix


def attachment_url(row: dict[str, str]) -> str:
    path = clean(row.get("ATTR_PATH"))
    if path:
        return "legacy-file://" + path.lstrip("/")
    return "legacy-file-id://" + clean(row.get("ID"))


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
        record = ET.SubElement(data, "record", {"id": row["external_id"], "model": "ir.attachment"})
        add_text_field(record, "name", row["name"], required=True)
        add_text_field(record, "type", "url", required=True)
        add_text_field(record, "url", row["url"], required=True)
        add_text_field(record, "res_model", "sc.receipt.invoice.line", required=True)
        add_ref_field(record, "res_id", row["receipt_invoice_line_external_id"])
        add_text_field(record, "mimetype", row["mimetype"])
        add_text_field(record, "description", row["description"], required=True)
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
        "business_priority": "receipt_invoice_attachment_relation",
        "dependencies": ["receipt_invoice_line_sc_v1"],
        "layer": "30_relation",
        "load_phase": 30,
        "package_type": "url_attachment_relation",
        "required": True,
        "risk_class": "attachment_url_relation",
        "target_model": "ir.attachment",
        "verification_command": "python3 scripts/migration/legacy_receipt_invoice_attachment_asset_verify.py --asset-root migration_assets --lane receipt_invoice_attachment --check",
    }
    catalog["package_order"] = [item for item in catalog.get("package_order", []) if item != ASSET_PACKAGE_ID]
    catalog["package_order"].append(ASSET_PACKAGE_ID)
    catalog["packages"] = [item for item in catalog.get("packages", []) if item.get("asset_package_id") != ASSET_PACKAGE_ID]
    catalog["packages"].append(package)
    catalog["generated_at"] = GENERATED_AT
    write_json(catalog_path, catalog)


def generate(asset_root: Path, runtime_root: Path, expected_ready: int) -> dict[str, Any]:
    pid_to_invoice_line = load_pid_index(asset_root)
    source_rows = parse_sql_rows(run_sql())
    records: list[dict[str, str]] = []
    match_counts: Counter[str] = Counter()
    target_counts: Counter[str] = Counter()
    skipped: Counter[str] = Counter()
    by_file_id: Counter[str] = Counter()

    for row in source_rows:
        file_id = clean(row.get("ID"))
        pid = clean(row.get("PID"))
        target_external_id = pid_to_invoice_line.get(pid, "")
        if not target_external_id:
            skipped["pid_not_receipt_invoice_line"] += 1
            continue
        if is_deleted(row.get("DEL")):
            skipped["deleted_file"] += 1
            continue
        by_file_id[file_id] += 1
        target_counts[target_external_id] += 1
        name = clean(row.get("ATTR_NAME")) or file_id
        mimetype = mimetypes.guess_type(name)[0] or ""
        records.append(
            {
                "external_id": f"legacy_receipt_invoice_attachment_sc_{safe_external_suffix(file_id)}",
                "legacy_file_id": file_id,
                "legacy_pid": pid,
                "receipt_invoice_line_external_id": target_external_id,
                "name": name,
                "url": attachment_url(row),
                "mimetype": mimetype,
                "file_md5": clean(row.get("FILEMD5")),
                "file_size": clean(row.get("FILESIZE")),
                "description": (
                    "[migration:receipt_invoice_attachment] "
                    f"legacy_file_id={file_id}; legacy_pid={pid}; binary_embedded=false"
                ),
            }
        )
        match_counts["PID->pid"] += 1

    duplicate_file_ids = sorted(key for key, count in by_file_id.items() if count > 1)
    require(not duplicate_file_ids, f"duplicate legacy file ids: {duplicate_file_ids[:10]}")
    require(len(records) == expected_ready, f"ready attachment count drifted: {len(records)} != {expected_ready}")

    xml_path = asset_root / XML_REL_PATH
    external_path = asset_root / EXTERNAL_REL_PATH
    validation_path = asset_root / VALIDATION_REL_PATH
    asset_manifest_path = asset_root / ASSET_MANIFEST_REL_PATH
    write_xml(xml_path, records)

    external_manifest = {
        "manifest_version": "1.0",
        "asset_package_id": ASSET_PACKAGE_ID,
        "generated_at": GENERATED_AT,
        "records": [
            {
                "external_id": row["external_id"],
                "legacy_file_id": row["legacy_file_id"],
                "legacy_pid": row["legacy_pid"],
                "receipt_invoice_line_external_id": row["receipt_invoice_line_external_id"],
                "target_model": "ir.attachment",
                "res_model": "sc.receipt.invoice.line",
                "status": "loadable",
                "file_md5": row["file_md5"],
                "file_size": row["file_size"],
                "binary_embedded": False,
            }
            for row in records
        ],
        "summary": {"loadable": len(records), "raw_file_rows": len(source_rows)},
        "db_writes": 0,
        "odoo_shell": False,
    }
    validation_manifest = {
        "manifest_version": "1.0",
        "asset_package_id": ASSET_PACKAGE_ID,
        "generated_at": GENERATED_AT,
        "validation_gates": {
            "generate_time": [
                "legacy_file_id_unique",
                "pid_to_receipt_invoice_line_resolves",
                "attachment_type_url_only",
                "binary_datas_field_not_emitted",
                "deleted_files_excluded",
            ]
        },
        "business_boundary": {
            "ir_attachment_record": "included",
            "receipt_invoice_line_relation": "included",
            "binary_file_custody": "excluded",
            "url_strategy": "legacy-file-url",
        },
        "match_counts": dict(sorted(match_counts.items())),
        "skipped_counts": dict(sorted(skipped.items())),
        "matched_receipt_invoice_lines": len(target_counts),
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
        "dependencies": ["receipt_invoice_line_sc_v1"],
        "lane": {"layer": "30_relation", "lane_id": "receipt_invoice_attachment"},
        "target": {"model": "ir.attachment", "res_model": "sc.receipt.invoice.line", "type": "url"},
        "counts": {
            "raw_rows": len(source_rows),
            "loadable_records": len(records),
            "blocked_records": 0,
            "matched_receipt_invoice_lines": len(target_counts),
        },
        "source_counts": {
            "match_counts": dict(sorted(match_counts.items())),
            "skipped_counts": dict(sorted(skipped.items())),
        },
        "assets": [
            {"path": str(XML_REL_PATH), "sha256": sha256_file(xml_path)},
            {"path": str(EXTERNAL_REL_PATH), "sha256": sha256_file(external_path)},
            {"path": str(VALIDATION_REL_PATH), "sha256": sha256_file(validation_path)},
        ],
    }
    write_json(asset_manifest_path, asset_manifest)
    update_catalog(asset_root, sha256_file(asset_manifest_path))

    runtime_root.mkdir(parents=True, exist_ok=True)
    write_json(runtime_root / "generation_result_v1.json", asset_manifest)
    return {
        "status": "PASS",
        "asset_package_id": ASSET_PACKAGE_ID,
        "raw_file_rows": len(source_rows),
        "loadable_records": len(records),
        "matched_receipt_invoice_lines": len(target_counts),
        "db_writes": 0,
        "odoo_shell": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate receipt invoice attachment URL XML assets.")
    parser.add_argument("--asset-root", default=str(REPO_ASSET_ROOT))
    parser.add_argument("--runtime-root", default=str(RUNTIME_ROOT))
    parser.add_argument("--expected-ready", type=int, default=1079)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    try:
        result = generate(Path(args.asset_root), Path(args.runtime_root), args.expected_ready)
    except (ReceiptInvoiceAttachmentAssetError, json.JSONDecodeError, OSError) as exc:
        payload = {"status": "FAIL", "error": str(exc), "db_writes": 0, "odoo_shell": False}
        print("RECEIPT_INVOICE_ATTACHMENT_ASSET_GENERATOR=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 1 if args.check else 0
    print("RECEIPT_INVOICE_ATTACHMENT_ASSET_GENERATOR=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
