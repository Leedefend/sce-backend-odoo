#!/usr/bin/env python3
"""Generate URL-type ir.attachment XML assets for prior business lanes."""

from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import re
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from typing import Any

import legacy_global_attachment_screen as global_screen
import legacy_receipt_invoice_attachment_asset_generator as receipt_attachment


REPO_ASSET_ROOT = Path("migration_assets")
RUNTIME_ROOT = Path(".runtime_artifacts/migration_assets/legacy_attachment_backfill_sc_v1")
XML_REL_PATH = Path("30_relation/legacy_attachment_backfill/legacy_attachment_backfill_v1.xml")
EXTERNAL_REL_PATH = Path("manifest/legacy_attachment_backfill_external_id_manifest_v1.json")
VALIDATION_REL_PATH = Path("manifest/legacy_attachment_backfill_validation_manifest_v1.json")
ASSET_MANIFEST_REL_PATH = Path("manifest/legacy_attachment_backfill_asset_manifest_v1.json")
CATALOG_REL_PATH = Path("manifest/migration_asset_catalog_v1.json")
ASSET_PACKAGE_ID = "legacy_attachment_backfill_sc_v1"
GENERATED_AT = "2026-04-15T16:20:00+00:00"

INCLUDED_LANES = {
    "project",
    "project_member",
    "actual_outflow",
    "supplier_contract",
    "supplier_contract_line",
    "outflow_request_line",
}
DEPENDENCIES = [
    "project_sc_v1",
    "project_member_sc_v1",
    "actual_outflow_sc_v1",
    "supplier_contract_sc_v1",
    "supplier_contract_line_sc_v1",
    "outflow_request_line_sc_v1",
]


class AttachmentBackfillAssetError(Exception):
    pass


def clean(value: object) -> str:
    text = "" if value is None else str(value).strip()
    return "" if text.upper() == "NULL" else text


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AttachmentBackfillAssetError(message)


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


def safe_suffix(value: str) -> str:
    suffix = re.sub(r"[^0-9A-Za-z_]+", "_", value).strip("_").lower()
    require(bool(suffix), "cannot build external id from blank value")
    return suffix


def add_text_field(record: ET.Element, name: str, value: object, *, required: bool = False) -> None:
    text = clean(value)
    if not text and not required:
        return
    field = ET.SubElement(record, "field", {"name": name})
    field.text = text


def add_ref_field(record: ET.Element, name: str, external_id: str) -> None:
    ET.SubElement(record, "field", {"name": name, "ref": external_id})


def write_xml(path: Path, records: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    root = ET.Element("odoo")
    data = ET.SubElement(root, "data", {"noupdate": "1"})
    for row in records:
        record = ET.SubElement(data, "record", {"id": row["external_id"], "model": "ir.attachment"})
        add_text_field(record, "name", row["name"], required=True)
        add_text_field(record, "type", "url", required=True)
        add_text_field(record, "url", row["url"], required=True)
        add_text_field(record, "res_model", row["res_model"], required=True)
        add_ref_field(record, "res_id", row["target_external_id"])
        add_text_field(record, "mimetype", row["mimetype"])
        add_text_field(record, "description", row["description"], required=True)
    ET.indent(root, space="  ")
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)


def update_catalog(asset_root: Path, manifest_hash: str) -> None:
    catalog_path = asset_root / CATALOG_REL_PATH
    catalog = load_json(catalog_path)
    package = {
        "asset_manifest_path": str(ASSET_MANIFEST_REL_PATH),
        "asset_manifest_sha256": manifest_hash,
        "asset_package_id": ASSET_PACKAGE_ID,
        "baseline_package": True,
        "business_priority": "legacy_attachment_backfill",
        "dependencies": DEPENDENCIES,
        "layer": "30_relation",
        "load_phase": 30,
        "package_type": "url_attachment_relation",
        "required": True,
        "risk_class": "attachment_url_relation",
        "target_model": "ir.attachment",
        "verification_command": "python3 scripts/migration/legacy_attachment_backfill_asset_verify.py --asset-root migration_assets --lane legacy_attachment_backfill --check",
    }
    catalog["package_order"] = [item for item in catalog.get("package_order", []) if item != ASSET_PACKAGE_ID]
    catalog["package_order"].append(ASSET_PACKAGE_ID)
    catalog["packages"] = [item for item in catalog.get("packages", []) if item.get("asset_package_id") != ASSET_PACKAGE_ID]
    catalog["packages"].append(package)
    catalog["generated_at"] = GENERATED_AT
    write_json(catalog_path, catalog)


