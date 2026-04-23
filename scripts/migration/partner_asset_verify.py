#!/usr/bin/env python3
"""Verify repository-tracked partner XML migration assets without DB access."""

from __future__ import annotations

import argparse
import hashlib
import json
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from typing import Any


REQUIRED_XML_FIELDS = ("legacy_partner_id", "legacy_partner_source", "name")
FORBIDDEN_ASSET_TOKENS = ("payment", "settlement", "security", "record_rule", "__manifest__")


class VerificationError(Exception):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise VerificationError(message)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    require(path.exists(), f"missing json manifest: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_asset_path(asset_root: Path, rel_path: str) -> Path:
    path = asset_root / rel_path
    require(path.exists(), f"declared asset does not exist: {rel_path}")
    return path


def verify_hashes(asset_root: Path, asset_manifest: dict[str, Any]) -> None:
    for asset in asset_manifest.get("assets", []):
        rel_path = asset.get("path")
        expected_hash = asset.get("sha256")
        require(isinstance(rel_path, str) and rel_path, "asset path must be non-empty")
        require(isinstance(expected_hash, str) and expected_hash, f"asset {rel_path} missing sha256")
        actual_hash = sha256_file(resolve_asset_path(asset_root, rel_path))
        require(actual_hash == expected_hash, f"sha256 mismatch for {rel_path}")


def parse_xml(xml_path: Path) -> list[dict[str, str]]:
    root = ET.parse(xml_path).getroot()
    records: list[dict[str, str]] = []
    for record in root.findall(".//record"):
        fields = {field.attrib.get("name", ""): (field.text or "").strip() for field in record.findall("field")}
        records.append(
            {
                "id": record.attrib.get("id", "").strip(),
                "model": record.attrib.get("model", "").strip(),
                **fields,
            }
        )
    return records


def verify_asset_manifest(asset_manifest: dict[str, Any], lane: str) -> None:
    require(asset_manifest.get("asset_manifest_version") == "1.0", "unsupported asset manifest version")
    require(asset_manifest.get("asset_package_id") == "partner_sc_v1", "unexpected partner package id")
    require(asset_manifest.get("baseline_package") is True, "asset package must be marked baseline_package")
    require(asset_manifest.get("db_writes") == 0, "asset manifest must declare db_writes=0")
    require(asset_manifest.get("odoo_shell") is False, "asset manifest must declare odoo_shell=false")
    lane_payload = asset_manifest.get("lane", {})
    require(lane_payload.get("lane_id") == lane, f"unexpected lane id: {lane_payload}")
    require(lane_payload.get("layer") == "10_master", "partner baseline must be 10_master")
    target = asset_manifest.get("target", {})
    require(target.get("model") == "res.partner", f"unexpected target model: {target}")
    counts = asset_manifest.get("counts", {})
    require(counts.get("loadable_records", 0) > 0, "partner baseline must have loadable records")
    require(counts.get("raw_rows", 0) >= counts.get("loadable_records", 0), "raw rows must cover loadable rows")
    require(counts.get("discarded_records", -1) >= 0, "discarded count must be non-negative")
    for asset in asset_manifest.get("assets", []):
        payload = json.dumps(asset, ensure_ascii=False)
        require(not any(token in payload for token in FORBIDDEN_ASSET_TOKENS), f"high-risk asset leakage: {payload}")


def verify_xml_records(records: list[dict[str, str]], expected_count: int) -> None:
    require(len(records) == expected_count, f"xml record count mismatch: {len(records)} != {expected_count}")
    require(records, "xml records must not be empty")
    ids = [row["id"] for row in records]
    duplicate_ids = [value for value, count in Counter(ids).items() if count > 1]
    require(not duplicate_ids, f"duplicate xml external ids: {duplicate_ids[:10]}")
    for row in records:
        require(row["id"].startswith("legacy_partner_sc_"), f"invalid partner external id: {row['id']}")
        require(row["model"] == "res.partner", f"invalid xml model for {row['id']}: {row['model']}")
        for field in REQUIRED_XML_FIELDS:
            require(bool(row.get(field)), f"missing required field {field} for {row['id']}")
        require(row.get("company_type") == "company", f"partner must be company type: {row['id']}")
        require(row.get("is_company") == "1", f"partner must be company: {row['id']}")


def verify_external_manifest(external_manifest: dict[str, Any], records: list[dict[str, str]]) -> None:
    manifest_records = external_manifest.get("records", [])
    require(isinstance(manifest_records, list), "external manifest records must be a list")
    xml_ids = {row["id"] for row in records}
    manifest_ids = {row.get("external_id") for row in manifest_records}
    require(xml_ids == manifest_ids, "external manifest ids do not match XML ids")
    summary = external_manifest.get("summary", {})
    require(summary.get("loadable") == len(records), "external manifest loadable count mismatch")
    require(summary.get("discarded", -1) >= 0, "external manifest discarded count must be non-negative")
    for row in manifest_records:
        require(row.get("target_model") == "res.partner", f"invalid target model in external manifest: {row}")
        require(row.get("status") == "loadable", f"non-loadable external manifest record in baseline: {row}")
        target_lookup = row.get("target_lookup", {})
        require(target_lookup.get("field") == "xml_id", f"invalid target lookup field: {row}")


def verify_validation_manifest(validation_manifest: dict[str, Any]) -> None:
    gates = validation_manifest.get("validation_gates", {})
    generate_time = set(gates.get("generate_time", []))
    required_gates = {
        "external_id_unique",
        "garbage_rows_discarded",
        "no_partner_rank_fields",
        "no_high_risk_lane_leakage",
    }
    missing = sorted(required_gates - generate_time)
    require(not missing, f"validation manifest missing gates: {missing}")


def verify(asset_root: Path, lane: str) -> dict[str, Any]:
    asset_manifest = load_json(asset_root / "manifest" / f"{lane}_asset_manifest_v1.json")
    external_manifest = load_json(asset_root / "manifest" / f"{lane}_external_id_manifest_v1.json")
    validation_manifest = load_json(asset_root / "manifest" / f"{lane}_validation_manifest_v1.json")
    records = parse_xml(asset_root / "10_master" / lane / f"{lane}_master_v1.xml")

    verify_asset_manifest(asset_manifest, lane)
    verify_hashes(asset_root, asset_manifest)
    verify_xml_records(records, asset_manifest["counts"]["loadable_records"])
    verify_external_manifest(external_manifest, records)
    verify_validation_manifest(validation_manifest)
    return {
        "status": "PASS",
        "asset_root": str(asset_root),
        "lane": lane,
        "records": len(records),
        "asset_package_id": asset_manifest.get("asset_package_id"),
        "discarded_records": asset_manifest["counts"].get("discarded_records"),
        "db_writes": 0,
        "odoo_shell": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify partner XML migration asset package without DB access.")
    parser.add_argument("--asset-root", default="migration_assets", help="Asset package root")
    parser.add_argument("--lane", default="partner", help="Lane id to verify")
    parser.add_argument("--check", action="store_true", help="Fail non-zero on verification errors")
    args = parser.parse_args()

    try:
        result = verify(Path(args.asset_root), args.lane)
    except (VerificationError, ET.ParseError, json.JSONDecodeError) as exc:
        payload = {"status": "FAIL", "error": str(exc), "db_writes": 0, "odoo_shell": False}
        print("PARTNER_ASSET_VERIFY=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 1 if args.check else 0

    print("PARTNER_ASSET_VERIFY=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
