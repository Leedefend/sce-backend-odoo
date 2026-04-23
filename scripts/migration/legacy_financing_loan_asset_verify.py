#!/usr/bin/env python3
"""Verify legacy financing and loan XML migration assets."""

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
    "source_direction",
    "document_date",
    "project_id",
    "legacy_project_id",
    "legacy_counterparty_name",
    "source_amount",
    "source_amount_field",
    "import_batch",
}
ALLOWED_XML_FIELDS = {
    "legacy_source_table",
    "legacy_record_id",
    "legacy_pid",
    "source_family",
    "source_direction",
    "document_no",
    "document_date",
    "due_date",
    "legacy_state",
    "project_id",
    "legacy_project_id",
    "legacy_project_name",
    "partner_id",
    "legacy_counterparty_id",
    "legacy_counterparty_name",
    "source_amount",
    "source_amount_field",
    "purpose",
    "source_type_label",
    "source_extra_ref",
    "source_extra_label",
    "note",
    "import_batch",
}
FORBIDDEN_XML_FIELDS = {"move_id", "settle_id", "request_id", "validation_status", "review_ids", "res_id"}
ALLOWED_FAMILIES = {"loan_registration", "borrowing_request"}
ALLOWED_DIRECTIONS = {"financing_in", "borrowed_fund"}


class FinancingLoanAssetVerificationError(Exception):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise FinancingLoanAssetVerificationError(message)


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


def partner_refs(asset_root: Path) -> set[str]:
    result = refs(asset_root, "manifest/partner_external_id_manifest_v1.json")
    for rel_path in (
        "manifest/contract_counterparty_partner_external_id_manifest_v1.json",
        "manifest/receipt_counterparty_partner_external_id_manifest_v1.json",
    ):
        path = asset_root / rel_path
        if path.exists():
            result.update(refs(asset_root, rel_path))
    return result


def verify_hashes(asset_root: Path, asset_manifest: dict[str, Any]) -> None:
    for asset in asset_manifest.get("assets", []):
        rel_path = asset.get("path")
        expected_hash = asset.get("sha256")
        require(isinstance(rel_path, str) and rel_path, "asset path must be non-empty")
        require(isinstance(expected_hash, str) and expected_hash, f"asset {rel_path} missing sha256")
        path = asset_root / rel_path
        require(path.exists(), f"declared asset does not exist: {rel_path}")
        require(sha256_file(path) == expected_hash, f"sha256 mismatch for {rel_path}")


def positive_amount(value: str) -> None:
    try:
        amount = Decimal(str(value).strip())
    except InvalidOperation as exc:
        raise FinancingLoanAssetVerificationError(f"invalid amount: {value}") from exc
    require(amount > 0, f"source amount must be positive: {value}")


def verify_xml_records(records: list[dict[str, str]], project_set: set[str], partner_set: set[str]) -> None:
    require(len(records) == 318, f"xml record count mismatch: {len(records)} != 318")
    ids = [row["id"] for row in records]
    require(len(ids) == len(set(ids)), "duplicate XML external ids")
    for row in records:
        require(row["id"].startswith("legacy_financing_loan_sc_"), f"invalid external id: {row['id']}")
        require(row["model"] == "sc.legacy.financing.loan.fact", f"invalid XML model: {row['model']}")
        missing = sorted(field for field in REQUIRED_FIELDS if not row.get(field))
        require(not missing, f"missing required fields for {row['id']}: {missing}")
        unexpected = sorted(set(row) - ALLOWED_XML_FIELDS - {"id", "model"})
        require(not unexpected, f"unexpected fields for {row['id']}: {unexpected}")
        forbidden = sorted(FORBIDDEN_XML_FIELDS & set(row))
        require(not forbidden, f"forbidden runtime fields for {row['id']}: {forbidden}")
        require(row["project_id"] in project_set, f"project external id does not resolve: {row['project_id']}")
        if row.get("partner_id"):
            require(row["partner_id"] in partner_set, f"partner external id does not resolve: {row['partner_id']}")
        require(row["source_family"] in ALLOWED_FAMILIES, f"bad family: {row['source_family']}")
        require(row["source_direction"] in ALLOWED_DIRECTIONS, f"bad direction: {row['source_direction']}")
        positive_amount(row["source_amount"])


def verify(asset_root: Path, lane: str) -> dict[str, Any]:
    asset_manifest = load_json(asset_root / "manifest/legacy_financing_loan_asset_manifest_v1.json")
    external_manifest = load_json(asset_root / "manifest/legacy_financing_loan_external_id_manifest_v1.json")
    validation_manifest = load_json(asset_root / "manifest/legacy_financing_loan_validation_manifest_v1.json")
    records = parse_xml(asset_root / "30_relation" / lane / "legacy_financing_loan_v1.xml")
    require(asset_manifest.get("asset_manifest_version") == "1.0", "unsupported asset manifest version")
    require(asset_manifest.get("asset_package_id") == "legacy_financing_loan_sc_v1", "unexpected package id")
    require(asset_manifest.get("baseline_package") is True, "asset package must be baseline")
    require(asset_manifest.get("db_writes") == 0, "asset manifest must declare db_writes=0")
    require(asset_manifest.get("odoo_shell") is False, "asset manifest must declare odoo_shell=false")
    require(asset_manifest.get("lane", {}).get("lane_id") == lane, "unexpected lane")
    require(asset_manifest.get("lane", {}).get("layer") == "30_relation", "unexpected layer")
    require(asset_manifest.get("target", {}).get("model") == "sc.legacy.financing.loan.fact", "unexpected target model")
    require(asset_manifest.get("counts", {}).get("loadable_records") == 318, "loadable count drifted")
    require(asset_manifest.get("counts", {}).get("management_snapshot_records") == 496, "snapshot exclusion count drifted")
    verify_hashes(asset_root, asset_manifest)
    verify_xml_records(records, refs(asset_root, "manifest/project_external_id_manifest_v1.json"), partner_refs(asset_root))
    require({row["id"] for row in records} == {row.get("external_id") for row in external_manifest.get("records", [])}, "external manifest ids do not match XML")
    boundary = validation_manifest.get("business_boundary", {})
    require(boundary.get("legacy_financing_loan_fact") == "included", "legacy financing fact must be included")
    require(boundary.get("management_balance_snapshot") == "excluded", "management snapshots must be excluded")
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
    parser = argparse.ArgumentParser(description="Verify legacy financing/loan XML migration assets.")
    parser.add_argument("--asset-root", default="migration_assets")
    parser.add_argument("--lane", default="legacy_financing_loan")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        result = verify(Path(args.asset_root), args.lane)
    except (FinancingLoanAssetVerificationError, ET.ParseError, json.JSONDecodeError) as exc:
        print("LEGACY_FINANCING_LOAN_ASSET_VERIFY=" + json.dumps({"status": "FAIL", "error": str(exc), "db_writes": 0, "odoo_shell": False}, ensure_ascii=False, sort_keys=True))
        return 1 if args.check else 0
    print("LEGACY_FINANCING_LOAN_ASSET_VERIFY=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
