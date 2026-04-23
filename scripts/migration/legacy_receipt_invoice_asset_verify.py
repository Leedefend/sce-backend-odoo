#!/usr/bin/env python3
"""Verify receipt invoice line XML migration assets."""

from __future__ import annotations

import argparse
import hashlib
import json
import xml.etree.ElementTree as ET
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any


REQUIRED_FIELDS = {
    "request_id",
    "sequence",
    "legacy_invoice_line_id",
    "legacy_receipt_id",
    "source_table_name",
    "amount_source",
    "invoice_amount",
    "note",
}
ALLOWED_XML_FIELDS = {
    "request_id",
    "sequence",
    "legacy_invoice_line_id",
    "legacy_receipt_id",
    "legacy_invoice_id",
    "legacy_invoice_child_id",
    "legacy_pid",
    "legacy_file_bill_id",
    "invoice_no",
    "invoice_party_name",
    "invoice_issue_company",
    "source_document_no",
    "source_table_name",
    "amount_source",
    "invoice_amount",
    "current_receipt_amount",
    "invoiced_before_amount",
    "note",
}
FORBIDDEN_XML_FIELDS = {
    "attachment_ids",
    "attachment_count",
    "request_type",
    "project_id",
    "partner_id",
    "contract_id",
    "currency_id",
    "import_batch",
    "active",
}


