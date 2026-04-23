#!/usr/bin/env python3
"""Verify legacy fund daily snapshot XML migration assets."""

from __future__ import annotations

import argparse
import hashlib
import json
import xml.etree.ElementTree as ET
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any


REQUIRED_FIELDS = {
    "legacy_source_table",
    "legacy_record_id",
    "source_family",
    "snapshot_date",
    "project_id",
    "legacy_project_id",
    "source_account_balance_total",
    "source_bank_balance_total",
    "source_bank_system_difference",
    "import_batch",
}
ALLOWED_XML_FIELDS = {
    "legacy_source_table",
    "legacy_record_id",
    "legacy_pid",
    "source_family",
    "document_no",
    "snapshot_date",
    "legacy_state",
    "subject",
    "project_id",
    "legacy_project_id",
    "legacy_project_name",
    "source_account_balance_total",
    "source_bank_balance_total",
    "source_bank_system_difference",
    "note",
    "import_batch",
}
FORBIDDEN_XML_FIELDS = {"move_id", "settle_id", "request_id", "review_ids", "res_id", "statement_id"}


class FundDailySnapshotAssetVerificationError(Exception):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise FundDailySnapshotAssetVerificationError(message)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    require(path.exists(), f"missing json manifest: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def parse_xml(xml_path: Path) -> list[dict[str, str]]:
    root = ET.parse(xml_path).getroot()
    records: list[dict[str, str]] = []
    for record in root.findall(".//record"):
        row = {"id": record.attrib.get("id", "").strip(), "model": record.attrib.get("model", "").strip()}
        for field in record.findall("field"):
            name = field.attrib.get("name", "").strip()
            row[name] = field.attrib.get("ref", "").strip() or (field.text or "").strip()
        records.append(row)
    return records


def refs(asset_root: Path, rel_path: str) -> set[str]:
    manifest = load_json(asset_root / rel_path)
    return {
        str(row.get("external_id", "")).strip()
        for row in manifest.get("records", [])
        if row.get("status") == "loadable" and str(row.get("external_id", "")).strip()
    }


def verify_hashes(asset_root: Path, asset_manifest: dict[str, Any]) -> None:
    for asset in asset_manifest.get("assets", []):
        rel_path = asset.get("path")
        expected_hash = asset.get("sha256")
        require(isinstance(rel_path, str) and rel_path, "asset path must be non-empty")
        require(isinstance(expected_hash, str) and expected_hash, f"asset {rel_path} missing sha256")
        path = asset_root / rel_path
        require(path.exists(), f"declared asset does not exist: {rel_path}")
        require(sha256_file(path) == expected_hash, f"sha256 mismatch for {rel_path}")


def decimal_value(value: str) -> Decimal:
    try:
        return Decimal(str(value).strip() or "0")
    except InvalidOperation as exc:
        raise FundDailySnapshotAssetVerificationError(f"invalid amount: {value}") from exc


def verify_xml_records(records: list[dict[str, str]], project_set: set[str]) -> None:
    require(len(records) == 496, f"xml record count mismatch: {len(records)} != 496")
    ids = [row["id"] for row in records]
    require(len(ids) == len(set(ids)), "duplicate XML external ids")
    for row in records:
        require(row["id"].startswith("legacy_fund_daily_snapshot_sc_"), f"invalid external id: {row['id']}")
        require(row["model"] == "sc.legacy.fund.daily.snapshot.fact", f"invalid XML model: {row['model']}")
        missing = sorted(field for field in REQUIRED_FIELDS if not row.get(field))
        require(not missing, f"missing required fields for {row['id']}: {missing}")
        unexpected = sorted(set(row) - ALLOWED_XML_FIELDS - {"id", "model"})
        require(not unexpected, f"unexpected fields for {row['id']}: {unexpected}")
        forbidden = sorted(FORBIDDEN_XML_FIELDS & set(row))
        require(not forbidden, f"forbidden runtime fields for {row['id']}: {forbidden}")
        require(row["project_id"] in project_set, f"project external id does not resolve: {row['project_id']}")
        require(row["source_family"] == "fund_daily_balance_snapshot", f"bad family: {row['source_family']}")
        amounts = [
            decimal_value(row["source_account_balance_total"]),
            decimal_value(row["source_bank_balance_total"]),
            decimal_value(row["source_bank_system_difference"]),
        ]
        require(any(amount != 0 for amount in amounts), f"snapshot amounts must not all be zero for {row['id']}")


def verify(asset_root: Path, lane: str) -> dict[str, Any]:
    asset_manifest = load_json(asset_root / "manifest/legacy_fund_daily_snapshot_asset_manifest_v1.json")
    external_manifest = load_json(asset_root / "manifest/legacy_fund_daily_snapshot_external_id_manifest_v1.json")
    validation_manifest = load_json(asset_root / "manifest/legacy_fund_daily_snapshot_validation_manifest_v1.json")
    records = parse_xml(asset_root / "30_relation" / lane / "legacy_fund_daily_snapshot_v1.xml")
    require(asset_manifest.get("asset_manifest_version") == "1.0", "unsupported asset manifest version")
    require(asset_manifest.get("asset_package_id") == "legacy_fund_daily_snapshot_sc_v1", "unexpected package id")
    require(asset_manifest.get("baseline_package") is True, "asset package must be baseline")
    require(asset_manifest.get("db_writes") == 0, "asset manifest must declare db_writes=0")
    require(asset_manifest.get("odoo_shell") is False, "asset manifest must declare odoo_shell=false")
    require(asset_manifest.get("lane", {}).get("lane_id") == lane, "unexpected lane")
    require(asset_manifest.get("lane", {}).get("layer") == "30_relation", "unexpected layer")
    require(asset_manifest.get("target", {}).get("model") == "sc.legacy.fund.daily.snapshot.fact", "unexpected target model")
    require(asset_manifest.get("counts", {}).get("loadable_records") == 496, "loadable count drifted")
    require(asset_manifest.get("counts", {}).get("loan_or_borrowing_records") == 318, "loan/borrowing exclusion count drifted")
    verify_hashes(asset_root, asset_manifest)
    verify_xml_records(records, refs(asset_root, "manifest/project_external_id_manifest_v1.json"))
    require({row["id"] for row in records} == {row.get("external_id") for row in external_manifest.get("records", [])}, "external manifest ids do not match XML")
    boundary = validation_manifest.get("business_boundary", {})
    require(boundary.get("legacy_fund_daily_snapshot_fact") == "included", "fund daily snapshot fact must be included")
    require(boundary.get("loan_registration") == "excluded", "loan registration must be excluded")
    require(boundary.get("borrowing_request") == "excluded", "borrowing request must be excluded")
    require(boundary.get("runtime_financial_execution") == "excluded", "runtime financial execution must be excluded")
    require(boundary.get("approval_runtime") == "excluded", "approval runtime must be excluded")
    return {
        "status": "PASS",
        "asset_root": str(asset_root),
        "lane": lane,
        "records": len(records),
        "asset_package_id": asset_manifest.get("asset_package_id"),
        "db_writes": 0,
        "odoo_shell": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify legacy fund daily snapshot XML migration assets.")
    parser.add_argument("--asset-root", default="migration_assets")
    parser.add_argument("--lane", default="legacy_fund_daily_snapshot")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        result = verify(Path(args.asset_root), args.lane)
    except (FundDailySnapshotAssetVerificationError, ET.ParseError, json.JSONDecodeError) as exc:
        print("LEGACY_FUND_DAILY_SNAPSHOT_ASSET_VERIFY=" + json.dumps({"status": "FAIL", "error": str(exc), "db_writes": 0, "odoo_shell": False}, ensure_ascii=False, sort_keys=True))
        return 1 if args.check else 0
    print("LEGACY_FUND_DAILY_SNAPSHOT_ASSET_VERIFY=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
