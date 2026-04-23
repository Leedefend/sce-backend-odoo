#!/usr/bin/env python3
"""Generate repository XML assets for legacy outflow request line facts."""

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
RUNTIME_ROOT = Path(".runtime_artifacts/migration_assets/outflow_request_line_sc_v1")
XML_REL_PATH = Path("20_business/outflow_request_line/outflow_request_line_v1.xml")
EXTERNAL_REL_PATH = Path("manifest/outflow_request_line_external_id_manifest_v1.json")
VALIDATION_REL_PATH = Path("manifest/outflow_request_line_validation_manifest_v1.json")
ASSET_MANIFEST_REL_PATH = Path("manifest/outflow_request_line_asset_manifest_v1.json")
ASSET_PACKAGE_ID = "outflow_request_line_sc_v1"
GENERATED_AT = "2026-04-15T14:30:00+00:00"
EXPECTED_RAW_ROWS = 17413

SQL = r"""
SET NOCOUNT ON;
DECLARE @sep varchar(1) = '|';
WITH src AS (
SELECT
  CONVERT(nvarchar(max), Id) AS Id,
  CONVERT(nvarchar(max), ZFSQID) AS ZFSQID,
  CONVERT(nvarchar(max), SupplierId) AS SupplierId,
  CONVERT(nvarchar(max), DJBH) AS DJBH,
  CONVERT(nvarchar(max), ZJE) AS ZJE,
  CONVERT(nvarchar(max), YGLZF) AS YGLZF,
  CONVERT(nvarchar(max), SY) AS SY,
  CONVERT(nvarchar(max), CCZFJE) AS CCZFJE,
  CONVERT(nvarchar(max), LX) AS LX,
  CONVERT(nvarchar(max), GLYWID) AS GLYWID,
  CONVERT(nvarchar(max), D_SCBSJS_DWMC) AS D_SCBSJS_DWMC,
  CONVERT(nvarchar(max), D_SCBSJS_HTZBH) AS D_SCBSJS_HTZBH,
  CONVERT(nvarchar(max), FPBHSJE) AS FPBHSJE
FROM dbo.C_ZFSQGL_CB
)
SELECT CONCAT(
  ISNULL(REPLACE(REPLACE(REPLACE(Id, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(ZFSQID, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(SupplierId, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(DJBH, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(ZJE, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(YGLZF, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(SY, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(CCZFJE, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(LX, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(GLYWID, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(D_SCBSJS_DWMC, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(D_SCBSJS_HTZBH, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(FPBHSJE, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), '')
) AS rowdata
FROM src
ORDER BY Id;
"""

SQL_COLUMNS = [
    "Id",
    "ZFSQID",
    "SupplierId",
    "DJBH",
    "ZJE",
    "YGLZF",
    "SY",
    "CCZFJE",
    "LX",
    "GLYWID",
    "D_SCBSJS_DWMC",
    "D_SCBSJS_HTZBH",
    "FPBHSJE",
]


class OutflowRequestLineAssetError(Exception):
    pass


def clean(value: object) -> str:
    text = "" if value is None else str(value).strip()
    return "" if text.upper() == "NULL" else text


def require(condition: bool, message: str) -> None:
    if not condition:
        raise OutflowRequestLineAssetError(message)


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


def load_outflow_request_map(asset_root: Path) -> dict[str, str]:
    manifest = load_json(asset_root / "manifest/outflow_request_external_id_manifest_v1.json")
    result: dict[str, str] = {}
    for row in manifest.get("records", []):
        legacy_id = clean(row.get("legacy_outflow_id"))
        external_id = clean(row.get("external_id"))
        if legacy_id and external_id and row.get("status") == "loadable":
            result[legacy_id] = external_id
    require(result, "outflow request anchor map is empty")
    return result


