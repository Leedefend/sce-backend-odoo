#!/usr/bin/env python3
"""Verify repository-tracked anchored contract header XML migration assets."""

from __future__ import annotations

import argparse
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


REQUIRED_FIELDS = {
    "legacy_contract_id",
    "legacy_project_id",
    "legacy_deleted_flag",
    "legacy_counterparty_text",
    "subject",
    "type",
    "project_id",
    "partner_id",
}
FORBIDDEN_XML_FIELDS = {"tax_id", "line_ids", "state", "amount_total", "amount_untaxed", "amount_tax"}
FORBIDDEN_ASSET_TOKENS = ("payment", "settlement", "account", "security", "record_rule", "__manifest__")


class ContractHeaderAssetVerificationError(Exception):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractHeaderAssetVerificationError(message)


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


def load_partner_ref_set(asset_root: Path) -> set[str]:
    refs = load_ref_set(asset_root / "manifest/partner_external_id_manifest_v1.json")
    supplemental_path = asset_root / "manifest/contract_counterparty_partner_external_id_manifest_v1.json"
    require(supplemental_path.exists(), "missing supplemental contract counterparty partner manifest")
    refs.update(load_ref_set(supplemental_path))
    return refs


def verify_hashes(asset_root: Path, asset_manifest: dict[str, Any]) -> None:
    for asset in asset_manifest.get("assets", []):
        rel_path = asset.get("path")
        expected_hash = asset.get("sha256")
        require(isinstance(rel_path, str) and rel_path, "asset path must be non-empty")
        require(isinstance(expected_hash, str) and expected_hash, f"asset {rel_path} missing sha256")
        require(sha256_file(resolve_asset_path(asset_root, rel_path)) == expected_hash, f"sha256 mismatch for {rel_path}")


def verify_asset_manifest(asset_manifest: dict[str, Any], lane: str) -> None:
    require(asset_manifest.get("asset_manifest_version") == "1.0", "unsupported asset manifest version")
    require(asset_manifest.get("asset_package_id") == "contract_sc_v1", "unexpected contract package id")
    require(asset_manifest.get("baseline_package") is True, "asset package must be baseline")
    require(asset_manifest.get("db_writes") == 0, "asset manifest must declare db_writes=0")
    require(asset_manifest.get("odoo_shell") is False, "asset manifest must declare odoo_shell=false")
    require(
        asset_manifest.get("dependencies") == ["project_sc_v1", "partner_sc_v1", "contract_counterparty_partner_sc_v1"],
        "unexpected dependencies",
    )
    require(asset_manifest.get("lane", {}).get("lane_id") == lane, "unexpected lane")
    require(asset_manifest.get("lane", {}).get("layer") == "20_business", "unexpected layer")
    require(asset_manifest.get("target", {}).get("model") == "construction.contract", "unexpected target model")
    for asset in asset_manifest.get("assets", []):
        payload = json.dumps(asset, ensure_ascii=False)
        require(not any(token in payload for token in FORBIDDEN_ASSET_TOKENS), f"high-risk asset leakage: {payload}")


def verify_xml_records(
    records: list[dict[str, str]],
    expected_count: int,
    project_refs: set[str],
    partner_refs: set[str],
) -> None:
    require(len(records) == expected_count, f"xml record count mismatch: {len(records)} != {expected_count}")
    ids = [row["id"] for row in records]
    legacy_contract_ids = [row.get("legacy_contract_id", "") for row in records]
    require(len(ids) == len(set(ids)), "duplicate XML external ids")
    require(len(legacy_contract_ids) == len(set(legacy_contract_ids)), "duplicate legacy contract ids")
    for row in records:
        require(row["id"].startswith("legacy_contract_sc_"), f"invalid external id: {row['id']}")
        require(row["model"] == "construction.contract", f"invalid XML model: {row['model']}")
        missing = sorted(field for field in REQUIRED_FIELDS if not row.get(field))
        require(not missing, f"missing required fields for {row['id']}: {missing}")
        forbidden = sorted(FORBIDDEN_XML_FIELDS & set(row))
        require(not forbidden, f"forbidden contract fields for {row['id']}: {forbidden}")
        require(row["project_id"] in project_refs, f"project ref does not resolve: {row['project_id']}")
        require(row["partner_id"] in partner_refs, f"partner ref does not resolve: {row['partner_id']}")
        require(row["type"] in {"out", "in"}, f"invalid contract type for {row['id']}: {row['type']}")
        require(row["legacy_deleted_flag"] != "1", f"deleted legacy row leaked into XML: {row['id']}")


def verify_external_manifest(external_manifest: dict[str, Any], records: list[dict[str, str]]) -> None:
    manifest_records = external_manifest.get("records", [])
    require(isinstance(manifest_records, list), "external manifest records must be a list")
    xml_ids = {row["id"] for row in records}
    manifest_ids = {row.get("external_id") for row in manifest_records}
    require(xml_ids == manifest_ids, "external manifest ids do not match XML ids")
    require(external_manifest.get("summary", {}).get("loadable") == len(records), "loadable count mismatch")
    for row in manifest_records:
        require(row.get("target_model") == "construction.contract", f"invalid target model: {row}")
        require(row.get("status") == "loadable", f"non-loadable manifest row: {row}")


def verify_validation_manifest(validation_manifest: dict[str, Any]) -> None:
    gates = set(validation_manifest.get("validation_gates", {}).get("generate_time", []))
    required = {
        "legacy_contract_id_unique",
        "project_external_id_resolves",
        "partner_external_id_resolves",
        "deleted_rows_excluded",
        "direction_resolved",
        "tax_id_omitted_target_default",
    }
    missing = sorted(required - gates)
    require(not missing, f"validation manifest missing gates: {missing}")
    require(validation_manifest.get("tax_policy", {}).get("xml_tax_id") == "omitted", "tax_id must be omitted")


def verify(asset_root: Path, lane: str) -> dict[str, Any]:
    asset_manifest = load_json(asset_root / "manifest" / f"{lane}_asset_manifest_v1.json")
    external_manifest = load_json(asset_root / "manifest" / f"{lane}_external_id_manifest_v1.json")
    validation_manifest = load_json(asset_root / "manifest" / f"{lane}_validation_manifest_v1.json")
    records = parse_xml(asset_root / "20_business" / lane / f"{lane}_header_v1.xml")
    project_refs = load_ref_set(asset_root / "manifest/project_external_id_manifest_v1.json")
    partner_refs = load_partner_ref_set(asset_root)

    verify_asset_manifest(asset_manifest, lane)
    verify_hashes(asset_root, asset_manifest)
    verify_xml_records(records, asset_manifest["counts"]["loadable_records"], project_refs, partner_refs)
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
    parser = argparse.ArgumentParser(description="Verify contract header XML migration assets.")
    parser.add_argument("--asset-root", default="migration_assets")
    parser.add_argument("--lane", default="contract")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    try:
        result = verify(Path(args.asset_root), args.lane)
    except (ContractHeaderAssetVerificationError, ET.ParseError, json.JSONDecodeError) as exc:
        payload = {"status": "FAIL", "error": str(exc), "db_writes": 0, "odoo_shell": False}
        print("CONTRACT_HEADER_ASSET_VERIFY=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 1 if args.check else 0
    print("CONTRACT_HEADER_ASSET_VERIFY=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
