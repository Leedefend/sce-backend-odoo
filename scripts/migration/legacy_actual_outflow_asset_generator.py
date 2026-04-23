#!/usr/bin/env python3
"""Generate repository XML assets for legacy actual outflow facts."""

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
RUNTIME_ROOT = Path(".runtime_artifacts/migration_assets/actual_outflow_sc_v1")
XML_REL_PATH = Path("20_business/actual_outflow/actual_outflow_core_v1.xml")
EXTERNAL_REL_PATH = Path("manifest/actual_outflow_external_id_manifest_v1.json")
VALIDATION_REL_PATH = Path("manifest/actual_outflow_validation_manifest_v1.json")
ASSET_MANIFEST_REL_PATH = Path("manifest/actual_outflow_asset_manifest_v1.json")
ASSET_PACKAGE_ID = "actual_outflow_sc_v1"
GENERATED_AT = "2026-04-15T11:10:00+00:00"
EXPECTED_RAW_ROWS = 13629

SQL = r"""
SET NOCOUNT ON;
SELECT
  Id,
  f_XMID,
  f_LYXMID,
  TSXMID,
  f_SupplierID,
  f_ZFSQGLId,
  f_FKJE,
  f_FKRQ,
  DJBH,
  DEL,
  f_SupplierName,
  ZFSQDH
FROM dbo.T_FK_Supplier
ORDER BY Id;
"""


class ActualOutflowAssetError(Exception):
    pass


def clean(value: object) -> str:
    text = "" if value is None else str(value).strip()
    return "" if text.upper() == "NULL" else text


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ActualOutflowAssetError(message)


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
    reader = csv.reader(output.splitlines(), delimiter="|")
    header: list[str] | None = None
    for raw_parts in reader:
        parts = [part.strip() for part in raw_parts]
        if not parts or len(parts) < 2:
            continue
        if parts[0] == "Id":
            header = parts
            continue
        if header is None or len(parts) != len(header):
            continue
        if all(part and set(part) <= {"-"} for part in parts):
            continue
        rows.append(dict(zip(header, parts)))
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
    require(result, "merged map is empty")
    return result