def load_supplier_contract_map(asset_root: Path) -> dict[str, str]:
    manifest = load_json(asset_root / "manifest/supplier_contract_external_id_manifest_v1.json")
    result: dict[str, str] = {}
    for row in manifest.get("records", []):
        legacy_id = clean(row.get("legacy_supplier_contract_id"))
        external_id = clean(row.get("external_id"))
        if legacy_id and external_id and row.get("status") == "loadable":
            result[legacy_id] = external_id
    return result


def parse_amount(value: object) -> Decimal:
    try:
        return Decimal(clean(value) or "0")
    except InvalidOperation:
        return Decimal("0")


def best_amount(row: dict[str, str]) -> tuple[str, Decimal]:
    for field in ("ZJE", "CCZFJE", "FPBHSJE"):
        amount = parse_amount(row.get(field))
        if amount > 0:
            return field, amount
    return "", Decimal("0")


def safe_external_suffix(value: str) -> str:
    suffix = re.sub(r"[^0-9A-Za-z_]+", "_", value).strip("_").lower()
    require(bool(suffix), "cannot build external id from blank legacy outflow line id")
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
        record = ET.SubElement(data, "record", {"id": row["external_id"], "model": "payment.request.line"})
        add_ref_field(record, "request_id", row["outflow_request_external_id"])
        add_text_field(record, "sequence", row["sequence"], required=True)
        add_text_field(record, "legacy_line_id", row["legacy_outflow_line_id"], required=True)
        add_text_field(record, "legacy_parent_id", row["legacy_outflow_id"], required=True)
        add_text_field(record, "legacy_supplier_contract_id", row["legacy_supplier_contract_id"])
        add_text_field(record, "source_document_no", row["source_document_no"])
        add_text_field(record, "source_line_type", row["line_type"])
        add_text_field(record, "source_counterparty_text", row["source_counterparty_text"])
        add_text_field(record, "source_contract_no", row["source_contract_no"])
        if row["supplier_contract_external_id"]:
            add_ref_field(record, "contract_id", row["supplier_contract_external_id"])
        add_text_field(record, "amount", row["amount"], required=True)
        add_text_field(record, "paid_before_amount", row["paid_before_amount"])
        add_text_field(record, "remaining_amount", row["remaining_amount"])
        add_text_field(record, "current_pay_amount", row["current_pay_amount"])
        add_text_field(record, "note", row["note"], required=True)
    ET.indent(root, space="  ")
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)


