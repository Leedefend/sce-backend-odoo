#!/usr/bin/env python3
"""Verify legacy workflow audit XML migration assets."""

from __future__ import annotations

import argparse
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


REQUIRED_FIELDS = {
    "legacy_workflow_id",
    "legacy_djid",
    "target_model",
    "target_external_id",
    "target_lane",
    "action_classification",
}
ALLOWED_XML_FIELDS = {
    "legacy_workflow_id",
    "legacy_pid",
    "legacy_djid",
    "legacy_business_id",
    "legacy_source_table",
    "legacy_detail_status_id",
    "legacy_detail_step_id",
    "legacy_setup_step_id",
    "legacy_template_id",
    "legacy_step_name",
    "legacy_template_name",
    "target_model",
    "target_external_id",
    "target_lane",
    "actor_legacy_user_id",
    "actor_name",
    "approved_at",
    "received_at",
    "approval_note",
    "action_classification",
    "legacy_status",
    "legacy_back_type",
    "legacy_approval_type",
}
FORBIDDEN_XML_FIELDS = {
    "review_ids",
    "validation_status",
    "tier_review",
    "definition_id",
    "res_id",
    "target_res_id",
    "import_batch",
}
TARGET_MANIFESTS = [
    "manifest/contract_external_id_manifest_v1.json",
    "manifest/receipt_external_id_manifest_v1.json",
    "manifest/outflow_request_external_id_manifest_v1.json",
    "manifest/actual_outflow_external_id_manifest_v1.json",
    "manifest/supplier_contract_external_id_manifest_v1.json",
]
WORKFLOW_XML_REL_PATH = "30_relation/legacy_workflow_audit/legacy_workflow_audit_v1.xml"
WORKFLOW_XML_PARTS_REL_DIR = WORKFLOW_XML_REL_PATH + ".parts"


