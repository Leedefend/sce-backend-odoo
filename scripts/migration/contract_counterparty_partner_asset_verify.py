#!/usr/bin/env python3
"""Verify supplemental contract counterparty partner XML assets."""

from __future__ import annotations

import argparse
import hashlib
import json
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from typing import Any


REQUIRED_XML_FIELDS = ("legacy_partner_id", "legacy_partner_source", "legacy_partner_name", "name")
FORBIDDEN_ASSET_TOKENS = ("payment", "settlement", "account", "security", "record_rule", "__manifest__")
PACKAGE_ID = "contract_counterparty_partner_sc_v1"


class VerificationError(Exception):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise VerificationError(message)


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
        fields = {field.attrib.get("name", ""): (field.text or "").strip() for field in record.findall("field")}
        records.append({"id": record.attrib.get("id", "").strip(), "model": record.attrib.get("model", "").strip(), **fields})
    return records


def verify_hashes(asset_root: Path, asset_manifest: dict[str, Any]) -> None:
    for asset in asset_manifest.get("assets", []):
        rel_path = asset.get("path")
        expected_hash = asset.get("sha256")
        require(isinstance(rel_path, str) and rel_path, "asset path must be non-empty")
        require(isinstance(expected_hash, str) and expected_hash, f"asset {rel_path} missing sha256")
        actual_hash = sha256_file(resolve_asset_path(asset_root, rel_path))
        require(actual_hash == expected_hash, f"sha256 mismatch for {rel_path}")


def verify_asset_manifest(asset_manifest: dict[str, Any], lane: str) -> None:
    require(asset_manifest.get("asset_manifest_version") == "1.0", "unsupported asset manifest version")
    require(asset_manifest.get("asset_package_id") == PACKAGE_ID, "unexpected package id")
    require(asset_manifest.get("baseline_package") is True, "asset package must be baseline")
    require(asset_manifest.get("db_writes") == 0, "asset manifest must declare db_writes=0")
    require(asset_manifest.get("odoo_shell") is False, "asset manifest must declare odoo_shell=false")
    require(asset_manifest.get("dependencies") == ["partner_sc_v1"], "unexpected dependencies")
    require(asset_manifest.get("lane", {}).get("lane_id") == lane, "unexpected lane")
    require(asset_manifest.get("lane", {}).get("layer") == "10_master", "unexpected layer")
    require(asset_manifest.get("target", {}).get("model") == "res.partner", "unexpected target model")
    counts = asset_manifest.get("counts", {})
    require(counts.get("loadable_records", 0) > 0, "supplemental partner package must have loadable records")
    require(counts.get("candidate_contract_rows", 0) >= counts.get("loadable_records", 0), "candidate contracts must cover partner records")
    for asset in asset_manifest.get("assets", []):
        payload = json.dumps(asset, ensure_ascii=False)
        require(not any(token in payload for token in FORBIDDEN_ASSET_TOKENS), f"high-risk asset leakage: {payload}")


def verify_xml_records(records: list[dict[str, str]], expected_count: int) -> None:
    require(len(records) == expected_count, f"xml record count mismatch: {len(records)} != {expected_count}")
    ids = [row["id"] for row in records]
    duplicates = [value for value, count in Counter(ids).items() if count > 1]
    require(not duplicates, f"duplicate xml ids: {duplicates[:10]}")
    for row in records:
        require(row["id"].startswith("legacy_contract_counterparty_sc_"), f"invalid external id: {row['id']}")
        require(row["model"] == "res.partner", f"invalid xml model for {row['id']}: {row['model']}")
        for field in REQUIRED_XML_FIELDS:
            require(bool(row.get(field)), f"missing required field {field} for {row['id']}")
        require(row.get("legacy_partner_source") == "contract_counterparty", f"unexpected source for {row['id']}")
        require(row.get("company_type") == "company", f"partner must be company type: {row['id']}")
        require(row.get("is_company") == "1", f"partner must be company: {row['id']}")


def verify_external_manifest(external_manifest: dict[str, Any], records: list[dict[str, str]]) -> None:
    manifest_records = external_manifest.get("records", [])
    require(isinstance(manifest_records, list), "external manifest records must be a list")
    xml_ids = {row["id"] for row in records}
    manifest_ids = {row.get("external_id") for row in manifest_records}
    require(xml_ids == manifest_ids, "external manifest ids do not match XML ids")
    require(external_manifest.get("summary", {}).get("loadable") == len(records), "external manifest loadable mismatch")
    for row in manifest_records:
        require(row.get("target_model") == "res.partner", f"invalid target model: {row}")
        require(row.get("status") == "loadable", f"non-loadable manifest row: {row}")
        require(row.get("legacy_partner_source") == "contract_counterparty", f"unexpected source: {row}")
        require(row.get("normalized_counterparty_name"), f"missing normalized counterparty name: {row}")


def verify_validation_manifest(validation_manifest: dict[str, Any]) -> None:
    gates = set(validation_manifest.get("validation_gates", {}).get("generate_time", []))
    required = {
        "contract_direction_explicit",
        "project_external_id_resolves",
        "subject_present",
        "counterparty_name_safe",
        "external_id_unique",
        "supplement_source_explicit",
        "no_db_writes",
    }
    missing = sorted(required - gates)
    require(not missing, f"validation manifest missing gates: {missing}")
    boundary = validation_manifest.get("business_boundary", {})
    require(boundary.get("financial_semantics") == "not_changed", "financial semantics must not change")


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
        "candidate_contract_rows": asset_manifest["counts"].get("candidate_contract_rows"),
        "asset_package_id": asset_manifest.get("asset_package_id"),
        "db_writes": 0,
        "odoo_shell": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify supplemental contract counterparty partner assets.")
    parser.add_argument("--asset-root", default="migration_assets")
    parser.add_argument("--lane", default="contract_counterparty_partner")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        result = verify(Path(args.asset_root), args.lane)
    except (VerificationError, ET.ParseError, json.JSONDecodeError) as exc:
        payload = {"status": "FAIL", "error": str(exc), "db_writes": 0, "odoo_shell": False}
        print("CONTRACT_COUNTERPARTY_PARTNER_ASSET_VERIFY=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 1 if args.check else 0
    print("CONTRACT_COUNTERPARTY_PARTNER_ASSET_VERIFY=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