def generate(asset_root: Path, runtime_root: Path, expected_ready: int) -> dict[str, Any]:
    source_rows = parse_sql_rows(run_sql())
    outflow_by_legacy = load_outflow_request_map(asset_root)
    supplier_contract_by_legacy = load_supplier_contract_map(asset_root)
    loadable: list[dict[str, str]] = []
    blocked: list[dict[str, str]] = []
    counters: Counter[str] = Counter()
    amount_source_counts: Counter[str] = Counter()
    supplier_contract_anchor_counts: Counter[str] = Counter()
    external_ids: Counter[str] = Counter()

    for line_no, row in enumerate(source_rows, start=2):
        legacy_line_id = clean(row.get("Id"))
        legacy_outflow_id = clean(row.get("ZFSQID"))
        outflow_external_id = outflow_by_legacy.get(legacy_outflow_id, "")
        legacy_supplier_contract_id = clean(row.get("GLYWID"))
        supplier_contract_external_id = supplier_contract_by_legacy.get(legacy_supplier_contract_id, "")
        amount_source, amount = best_amount(row)
        errors: list[str] = []
        if not legacy_line_id:
            errors.append("missing_legacy_outflow_line_id")
        if not legacy_outflow_id:
            errors.append("missing_parent_outflow_id")
        elif not outflow_external_id:
            errors.append("outflow_request_anchor_missing")
        if amount <= 0:
            errors.append("amount_not_positive")

        if supplier_contract_external_id:
            supplier_contract_anchor_counts["supplier_contract_anchor_resolved"] += 1
        elif legacy_supplier_contract_id:
            supplier_contract_anchor_counts["supplier_contract_anchor_unresolved"] += 1
        else:
            supplier_contract_anchor_counts["supplier_contract_anchor_empty"] += 1

        if errors:
            for error in errors:
                counters[error] += 1
            blocked.append(
                {
                    "line_no": str(line_no),
                    "legacy_outflow_line_id": legacy_line_id,
                    "legacy_outflow_id": legacy_outflow_id,
                    "errors": ",".join(errors),
                }
            )
            continue

        amount_source_counts[amount_source] += 1
        external_id = f"legacy_outflow_request_line_sc_{safe_external_suffix(legacy_line_id)}"
        external_ids[external_id] += 1
        loadable.append(
            {
                "external_id": external_id,
                "sequence": str(len(loadable) + 10),
                "legacy_outflow_line_id": legacy_line_id,
                "legacy_outflow_id": legacy_outflow_id,
                "outflow_request_external_id": outflow_external_id,
                "legacy_supplier_contract_id": legacy_supplier_contract_id,
                "supplier_contract_external_id": supplier_contract_external_id,
                "amount": str(amount),
                "amount_source": amount_source,
                "paid_before_amount": str(parse_amount(row.get("YGLZF"))),
                "remaining_amount": str(parse_amount(row.get("SY"))),
                "current_pay_amount": str(parse_amount(row.get("CCZFJE"))),
                "line_type": clean(row.get("LX")),
                "source_document_no": clean(row.get("DJBH")),
                "source_counterparty_text": clean(row.get("D_SCBSJS_DWMC")),
                "source_contract_no": clean(row.get("D_SCBSJS_HTZBH")),
                "note": (
                    "[migration:outflow_request_line] "
                    f"legacy_outflow_line_id={legacy_line_id}; "
                    f"legacy_outflow_id={legacy_outflow_id}; "
                    f"amount_source={amount_source}; "
                    "line_fact=true; "
                    "not_ledger=true; "
                    "not_settlement=true"
                ),
            }
        )

    duplicate_ids = sorted(key for key, count in external_ids.items() if count > 1)
    require(not duplicate_ids, f"duplicate outflow request line external ids: {duplicate_ids[:10]}")
    require(len(loadable) == expected_ready, f"ready outflow request line count drifted: {len(loadable)} != {expected_ready}")

    xml_path = asset_root / XML_REL_PATH
    external_path = asset_root / EXTERNAL_REL_PATH
    validation_path = asset_root / VALIDATION_REL_PATH
    asset_manifest_path = asset_root / ASSET_MANIFEST_REL_PATH
    write_xml(xml_path, loadable)

    external_manifest = {
        "asset_manifest_version": "1.0",
        "asset_package_id": ASSET_PACKAGE_ID,
        "external_id_rule": {
            "legacy_key_policy": "stable_legacy_outflow_request_line_pk",
            "pattern": "legacy_outflow_request_line_sc_<legacy_outflow_line_id>",
            "source": "sc",
        },
        "lane_id": "outflow_request_line",
        "records": [
            {
                "amount": row["amount"],
                "amount_source": row["amount_source"],
                "external_id": row["external_id"],
                "legacy_outflow_id": row["legacy_outflow_id"],
                "legacy_outflow_line_id": row["legacy_outflow_line_id"],
                "outflow_request_external_id": row["outflow_request_external_id"],
                "status": "loadable",
                "supplier_contract_external_id": row["supplier_contract_external_id"],
                "target_model": "payment.request.line",
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
        "source_table": "C_ZFSQGL_CB",
        "target_model": "payment.request.line",
        "business_boundary": {
            "line_fact": "included",
            "parent_outflow_request_anchor": "required",
            "supplier_contract_anchor": "optional_when_resolved",
            "ledger_fact": "excluded",
            "settlement_fact": "excluded",
        },
        "validation_gates": {
            "generate_time": [
                "legacy_outflow_line_id_unique",
                "outflow_request_external_id_resolves",
                "amount_positive",
                "supplier_contract_external_id_resolves_when_emitted",
                "line_fact_not_ledger",
                "line_fact_not_settlement",
            ],
            "postload": ["xml_external_id_resolves", "parent_request_line_visible"],
        },
        "screen_profile": {
            "blocked_rows": len(blocked),
            "blocker_counts": dict(sorted(counters.items())),
            "ready_rows": len(loadable),
            "amount_source_counts": dict(sorted(amount_source_counts.items())),
            "supplier_contract_anchor_counts": dict(sorted(supplier_contract_anchor_counts.items())),
        },
    }
    write_json(validation_path, validation_manifest)

    asset_manifest = {
        "asset_manifest_version": "1.0",
        "asset_package_id": ASSET_PACKAGE_ID,
        "assets": [
            {
                "asset_id": "outflow_request_line_xml_v1",
                "format": "xml",
                "path": str(XML_REL_PATH),
                "record_count": len(loadable),
                "required": True,
                "sha256": sha256_file(xml_path),
            },
            {
                "asset_id": "outflow_request_line_external_id_manifest_v1",
                "format": "json",
                "path": str(EXTERNAL_REL_PATH),
                "record_count": len(loadable),
                "required": True,
                "sha256": sha256_file(external_path),
            },
            {
                "asset_id": "outflow_request_line_validation_manifest_v1",
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
        "dependencies": ["outflow_request_sc_v1", "supplier_contract_sc_v1"],
        "generated_at": GENERATED_AT,
        "idempotency": {
            "conflict_policy": "block_package",
            "duplicate_policy": "update_existing_same_external_id",
            "mode": "odoo_xml_external_id",
        },
        "lane": {
            "business_priority": "outflow_request_line_fact",
            "lane_id": "outflow_request_line",
            "layer": "20_business",
            "risk_class": "line_fact",
        },
        "load_order": [
            "outflow_request_line_xml_v1",
            "outflow_request_line_external_id_manifest_v1",
            "outflow_request_line_validation_manifest_v1",
        ],
        "odoo_shell": False,
        "source_snapshot": {
            "extract_batch_id": "outflow_request_line_xml_baseline_v1",
            "source_system": "sc",
            "source_tables": ["C_ZFSQGL_CB"],
        },
        "target": {
            "identity_field": "legacy_outflow_line_id",
            "load_strategy": "odoo_xml_external_id",
            "model": "payment.request.line",
        },
        "validation_gates": [
            "source_outflow_request_line_query_passed",
            "legacy_outflow_line_id_non_empty",
            "outflow_request_anchor_resolves",
            "amount_positive",
            "supplier_contract_anchor_resolves_when_emitted",
            "line_fact_not_ledger",
            "line_fact_not_settlement",
        ],
    }
    write_json(asset_manifest_path, asset_manifest)

    runtime_root.mkdir(parents=True, exist_ok=True)
    write_json(runtime_root / "outflow_request_line_blocked_v1.json", {"blocked": blocked, "blocker_counts": dict(counters)})
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
    parser = argparse.ArgumentParser(description="Generate outflow request line XML migration assets.")
    parser.add_argument("--asset-root", default=str(REPO_ASSET_ROOT))
    parser.add_argument("--runtime-root", default=str(RUNTIME_ROOT))
    parser.add_argument("--expected-ready", type=int, default=15917)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    try:
        result = generate(Path(args.asset_root), Path(args.runtime_root), args.expected_ready)
    except (OutflowRequestLineAssetError, json.JSONDecodeError) as exc:
        payload = {"status": "FAIL", "error": str(exc), "db_writes": 0, "odoo_shell": False}
        print("OUTFLOW_REQUEST_LINE_ASSET_GENERATOR=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 1 if args.check else 0

    print("OUTFLOW_REQUEST_LINE_ASSET_GENERATOR=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
