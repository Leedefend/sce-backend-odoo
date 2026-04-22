#!/usr/bin/env python3
"""Verify legacy receipt and income XML migration assets."""

from __future__ import annotations

import argparse
import hashlib
import json
import xml.etree.ElementTree as ET
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any


REQUIRED_FIELDS = {"legacy_source_table", "legacy_record_id", "source_family", "direction", "project_id", "legacy_project_id", "source_amount", "import_batch"}
ALLOWED_FIELDS = {"legacy_source_table", "legacy_record_id", "legacy_pid", "source_family", "direction", "document_no", "document_date", "legacy_state", "income_category", "project_id", "legacy_project_id", "legacy_project_name", "partner_id", "legacy_partner_id", "legacy_partner_name", "source_amount", "note", "import_batch"}
FORBIDDEN_FIELDS = {"payment_request_id", "account_move_id", "settlement_id", "validation_status", "review_ids", "res_id"}
ALLOWED_FAMILIES = {"customer_receipt", "receipt_confirmation", "company_financial_income"}


class ReceiptIncomeAssetVerificationError(Exception):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ReceiptIncomeAssetVerificationError(message)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    require(path.exists(), f"missing json manifest: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def parse_xml(path: Path) -> list[dict[str, str]]:
    root = ET.parse(path).getroot()
    records: list[dict[str, str]] = []
    for record in root.findall(".//record"):
        row = {"id": record.attrib.get("id", "").strip(), "model": record.attrib.get("model", "").strip()}
        for field in record.findall("field"):
            row[field.attrib.get("name", "").strip()] = field.attrib.get("ref", "").strip() or (field.text or "").strip()
        records.append(row)
    return records


def refs(asset_root: Path, rel_path: str) -> set[str]:
    manifest = load_json(asset_root / rel_path)
    return {str(row.get("external_id", "")).strip() for row in manifest.get("records", []) if row.get("status") == "loadable" and str(row.get("external_id", "")).strip()}


def partner_refs(asset_root: Path) -> set[str]:
    result = refs(asset_root, "manifest/partner_external_id_manifest_v1.json")
    path = asset_root / "manifest/receipt_counterparty_partner_external_id_manifest_v1.json"
    if path.exists():
        result.update(refs(asset_root, "manifest/receipt_counterparty_partner_external_id_manifest_v1.json"))
    return result


def positive(value: str) -> bool:
    try:
        return Decimal(value or "0") > 0
    except InvalidOperation:
        return False


def verify(asset_root: Path, lane: str) -> dict[str, Any]:
    asset_manifest = load_json(asset_root / "manifest/legacy_receipt_income_asset_manifest_v1.json")
    external_manifest = load_json(asset_root / "manifest/legacy_receipt_income_external_id_manifest_v1.json")
    validation_manifest = load_json(asset_root / "manifest/legacy_receipt_income_validation_manifest_v1.json")
    records = parse_xml(asset_root / "30_relation" / lane / "legacy_receipt_income_v1.xml")
    require(asset_manifest.get("asset_package_id") == "legacy_receipt_income_sc_v1", "unexpected package id")
    require(asset_manifest.get("db_writes") == 0, "asset manifest must declare db_writes=0")
    require(asset_manifest.get("odoo_shell") is False, "asset manifest must declare odoo_shell=false")
    require(asset_manifest.get("target", {}).get("model") == "sc.legacy.receipt.income.fact", "unexpected target model")
    require(asset_manifest.get("counts", {}).get("loadable_records") == 7220, "loadable count drifted")
    for asset in asset_manifest.get("assets", []):
        require(sha256_file(asset_root / asset["path"]) == asset["sha256"], f"sha256 mismatch for {asset['path']}")
    project_refs = refs(asset_root, "manifest/project_external_id_manifest_v1.json")
    p_refs = partner_refs(asset_root)
    require(len(records) == 7220, f"xml record count mismatch: {len(records)}")
    ids = [row["id"] for row in records]
    require(len(ids) == len(set(ids)), "duplicate XML external ids")
    for row in records:
        require(row["id"].startswith("legacy_receipt_income_sc_"), f"invalid external id: {row['id']}")
        require(row["model"] == "sc.legacy.receipt.income.fact", f"invalid model: {row['model']}")
        require(not sorted(REQUIRED_FIELDS - set(k for k, v in row.items() if v)), f"missing required fields for {row['id']}")
        require(not sorted(set(row) - ALLOWED_FIELDS - {"id", "model"}), f"unexpected fields for {row['id']}")
        require(not sorted(FORBIDDEN_FIELDS & set(row)), f"forbidden runtime fields for {row['id']}")
        require(row["project_id"] in project_refs, f"project external id does not resolve: {row['project_id']}")
        if row.get("partner_id"):
            require(row["partner_id"] in p_refs, f"partner external id does not resolve: {row['partner_id']}")
        require(row["source_family"] in ALLOWED_FAMILIES, f"bad family: {row['source_family']}")
        require(row["direction"] == "inflow", f"bad direction: {row['direction']}")
        require(positive(row["source_amount"]), f"amount must be positive for {row['id']}")
    require({row["id"] for row in records} == {row.get("external_id") for row in external_manifest.get("records", [])}, "external manifest ids do not match XML")
    boundary = validation_manifest.get("business_boundary", {})
    require(boundary.get("payment_request") == "excluded", "payment request must be excluded")
    require(boundary.get("account_move") == "excluded", "account move must be excluded")
    require(boundary.get("settlement_state") == "excluded", "settlement must be excluded")
    return {"status": "PASS", "asset_root": str(asset_root), "lane": lane, "records": len(records), "blocked_records": asset_manifest["counts"].get("blocked_records"), "asset_package_id": asset_manifest.get("asset_package_id"), "db_writes": 0, "odoo_shell": False}


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify legacy receipt/income XML migration assets.")
    parser.add_argument("--asset-root", default="migration_assets")
    parser.add_argument("--lane", default="legacy_receipt_income")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        result = verify(Path(args.asset_root), args.lane)
    except (ReceiptIncomeAssetVerificationError, ET.ParseError, json.JSONDecodeError) as exc:
        print("LEGACY_RECEIPT_INCOME_ASSET_VERIFY=" + json.dumps({"status": "FAIL", "error": str(exc), "db_writes": 0, "odoo_shell": False}, ensure_ascii=False, sort_keys=True))
        return 1 if args.check else 0
    print("LEGACY_RECEIPT_INCOME_ASSET_VERIFY=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
