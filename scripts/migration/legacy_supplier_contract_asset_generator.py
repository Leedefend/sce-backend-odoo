#!/usr/bin/env python3
"""Generate repository XML assets for legacy supplier contract facts."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any


REPO_ASSET_ROOT = Path("migration_assets")
RUNTIME_ROOT = Path(".runtime_artifacts/migration_assets/supplier_contract_sc_v1")
XML_REL_PATH = Path("20_business/supplier_contract/supplier_contract_header_v1.xml")
EXTERNAL_REL_PATH = Path("manifest/supplier_contract_external_id_manifest_v1.json")
VALIDATION_REL_PATH = Path("manifest/supplier_contract_validation_manifest_v1.json")
ASSET_MANIFEST_REL_PATH = Path("manifest/supplier_contract_asset_manifest_v1.json")
ASSET_PACKAGE_ID = "supplier_contract_sc_v1"
GENERATED_AT = "2026-04-15T12:00:00+00:00"
EXPECTED_RAW_ROWS = 5535

SQL = r"""
SET NOCOUNT ON;
DECLARE @sep varchar(1) = '|';
WITH src AS (
SELECT
  CONVERT(nvarchar(max), Id) AS Id,
  CONVERT(nvarchar(max), XMID) AS XMID,
  CONVERT(nvarchar(max), TSXMID) AS TSXMID,
  CONVERT(nvarchar(max), DJBH) AS DJBH,
  CONVERT(nvarchar(max), f_HTBH) AS f_HTBH,
  CONVERT(nvarchar(max), f_GYSID) AS f_GYSID,
  CONVERT(nvarchar(max), f_GYSName) AS f_GYSName,
  CONVERT(nvarchar(max), f_QYRQ, 120) AS f_QYRQ,
  CONVERT(nvarchar(max), f_ZT) AS f_ZT,
  CONVERT(nvarchar(max), DJZT) AS DJZT,
  CONVERT(nvarchar(max), ZJE) AS ZJE,
  CONVERT(nvarchar(max), ZJE_NO) AS ZJE_NO,
  CONVERT(nvarchar(max), HTLX) AS HTLX,
  CONVERT(nvarchar(max), HTLX_New) AS HTLX_New,
  CONVERT(nvarchar(max), HTMC) AS HTMC,
  CONVERT(nvarchar(max), DEL) AS DEL,
  CONVERT(nvarchar(max), SCRID) AS SCRID,
  CONVERT(nvarchar(max), SCR) AS SCR,
  CONVERT(nvarchar(max), SCRQ, 120) AS SCRQ
FROM dbo.T_GYSHT_INFO
)
SELECT CONCAT(
  ISNULL(REPLACE(REPLACE(REPLACE(Id, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(XMID, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(TSXMID, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(DJBH, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(f_HTBH, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(f_GYSID, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(f_GYSName, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(f_QYRQ, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(f_ZT, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(DJZT, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(ZJE, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(ZJE_NO, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(HTLX, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(HTLX_New, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(HTMC, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(DEL, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(SCRID, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(SCR, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(SCRQ, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), '')
) AS rowdata
FROM src
ORDER BY Id;
"""

SQL_COLUMNS = [
    "Id",
    "XMID",
    "TSXMID",
    "DJBH",
    "f_HTBH",
    "f_GYSID",
    "f_GYSName",
    "f_QYRQ",
    "f_ZT",
    "DJZT",
    "ZJE",
    "ZJE_NO",
    "HTLX",
    "HTLX_New",
    "HTMC",
    "DEL",
    "SCRID",
    "SCR",
    "SCRQ",
]


class SupplierContractAssetError(Exception):
    pass


def clean(value: object) -> str:
    text = "" if value is None else str(value).strip()
    return "" if text.upper() == "NULL" else text


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SupplierContractAssetError(message)


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


def build_project_map(manifest: dict[str, Any]) -> dict[str, str]:
    result: dict[str, str] = {}
    for row in manifest.get("records", []):
        legacy_id = clean(row.get("target_lookup", {}).get("value"))
        external_id = clean(row.get("external_id"))
        if legacy_id and external_id and row.get("status") == "loadable":
            result[legacy_id] = external_id
    require(result, "project external id map is empty")
    return result


def build_partner_map(manifest: dict[str, Any]) -> dict[str, str]:
    result: dict[str, str] = {}
    for row in manifest.get("records", []):
        legacy_id = clean(row.get("legacy_partner_id"))
        external_id = clean(row.get("external_id"))
        if legacy_id and external_id and row.get("status") == "loadable":
            result[legacy_id] = external_id
    return result


def merge_maps(*maps: dict[str, str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for mapping in maps:
        for key, value in mapping.items():
            result.setdefault(key, value)
    require(result, "merged partner map is empty")
    return result


def parse_amount(value: object) -> Decimal:
    try:
        return Decimal(clean(value) or "0")
    except InvalidOperation:
        return Decimal("0")


def parse_date(value: object) -> str:
    raw = clean(value)
    if not raw:
        return ""
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%m/%d/%Y %H:%M:%S", "%m/%d/%Y"):
        try:
            return datetime.strptime(raw, fmt).date().isoformat()
        except ValueError:
            continue
    return ""


def first_nonempty(row: dict[str, str], fields: list[str]) -> str:
    for field in fields:
        value = clean(row.get(field))
        if value:
            return value
    return ""


def is_deleted(row: dict[str, str]) -> bool:
    return clean(row.get("DEL")) == "1" or bool(clean(row.get("SCRID")) or clean(row.get("SCR")) or clean(row.get("SCRQ")))


def safe_external_suffix(value: str) -> str:
    suffix = re.sub(r"[^0-9A-Za-z_]+", "_", value).strip("_").lower()
    require(bool(suffix), "cannot build external id from blank legacy supplier contract id")
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
        record = ET.SubElement(data, "record", {"id": row["external_id"], "model": "construction.contract"})
        add_text_field(record, "legacy_contract_id", row["legacy_supplier_contract_id"], required=True)
        add_text_field(record, "legacy_project_id", row["legacy_project_id"], required=True)
        add_text_field(record, "legacy_document_no", row["legacy_document_no"])
        add_text_field(record, "legacy_contract_no", row["legacy_contract_no"])
        add_text_field(record, "legacy_status", row["legacy_status"])
        add_text_field(record, "legacy_deleted_flag", row["legacy_deleted_flag"])
        add_text_field(record, "legacy_counterparty_text", row["legacy_counterparty_text"])
        add_text_field(record, "subject", row["subject"], required=True)
        add_text_field(record, "type", "in", required=True)
        add_ref_field(record, "project_id", row["project_external_id"])
        add_ref_field(record, "partner_id", row["partner_external_id"])
        add_text_field(record, "date_contract", row["date_contract"])
        add_text_field(record, "note", row["note"], required=True)
    ET.indent(root, space="  ")
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)


def generate(asset_root: Path, runtime_root: Path, expected_ready: int) -> dict[str, Any]:
    source_rows = parse_sql_rows(run_sql())
    project_by_legacy = build_project_map(load_json(asset_root / "manifest/project_external_id_manifest_v1.json"))
    partner_by_legacy = merge_maps(
        build_partner_map(load_json(asset_root / "manifest/partner_external_id_manifest_v1.json")),
        build_partner_map(load_json(asset_root / "manifest/contract_counterparty_partner_external_id_manifest_v1.json")),
        build_partner_map(load_json(asset_root / "manifest/receipt_counterparty_partner_external_id_manifest_v1.json")),
    )

    loadable: list[dict[str, str]] = []
    blocked: list[dict[str, str]] = []
    counters: Counter[str] = Counter()
    supplier_contract_ids: Counter[str] = Counter()

    for line_no, row in enumerate(source_rows, start=2):
        legacy_id = clean(row.get("Id"))
        legacy_project_id = first_nonempty(row, ["XMID", "TSXMID"])
        legacy_partner_id = clean(row.get("f_GYSID"))
        legacy_contract_no = first_nonempty(row, ["f_HTBH", "DJBH"])
        legacy_document_no = clean(row.get("DJBH"))
        project_external_id = project_by_legacy.get(legacy_project_id, "")
        partner_external_id = partner_by_legacy.get(legacy_partner_id, "")
        amount = parse_amount(row.get("ZJE")) or parse_amount(row.get("ZJE_NO"))
        subject = first_nonempty(row, ["HTMC", "HTLX_New", "HTLX", "f_HTBH", "DJBH"])
        errors: list[str] = []
        if not legacy_id:
            errors.append("missing_legacy_supplier_contract_id")
        if is_deleted(row):
            errors.append("discard_deleted")
        if not legacy_contract_no:
            errors.append("missing_contract_identity")
        if not subject:
            errors.append("missing_subject")
        if not project_external_id:
            errors.append("project_not_in_asset")
        if not legacy_partner_id:
            errors.append("missing_partner_ref")
        elif not partner_external_id:
            errors.append("partner_not_in_asset")

        if errors:
            for error in errors:
                counters[error] += 1
            blocked.append(
                {
                    "line_no": str(line_no),
                    "legacy_supplier_contract_id": legacy_id,
                    "legacy_project_id": legacy_project_id,
                    "legacy_partner_id": legacy_partner_id,
                    "errors": ",".join(errors),
                }
            )
            continue

        supplier_contract_ids[legacy_id] += 1
        loadable.append(
            {
                "external_id": f"legacy_supplier_contract_sc_{safe_external_suffix(legacy_id)}",
                "legacy_supplier_contract_id": legacy_id,
                "legacy_project_id": legacy_project_id,
                "legacy_partner_id": legacy_partner_id,
                "legacy_document_no": legacy_document_no,
                "legacy_contract_no": legacy_contract_no,
                "legacy_status": first_nonempty(row, ["DJZT", "f_ZT"]),
                "legacy_deleted_flag": clean(row.get("DEL")),
                "legacy_counterparty_text": clean(row.get("f_GYSName")),
                "subject": subject,
                "type": "in",
                "project_external_id": project_external_id,
                "partner_external_id": partner_external_id,
                "date_contract": parse_date(row.get("f_QYRQ")),
                "amount_trace": str(amount),
                "note": (
                    "[migration:supplier_contract_header] "
                    f"legacy_supplier_contract_id={legacy_id}; "
                    f"legacy_project_id={legacy_project_id}; "
                    f"legacy_partner_id={legacy_partner_id}; "
                    f"legacy_contract_no={legacy_contract_no}; "
                    f"amount_trace={amount}; "
                    "type_in_supplier_expense=true; "
                    "amount_header_not_written=true"
                ),
            }
        )

    duplicate_ids = sorted(key for key, count in supplier_contract_ids.items() if count > 1)
    require(not duplicate_ids, f"duplicate loadable supplier contract ids: {duplicate_ids[:10]}")
    require(len({row["external_id"] for row in loadable}) == len(loadable), "duplicate XML external ids")
    require(len(loadable) == expected_ready, f"ready supplier contract count drifted: {len(loadable)} != {expected_ready}")

    xml_path = asset_root / XML_REL_PATH
    external_path = asset_root / EXTERNAL_REL_PATH
    validation_path = asset_root / VALIDATION_REL_PATH
    asset_manifest_path = asset_root / ASSET_MANIFEST_REL_PATH
    write_xml(xml_path, loadable)

    external_manifest = {
        "asset_manifest_version": "1.0",
        "asset_package_id": ASSET_PACKAGE_ID,
        "external_id_rule": {
            "legacy_key_policy": "stable_legacy_supplier_contract_pk",
            "pattern": "legacy_supplier_contract_sc_<legacy_supplier_contract_id>",
            "source": "sc",
        },
        "lane_id": "supplier_contract",
        "records": [
            {
                "amount_trace": row["amount_trace"],
                "external_id": row["external_id"],
                "legacy_partner_id": row["legacy_partner_id"],
                "legacy_project_id": row["legacy_project_id"],
                "legacy_supplier_contract_id": row["legacy_supplier_contract_id"],
                "partner_external_id": row["partner_external_id"],
                "project_external_id": row["project_external_id"],
                "status": "loadable",
                "target_model": "construction.contract",
                "target_type": "in",
            }
            for row in loadable
        ],
        "summary": {
            "blocked": len(blocked),
            "loadable": len(loadable),
            "raw_rows": len(source_rows),
        },
    }
    write_json(external_path, external_manifest)

    validation_manifest = {
        "asset_manifest_version": "1.0",
        "asset_package_id": ASSET_PACKAGE_ID,
        "db_writes": 0,
        "generated_at": GENERATED_AT,
        "odoo_shell": False,
        "source_table": "T_GYSHT_INFO",
        "target_model": "construction.contract",
        "target_type": "in",
        "business_boundary": {
            "carrier": "type_in_supplier_expense",
            "type_key_rename": "excluded",
            "header_amount_write": "excluded",
            "tax_write": "excluded",
            "state_replay": "excluded",
            "line_write": "excluded",
        },
        "validation_gates": {
            "generate_time": [
                "legacy_supplier_contract_id_unique",
                "contract_identity_present",
                "subject_present",
                "project_external_id_resolves",
                "partner_external_id_resolves",
                "type_in_supplier_expense",
                "type_key_not_renamed",
                "amount_header_not_written",
                "tax_not_written",
                "state_not_written",
                "line_not_written",
            ],
            "postload": ["xml_external_id_resolves", "draft_defaults_apply"],
        },
        "screen_profile": {
            "blocked_rows": len(blocked),
            "blocker_counts": dict(sorted(counters.items())),
            "ready_rows": len(loadable),
        },
    }
    write_json(validation_path, validation_manifest)

    asset_manifest = {
        "asset_manifest_version": "1.0",
        "asset_package_id": ASSET_PACKAGE_ID,
        "assets": [
            {
                "asset_id": "supplier_contract_header_xml_v1",
                "format": "xml",
                "path": str(XML_REL_PATH),
                "record_count": len(loadable),
                "required": True,
                "sha256": sha256_file(xml_path),
            },
            {
                "asset_id": "supplier_contract_external_id_manifest_v1",
                "format": "json",
                "path": str(EXTERNAL_REL_PATH),
                "record_count": len(loadable),
                "required": True,
                "sha256": sha256_file(external_path),
            },
            {
                "asset_id": "supplier_contract_validation_manifest_v1",
                "format": "json",
                "path": str(VALIDATION_REL_PATH),
                "record_count": 1,
                "required": True,
                "sha256": sha256_file(validation_path),
            },
        ],
        "baseline_package": True,
        "counts": {
            "blocked_records": len(blocked),
            "loadable_records": len(loadable),
            "raw_rows": len(source_rows),
        },
        "db_writes": 0,
        "dependencies": [
            "project_sc_v1",
            "partner_sc_v1",
            "contract_counterparty_partner_sc_v1",
            "receipt_counterparty_partner_sc_v1",
        ],
        "generated_at": GENERATED_AT,
        "idempotency": {
            "conflict_policy": "block_package",
            "duplicate_policy": "update_existing_same_external_id",
            "mode": "odoo_xml_external_id",
        },
        "lane": {
            "business_priority": "supplier_contract_header_fact",
            "lane_id": "supplier_contract",
            "layer": "20_business",
            "risk_class": "supplier_contract_header",
        },
        "load_order": [
            "supplier_contract_header_xml_v1",
            "supplier_contract_external_id_manifest_v1",
            "supplier_contract_validation_manifest_v1",
        ],
        "odoo_shell": False,
        "source_snapshot": {
            "extract_batch_id": "supplier_contract_header_xml_baseline_v1",
            "source_system": "sc",
            "source_tables": ["T_GYSHT_INFO"],
        },
        "target": {
            "identity_field": "legacy_supplier_contract_id",
            "load_strategy": "odoo_xml_external_id",
            "model": "construction.contract",
            "type": "in",
        },
        "validation_gates": [
            "source_supplier_contract_query_passed",
            "legacy_supplier_contract_id_non_empty",
            "legacy_supplier_contract_id_unique",
            "contract_identity_present",
            "project_anchor_resolves",
            "partner_anchor_resolves",
            "type_in_supplier_expense",
            "type_key_not_renamed",
            "amount_header_not_written",
            "tax_not_written",
            "state_not_written",
            "line_not_written",
        ],
    }
    write_json(asset_manifest_path, asset_manifest)

    runtime_root.mkdir(parents=True, exist_ok=True)
    write_json(runtime_root / "supplier_contract_blocked_v1.json", {"blocked": blocked, "blocker_counts": dict(counters)})
    return {
        "status": "PASS",
        "asset_package_id": ASSET_PACKAGE_ID,
        "db_writes": 0,
        "odoo_shell": False,
        "raw_rows": len(source_rows),
        "loadable_records": len(loadable),
        "blocked_records": len(blocked),
        "asset_manifest_sha256": sha256_file(asset_manifest_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate legacy supplier contract XML migration assets.")
    parser.add_argument("--asset-root", default=str(REPO_ASSET_ROOT))
    parser.add_argument("--runtime-root", default=str(RUNTIME_ROOT))
    parser.add_argument("--expected-ready", type=int, default=5301)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    try:
        result = generate(Path(args.asset_root), Path(args.runtime_root), args.expected_ready)
    except (SupplierContractAssetError, json.JSONDecodeError) as exc:
        payload = {"status": "FAIL", "error": str(exc), "db_writes": 0, "odoo_shell": False}
        print("SUPPLIER_CONTRACT_ASSET_GENERATOR=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 1 if args.check else 0

    print("SUPPLIER_CONTRACT_ASSET_GENERATOR=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
