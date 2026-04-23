#!/usr/bin/env python3
"""Generate repository XML assets for neutral project-member staging facts."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ASSET_ROOT = Path("migration_assets")
RUNTIME_ROOT = Path(".runtime_artifacts/migration_assets/project_member_sc_v1")
SOURCE_CSV = Path("tmp/raw/project_member/project_member.csv")
PROJECT_EXTERNAL_MANIFEST = REPO_ASSET_ROOT / "manifest/project_external_id_manifest_v1.json"
USER_EXTERNAL_MANIFEST = REPO_ASSET_ROOT / "manifest/user_external_id_manifest_v1.json"
XML_REL_PATH = Path("30_relation/project_member/project_member_neutral_v1.xml")
EXTERNAL_REL_PATH = Path("manifest/project_member_external_id_manifest_v1.json")
VALIDATION_REL_PATH = Path("manifest/project_member_validation_manifest_v1.json")
ASSET_MANIFEST_REL_PATH = Path("manifest/project_member_asset_manifest_v1.json")
REQUIRED_COLUMNS = {"ID", "USERID", "XMID"}
ASSET_PACKAGE_ID = "project_member_sc_v1"
IMPORT_BATCH = "project_member_neutral_xml_v1"
GENERATED_AT = "2026-04-15T07:20:00+00:00"


class ProjectMemberAssetError(Exception):
    pass


def clean(value: object) -> str:
    return ("" if value is None else str(value)).strip()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ProjectMemberAssetError(message)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    require(path.exists(), f"missing json file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def read_source(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    require(path.exists(), f"missing project-member source csv: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = list(reader.fieldnames or [])
        rows = [dict(row) for row in reader]
    missing = sorted(REQUIRED_COLUMNS - set(fields))
    require(not missing, f"missing project-member source columns: {missing}")
    return fields, rows


def safe_external_suffix(value: str) -> str:
    suffix = re.sub(r"[^0-9A-Za-z_]+", "_", value).strip("_").lower()
    require(bool(suffix), "cannot build external id from blank legacy_member_id")
    return suffix


def build_project_map(manifest: dict[str, Any]) -> dict[str, str]:
    result: dict[str, str] = {}
    for row in manifest.get("records", []):
        legacy_id = clean(row.get("target_lookup", {}).get("value"))
        external_id = clean(row.get("external_id"))
        if legacy_id and external_id and row.get("status") == "loadable":
            result[legacy_id] = external_id
    require(result, "project external id map is empty")
    return result


def build_user_map(manifest: dict[str, Any]) -> dict[str, str]:
    result: dict[str, str] = {}
    for row in manifest.get("records", []):
        legacy_id = clean(row.get("legacy_user_id"))
        external_id = clean(row.get("external_id"))
        if legacy_id and external_id and row.get("status") == "loadable":
            result[legacy_id] = external_id
    require(result, "user external id map is empty")
    return result


def add_text_field(record: ET.Element, name: str, value: object) -> None:
    field = ET.SubElement(record, "field", {"name": name})
    field.text = clean(value)


def add_ref_field(record: ET.Element, name: str, external_id: str) -> None:
    ET.SubElement(record, "field", {"name": name, "ref": external_id})


def write_xml(path: Path, records: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    root = ET.Element("odoo")
    data = ET.SubElement(root, "data", {"noupdate": "1"})
    for row in records:
        record = ET.SubElement(data, "record", {"id": row["external_id"], "model": "sc.project.member.staging"})
        add_text_field(record, "legacy_member_id", row["legacy_member_id"])
        add_text_field(record, "legacy_project_id", row["legacy_project_id"])
        add_text_field(record, "legacy_user_ref", row["legacy_user_ref"])
        add_ref_field(record, "project_id", row["project_external_id"])
        add_ref_field(record, "user_id", row["user_external_id"])
        add_text_field(record, "role_fact_status", "missing")
        add_text_field(record, "import_batch", IMPORT_BATCH)
        add_text_field(record, "evidence", f"BASE_SYSTEM_PROJECT_USER:{row['legacy_member_id']}")
        add_text_field(record, "notes", "neutral staging only; role fact missing")
        add_text_field(record, "active", "1")
    ET.indent(root, space="  ")
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)


def generate(asset_root: Path, runtime_root: Path, source_csv: Path) -> dict[str, Any]:
    _fields, source_rows = read_source(source_csv)
    project_map = build_project_map(load_json(PROJECT_EXTERNAL_MANIFEST))
    user_map = build_user_map(load_json(USER_EXTERNAL_MANIFEST))

    counters: Counter[str] = Counter()
    member_ids: Counter[str] = Counter()
    relation_keys: Counter[tuple[str, str]] = Counter()
    loadable: list[dict[str, str]] = []
    discarded: list[dict[str, str]] = []

    for line_no, row in enumerate(source_rows, start=2):
        legacy_member_id = clean(row.get("ID"))
        legacy_project_id = clean(row.get("XMID"))
        legacy_user_ref = clean(row.get("USERID"))
        errors: list[str] = []
        if not legacy_member_id:
            errors.append("missing_legacy_member_id")
        if not legacy_project_id:
            errors.append("missing_legacy_project_id")
        if not legacy_user_ref:
            errors.append("missing_legacy_user_ref")
        project_external_id = project_map.get(legacy_project_id)
        user_external_id = user_map.get(legacy_user_ref)
        if legacy_project_id and not project_external_id:
            errors.append("project_anchor_missing")
        if legacy_user_ref and not user_external_id:
            errors.append("user_anchor_missing")

        if errors:
            for error in errors:
                counters[error] += 1
            discarded.append(
                {
                    "line_no": str(line_no),
                    "legacy_member_id": legacy_member_id,
                    "legacy_project_id": legacy_project_id,
                    "legacy_user_ref": legacy_user_ref,
                    "errors": ",".join(errors),
                }
            )
            continue

        external_id = f"legacy_project_member_sc_{safe_external_suffix(legacy_member_id)}"
        member_ids[legacy_member_id] += 1
        relation_keys[(legacy_project_id, legacy_user_ref)] += 1
        loadable.append(
            {
                "external_id": external_id,
                "legacy_member_id": legacy_member_id,
                "legacy_project_id": legacy_project_id,
                "legacy_user_ref": legacy_user_ref,
                "project_external_id": project_external_id or "",
                "user_external_id": user_external_id or "",
            }
        )

    duplicate_member_ids = sorted(key for key, count in member_ids.items() if count > 1)
    require(not duplicate_member_ids, f"duplicate legacy member ids are not loadable: {duplicate_member_ids[:10]}")
    require(len({row["external_id"] for row in loadable}) == len(loadable), "duplicate XML external ids")

    xml_path = asset_root / XML_REL_PATH
    external_path = asset_root / EXTERNAL_REL_PATH
    validation_path = asset_root / VALIDATION_REL_PATH
    asset_manifest_path = asset_root / ASSET_MANIFEST_REL_PATH
    write_xml(xml_path, loadable)

    external_manifest = {
        "asset_manifest_version": "1.0",
        "asset_package_id": ASSET_PACKAGE_ID,
        "external_id_rule": {
            "legacy_key_policy": "stable_legacy_member_pk",
            "pattern": "legacy_project_member_sc_<legacy_member_id>",
            "source": "sc",
        },
        "lane_id": "project_member",
        "records": [
            {
                "external_id": row["external_id"],
                "legacy_member_id": row["legacy_member_id"],
                "legacy_project_id": row["legacy_project_id"],
                "legacy_user_ref": row["legacy_user_ref"],
                "project_external_id": row["project_external_id"],
                "status": "loadable",
                "target_model": "sc.project.member.staging",
                "user_external_id": row["user_external_id"],
            }
            for row in loadable
        ],
        "summary": {
            "discarded": len(discarded),
            "loadable": len(loadable),
            "raw_rows": len(source_rows),
        },
    }
    write_json(external_path, external_manifest)

    duplicate_relation_keys = sum(1 for count in relation_keys.values() if count > 1)
    rows_in_duplicate_relations = sum(count for count in relation_keys.values() if count > 1)
    validation_manifest = {
        "asset_manifest_version": "1.0",
        "asset_package_id": ASSET_PACKAGE_ID,
        "db_writes": 0,
        "generated_at": GENERATED_AT,
        "odoo_shell": False,
        "source": str(source_csv),
        "target_model": "sc.project.member.staging",
        "validation_gates": {
            "generate_time": [
                "required_source_headers_present",
                "legacy_member_id_unique",
                "project_external_id_resolves",
                "user_external_id_resolves",
                "role_fact_status_missing",
                "duplicate_project_user_relations_preserved",
                "no_responsibility_or_authority_claim",
            ],
            "postload": ["xml_external_id_resolves", "project_id_ref_resolves", "user_id_ref_resolves"],
        },
        "relationship_profile": {
            "distinct_project_user_relation_keys": len(relation_keys),
            "duplicate_project_user_relation_keys": duplicate_relation_keys,
            "rows_in_duplicate_project_user_relations": rows_in_duplicate_relations,
            "duplicate_relation_strategy": "preserve_as_neutral_evidence",
        },
    }
    write_json(validation_path, validation_manifest)

    asset_manifest = {
        "asset_manifest_version": "1.0",
        "asset_package_id": ASSET_PACKAGE_ID,
        "assets": [
            {
                "asset_id": "project_member_neutral_xml_v1",
                "format": "xml",
                "path": str(XML_REL_PATH),
                "record_count": len(loadable),
                "required": True,
                "sha256": sha256_file(xml_path),
            },
            {
                "asset_id": "project_member_external_id_manifest_v1",
                "format": "json",
                "path": str(EXTERNAL_REL_PATH),
                "record_count": len(loadable),
                "required": True,
                "sha256": sha256_file(external_path),
            },
            {
                "asset_id": "project_member_validation_manifest_v1",
                "format": "json",
                "path": str(VALIDATION_REL_PATH),
                "record_count": 1,
                "required": True,
                "sha256": sha256_file(validation_path),
            },
        ],
        "baseline_package": True,
        "counts": {
            "discarded_records": len(discarded),
            "loadable_records": len(loadable),
            "raw_rows": len(source_rows),
        },
        "db_writes": 0,
        "dependencies": ["project_sc_v1", "user_sc_v1"],
        "generated_at": GENERATED_AT,
        "idempotency": {
            "conflict_policy": "block_package",
            "duplicate_policy": "update_existing_same_external_id",
            "mode": "odoo_xml_external_id",
        },
        "lane": {
            "business_priority": "relation_business_fact",
            "lane_id": "project_member",
            "layer": "30_relation",
            "risk_class": "neutral_relation",
        },
        "load_order": [
            "project_member_neutral_xml_v1",
            "project_member_external_id_manifest_v1",
            "project_member_validation_manifest_v1",
        ],
        "odoo_shell": False,
        "source_snapshot": {
            "extract_batch_id": "project_member_xml_baseline_v1",
            "source_system": "sc",
            "source_tables": ["BASE_SYSTEM_PROJECT_USER"],
        },
        "target": {
            "identity_field": "legacy_member_id",
            "load_strategy": "odoo_xml_external_id",
            "model": "sc.project.member.staging",
        },
        "validation_gates": [
            "source_member_file_exists",
            "required_source_headers_present",
            "legacy_member_id_non_empty",
            "legacy_member_id_unique",
            "project_anchor_resolves",
            "user_anchor_resolves",
            "role_fact_status_missing",
            "no_responsibility_or_authority_claim",
        ],
    }
    write_json(asset_manifest_path, asset_manifest)

    runtime_root.mkdir(parents=True, exist_ok=True)
    write_json(runtime_root / "project_member_discard_v1.json", {"discarded": discarded, "counters": dict(counters)})
    return {
        "status": "PASS",
        "asset_package_id": ASSET_PACKAGE_ID,
        "db_writes": 0,
        "odoo_shell": False,
        "raw_rows": len(source_rows),
        "loadable_records": len(loadable),
        "discarded_records": len(discarded),
        "duplicate_project_user_relation_keys": duplicate_relation_keys,
        "rows_in_duplicate_project_user_relations": rows_in_duplicate_relations,
        "asset_manifest_sha256": sha256_file(asset_manifest_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate project-member neutral XML migration assets.")
    parser.add_argument("--asset-root", default=str(REPO_ASSET_ROOT))
    parser.add_argument("--runtime-root", default=str(RUNTIME_ROOT))
    parser.add_argument("--source", default=str(SOURCE_CSV))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    try:
        result = generate(Path(args.asset_root), Path(args.runtime_root), Path(args.source))
    except (ProjectMemberAssetError, json.JSONDecodeError) as exc:
        payload = {"status": "FAIL", "error": str(exc), "db_writes": 0, "odoo_shell": False}
        print("PROJECT_MEMBER_ASSET_GENERATOR=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 1 if args.check else 0

    print("PROJECT_MEMBER_ASSET_GENERATOR=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