class ReceiptInvoiceAssetVerificationError(Exception):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ReceiptInvoiceAssetVerificationError(message)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    require(path.exists(), f"missing json manifest: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_asset_path(asset_root: Path, rel_path: str) -> Path:
    path = asset_root / rel_path
    require(path.exists(), f"declared asset does not exist: {rel_path}")
    return path


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


def load_ref_set(path: Path) -> set[str]:
    manifest = load_json(path)
    return {
        str(row.get("external_id")).strip()
        for row in manifest.get("records", [])
        if str(row.get("external_id", "")).strip() and row.get("status") == "loadable"
    }


def positive_decimal(value: str) -> bool:
    try:
        return Decimal(value) > 0
    except InvalidOperation:
        return False


def verify_hashes(asset_root: Path, asset_manifest: dict[str, Any]) -> None:
    for asset in asset_manifest.get("assets", []):
        rel_path = asset.get("path")
        expected_hash = asset.get("sha256")
        require(isinstance(rel_path, str) and rel_path, "asset path must be non-empty")
        require(isinstance(expected_hash, str) and expected_hash, f"asset {rel_path} missing sha256")
        require(sha256_file(resolve_asset_path(asset_root, rel_path)) == expected_hash, f"sha256 mismatch for {rel_path}")


def verify_asset_manifest(asset_manifest: dict[str, Any], lane: str) -> None:
    require(asset_manifest.get("asset_manifest_version") == "1.0", "unsupported asset manifest version")
    require(asset_manifest.get("asset_package_id") == "receipt_invoice_line_sc_v1", "unexpected package id")
    require(asset_manifest.get("baseline_package") is True, "asset package must be baseline")
    require(asset_manifest.get("db_writes") == 0, "asset manifest must declare db_writes=0")
    require(asset_manifest.get("odoo_shell") is False, "asset manifest must declare odoo_shell=false")
    require(asset_manifest.get("dependencies") == ["receipt_sc_v1"], "unexpected dependencies")
    require(asset_manifest.get("lane", {}).get("lane_id") == lane, "unexpected lane")
    require(asset_manifest.get("lane", {}).get("layer") == "20_business", "unexpected layer")
    require(asset_manifest.get("target", {}).get("model") == "sc.receipt.invoice.line", "unexpected target model")
    require(asset_manifest.get("target", {}).get("source_table") == "C_JFHKLR_CB", "unexpected source table")


def verify_xml_records(records: list[dict[str, str]], expected_count: int, receipt_refs: set[str]) -> None:
    require(len(records) == expected_count, f"xml record count mismatch: {len(records)} != {expected_count}")
    ids = [row["id"] for row in records]
    require(len(ids) == len(set(ids)), "duplicate XML external ids")
    for row in records:
        require(row["id"].startswith("legacy_receipt_invoice_line_sc_"), f"invalid external id: {row['id']}")
        require(row["model"] == "sc.receipt.invoice.line", f"invalid XML model: {row['model']}")
        missing = sorted(field for field in REQUIRED_FIELDS if not row.get(field))
        require(not missing, f"missing required fields for {row['id']}: {missing}")
        unexpected = sorted(set(row) - ALLOWED_XML_FIELDS - {"id", "model"})
        require(not unexpected, f"unexpected invoice line fields for {row['id']}: {unexpected}")
        forbidden = sorted(FORBIDDEN_XML_FIELDS & set(row))
        require(not forbidden, f"forbidden computed/default/attachment fields for {row['id']}: {forbidden}")
        require(row["request_id"] in receipt_refs, f"receipt ref does not resolve: {row['request_id']}")
        require(row["source_table_name"] == "C_JFHKLR_CB", f"source table drift for {row['id']}")
        require(positive_decimal(row["invoice_amount"]), f"invoice amount must be positive for {row['id']}")
        require("invoice_fact=true" in row["note"], f"missing invoice fact marker for {row['id']}")
        require("not_account_move=true" in row["note"], f"missing accounting boundary marker for {row['id']}")
        require("not_settlement=true" in row["note"], f"missing settlement boundary marker for {row['id']}")
        require("attachment_binary=false" in row["note"], f"missing attachment binary boundary marker for {row['id']}")


def verify_external_manifest(external_manifest: dict[str, Any], records: list[dict[str, str]]) -> None:
    manifest_records = external_manifest.get("records", [])
    require(isinstance(manifest_records, list), "external manifest records must be a list")
    xml_ids = {row["id"] for row in records}
    manifest_ids = {row.get("external_id") for row in manifest_records}
    require(xml_ids == manifest_ids, "external manifest ids do not match XML ids")
    require(external_manifest.get("summary", {}).get("loadable") == len(records), "loadable count mismatch")
    for row in manifest_records:
        require(row.get("target_model") == "sc.receipt.invoice.line", f"invalid target model: {row}")
        require(row.get("status") == "loadable", f"non-loadable manifest row: {row}")
        require(row.get("receipt_external_id"), f"missing parent receipt external id: {row}")
        require(isinstance(row.get("attachment_candidate_keys"), dict), f"missing attachment candidate keys: {row}")


def verify_validation_manifest(validation_manifest: dict[str, Any]) -> None:
    gates = set(validation_manifest.get("validation_gates", {}).get("generate_time", []))
    required = {
        "legacy_receipt_invoice_line_id_unique",
        "receipt_external_id_resolves",
        "invoice_amount_positive",
        "source_table_preserved",
        "account_move_not_written",
        "settlement_not_written",
        "attachment_binary_not_imported",
    }
    missing = sorted(required - gates)
    require(not missing, f"validation manifest missing gates: {missing}")
    boundary = validation_manifest.get("business_boundary", {})
    require(boundary.get("receipt_invoice_line_fact") == "included", "invoice line fact must be included")
    require(boundary.get("parent_receipt_anchor") == "required", "parent receipt anchor policy drift")
    require(boundary.get("accounting") == "excluded", "accounting must be excluded")
    require(boundary.get("posted_invoice") == "excluded", "posted invoice truth must be excluded")
    require(boundary.get("settlement") == "excluded", "settlement must be excluded")
    require(boundary.get("attachment_binary") == "excluded_later_lane", "attachment binary policy drift")


def verify(asset_root: Path, lane: str) -> dict[str, Any]:
    asset_manifest = load_json(asset_root / "manifest/receipt_invoice_line_asset_manifest_v1.json")
    external_manifest = load_json(asset_root / "manifest/receipt_invoice_line_external_id_manifest_v1.json")
    validation_manifest = load_json(asset_root / "manifest/receipt_invoice_line_validation_manifest_v1.json")
    records = parse_xml(asset_root / "20_business" / lane / "receipt_invoice_line_v1.xml")
    receipt_refs = load_ref_set(asset_root / "manifest/receipt_external_id_manifest_v1.json")

    verify_asset_manifest(asset_manifest, lane)
    verify_hashes(asset_root, asset_manifest)
    verify_xml_records(records, asset_manifest["counts"]["loadable_records"], receipt_refs)
    verify_external_manifest(external_manifest, records)
    verify_validation_manifest(validation_manifest)
    return {
        "status": "PASS",
        "asset_root": str(asset_root),
        "lane": lane,
        "records": len(records),
        "blocked_records": asset_manifest["counts"].get("blocked_records"),
        "asset_package_id": asset_manifest.get("asset_package_id"),
        "db_writes": 0,
        "odoo_shell": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify receipt invoice line XML migration assets.")
    parser.add_argument("--asset-root", default="migration_assets")
    parser.add_argument("--lane", default="receipt_invoice_line")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    try:
        result = verify(Path(args.asset_root), args.lane)
    except (ReceiptInvoiceAssetVerificationError, ET.ParseError, json.JSONDecodeError, InvalidOperation) as exc:
        payload = {"status": "FAIL", "error": str(exc), "db_writes": 0, "odoo_shell": False}
        print("RECEIPT_INVOICE_ASSET_VERIFY=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 1 if args.check else 0
    print("RECEIPT_INVOICE_ASSET_VERIFY=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