def generate(asset_root: Path, runtime_root: Path, expected_ready: int) -> dict[str, Any]:
    index = global_screen.build_candidate_index(asset_root)
    source_rows = receipt_attachment.parse_sql_rows(receipt_attachment.run_sql())
    records: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    lane_counts: Counter[str] = Counter()
    target_counts: Counter[str] = Counter()

    for row in source_rows:
        if receipt_attachment.is_deleted(row.get("DEL")):
            continue
        file_id = clean(row.get("ID"))
        for source_field in global_screen.SOURCE_FIELDS:
            source_value = clean(row.get(source_field))
            if not source_value:
                continue
            for candidate in index.get(source_value, []):
                lane = candidate["lane"]
                if lane not in INCLUDED_LANES:
                    continue
                key = (lane, file_id)
                if key in seen:
                    continue
                seen.add(key)
                name = clean(row.get("ATTR_NAME")) or file_id
                mimetype = mimetypes.guess_type(name)[0] or ""
                external_id = f"legacy_attachment_backfill_sc_{safe_suffix(lane)}_{safe_suffix(file_id)}"
                records.append(
                    {
                        "external_id": external_id,
                        "lane": lane,
                        "legacy_file_id": file_id,
                        "target_external_id": candidate["external_id"],
                        "res_model": candidate["target_model"],
                        "name": name,
                        "url": receipt_attachment.attachment_url(row),
                        "mimetype": mimetype,
                        "file_md5": clean(row.get("FILEMD5")),
                        "file_size": clean(row.get("FILESIZE")),
                        "description": (
                            "[migration:legacy_attachment_backfill] "
                            f"lane={lane}; legacy_file_id={file_id}; source_field={source_field}; "
                            f"candidate_key={candidate['candidate_key']}; binary_embedded=false"
                        ),
                    }
                )
                lane_counts[lane] += 1
                target_counts[f"{lane}:{candidate['external_id']}"] += 1

    require(len(records) == expected_ready, f"ready attachment count drifted: {len(records)} != {expected_ready}")
    require(len({row["external_id"] for row in records}) == len(records), "duplicate attachment external ids")

    xml_path = asset_root / XML_REL_PATH
    external_path = asset_root / EXTERNAL_REL_PATH
    validation_path = asset_root / VALIDATION_REL_PATH
    asset_manifest_path = asset_root / ASSET_MANIFEST_REL_PATH
    write_xml(xml_path, records)

    external_manifest = {
        "manifest_version": "1.0",
        "asset_package_id": ASSET_PACKAGE_ID,
        "generated_at": GENERATED_AT,
        "records": [
            {
                "external_id": row["external_id"],
                "lane": row["lane"],
                "legacy_file_id": row["legacy_file_id"],
                "target_external_id": row["target_external_id"],
                "target_model": "ir.attachment",
                "res_model": row["res_model"],
                "status": "loadable",
                "file_md5": row["file_md5"],
                "file_size": row["file_size"],
                "binary_embedded": False,
            }
            for row in records
        ],
        "summary": {"loadable": len(records), "raw_file_rows": len(source_rows), "lane_counts": dict(sorted(lane_counts.items()))},
        "db_writes": 0,
        "odoo_shell": False,
    }
    validation_manifest = {
        "manifest_version": "1.0",
        "asset_package_id": ASSET_PACKAGE_ID,
        "generated_at": GENERATED_AT,
        "validation_gates": {
            "generate_time": [
                "lane_file_external_id_unique",
                "target_external_id_resolves_by_lane",
                "attachment_type_url_only",
                "binary_datas_field_not_emitted",
                "deleted_files_excluded",
            ]
        },
        "business_boundary": {
            "ir_attachment_record": "included",
            "business_relation": "included",
            "binary_file_custody": "excluded",
            "url_strategy": "legacy-file-url",
        },
        "lane_counts": dict(sorted(lane_counts.items())),
        "matched_target_records": len(target_counts),
        "db_writes": 0,
        "odoo_shell": False,
    }
    write_json(external_path, external_manifest)
    write_json(validation_path, validation_manifest)

    asset_manifest = {
        "asset_manifest_version": "1.0",
        "asset_package_id": ASSET_PACKAGE_ID,
        "generated_at": GENERATED_AT,
        "baseline_package": True,
        "db_writes": 0,
        "odoo_shell": False,
        "dependencies": DEPENDENCIES,
        "lane": {"layer": "30_relation", "lane_id": "legacy_attachment_backfill"},
        "target": {"model": "ir.attachment", "type": "url", "res_models": sorted({row["res_model"] for row in records})},
        "counts": {
            "raw_rows": len(source_rows),
            "loadable_records": len(records),
            "blocked_records": 0,
            "matched_target_records": len(target_counts),
        },
        "source_counts": {"lane_counts": dict(sorted(lane_counts.items()))},
        "assets": [
            {"path": str(XML_REL_PATH), "sha256": sha256_file(xml_path)},
            {"path": str(EXTERNAL_REL_PATH), "sha256": sha256_file(external_path)},
            {"path": str(VALIDATION_REL_PATH), "sha256": sha256_file(validation_path)},
        ],
    }
    write_json(asset_manifest_path, asset_manifest)
    update_catalog(asset_root, sha256_file(asset_manifest_path))

    runtime_root.mkdir(parents=True, exist_ok=True)
    write_json(runtime_root / "generation_result_v1.json", asset_manifest)
    return {
        "status": "PASS",
        "asset_package_id": ASSET_PACKAGE_ID,
        "loadable_records": len(records),
        "lane_counts": dict(sorted(lane_counts.items())),
        "matched_target_records": len(target_counts),
        "db_writes": 0,
        "odoo_shell": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate legacy attachment backfill URL XML assets.")
    parser.add_argument("--asset-root", default=str(REPO_ASSET_ROOT))
    parser.add_argument("--runtime-root", default=str(RUNTIME_ROOT))
    parser.add_argument("--expected-ready", type=int, default=18458)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        result = generate(Path(args.asset_root), Path(args.runtime_root), args.expected_ready)
    except (AttachmentBackfillAssetError, json.JSONDecodeError, OSError) as exc:
        payload = {"status": "FAIL", "error": str(exc), "db_writes": 0, "odoo_shell": False}
        print("LEGACY_ATTACHMENT_BACKFILL_ASSET_GENERATOR=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 1 if args.check else 0
    print("LEGACY_ATTACHMENT_BACKFILL_ASSET_GENERATOR=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
