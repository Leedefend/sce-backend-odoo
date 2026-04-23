#!/usr/bin/env python3
"""Verify receipt invoice attachment URL XML assets."""

from __future__ import annotations

import argparse
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


REQUIRED_FIELDS = {"name", "type", "url", "res_model", "res_id", "description"}
FORBIDDEN_FIELDS = {"datas", "raw", "db_datas", "store_fname"}


class ReceiptInvoiceAttachmentAssetVerificationError(Exception):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ReceiptInvoiceAttachmentAssetVerificationError(message)


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


def load_ref_set(path: Path) -> set[str]:
    manifest = load_json(path)
    return {
        str(row.get("external_id")).strip()
        for row in manifest.get("records", [])
        if str(row.get("external_id", "")).strip() and row.get("status") == "loadable"
    }


def verify_hashes(asset_root: Path, asset_manifest: dict[str, Any]) -> None:
    for asset in asset_manifest.get("assets", []):
        rel_path = asset.get("path")
        expected_hash = asset.get("sha256")
        require(isinstance(rel_path, str) and rel_path, "asset path must be non-empty")
        require(isinstance(expected_hash, str) and expected_hash, f"asset {rel_path} missing sha256")
        require(sha256_file(asset_root / rel_path) == expected_hash, f"sha256 mismatch for {rel_path}")


def verify_asset_manifest(asset_manifest: dict[str, Any], lane: str) -> None:
    require(asset_manifest.get("asset_manifest_version") == "1.0", "unsupported asset manifest version")
    require(asset_manifest.get("asset_package_id") == "receipt_invoice_attachment_sc_v1", "unexpected package id")
    require(asset_manifest.get("baseline_package") is True, "asset package must be baseline")
    require(asset_manifest.get("db_writes") == 0, "asset manifest must declare db_writes=0")
    require(asset_manifest.get("odoo_shell") is False, "asset manifest must declare odoo_shell=false")
    require(asset_manifest.get("dependencies") == ["receipt_invoice_line_sc_v1"], "unexpected dependencies")
    require(asset_manifest.get("lane", {}).get("lane_id") == lane, "unexpected lane")
    require(asset_manifest.get("lane", {}).get("layer") == "30_relation", "unexpected layer")
    require(asset_manifest.get("target", {}).get("model") == "ir.attachment", "unexpected target model")
    require(asset_manifest.get("target", {}).get("type") == "url", "attachments must be url type")


def verify_xml_records(records: list[dict[str, str]], expected_count: int, receipt_invoice_refs: set[str]) -> None:
    require(len(records) == expected_count, f"xml record count mismatch: {len(records)} != {expected_count}")
    ids = [row["id"] for row in records]
    require(len(ids) == len(set(ids)), "duplicate XML external ids")
    for row in records:
        require(row["id"].startswith("legacy_receipt_invoice_attachment_sc_"), f"invalid external id: {row['id']}")
        require(row["model"] == "ir.attachment", f"invalid XML model: {row['model']}")
        missing = sorted(field for field in REQUIRED_FIELDS if not row.get(field))
        require(not missing, f"missing required fields for {row['id']}: {missing}")
        forbidden = sorted(FORBIDDEN_FIELDS & set(row))
        require(not forbidden, f"binary/storage fields emitted for {row['id']}: {forbidden}")
        require(row["type"] == "url", f"attachment must be url type for {row['id']}")
        require(row["url"].startswith(("legacy-file://", "legacy-file-id://")), f"invalid legacy url for {row['id']}")
        require(row["res_model"] == "sc.receipt.invoice.line", f"invalid res_model for {row['id']}")
        require(row["res_id"] in receipt_invoice_refs, f"receipt invoice line ref does not resolve: {row['res_id']}")
        require("binary_embedded=false" in row["description"], f"missing binary boundary marker for {row['id']}")


def verify_external_manifest(external_manifest: dict[str, Any], records: list[dict[str, str]]) -> None:
    manifest_records = external_manifest.get("records", [])
    xml_ids = {row["id"] for row in records}
    manifest_ids = {row.get("external_id") for row in manifest_records}
    require(xml_ids == manifest_ids, "external manifest ids do not match XML ids")
    require(external_manifest.get("summary", {}).get("loadable") == len(records), "loadable count mismatch")
    for row in manifest_records:
        require(row.get("target_model") == "ir.attachment", f"invalid target model: {row}")
        require(row.get("res_model") == "sc.receipt.invoice.line", f"invalid res_model: {row}")
        require(row.get("binary_embedded") is False, f"binary flag drift: {row}")
        require(row.get("receipt_invoice_line_external_id"), f"missing parent ref: {row}")


def verify_validation_manifest(validation_manifest: dict[str, Any]) -> None:
    gates = set(validation_manifest.get("validation_gates", {}).get("generate_time", []))
    required = {
        "legacy_file_id_unique",
        "pid_to_receipt_invoice_line_resolves",
        "attachment_type_url_only",
        "binary_datas_field_not_emitted",
        "deleted_files_excluded",
    }
    missing = sorted(required - gates)
    require(not missing, f"validation manifest missing gates: {missing}")
    boundary = validation_manifest.get("business_boundary", {})
    require(boundary.get("ir_attachment_record") == "included", "ir.attachment record must be included")
    require(boundary.get("receipt_invoice_line_relation") == "included", "business relation must be included")
    require(boundary.get("binary_file_custody") == "excluded", "binary custody must be excluded")


def verify(asset_root: Path, lane: str) -> dict[str, Any]:
    asset_manifest = load_json(asset_root / "manifest/receipt_invoice_attachment_asset_manifest_v1.json")
    external_manifest = load_json(asset_root / "manifest/receipt_invoice_attachment_external_id_manifest_v1.json")
    validation_manifest = load_json(asset_root / "manifest/receipt_invoice_attachment_validation_manifest_v1.json")
    records = parse_xml(asset_root / "30_relation" / lane / "receipt_invoice_attachment_v1.xml")
    receipt_invoice_refs = load_ref_set(asset_root / "manifest/receipt_invoice_line_external_id_manifest_v1.json")

    verify_asset_manifest(asset_manifest, lane)
    verify_hashes(asset_root, asset_manifest)
    verify_xml_records(records, asset_manifest["counts"]["loadable_records"], receipt_invoice_refs)
    verify_external_manifest(external_manifest, records)
    verify_validation_manifest(validation_manifest)
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
    parser = argparse.ArgumentParser(description="Verify receipt invoice attachment URL XML assets.")
    parser.add_argument("--asset-root", default="migration_assets")
    parser.add_argument("--lane", default="receipt_invoice_attachment")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    try:
        result = verify(Path(args.asset_root), args.lane)
    except (ReceiptInvoiceAttachmentAssetVerificationError, ET.ParseError, json.JSONDecodeError) as exc:
        payload = {"status": "FAIL", "error": str(exc), "db_writes": 0, "odoo_shell": False}
        print("RECEIPT_INVOICE_ATTACHMENT_ASSET_VERIFY=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 1 if args.check else 0
    print("RECEIPT_INVOICE_ATTACHMENT_ASSET_VERIFY=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
