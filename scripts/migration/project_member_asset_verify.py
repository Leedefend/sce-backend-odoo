#!/usr/bin/env python3
"""Verify repository-tracked neutral project-member XML migration assets."""

from __future__ import annotations

import argparse
import hashlib
import json
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from typing import Any


REQUIRED_FIELDS = {
    "legacy_member_id",
    "legacy_project_id",
    "legacy_user_ref",
    "project_id",
    "user_id",
    "role_fact_status",
    "import_batch",
    "active",
}
FORBIDDEN_FIELDS = {"role_key", "responsibility_id", "groups_id", "company_ids"}
FORBIDDEN_ASSET_TOKENS = ("payment", "settlement", "account", "security", "record_rule", "__manifest__")


class ProjectMemberAssetVerificationError(Exception):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ProjectMemberAssetVerificationError(message)


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


def load_ref_set(path: Path, key: str = "external_id") -> set[str]:
    manifest = load_json(path)
    return {
        str(row.get(key)).strip()
        for row in manifest.get("records", [])
        if str(row.get(key, "")).strip() and row.get("status") == "loadable"
    }


def verify_hashes(asset_root: Path, asset_manifest: dict[str, Any]) -> None:
    for asset in asset_manifest.get("assets", []):
        rel_path = asset.get("path")
        expected_hash = asset.get("sha256")
        require(isinstance(rel_path, str) and rel_path, "asset path must be non-empty")
        require(isinstance(expected_hash, str) and expected_hash, f"asset {rel_path} missing sha256")
        require(sha256_file(resolve_asset_path(asset_root, rel_path)) == expected_hash, f"sha256 mismatch for {rel_path}")


def verify_asset_manifest(asset_manifest: dict[str, Any], lane: str) -> None:
    require(asset_manifest.get("asset_manifest_version") == "1.0", "unsupported asset manifest version")
    require(asset_manifest.get("asset_package_id") == "project_member_sc_v1", "unexpected package id")
    require(asset_manifest.get("baseline_package") is True, "asset package must be baseline")
    require(asset_manifest.get("db_writes") == 0, "asset manifest must declare db_writes=0")
    require(asset_manifest.get("odoo_shell") is False, "asset manifest must declare odoo_shell=false")
    require(asset_manifest.get("dependencies") == ["project_sc_v1", "user_sc_v1"], "unexpected dependencies")
    require(asset_manifest.get("lane", {}).get("lane_id") == lane, "unexpected lane")
    require(asset_manifest.get("lane", {}).get("layer") == "30_relation", "unexpected layer")
    require(asset_manifest.get("target", {}).get("model") == "sc.project.member.staging", "unexpected target model")
    for asset in asset_manifest.get("assets", []):
        payload = json.dumps(asset, ensure_ascii=False)
        require(not any(token in payload for token in FORBIDDEN_ASSET_TOKENS), f"high-risk asset leakage: {payload}")


def verify_xml_records(
    records: list[dict[str, str]],
    expected_count: int,
    project_refs: set[str],
    user_refs: set[str],
) -> dict[str, int]:
    require(len(records) == expected_count, f"xml record count mismatch: {len(records)} != {expected_count}")
    ids = [row["id"] for row in records]
    legacy_member_ids = [row.get("legacy_member_id", "") for row in records]
    require(len(ids) == len(set(ids)), "duplicate XML external ids")
    require(len(legacy_member_ids) == len(set(legacy_member_ids)), "duplicate legacy member ids")

    relation_keys: Counter[tuple[str, str]] = Counter()
    for row in records:
        require(row["id"].startswith("legacy_project_member_sc_"), f"invalid external id: {row['id']}")
        require(row["model"] == "sc.project.member.staging", f"invalid XML model: {row['model']}")
        missing = sorted(field for field in REQUIRED_FIELDS if not row.get(field))
        require(not missing, f"missing required fields for {row['id']}: {missing}")
        forbidden = sorted(FORBIDDEN_FIELDS & set(row))
        require(not forbidden, f"forbidden fields for {row['id']}: {forbidden}")
        require(row["project_id"] in project_refs, f"project ref does not resolve: {row['project_id']}")
        require(row["user_id"] in user_refs, f"user ref does not resolve: {row['user_id']}")
        require(row["role_fact_status"] == "missing", f"role_fact_status must be missing for {row['id']}")
        require(row["active"] == "1", f"active must be 1 for {row['id']}")
        relation_keys[(row["project_id"], row["user_id"])] += 1

    return {
        "duplicate_project_user_relation_keys": sum(1 for count in relation_keys.values() if count > 1),
        "rows_in_duplicate_project_user_relations": sum(count for count in relation_keys.values() if count > 1),
    }


def verify_external_manifest(external_manifest: dict[str, Any], records: list[dict[str, str]]) -> None:
    manifest_records = external_manifest.get("records", [])
    require(isinstance(manifest_records, list), "external manifest records must be a list")
    xml_ids = {row["id"] for row in records}
    manifest_ids = {row.get("external_id") for row in manifest_records}
    require(xml_ids == manifest_ids, "external manifest ids do not match XML ids")
    require(external_manifest.get("summary", {}).get("loadable") == len(records), "loadable count mismatch")
    for row in manifest_records:
        require(row.get("target_model") == "sc.project.member.staging", f"invalid target model: {row}")
        require(row.get("status") == "loadable", f"non-loadable manifest row: {row}")


def verify_validation_manifest(validation_manifest: dict[str, Any]) -> None:
    gates = set(validation_manifest.get("validation_gates", {}).get("generate_time", []))
    required = {
        "legacy_member_id_unique",
        "project_external_id_resolves",
        "user_external_id_resolves",
        "role_fact_status_missing",
        "duplicate_project_user_relations_preserved",
        "no_responsibility_or_authority_claim",
    }
    missing = sorted(required - gates)
    require(not missing, f"validation manifest missing gates: {missing}")


def verify(asset_root: Path, lane: str) -> dict[str, Any]:
    asset_manifest = load_json(asset_root / "manifest" / f"{lane}_asset_manifest_v1.json")
    external_manifest = load_json(asset_root / "manifest" / f"{lane}_external_id_manifest_v1.json")
    validation_manifest = load_json(asset_root / "manifest" / f"{lane}_validation_manifest_v1.json")
    records = parse_xml(asset_root / "30_relation" / lane / f"{lane}_neutral_v1.xml")
    project_refs = load_ref_set(asset_root / "manifest/project_external_id_manifest_v1.json")
    user_refs = load_ref_set(asset_root / "manifest/user_external_id_manifest_v1.json")

    verify_asset_manifest(asset_manifest, lane)
    verify_hashes(asset_root, asset_manifest)
    relation_profile = verify_xml_records(records, asset_manifest["counts"]["loadable_records"], project_refs, user_refs)
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
        **relation_profile,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify project-member neutral XML migration assets.")
    parser.add_argument("--asset-root", default="migration_assets")
    parser.add_argument("--lane", default="project_member")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    try:
        result = verify(Path(args.asset_root), args.lane)
    except (ProjectMemberAssetVerificationError, ET.ParseError, json.JSONDecodeError) as exc:
        payload = {"status": "FAIL", "error": str(exc), "db_writes": 0, "odoo_shell": False}
        print("PROJECT_MEMBER_ASSET_VERIFY=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 1 if args.check else 0
    print("PROJECT_MEMBER_ASSET_VERIFY=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
