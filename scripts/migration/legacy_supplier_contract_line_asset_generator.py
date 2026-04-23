#!/usr/bin/env python3
"""Generate repository XML assets for supplier contract summary amount lines."""

from __future__ import annotations

import argparse
import csv
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
RUNTIME_ROOT = Path(".runtime_artifacts/migration_assets/supplier_contract_line_sc_v1")
XML_REL_PATH = Path("20_business/supplier_contract_line/supplier_contract_summary_line_v1.xml")
EXTERNAL_REL_PATH = Path("manifest/supplier_contract_line_external_id_manifest_v1.json")
VALIDATION_REL_PATH = Path("manifest/supplier_contract_line_validation_manifest_v1.json")
ASSET_MANIFEST_REL_PATH = Path("manifest/supplier_contract_line_asset_manifest_v1.json")
ASSET_PACKAGE_ID = "supplier_contract_line_sc_v1"
GENERATED_AT = "2026-04-15T12:45:00+00:00"
EXPECTED_RAW_ROWS = 5535

SQL = r"""
SET NOCOUNT ON;
DECLARE @sep varchar(1) = '|';
WITH src AS (
SELECT
  CONVERT(nvarchar(max), Id) AS Id,
  CONVERT(nvarchar(max), ZJE) AS ZJE,
  CONVERT(nvarchar(max), ZJE_NO) AS ZJE_NO,
  CONVERT(nvarchar(max), ZSL) AS ZSL,
  CONVERT(nvarchar(max), DJ) AS DJ,
  CONVERT(nvarchar(max), CLMC) AS CLMC,
  CONVERT(nvarchar(max), DEL) AS DEL,
  CONVERT(nvarchar(max), SCRID) AS SCRID,
  CONVERT(nvarchar(max), SCR) AS SCR,
  CONVERT(nvarchar(max), SCRQ, 120) AS SCRQ
FROM dbo.T_GYSHT_INFO
)
SELECT CONCAT(
  ISNULL(REPLACE(REPLACE(REPLACE(Id, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(ZJE, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(ZJE_NO, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(ZSL, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(DJ, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(CLMC, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(DEL, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(SCRID, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(SCR, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(SCRQ, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), '')
) AS rowdata
FROM src
ORDER BY Id;
"""

SQL_COLUMNS = ["Id", "ZJE", "ZJE_NO", "ZSL", "DJ", "CLMC", "DEL", "SCRID", "SCR", "SCRQ"]


class SupplierContractLineAssetError(Exception):
    pass


def clean(value: object) -> str:
    text = "" if value is None else str(value).strip()
    return "" if text.upper() == "NULL" else text


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SupplierContractLineAssetError(message)


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


def load_supplier_contract_map(asset_root: Path) -> dict[str, str]:
    manifest = load_json(asset_root / "manifest/supplier_contract_external_id_manifest_v1.json")
    result: dict[str, str] = {}
    for row in manifest.get("records", []):
        legacy_id = clean(row.get("legacy_supplier_contract_id"))
        external_id = clean(row.get("external_id"))
        if legacy_id and external_id and row.get("status") == "loadable":
            result[legacy_id] = external_id
    require(len(result) == 5301, f"supplier contract anchor count drifted: {len(result)} != 5301")
    return result


def parse_amount(value: object) -> Decimal:
    try:
        return Decimal(clean(value) or "0")
    except InvalidOperation:
        return Decimal("0")


def best_amount(row: dict[str, str]) -> tuple[str, Decimal]:
    for field in ("ZJE", "ZJE_NO"):
        amount = parse_amount(row.get(field))
        if amount > 0:
            return field, amount
    return "", Decimal("0")


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
        record = ET.SubElement(data, "record", {"id": row["external_id"], "model": "construction.contract.line"})
        add_ref_field(record, "contract_id", row["contract_external_id"])
        add_text_field(record, "sequence", "10", required=True)
        add_text_field(record, "qty_contract", "1", required=True)
        add_text_field(record, "price_contract", row["amount"], required=True)
        add_text_field(record, "note", row["note"], required=True)
    ET.indent(root, space="  ")
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)


