#!/usr/bin/env python3
"""Generate XML assets for legacy fund daily balance snapshots."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from collections import Counter
from decimal import Decimal
from pathlib import Path
from typing import Any

from legacy_fund_loan_residual_screen import clean, classify_row, load_project_refs, parse_amount, parse_sql_rows, run_sql


RUNTIME_ROOT = Path(".runtime_artifacts/migration_assets/legacy_fund_daily_snapshot_sc_v1")
XML_REL_PATH = Path("30_relation/legacy_fund_daily_snapshot/legacy_fund_daily_snapshot_v1.xml")
EXTERNAL_REL_PATH = Path("manifest/legacy_fund_daily_snapshot_external_id_manifest_v1.json")
VALIDATION_REL_PATH = Path("manifest/legacy_fund_daily_snapshot_validation_manifest_v1.json")
ASSET_MANIFEST_REL_PATH = Path("manifest/legacy_fund_daily_snapshot_asset_manifest_v1.json")
CATALOG_REL_PATH = Path("manifest/migration_asset_catalog_v1.json")
ASSET_PACKAGE_ID = "legacy_fund_daily_snapshot_sc_v1"
GENERATED_AT = "2026-04-15T22:05:00+08:00"
EXPECTED_RAW_ROWS = 873
EXPECTED_RECORDS = 496


class FundDailySnapshotAssetError(Exception):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise FundDailySnapshotAssetError(message)


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


def project_map(asset_root: Path) -> dict[str, str]:
    manifest = load_json(asset_root / "manifest/project_external_id_manifest_v1.json")
    result: dict[str, str] = {}
    for row in manifest.get("records", []):
        if row.get("status") == "loadable":
            external_id = clean(row.get("external_id"))
            for value in (clean(row.get("legacy_key")), clean((row.get("target_lookup") or {}).get("value"))):
                if value and external_id:
                    result[value] = external_id
    require(result, "project map is empty")
    return result


def safe_suffix(source_table: str, legacy_id: str) -> str:
    suffix = re.sub(r"[^0-9A-Za-z_]+", "_", f"{source_table}_{legacy_id}").strip("_").lower()
    require(bool(suffix), "cannot build external id")
    return suffix


def date_text(value: str) -> str:
    text = clean(value)
    return text[:10] if text else ""


def money(value: Decimal) -> str:
    return format(value.quantize(Decimal("0.01")), "f")


def add_text(record: ET.Element, name: str, value: object, required: bool = False) -> None:
    text = clean(value)
    if not text and not required:
        return
    field = ET.SubElement(record, "field", {"name": name})
    field.text = text


def add_ref(record: ET.Element, name: str, ref: str, required: bool = False) -> None:
    text = clean(ref)
    if not text and not required:
        return
    ET.SubElement(record, "field", {"name": name, "ref": text})


def write_xml(path: Path, records: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    root = ET.Element("odoo")
    data = ET.SubElement(root, "data", {"noupdate": "1"})
    for row in records:
        record = ET.SubElement(data, "record", {"id": row["external_id"], "model": "sc.legacy.fund.daily.snapshot.fact"})
        for field in (
            "legacy_source_table",
            "legacy_record_id",
            "legacy_pid",
            "source_family",
            "document_no",
            "snapshot_date",
            "legacy_state",
            "subject",
        ):
            add_text(record, field, row[field], field in {"legacy_source_table", "legacy_record_id", "source_family", "snapshot_date"})
        add_ref(record, "project_id", row["project_external_id"], True)
        add_text(record, "legacy_project_id", row["legacy_project_id"], True)
        add_text(record, "legacy_project_name", row["legacy_project_name"])
        add_text(record, "source_account_balance_total", row["source_account_balance_total"], True)
        add_text(record, "source_bank_balance_total", row["source_bank_balance_total"], True)
        add_text(record, "source_bank_system_difference", row["source_bank_system_difference"], True)
        add_text(record, "note", row["note"])
        add_text(record, "import_batch", "legacy_fund_daily_snapshot_asset_v1", True)
    ET.indent(root, space="  ")
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)


def update_catalog(asset_root: Path, manifest_hash: str) -> None:
    path = asset_root / CATALOG_REL_PATH
    catalog = load_json(path)
    package = {
        "asset_manifest_path": str(ASSET_MANIFEST_REL_PATH),
        "asset_manifest_sha256": manifest_hash,
        "asset_package_id": ASSET_PACKAGE_ID,
        "baseline_package": True,
        "business_priority": "legacy_fund_daily_snapshot_fact",
        "dependencies": ["project_sc_v1"],
        "layer": "30_relation",
        "load_phase": 30,
        "package_type": "legacy_fund_daily_snapshot_fact",
        "required": True,
        "risk_class": "historical_balance_snapshot_fact",
        "target_model": "sc.legacy.fund.daily.snapshot.fact",
        "verification_command": "python3 scripts/migration/legacy_fund_daily_snapshot_asset_verify.py --asset-root migration_assets --lane legacy_fund_daily_snapshot --check",
    }
    catalog["package_order"] = [item for item in catalog.get("package_order", []) if item != ASSET_PACKAGE_ID]
    catalog["package_order"].append(ASSET_PACKAGE_ID)
    catalog["packages"] = [item for item in catalog.get("packages", []) if item.get("asset_package_id") != ASSET_PACKAGE_ID]
    catalog["packages"].append(package)
    catalog["generated_at"] = GENERATED_AT
    write_json(path, catalog)


def build_records(asset_root: Path) -> tuple[list[dict[str, str]], dict[str, Any]]:
    rows = parse_sql_rows(run_sql())
    require(len(rows) == EXPECTED_RAW_ROWS, f"raw row count drifted: {len(rows)} != {EXPECTED_RAW_ROWS}")
    project_refs = load_project_refs(asset_root)
    pmap = project_map(asset_root)
    records: list[dict[str, str]] = []
    routes: Counter[str] = Counter()
    reasons: Counter[str] = Counter()
    tables: Counter[str] = Counter()
    ids: Counter[str] = Counter()

    for row in rows:
        route, blocked_reasons = classify_row(row, project_refs)
        routes[route] += 1
        table = clean(row.get("source_table"))
        tables[table] += 1
        for reason in blocked_reasons:
            reasons[reason] += 1
        if route != "management_snapshot_candidate":
            continue
        legacy_id = clean(row.get("legacy_id"))
        project_id = clean(row.get("project_id"))
        external_id = "legacy_fund_daily_snapshot_sc_%s" % safe_suffix(table, legacy_id)
        ids[external_id] += 1
        records.append(
            {
                "external_id": external_id,
                "legacy_source_table": table,
                "legacy_record_id": legacy_id,
                "legacy_pid": clean(row.get("legacy_pid")),
                "source_family": "fund_daily_balance_snapshot",
                "document_no": clean(row.get("document_no")),
                "snapshot_date": date_text(row.get("document_date", "")),
                "legacy_state": clean(row.get("state")),
                "subject": clean(row.get("subject")),
                "project_external_id": pmap[project_id],
                "legacy_project_id": project_id,
                "legacy_project_name": clean(row.get("project_name")),
                "source_account_balance_total": money(parse_amount(row.get("amount", ""))),
                "source_bank_balance_total": money(parse_amount(row.get("amount_secondary", ""))),
                "source_bank_system_difference": money(parse_amount(row.get("amount_delta", ""))),
                "note": clean(row.get("note")),
            }
        )
    require(len(records) == EXPECTED_RECORDS, f"record count drifted: {len(records)} != {EXPECTED_RECORDS}")
    require(not [key for key, count in ids.items() if count > 1], "duplicate external ids")
    return records, {
        "raw_rows": len(rows),
        "loadable_records": len(records),
        "loan_or_borrowing_records": routes["project_anchored_financing_candidate"],
        "blocked_records": routes["blocked"],
        "blocked_reason_counts": dict(reasons.most_common()),
        "source_table_counts": dict(tables.most_common()),
    }


def generate(asset_root: Path, runtime_root: Path) -> dict[str, Any]:
    records, summary = build_records(asset_root)
    xml_path = asset_root / XML_REL_PATH
    external_path = asset_root / EXTERNAL_REL_PATH
    validation_path = asset_root / VALIDATION_REL_PATH
    manifest_path = asset_root / ASSET_MANIFEST_REL_PATH
    write_xml(xml_path, records)
    write_json(
        external_path,
        {
            "asset_manifest_version": "1.0",
            "asset_package_id": ASSET_PACKAGE_ID,
            "external_id_rule": "legacy_fund_daily_snapshot_sc_<source_table>_<legacy_id>",
            "lane_id": "legacy_fund_daily_snapshot",
            "records": [
                {
                    "external_id": row["external_id"],
                    "legacy_source_table": row["legacy_source_table"],
                    "legacy_record_id": row["legacy_record_id"],
                    "project_external_id": row["project_external_id"],
                    "status": "loadable",
                }
                for row in records
            ],
            "summary": summary,
        },
    )
    write_json(
        validation_path,
        {
            "asset_manifest_version": "1.0",
            "asset_package_id": ASSET_PACKAGE_ID,
            "business_boundary": {
                "legacy_fund_daily_snapshot_fact": "included",
                "loan_registration": "excluded",
                "borrowing_request": "excluded",
                "runtime_financial_execution": "excluded",
                "approval_runtime": "excluded",
            },
            "counts": summary,
            "validation_gates": {
                "generate_time": [
                    "legacy_source_key_unique",
                    "project_external_id_required_and_resolves",
                    "snapshot_date_required",
                    "snapshot_amount_present",
                    "loan_and_borrowing_records_excluded",
                    "blocked_rows_excluded",
                    "no_runtime_financial_execution_generated",
                    "no_runtime_approval_records_generated",
                ]
            },
        },
    )
    asset_manifest = {
        "asset_manifest_version": "1.0",
        "asset_package_id": ASSET_PACKAGE_ID,
        "assets": [
            {"path": str(XML_REL_PATH), "sha256": sha256_file(xml_path), "type": "xml"},
            {"path": str(EXTERNAL_REL_PATH), "sha256": sha256_file(external_path), "type": "external_id_manifest"},
            {"path": str(VALIDATION_REL_PATH), "sha256": sha256_file(validation_path), "type": "validation_manifest"},
        ],
        "baseline_package": True,
        "counts": summary,
        "db_writes": 0,
        "dependencies": ["project_sc_v1"],
        "generated_at": GENERATED_AT,
        "lane": {"lane_id": "legacy_fund_daily_snapshot", "layer": "30_relation", "load_phase": 30},
        "odoo_shell": False,
        "target": {"model": "sc.legacy.fund.daily.snapshot.fact", "source_tables": ["D_SCBSJS_ZJGL_ZJSZ_ZJRBB"]},
    }
    write_json(manifest_path, asset_manifest)
    update_catalog(asset_root, sha256_file(manifest_path))
    payload = {
        "status": "PASS",
        "asset_package_id": ASSET_PACKAGE_ID,
        "xml_path": str(xml_path),
        "asset_manifest_path": str(manifest_path),
        "counts": summary,
        "db_writes": 0,
        "odoo_shell": False,
    }
    write_json(runtime_root / "legacy_fund_daily_snapshot_asset_generation_v1.json", payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate legacy fund daily snapshot XML assets.")
    parser.add_argument("--asset-root", default="migration_assets")
    parser.add_argument("--runtime-root", default=str(RUNTIME_ROOT))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        result = generate(Path(args.asset_root), Path(args.runtime_root))
    except (FundDailySnapshotAssetError, json.JSONDecodeError, ET.ParseError, KeyError) as exc:
        print("LEGACY_FUND_DAILY_SNAPSHOT_ASSET_GENERATE=" + json.dumps({"status": "FAIL", "error": str(exc), "db_writes": 0, "odoo_shell": False}, ensure_ascii=False, sort_keys=True))
        return 1 if args.check else 0
    print("LEGACY_FUND_DAILY_SNAPSHOT_ASSET_GENERATE=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