class WorkflowAuditAssetVerificationError(Exception):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise WorkflowAuditAssetVerificationError(message)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    require(path.exists(), f"missing json manifest: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def materialize_workflow_xml_from_parts(asset_root: Path) -> None:
    xml_path = asset_root / WORKFLOW_XML_REL_PATH
    if xml_path.exists():
        return
    parts_dir = asset_root / WORKFLOW_XML_PARTS_REL_DIR
    require(parts_dir.exists(), f"missing workflow XML and parts directory: {WORKFLOW_XML_REL_PATH}")
    parts = sorted(path for path in parts_dir.iterdir() if path.is_file())
    require(parts, f"workflow XML parts directory is empty: {WORKFLOW_XML_PARTS_REL_DIR}")
    xml_path.parent.mkdir(parents=True, exist_ok=True)
    with xml_path.open("wb") as target:
        for part in parts:
            with part.open("rb") as source:
                for chunk in iter(lambda: source.read(1024 * 1024), b""):
                    target.write(chunk)


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


def target_refs(asset_root: Path) -> set[str]:
    refs: set[str] = set()
    for rel_path in TARGET_MANIFESTS:
        manifest = load_json(asset_root / rel_path)
        refs.update(
            str(row.get("external_id", "")).strip()
            for row in manifest.get("records", [])
            if row.get("status") == "loadable" and str(row.get("external_id", "")).strip()
        )
    require(refs, "target reference set is empty")
    return refs


def verify_hashes(asset_root: Path, asset_manifest: dict[str, Any]) -> None:
    for asset in asset_manifest.get("assets", []):
        rel_path = asset.get("path")
        expected_hash = asset.get("sha256")
        require(isinstance(rel_path, str) and rel_path, "asset path must be non-empty")
        require(isinstance(expected_hash, str) and expected_hash, f"asset {rel_path} missing sha256")
        path = asset_root / rel_path
        require(path.exists(), f"declared asset does not exist: {rel_path}")
        require(sha256_file(path) == expected_hash, f"sha256 mismatch for {rel_path}")


def verify_asset_manifest(asset_manifest: dict[str, Any], lane: str) -> None:
    require(asset_manifest.get("asset_manifest_version") == "1.0", "unsupported asset manifest version")
    require(asset_manifest.get("asset_package_id") == "legacy_workflow_audit_sc_v1", "unexpected package id")
    require(asset_manifest.get("baseline_package") is True, "asset package must be baseline")
    require(asset_manifest.get("db_writes") == 0, "asset manifest must declare db_writes=0")
    require(asset_manifest.get("odoo_shell") is False, "asset manifest must declare odoo_shell=false")
    require(asset_manifest.get("lane", {}).get("lane_id") == lane, "unexpected lane")
    require(asset_manifest.get("lane", {}).get("layer") == "30_relation", "unexpected layer")
    require(asset_manifest.get("target", {}).get("model") == "sc.legacy.workflow.audit", "unexpected target model")
    require(asset_manifest.get("target", {}).get("source_table") == "S_Execute_Approval", "unexpected source table")
    require(asset_manifest.get("counts", {}).get("loadable_records") == 79702, "loadable count drifted")


def verify_xml_records(records: list[dict[str, str]], expected_count: int, refs: set[str]) -> None:
    require(len(records) == expected_count, f"xml record count mismatch: {len(records)} != {expected_count}")
    ids = [row["id"] for row in records]
    require(len(ids) == len(set(ids)), "duplicate XML external ids")
    for row in records:
        require(row["id"].startswith("legacy_workflow_audit_sc_"), f"invalid external id: {row['id']}")
        require(row["model"] == "sc.legacy.workflow.audit", f"invalid XML model: {row['model']}")
        missing = sorted(field for field in REQUIRED_FIELDS if not row.get(field))
        require(not missing, f"missing required fields for {row['id']}: {missing}")
        unexpected = sorted(set(row) - ALLOWED_XML_FIELDS - {"id", "model"})
        require(not unexpected, f"unexpected workflow audit fields for {row['id']}: {unexpected}")
        forbidden = sorted(FORBIDDEN_XML_FIELDS & set(row))
        require(not forbidden, f"forbidden runtime approval fields for {row['id']}: {forbidden}")
        require(row["target_external_id"] in refs, f"target external id does not resolve: {row['target_external_id']}")
        require(row["target_model"] in {"payment.request", "construction.contract"}, f"unexpected target model: {row['target_model']}")
        require(row["action_classification"] in {"unknown", "approve", "reject_or_back", "reject_or_cancel"}, f"bad action classification: {row['action_classification']}")


def verify_external_manifest(external_manifest: dict[str, Any], records: list[dict[str, str]]) -> None:
    manifest_records = external_manifest.get("records", [])
    require(isinstance(manifest_records, list), "external manifest records must be a list")
    xml_ids = {row["id"] for row in records}
    manifest_ids = {row.get("external_id") for row in manifest_records}
    require(xml_ids == manifest_ids, "external manifest ids do not match XML ids")
    require(external_manifest.get("summary", {}).get("loadable") == len(records), "loadable count mismatch")
    for row in manifest_records:
        require(row.get("target_model") in {"payment.request", "construction.contract"}, f"invalid target model: {row}")
        require(row.get("status") == "loadable", f"non-loadable manifest row: {row}")
        require(row.get("target_external_id"), f"missing target external id: {row}")


def verify_validation_manifest(validation_manifest: dict[str, Any]) -> None:
    gates = set(validation_manifest.get("validation_gates", {}).get("generate_time", []))
    required = {
        "legacy_workflow_id_unique",
        "target_external_id_resolves_to_asset_manifest",
        "no_tier_review_records_generated",
        "no_tier_definition_records_generated",
        "no_runtime_workflow_records_generated",
        "no_database_integer_ids_required",
    }
    missing = sorted(required - gates)
    require(not missing, f"validation manifest missing gates: {missing}")
    boundary = validation_manifest.get("business_boundary", {})
    require(boundary.get("historical_approval_audit_fact") == "included", "historical audit fact must be included")
    require(boundary.get("tier_review") == "excluded", "tier.review must be excluded")
    require(boundary.get("tier_definition") == "excluded", "tier.definition must be excluded")
    require(boundary.get("runtime_workflow_state") == "excluded", "runtime workflow must be excluded")
    require(boundary.get("target_business_state_mutation") == "excluded", "target mutation must be excluded")


def verify(asset_root: Path, lane: str) -> dict[str, Any]:
    asset_manifest = load_json(asset_root / "manifest/legacy_workflow_audit_asset_manifest_v1.json")
    external_manifest = load_json(asset_root / "manifest/legacy_workflow_audit_external_id_manifest_v1.json")
    validation_manifest = load_json(asset_root / "manifest/legacy_workflow_audit_validation_manifest_v1.json")
    materialize_workflow_xml_from_parts(asset_root)
    records = parse_xml(asset_root / "30_relation" / lane / "legacy_workflow_audit_v1.xml")
    refs = target_refs(asset_root)
    verify_asset_manifest(asset_manifest, lane)
    verify_hashes(asset_root, asset_manifest)
    verify_xml_records(records, asset_manifest["counts"]["loadable_records"], refs)
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
    parser = argparse.ArgumentParser(description="Verify legacy workflow audit XML migration assets.")
    parser.add_argument("--asset-root", default="migration_assets")
    parser.add_argument("--lane", default="legacy_workflow_audit")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        result = verify(Path(args.asset_root), args.lane)
    except (WorkflowAuditAssetVerificationError, ET.ParseError, json.JSONDecodeError) as exc:
        payload = {"status": "FAIL", "error": str(exc), "db_writes": 0, "odoo_shell": False}
        print("LEGACY_WORKFLOW_AUDIT_ASSET_VERIFY=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 1 if args.check else 0
    print("LEGACY_WORKFLOW_AUDIT_ASSET_VERIFY=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