def build_request_map(manifest: dict[str, Any]) -> dict[str, str]:
    result: dict[str, str] = {}
    for row in manifest.get("records", []):
        legacy_id = clean(row.get("legacy_outflow_id"))
        external_id = clean(row.get("external_id"))
        if legacy_id and external_id and row.get("status") == "loadable":
            result[legacy_id] = external_id
    require(result, "outflow request external id map is empty")
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
    for fmt in ("%m/%d/%Y %H:%M:%S", "%m/%d/%Y", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
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
    return clean(row.get("DEL")) == "1"


def safe_external_suffix(value: str) -> str:
    suffix = re.sub(r"[^0-9A-Za-z_]+", "_", value).strip("_").lower()
    require(bool(suffix), "cannot build external id from blank legacy actual outflow id")
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
        record = ET.SubElement(data, "record", {"id": row["external_id"], "model": "payment.request"})
        add_text_field(record, "type", "pay", required=True)
        add_ref_field(record, "project_id", row["project_external_id"])
        add_ref_field(record, "partner_id", row["partner_external_id"])
        add_text_field(record, "amount", row["amount"], required=True)
        add_text_field(record, "date_request", row["date_request"])
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
    request_by_legacy = build_request_map(load_json(asset_root / "manifest/outflow_request_external_id_manifest_v1.json"))

    loadable: list[dict[str, str]] = []
    blocked: list[dict[str, str]] = []
    counters: Counter[str] = Counter()
    request_anchor_counts: Counter[str] = Counter()
    actual_outflow_ids: Counter[str] = Counter()

    for line_no, row in enumerate(source_rows, start=2):
        legacy_actual_outflow_id = clean(row.get("Id"))
        legacy_project_id = first_nonempty(row, ["f_XMID", "f_LYXMID", "TSXMID"])
        legacy_partner_id = clean(row.get("f_SupplierID"))
        legacy_request_id = clean(row.get("f_ZFSQGLId"))
        amount = parse_amount(row.get("f_FKJE"))
        project_external_id = project_by_legacy.get(legacy_project_id, "")
        partner_external_id = partner_by_legacy.get(legacy_partner_id, "")
        request_external_id = request_by_legacy.get(legacy_request_id, "") if legacy_request_id else ""
        errors: list[str] = []
        if not legacy_actual_outflow_id:
            errors.append("missing_legacy_actual_outflow_id")
        if is_deleted(row):
            errors.append("discard_deleted")
        if amount <= 0:
            errors.append("zero_or_negative_amount")
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
                    "legacy_actual_outflow_id": legacy_actual_outflow_id,
                    "legacy_project_id": legacy_project_id,
                    "legacy_partner_id": legacy_partner_id,
                    "legacy_request_id": legacy_request_id,
                    "errors": ",".join(errors),
                }
            )
            continue

        actual_outflow_ids[legacy_actual_outflow_id] += 1
        if request_external_id:
            request_anchor_policy = "request_ref"
        elif legacy_request_id:
            request_anchor_policy = "request_optional_unresolved"
        else:
            request_anchor_policy = "request_optional_empty"
        request_anchor_counts[request_anchor_policy] += 1
        document_no = clean(row.get("DJBH")) or clean(row.get("ZFSQDH"))
        supplier_name = clean(row.get("f_SupplierName"))
        loadable.append(
            {
                "external_id": f"legacy_actual_outflow_sc_{safe_external_suffix(legacy_actual_outflow_id)}",
                "legacy_actual_outflow_id": legacy_actual_outflow_id,
                "legacy_project_id": legacy_project_id,
                "legacy_partner_id": legacy_partner_id,
                "legacy_request_id": legacy_request_id,
                "project_external_id": project_external_id,
                "partner_external_id": partner_external_id,
                "request_external_id": request_external_id,
                "request_anchor_policy": request_anchor_policy,
                "amount": str(amount),
                "date_request": parse_date(row.get("f_FKRQ")),
                "document_no": document_no,
                "note": (
                    "[migration:actual_outflow_core] "
                    f"legacy_actual_outflow_id={legacy_actual_outflow_id}; "
                    f"legacy_project_id={legacy_project_id}; "
                    f"legacy_partner_id={legacy_partner_id}; "
                    f"legacy_request_id={legacy_request_id}; "
                    f"request_anchor_policy={request_anchor_policy}; "
                    f"request_external_id={request_external_id}; "
                    f"document_no={document_no}; "
                    f"supplier_name={supplier_name}"
                ),
            }
        )

    duplicate_ids = sorted(key for key, count in actual_outflow_ids.items() if count > 1)
    require(not duplicate_ids, f"duplicate loadable actual outflow ids: {duplicate_ids[:10]}")
    require(len({row["external_id"] for row in loadable}) == len(loadable), "duplicate XML external ids")
    require(len(loadable) == expected_ready, f"ready actual outflow count drifted: {len(loadable)} != {expected_ready}")

    xml_path = asset_root / XML_REL_PATH
    external_path = asset_root / EXTERNAL_REL_PATH
    validation_path = asset_root / VALIDATION_REL_PATH
    asset_manifest_path = asset_root / ASSET_MANIFEST_REL_PATH
    write_xml(xml_path, loadable)

    external_manifest = {
        "asset_manifest_version": "1.0",
        "asset_package_id": ASSET_PACKAGE_ID,
        "external_id_rule": {
            "legacy_key_policy": "stable_legacy_actual_outflow_pk",
            "pattern": "legacy_actual_outflow_sc_<legacy_actual_outflow_id>",
            "source": "sc",
        },
        "lane_id": "actual_outflow",
        "records": [
            {
                "amount": row["amount"],
                "external_id": row["external_id"],
                "legacy_actual_outflow_id": row["legacy_actual_outflow_id"],
                "legacy_partner_id": row["legacy_partner_id"],
                "legacy_project_id": row["legacy_project_id"],
                "legacy_request_id": row["legacy_request_id"],
                "partner_external_id": row["partner_external_id"],
                "project_external_id": row["project_external_id"],
                "request_anchor_policy": row["request_anchor_policy"],
                "request_external_id": row["request_external_id"],
                "status": "loadable",
                "target_model": "payment.request",
                "target_type": "pay",
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
        "source_table": "T_FK_Supplier",
        "target_model": "payment.request",
        "target_type": "pay",
        "business_boundary": {
            "carrier": "draft_carrier",
            "state_replay": "excluded",
            "settlement_link": "excluded",
            "ledger": "excluded",
            "accounting": "excluded",
            "workflow": "excluded",
        },
        "validation_gates": {
            "generate_time": [
                "legacy_actual_outflow_id_unique",
                "amount_positive",
                "project_external_id_resolves",
                "partner_external_id_resolves",
                "type_pay_only",
                "state_not_written",
                "settlement_not_written",
                "ledger_not_written",
                "accounting_not_written",
                "workflow_not_written",
                "source_request_anchor_optional",
            ],
            "postload": ["xml_external_id_resolves", "draft_defaults_apply"],
        },
        "screen_profile": {
            "blocked_rows": len(blocked),
            "blocker_counts": dict(sorted(counters.items())),
            "ready_rows": len(loadable),
            "request_anchor_counts": dict(sorted(request_anchor_counts.items())),
        },
    }
    write_json(validation_path, validation_manifest)

    asset_manifest = {
        "asset_manifest_version": "1.0",
        "asset_package_id": ASSET_PACKAGE_ID,
        "assets": [
            {
                "asset_id": "actual_outflow_core_xml_v1",
                "format": "xml",
                "path": str(XML_REL_PATH),
                "record_count": len(loadable),
                "required": True,
                "sha256": sha256_file(xml_path),
            },
            {
                "asset_id": "actual_outflow_external_id_manifest_v1",
                "format": "json",
                "path": str(EXTERNAL_REL_PATH),
                "record_count": len(loadable),
                "required": True,
                "sha256": sha256_file(external_path),
            },
            {
                "asset_id": "actual_outflow_validation_manifest_v1",
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
            "outflow_request_sc_v1",
        ],
        "generated_at": GENERATED_AT,
        "idempotency": {
            "conflict_policy": "block_package",
            "duplicate_policy": "update_existing_same_external_id",
            "mode": "odoo_xml_external_id",
        },
        "lane": {
            "business_priority": "actual_outflow_core_fact",
            "lane_id": "actual_outflow",
            "layer": "20_business",
            "risk_class": "draft_actual_outflow_core",
        },
        "load_order": [
            "actual_outflow_core_xml_v1",
            "actual_outflow_external_id_manifest_v1",
            "actual_outflow_validation_manifest_v1",
        ],
        "odoo_shell": False,
        "source_snapshot": {
            "extract_batch_id": "actual_outflow_core_xml_baseline_v1",
            "source_system": "sc",
            "source_tables": ["T_FK_Supplier"],
        },
        "target": {
            "identity_field": "legacy_actual_outflow_id",
            "load_strategy": "odoo_xml_external_id",
            "model": "payment.request",
            "type": "pay",
        },
        "validation_gates": [
            "source_actual_outflow_query_passed",
            "legacy_actual_outflow_id_non_empty",
            "legacy_actual_outflow_id_unique",
            "amount_positive",
            "project_anchor_resolves",
            "partner_anchor_resolves",
            "source_request_anchor_optional",
            "state_not_written",
            "settlement_not_written",
            "ledger_not_written",
            "accounting_not_written",
            "workflow_not_written",
        ],
    }
    write_json(asset_manifest_path, asset_manifest)

    runtime_root.mkdir(parents=True, exist_ok=True)
    write_json(runtime_root / "actual_outflow_blocked_v1.json", {"blocked": blocked, "blocker_counts": dict(counters)})
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
    parser = argparse.ArgumentParser(description="Generate legacy actual outflow XML migration assets.")
    parser.add_argument("--asset-root", default=str(REPO_ASSET_ROOT))
    parser.add_argument("--runtime-root", default=str(RUNTIME_ROOT))
    parser.add_argument("--expected-ready", type=int, default=12463)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    try:
        result = generate(Path(args.asset_root), Path(args.runtime_root), args.expected_ready)
    except (ActualOutflowAssetError, json.JSONDecodeError) as exc:
        payload = {"status": "FAIL", "error": str(exc), "db_writes": 0, "odoo_shell": False}
        print("ACTUAL_OUTFLOW_ASSET_GENERATOR=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 1 if args.check else 0

    print("ACTUAL_OUTFLOW_ASSET_GENERATOR=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