def generate(asset_root: Path, runtime_root: Path, expected_ready: int) -> dict[str, Any]:
    source_rows = parse_sql_rows(run_sql())
    contract_by_legacy = load_supplier_contract_map(asset_root)
    loadable: list[dict[str, str]] = []
    blocked: list[dict[str, str]] = []
    counters: Counter[str] = Counter()
    amount_source_counts: Counter[str] = Counter()
    line_ids: Counter[str] = Counter()

    for line_no, row in enumerate(source_rows, start=2):
        legacy_id = clean(row.get("Id"))
        contract_external_id = contract_by_legacy.get(legacy_id, "")
        amount_source, amount = best_amount(row)
        errors: list[str] = []
        if not legacy_id:
            errors.append("missing_legacy_supplier_contract_id")
        if is_deleted(row):
            errors.append("discard_deleted")
        if not contract_external_id:
            errors.append("supplier_contract_anchor_missing")
        if amount <= 0:
            errors.append("amount_not_positive")

        if errors:
            for error in errors:
                counters[error] += 1
            blocked.append(
                {
                    "line_no": str(line_no),
                    "legacy_supplier_contract_id": legacy_id,
                    "errors": ",".join(errors),
                }
            )
            continue

        amount_source_counts[amount_source] += 1
        external_id = f"legacy_supplier_contract_line_sc_{safe_external_suffix(legacy_id)}"
        line_ids[external_id] += 1
        loadable.append(
            {
                "external_id": external_id,
                "legacy_supplier_contract_id": legacy_id,
                "contract_external_id": contract_external_id,
                "amount": str(amount),
                "amount_source": amount_source,
                "legacy_qty": clean(row.get("ZSL")),
                "legacy_price": clean(row.get("DJ")),
                "legacy_line_name": clean(row.get("CLMC")),
                "note": (
                    "[migration:supplier_contract_summary_line] "
                    f"legacy_supplier_contract_id={legacy_id}; "
                    f"amount_source={amount_source}; "
                    f"source_amount={amount}; "
                    f"legacy_qty={clean(row.get('ZSL'))}; "
                    f"legacy_price={clean(row.get('DJ'))}; "
                    "summary_amount_line=true; "
                    "qty_contract_one=true; "
                    "price_contract_source_amount=true; "
                    "header_amount_not_written=true"
                ),
            }
        )

    duplicate_ids = sorted(key for key, count in line_ids.items() if count > 1)
    require(not duplicate_ids, f"duplicate supplier contract line external ids: {duplicate_ids[:10]}")
    require(len(loadable) == expected_ready, f"ready supplier contract line count drifted: {len(loadable)} != {expected_ready}")

    xml_path = asset_root / XML_REL_PATH
    external_path = asset_root / EXTERNAL_REL_PATH
    validation_path = asset_root / VALIDATION_REL_PATH
    asset_manifest_path = asset_root / ASSET_MANIFEST_REL_PATH
    write_xml(xml_path, loadable)

    external_manifest = {
        "asset_manifest_version": "1.0",
        "asset_package_id": ASSET_PACKAGE_ID,
        "external_id_rule": {
            "legacy_key_policy": "stable_legacy_supplier_contract_pk_summary_line",
            "pattern": "legacy_supplier_contract_line_sc_<legacy_supplier_contract_id>",
            "source": "sc",
        },
        "lane_id": "supplier_contract_line",
        "records": [
            {
                "amount": row["amount"],
                "amount_source": row["amount_source"],
                "contract_external_id": row["contract_external_id"],
                "external_id": row["external_id"],
                "legacy_supplier_contract_id": row["legacy_supplier_contract_id"],
                "status": "loadable",
                "summary_amount_line": True,
                "target_model": "construction.contract.line",
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
        "target_model": "construction.contract.line",
        "business_boundary": {
            "summary_amount_line": "included",
            "qty_contract": "constant_1",
            "price_contract": "source_total_amount",
            "header_amount_write": "excluded",
            "legacy_quantity_unit_price_detail": "not_claimed",
        },
        "validation_gates": {
            "generate_time": [
                "legacy_supplier_contract_id_unique",
                "supplier_contract_external_id_resolves",
                "amount_positive",
                "summary_amount_line",
                "qty_contract_one",
                "price_contract_source_amount",
                "header_amount_not_written",
            ],
            "postload": ["xml_external_id_resolves", "header_totals_compute_from_lines"],
        },
        "screen_profile": {
            "blocked_rows": len(blocked),
            "blocker_counts": dict(sorted(counters.items())),
            "ready_rows": len(loadable),
            "amount_source_counts": dict(sorted(amount_source_counts.items())),
        },
    }
    write_json(validation_path, validation_manifest)

    asset_manifest = {
        "asset_manifest_version": "1.0",
        "asset_package_id": ASSET_PACKAGE_ID,
        "assets": [
            {
                "asset_id": "supplier_contract_summary_line_xml_v1",
                "format": "xml",
                "path": str(XML_REL_PATH),
                "record_count": len(loadable),
                "required": True,
                "sha256": sha256_file(xml_path),
            },
            {
                "asset_id": "supplier_contract_line_external_id_manifest_v1",
                "format": "json",
                "path": str(EXTERNAL_REL_PATH),
                "record_count": len(loadable),
                "required": True,
                "sha256": sha256_file(external_path),
            },
            {
                "asset_id": "supplier_contract_line_validation_manifest_v1",
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
        "dependencies": ["supplier_contract_sc_v1"],
        "generated_at": GENERATED_AT,
        "idempotency": {
            "conflict_policy": "block_package",
            "duplicate_policy": "update_existing_same_external_id",
            "mode": "odoo_xml_external_id",
        },
        "lane": {
            "business_priority": "supplier_contract_amount_fact",
            "lane_id": "supplier_contract_line",
            "layer": "20_business",
            "risk_class": "summary_amount_line",
        },
        "load_order": [
            "supplier_contract_summary_line_xml_v1",
            "supplier_contract_line_external_id_manifest_v1",
            "supplier_contract_line_validation_manifest_v1",
        ],
        "odoo_shell": False,
        "source_snapshot": {
            "extract_batch_id": "supplier_contract_summary_line_xml_baseline_v1",
            "source_system": "sc",
            "source_tables": ["T_GYSHT_INFO"],
        },
        "target": {
            "identity_field": "legacy_supplier_contract_id",
            "load_strategy": "odoo_xml_external_id",
            "model": "construction.contract.line",
        },
        "validation_gates": [
            "source_supplier_contract_line_query_passed",
            "legacy_supplier_contract_id_non_empty",
            "supplier_contract_anchor_resolves",
            "amount_positive",
            "summary_amount_line",
            "qty_contract_one",
            "price_contract_source_amount",
            "header_amount_not_written",
        ],
    }
    write_json(asset_manifest_path, asset_manifest)

    runtime_root.mkdir(parents=True, exist_ok=True)
    write_json(runtime_root / "supplier_contract_line_blocked_v1.json", {"blocked": blocked, "blocker_counts": dict(counters)})
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
    parser = argparse.ArgumentParser(description="Generate supplier contract summary line XML migration assets.")
    parser.add_argument("--asset-root", default=str(REPO_ASSET_ROOT))
    parser.add_argument("--runtime-root", default=str(RUNTIME_ROOT))
    parser.add_argument("--expected-ready", type=int, default=5065)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    try:
        result = generate(Path(args.asset_root), Path(args.runtime_root), args.expected_ready)
    except (SupplierContractLineAssetError, json.JSONDecodeError) as exc:
        payload = {"status": "FAIL", "error": str(exc), "db_writes": 0, "odoo_shell": False}
        print("SUPPLIER_CONTRACT_LINE_ASSET_GENERATOR=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 1 if args.check else 0

    print("SUPPLIER_CONTRACT_LINE_ASSET_GENERATOR=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
