#!/usr/bin/env python3
"""Verify URL-type ir.attachment backfill XML assets."""

from __future__ import annotations

import argparse
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


REQUIRED_FIELDS = {"name", "type", "url", "res_model", "res_id", "description"}
FORBIDDEN_FIELDS = {"datas", "raw", "db_datas", "store_fname"}
LANE_REFS = {
    "project": ("project.project", "manifest/project_external_id_manifest_v1.json"),
    "project_member": ("sc.project.member.staging", "manifest/project_member_external_id_manifest_v1.json"),
    "actual_outflow": ("payment.request", "manifest/actual_outflow_external_id_manifest_v1.json"),
    "supplier_contract": ("construction.contract", "manifest/supplier_contract_external_id_manifest_v1.json"),
    "supplier_contract_line": ("construction.contract.line", "manifest/supplier_contract_line_external_id_manifest_v1.json"),
    "outflow_request_line": ("payment.request.line", "manifest/outflow_request_line_external_id_manifest_v1.json"),
}


class AttachmentBackfillVerificationError(Exception):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AttachmentBackfillVerificationError(message)


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


def load_ref_set(asset_root: Path, rel_path: str) -> set[str]:
    manifest = load_json(asset_root / rel_path)
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


def verify(asset_root: Path, lane: str) -> dict[str, Any]:
    asset_manifest = load_json(asset_root / "manifest/legacy_attachment_backfill_asset_manifest_v1.json")
    external_manifest = load_json(asset_root / "manifest/legacy_attachment_backfill_external_id_manifest_v1.json")
    validation_manifest = load_json(asset_root / "manifest/legacy_attachment_backfill_validation_manifest_v1.json")
    records = parse_xml(asset_root / "30_relation" / lane / "legacy_attachment_backfill_v1.xml")

    require(asset_manifest.get("asset_package_id") == "legacy_attachment_backfill_sc_v1", "unexpected package id")
    require(asset_manifest.get("db_writes") == 0, "asset manifest must declare db_writes=0")
    require(asset_manifest.get("odoo_shell") is False, "asset manifest must declare odoo_shell=false")
    require(asset_manifest.get("lane", {}).get("layer") == "30_relation", "unexpected layer")
    require(asset_manifest.get("target", {}).get("model") == "ir.attachment", "unexpected target model")
    require(asset_manifest.get("target", {}).get("type") == "url", "attachments must be url type")
    verify_hashes(asset_root, asset_manifest)

    require(len(records) == asset_manifest["counts"]["loadable_records"], "record count mismatch")
    require(len({row["id"] for row in records}) == len(records), "duplicate XML ids")
    refs = {lane_id: load_ref_set(asset_root, rel_path) for lane_id, (_model, rel_path) in LANE_REFS.items()}
    manifest_records = external_manifest.get("records", [])
    require({row["id"] for row in records} == {row.get("external_id") for row in manifest_records}, "manifest ids mismatch")

    for row in records:
        require(row["model"] == "ir.attachment", f"invalid XML model: {row['model']}")
        missing = sorted(field for field in REQUIRED_FIELDS if not row.get(field))
        require(not missing, f"missing required fields for {row['id']}: {missing}")
        forbidden = sorted(FORBIDDEN_FIELDS & set(row))
        require(not forbidden, f"binary/storage fields emitted for {row['id']}: {forbidden}")
        require(row["type"] == "url", f"attachment must be url type for {row['id']}")
        require(row["url"].startswith(("legacy-file://", "legacy-file-id://")), f"invalid legacy url for {row['id']}")
        require("binary_embedded=false" in row["description"], f"missing binary boundary marker for {row['id']}")

    for item in manifest_records:
        lane_id = item.get("lane")
        require(lane_id in LANE_REFS, f"unexpected lane: {lane_id}")
        expected_model = LANE_REFS[lane_id][0]
        require(item.get("res_model") == expected_model, f"res_model drift: {item}")
        require(item.get("target_external_id") in refs[lane_id], f"target ref does not resolve: {item}")
        require(item.get("binary_embedded") is False, f"binary flag drift: {item}")

    gates = set(validation_manifest.get("validation_gates", {}).get("generate_time", []))
    required_gates = {
        "lane_file_external_id_unique",
        "target_external_id_resolves_by_lane",
        "attachment_type_url_only",
        "binary_datas_field_not_emitted",
        "deleted_files_excluded",
    }
    require(not sorted(required_gates - gates), f"validation gates missing: {sorted(required_gates - gates)}")
    return {
        "status": "PASS",
        "asset_package_id": asset_manifest.get("asset_package_id"),
        "records": len(records),
        "db_writes": 0,
        "odoo_shell": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify legacy attachment backfill XML assets.")
    parser.add_argument("--asset-root", default="migration_assets")
    parser.add_argument("--lane", default="legacy_attachment_backfill")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        result = verify(Path(args.asset_root), args.lane)
    except (AttachmentBackfillVerificationError, ET.ParseError, json.JSONDecodeError) as exc:
        payload = {"status": "FAIL", "error": str(exc), "db_writes": 0, "odoo_shell": False}
        print("LEGACY_ATTACHMENT_BACKFILL_ASSET_VERIFY=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 1 if args.check else 0
    print("LEGACY_ATTACHMENT_BACKFILL_ASSET_VERIFY=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
