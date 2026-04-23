#!/usr/bin/env python3
"""Generate no-DB project migration assets from legacy project facts."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape


REQUIRED_HEADERS = ("ID", "XMMC")
OPTIONAL_DIRECT_HEADERS = (
    "PID",
    "SHORT_NAME",
    "PROJECT_ENV",
    "NATURE",
    "DETAIL_ADDRESS",
    "PROFILE",
    "AREA",
    "PROJECTOVERVIEW",
    "OTHER_SYSTEM_ID",
    "OTHER_SYSTEM_CODE",
)
DEFERRED_HEADERS = (
    "PROJECT_CODE",
    "SPECIALTY_TYPE_ID",
    "SPECIALTY_TYPE_NAME",
    "PRICE_METHOD",
    "CONTRACT_STATUS",
    "IS_COMPLETE_PROJECT",
    "COMPANYID",
    "COMPANYNAME",
    "TAX_ORGANIZATION_ID",
    "TAX_ORGANIZATION_NAME",
    "ACCOUNT_NAME",
    "ACCOUNT_NUMBER",
    "ACCOUNT_BANK",
    "COST",
    "MANAGE_FEE_RATIO",
    "IS_SHARED_BASE",
    "SORT",
    "NOTE",
    "FJ",
    "LRR",
    "LRRID",
    "LRSJ",
    "XGR",
    "XGRID",
    "XGSJ",
    "DEL",
    "PROJECTMANAGER",
    "TECHNICALRESPONSIBILITY",
    "OWNERSUNIT",
    "OWNERSCONTACT",
    "OWNERSCONTACTPHONE",
    "SUPERVISIONUNIT",
    "SUPERVISORYENGINEER",
    "SUPERVISOPHONE",
    "CONTRACTAGREEMENT",
    "PROJECTFILE",
    "CONTRACTINGMETHOD",
    "PROJECT_NATURE",
    "IS_MACHINTERIAL_LIBRARY",
    "WBHTID",
    "ZSLX",
    "XMJDID",
    "XMJD",
    "SSDQID",
    "SSDQ",
    "STATE",
    "XQRGZ",
    "XQRGZR",
    "XQRGZRID",
    "XQRGZXZRID",
    "XQRGZXZR",
)
MASTER_FIELDS = (
    "external_id",
    "legacy_identity_key",
    "legacy_project_id",
    "name",
    "short_name",
    "project_environment",
    "business_nature",
    "detail_address",
    "project_profile",
    "project_area",
    "project_overview",
    "legacy_parent_id",
    "other_system_id",
    "other_system_code",
)
DEFERRED_FIELDS = (
    "legacy_project_id",
    "legacy_field",
    "legacy_value",
    "defer_reason",
    "target_candidate",
)
DISCARD_FIELDS = ("discard_reason", "count")

DEFER_RULES = {
    "PROJECT_CODE": ("project_code_write_policy_not_frozen", "project_code"),
    "SPECIALTY_TYPE_ID": ("dictionary_mapping_not_frozen", "project_type_id"),
    "SPECIALTY_TYPE_NAME": ("dictionary_mapping_not_frozen", "project_type_id"),
    "PRICE_METHOD": ("pricing_behavior_deferred", "legacy_price_method"),
    "CONTRACT_STATUS": ("contract_adjacent_lane", ""),
    "CONTRACTAGREEMENT": ("contract_adjacent_lane", ""),
    "CONTRACTINGMETHOD": ("contract_adjacent_lane", ""),
    "WBHTID": ("contract_adjacent_lane", ""),
    "COMPANYID": ("partner_or_user_dependency", "company_id"),
    "COMPANYNAME": ("partner_or_user_dependency", "company_id"),
    "PROJECTMANAGER": ("partner_or_user_dependency", "project_manager_user_id"),
    "TECHNICALRESPONSIBILITY": ("partner_or_user_dependency", "technical_lead_user_id"),
    "OWNERSUNIT": ("partner_or_user_dependency", "owner_id"),
    "OWNERSCONTACT": ("partner_or_user_dependency", "owner_contact"),
    "OWNERSCONTACTPHONE": ("partner_or_user_dependency", "owner_contact_phone"),
    "SUPERVISIONUNIT": ("partner_or_user_dependency", "supervision_partner_id"),
    "SUPERVISORYENGINEER": ("partner_or_user_dependency", "supervisory_engineer_name"),
    "SUPERVISOPHONE": ("partner_or_user_dependency", "supervision_phone"),
    "ACCOUNT_NAME": ("tax_bank_account_out_of_scope", ""),
    "ACCOUNT_NUMBER": ("tax_bank_account_out_of_scope", ""),
    "ACCOUNT_BANK": ("tax_bank_account_out_of_scope", ""),
    "TAX_ORGANIZATION_ID": ("tax_bank_account_out_of_scope", ""),
    "TAX_ORGANIZATION_NAME": ("tax_bank_account_out_of_scope", ""),
    "COST": ("cost_financial_semantics_deferred", ""),
    "MANAGE_FEE_RATIO": ("cost_financial_semantics_deferred", ""),
    "STATE": ("lifecycle_policy_deferred", "lifecycle_state"),
    "XMJDID": ("lifecycle_policy_deferred", "stage_id"),
    "XMJD": ("lifecycle_policy_deferred", "stage_id"),
    "IS_COMPLETE_PROJECT": ("lifecycle_policy_deferred", ""),
    "LRR": ("legacy_audit_metadata_policy_deferred", ""),
    "LRRID": ("legacy_audit_metadata_policy_deferred", ""),
    "LRSJ": ("legacy_audit_metadata_policy_deferred", ""),
    "XGR": ("legacy_audit_metadata_policy_deferred", ""),
    "XGRID": ("legacy_audit_metadata_policy_deferred", ""),
    "XGSJ": ("legacy_audit_metadata_policy_deferred", ""),
    "DEL": ("archive_delete_policy_deferred", "active"),
    "PROJECTFILE": ("attachment_import_deferred", ""),
    "FJ": ("attachment_import_deferred", ""),
    "XQRGZ": ("requirement_confirmation_workflow_deferred", ""),
    "XQRGZR": ("requirement_confirmation_workflow_deferred", ""),
    "XQRGZRID": ("requirement_confirmation_workflow_deferred", ""),
    "XQRGZXZRID": ("requirement_confirmation_workflow_deferred", ""),
    "XQRGZXZR": ("requirement_confirmation_workflow_deferred", ""),
    "IS_SHARED_BASE": ("shared_base_workflow_deferred", ""),
    "SORT": ("sort_order_policy_deferred", ""),
    "NOTE": ("note_target_policy_deferred", ""),
    "PROJECT_NATURE": ("project_nature_mapping_deferred", ""),
    "IS_MACHINTERIAL_LIBRARY": ("material_library_workflow_deferred", ""),
    "ZSLX": ("unknown_legacy_semantics_deferred", ""),
    "SSDQID": ("region_dictionary_mapping_deferred", "region_id"),
    "SSDQ": ("region_dictionary_mapping_deferred", "region_id"),
}


class ValidationError(Exception):
    pass


def clean(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_csv(path: Path, fieldnames: tuple[str, ...], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_project_xml(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    model_fields = (
        "legacy_project_id",
        "name",
        "short_name",
        "project_environment",
        "business_nature",
        "detail_address",
        "project_profile",
        "project_area",
        "project_overview",
        "legacy_parent_id",
        "other_system_id",
        "other_system_code",
    )
    lines = [
        '<?xml version="1.0" encoding="utf-8"?>',
        "<odoo>",
        '  <data noupdate="1">',
    ]
    for row in rows:
        external_id = clean(row.get("external_id"))
        lines.append(f'    <record id="{escape(external_id)}" model="project.project">')
        for field in model_fields:
            value = clean(row.get(field))
            if value:
                lines.append(f'      <field name="{field}">{escape(value)}</field>')
        lines.append("    </record>")
    lines.extend(["  </data>", "</odoo>", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def read_source(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        headers = list(reader.fieldnames or [])
        rows = [dict(row) for row in reader]
    return headers, rows


def defer_rule(field: str) -> tuple[str, str]:
    return DEFER_RULES.get(field, ("field_deferred_by_v1_scope", ""))


def build_assets(rows: list[dict[str, str]], headers: list[str], source: str) -> dict[str, Any]:
    missing_headers = [header for header in REQUIRED_HEADERS if header not in headers]
    if missing_headers:
        raise ValidationError(f"missing required source headers: {', '.join(missing_headers)}")

    id_counts = Counter(clean(row.get("ID")) for row in rows if clean(row.get("ID")))
    duplicate_ids = sorted(project_id for project_id, count in id_counts.items() if count > 1)
    if duplicate_ids:
        raise ValidationError(f"duplicate legacy project ids block package: {duplicate_ids[:10]}")

    master_rows: list[dict[str, Any]] = []
    deferred_rows: list[dict[str, Any]] = []
    discard_reasons: Counter[str] = Counter()
    external_records: list[dict[str, Any]] = []

    for row in rows:
        legacy_project_id = clean(row.get("ID"))
        project_name = clean(row.get("XMMC"))
        if not legacy_project_id:
            discard_reasons["missing_legacy_project_id"] += 1
            continue
        if not project_name:
            discard_reasons["missing_project_name"] += 1
            continue

        external_id = f"legacy_project_{source}_{legacy_project_id}"
        legacy_identity_key = f"project:{source}:{legacy_project_id}"
        master_rows.append(
            {
                "external_id": external_id,
                "legacy_identity_key": legacy_identity_key,
                "legacy_project_id": legacy_project_id,
                "name": project_name,
                "short_name": clean(row.get("SHORT_NAME")),
                "project_environment": clean(row.get("PROJECT_ENV")),
                "business_nature": clean(row.get("NATURE")),
                "detail_address": clean(row.get("DETAIL_ADDRESS")),
                "project_profile": clean(row.get("PROFILE")),
                "project_area": clean(row.get("AREA")),
                "project_overview": clean(row.get("PROJECTOVERVIEW")),
                "legacy_parent_id": clean(row.get("PID")),
                "other_system_id": clean(row.get("OTHER_SYSTEM_ID")),
                "other_system_code": clean(row.get("OTHER_SYSTEM_CODE")),
            }
        )
        external_records.append(
            {
                "external_id": external_id,
                "legacy_key": legacy_project_id,
                "legacy_key_type": "single_pk",
                "source_table": "project",
                "target_model": "project.project",
                "target_lookup": {"field": "legacy_project_id", "value": legacy_project_id},
                "status": "loadable",
            }
        )

        for field in DEFERRED_HEADERS:
            if field not in headers:
                continue
            value = clean(row.get(field))
            if not value:
                continue
            reason, target = defer_rule(field)
            deferred_rows.append(
                {
                    "legacy_project_id": legacy_project_id,
                    "legacy_field": field,
                    "legacy_value": value,
                    "defer_reason": reason,
                    "target_candidate": target,
                }
            )

    discard_rows = [{"discard_reason": reason, "count": count} for reason, count in sorted(discard_reasons.items())]
    for required_reason in ("missing_legacy_project_id", "duplicate_legacy_project_id", "missing_project_name"):
        if required_reason not in discard_reasons:
            discard_rows.append({"discard_reason": required_reason, "count": 0})

    return {
        "master_rows": master_rows,
        "deferred_rows": deferred_rows,
        "discard_rows": sorted(discard_rows, key=lambda item: item["discard_reason"]),
        "external_records": external_records,
        "missing_optional_headers": [header for header in OPTIONAL_DIRECT_HEADERS if header not in headers],
        "missing_deferred_headers": [header for header in DEFERRED_HEADERS if header not in headers],
        "raw_rows": len(rows),
        "discarded_records": sum(discard_reasons.values()),
    }


def assert_unique(rows: list[dict[str, Any]], field: str) -> None:
    values = [clean(row.get(field)) for row in rows if clean(row.get(field))]
    duplicates = [value for value, count in Counter(values).items() if count > 1]
    if duplicates:
        raise ValidationError(f"duplicate {field}: {duplicates[:10]}")


def build_validation_manifest(
    package_id: str,
    hashes: dict[str, str],
    missing_optional_headers: list[str],
    missing_deferred_headers: list[str],
) -> dict[str, Any]:
    return {
        "asset_manifest_version": "1.0",
        "asset_package_id": package_id,
        "validation_gates": {
            "generate_time": [
                "source_project_file_exists",
                "required_source_headers_present",
                "legacy_project_id_non_empty",
                "legacy_project_id_unique",
                "project_name_present",
                "external_id_unique",
                "legacy_identity_key_unique",
                "deferred_fields_written",
                "discard_summary_written",
                "no_lifecycle_fabrication",
                "no_partner_dependency_fabrication",
                "no_high_risk_lane_leakage",
            ],
            "preload": ["asset_files_exist", "asset_hashes_match", "target_model_available"],
            "postload": [
                "target_count_matches_manifest",
                "external_id_resolves",
                "rerun_is_idempotent",
                "no_duplicate_business_identity",
            ],
        },
        "failure_policy": {
            "missing_source_file": "block_package",
            "missing_required_header": "block_package",
            "duplicate_legacy_project_id": "block_package",
            "missing_project_name": "discard_record",
            "external_id_duplicate": "block_package",
            "lifecycle_normalization_attempted": "block_package",
            "high_risk_lane_leakage": "block_package",
        },
        "missing_optional_headers": missing_optional_headers,
        "missing_deferred_headers": missing_deferred_headers,
        "generated_asset_hashes": hashes,
    }


def write_baseline_package(
    baseline_dir: Path,
    package_id: str,
    source: str,
    asset_version: str,
    project_xml_path: Path,
    external_manifest: dict[str, Any],
    validation_manifest: dict[str, Any],
    counts: dict[str, int],
) -> None:
    version_suffix = asset_version if asset_version.startswith("v") else f"v{asset_version}"
    baseline_project_dir = baseline_dir / "10_master" / "project"
    baseline_manifest_dir = baseline_dir / "manifest"
    baseline_xml_path = baseline_project_dir / "project_master_v1.xml"
    baseline_external_path = baseline_manifest_dir / "project_external_id_manifest_v1.json"
    baseline_validation_path = baseline_manifest_dir / "project_validation_manifest_v1.json"
    baseline_asset_path = baseline_manifest_dir / "project_asset_manifest_v1.json"

    baseline_project_dir.mkdir(parents=True, exist_ok=True)
    baseline_manifest_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(project_xml_path, baseline_xml_path)
    write_json(baseline_external_path, external_manifest)

    baseline_hashes = {
        "project_master_xml_v1": sha256_file(baseline_xml_path),
        "project_external_id_manifest_v1": sha256_file(baseline_external_path),
    }
    baseline_validation = dict(validation_manifest)
    baseline_validation["generated_asset_hashes"] = baseline_hashes
    baseline_validation["baseline_package"] = True
    write_json(baseline_validation_path, baseline_validation)
    baseline_hashes["project_validation_manifest_v1"] = sha256_file(baseline_validation_path)

    baseline_asset_manifest = {
        "asset_manifest_version": "1.0",
        "asset_package_id": package_id,
        "baseline_package": True,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_snapshot": {
            "source_system": source,
            "source_tables": ["project"],
            "extract_batch_id": f"project_xml_baseline_{version_suffix}",
        },
        "lane": {
            "lane_id": "project",
            "layer": "10_master",
            "business_priority": "core_business_body",
            "risk_class": "normal",
        },
        "target": {
            "model": "project.project",
            "identity_field": "legacy_project_id",
            "load_strategy": "odoo_xml_external_id",
        },
        "assets": [
            {
                "asset_id": "project_master_xml_v1",
                "path": "10_master/project/project_master_v1.xml",
                "format": "xml",
                "record_count": counts["loadable_records"],
                "sha256": baseline_hashes["project_master_xml_v1"],
                "required": True,
            },
            {
                "asset_id": "project_external_id_manifest_v1",
                "path": "manifest/project_external_id_manifest_v1.json",
                "format": "json",
                "record_count": counts["loadable_records"],
                "sha256": baseline_hashes["project_external_id_manifest_v1"],
                "required": True,
            },
            {
                "asset_id": "project_validation_manifest_v1",
                "path": "manifest/project_validation_manifest_v1.json",
                "format": "json",
                "record_count": 1,
                "sha256": baseline_hashes["project_validation_manifest_v1"],
                "required": True,
            },
        ],
        "load_order": [
            "project_master_xml_v1",
            "project_external_id_manifest_v1",
            "project_validation_manifest_v1",
        ],
        "dependencies": [],
        "counts": counts,
        "idempotency": {
            "mode": "odoo_xml_external_id",
            "duplicate_policy": "update_existing_same_external_id",
            "conflict_policy": "block_package",
        },
        "validation_gates": validation_manifest["validation_gates"]["generate_time"],
        "db_writes": 0,
        "odoo_shell": False,
    }
    write_json(baseline_asset_path, baseline_asset_manifest)


def generate(
    project_path: Path,
    out_dir: Path,
    source: str,
    asset_version: str,
    check: bool,
    baseline_out: Path | None,
) -> dict[str, Any]:
    if not project_path.exists():
        raise ValidationError(f"source project file does not exist: {project_path}")
    version_suffix = asset_version if asset_version.startswith("v") else f"v{asset_version}"
    package_id = f"project_{source}_{version_suffix}"
    generated_at = datetime.now(timezone.utc).isoformat()

    headers, source_rows = read_source(project_path)
    assets = build_assets(source_rows, headers, source)
    master_rows = assets["master_rows"]
    deferred_rows = assets["deferred_rows"]
    discard_rows = assets["discard_rows"]
    external_records = assets["external_records"]

    assert_unique(master_rows, "external_id")
    assert_unique(master_rows, "legacy_identity_key")

    project_dir = out_dir / "10_master" / "project"
    manifest_dir = out_dir / "manifest"
    master_path = project_dir / "project_master_v1.csv"
    master_xml_path = project_dir / "project_master_v1.xml"
    deferred_path = project_dir / "project_deferred_fields_v1.csv"
    discard_path = project_dir / "project_discard_summary_v1.csv"
    external_manifest_path = manifest_dir / "project_external_id_manifest_v1.json"
    validation_manifest_path = manifest_dir / "project_validation_manifest_v1.json"
    asset_manifest_path = manifest_dir / "project_asset_manifest_v1.json"

    write_csv(master_path, MASTER_FIELDS, master_rows)
    write_project_xml(master_xml_path, master_rows)
    write_csv(deferred_path, DEFERRED_FIELDS, deferred_rows)
    write_csv(discard_path, DISCARD_FIELDS, discard_rows)

    csv_hashes = {
        "project_master_csv_v1": sha256_file(master_path),
        "project_master_xml_v1": sha256_file(master_xml_path),
        "project_deferred_fields_csv_v1": sha256_file(deferred_path),
        "project_discard_summary_csv_v1": sha256_file(discard_path),
    }
    external_manifest = {
        "asset_manifest_version": "1.0",
        "asset_package_id": package_id,
        "lane_id": "project",
        "external_id_rule": {
            "pattern": "legacy_<lane>_<source>_<legacy_pk>",
            "source": source,
            "legacy_key_policy": "stable_legacy_pk",
        },
        "records": external_records,
        "summary": {
            "total": len(external_records) + assets["discarded_records"],
            "loadable": len(external_records),
            "discarded": assets["discarded_records"],
            "deferred": len(deferred_rows),
            "conflict_blocked": 0,
        },
    }
    write_json(external_manifest_path, external_manifest)

    hashes = {**csv_hashes, "project_external_id_manifest_v1": sha256_file(external_manifest_path)}
    validation_manifest = build_validation_manifest(
        package_id,
        hashes,
        assets["missing_optional_headers"],
        assets["missing_deferred_headers"],
    )
    write_json(validation_manifest_path, validation_manifest)
    hashes["project_validation_manifest_v1"] = sha256_file(validation_manifest_path)

    asset_manifest = {
        "asset_manifest_version": "1.0",
        "asset_package_id": package_id,
        "generated_at": generated_at,
        "source_snapshot": {
            "source_system": source,
            "source_files": [str(project_path)],
            "source_tables": ["project"],
            "extract_batch_id": f"project_asset_{version_suffix}",
        },
        "lane": {
            "lane_id": "project",
            "layer": "10_master",
            "business_priority": "core_business_body",
            "risk_class": "normal",
        },
        "target": {
            "model": "project.project",
            "identity_field": "legacy_project_id",
            "load_strategy": "upsert_by_external_id",
        },
        "assets": [
            {
                "asset_id": "project_master_csv_v1",
                "path": "10_master/project/project_master_v1.csv",
                "format": "csv",
                "record_count": len(master_rows),
                "sha256": hashes["project_master_csv_v1"],
                "required": True,
            },
            {
                "asset_id": "project_master_xml_v1",
                "path": "10_master/project/project_master_v1.xml",
                "format": "xml",
                "record_count": len(master_rows),
                "sha256": hashes["project_master_xml_v1"],
                "required": True,
            },
            {
                "asset_id": "project_deferred_fields_csv_v1",
                "path": "10_master/project/project_deferred_fields_v1.csv",
                "format": "csv",
                "record_count": len(deferred_rows),
                "sha256": hashes["project_deferred_fields_csv_v1"],
                "required": True,
            },
            {
                "asset_id": "project_discard_summary_csv_v1",
                "path": "10_master/project/project_discard_summary_v1.csv",
                "format": "csv",
                "record_count": len(discard_rows),
                "sha256": hashes["project_discard_summary_csv_v1"],
                "required": True,
            },
            {
                "asset_id": "project_external_id_manifest_v1",
                "path": "manifest/project_external_id_manifest_v1.json",
                "format": "json",
                "record_count": len(external_records),
                "sha256": hashes["project_external_id_manifest_v1"],
                "required": True,
            },
            {
                "asset_id": "project_validation_manifest_v1",
                "path": "manifest/project_validation_manifest_v1.json",
                "format": "json",
                "record_count": 1,
                "sha256": hashes["project_validation_manifest_v1"],
                "required": True,
            },
        ],
        "load_order": [
        "project_external_id_manifest_v1",
        "project_master_csv_v1",
        "project_master_xml_v1",
        "project_deferred_fields_csv_v1",
            "project_discard_summary_csv_v1",
            "project_validation_manifest_v1",
        ],
        "dependencies": [],
        "counts": {
            "raw_rows": assets["raw_rows"],
            "normalized_rows": len(master_rows),
            "loadable_records": len(master_rows),
            "discarded_records": assets["discarded_records"],
            "deferred_records": len(deferred_rows),
            "high_risk_excluded_records": 0,
        },
        "idempotency": {
            "mode": "external_id",
            "duplicate_policy": "update_existing_same_external_id",
            "conflict_policy": "block_package",
        },
        "validation_gates": validation_manifest["validation_gates"]["generate_time"],
        "db_writes": 0,
        "odoo_shell": False,
    }
    write_json(asset_manifest_path, asset_manifest)

    if baseline_out is not None:
        write_baseline_package(
            baseline_out,
            package_id,
            source,
            asset_version,
            master_xml_path,
            external_manifest,
            validation_manifest,
            asset_manifest["counts"],
        )

    if check:
        check_paths = [master_path, master_xml_path, deferred_path, discard_path, external_manifest_path, validation_manifest_path, asset_manifest_path]
        if baseline_out is not None:
            check_paths.extend(
                [
                    baseline_out / "10_master" / "project" / "project_master_v1.xml",
                    baseline_out / "manifest" / "project_asset_manifest_v1.json",
                    baseline_out / "manifest" / "project_external_id_manifest_v1.json",
                    baseline_out / "manifest" / "project_validation_manifest_v1.json",
                ]
            )
        for path in check_paths:
            if not path.exists() or path.stat().st_size == 0:
                raise ValidationError(f"generated asset missing or empty: {path}")
        assert_unique(master_rows, "external_id")
        assert_unique(master_rows, "legacy_identity_key")
        if len(master_rows) + assets["discarded_records"] != assets["raw_rows"]:
            raise ValidationError("manifest counts do not explain raw rows")

    return {
        "status": "PASS",
        "asset_package_id": package_id,
        "raw_rows": assets["raw_rows"],
        "loadable_records": len(master_rows),
        "discarded_records": assets["discarded_records"],
        "deferred_records": len(deferred_rows),
        "output": str(out_dir),
        "baseline_output": str(baseline_out) if baseline_out is not None else "",
        "db_writes": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate project migration asset package without DB writes.")
    parser.add_argument("--project", required=True, help="Path to legacy project CSV")
    parser.add_argument("--out", required=True, help="Output asset package directory")
    parser.add_argument("--source", default="sc", help="Legacy source identifier")
    parser.add_argument("--asset-version", default="v1", help="Asset package version, e.g. v1")
    parser.add_argument("--baseline-out", help="Repository baseline output directory for XML rebuild assets")
    parser.add_argument("--check", action="store_true", help="Run local no-DB validations")
    args = parser.parse_args()

    try:
        baseline_out = Path(args.baseline_out) if args.baseline_out else None
        result = generate(Path(args.project), Path(args.out), args.source, args.asset_version, args.check, baseline_out)
    except ValidationError as exc:
        print("PROJECT_ASSET_GENERATOR=" + json.dumps({"status": "FAIL", "error": str(exc)}, ensure_ascii=False, sort_keys=True))
        return 1

    print("PROJECT_ASSET_GENERATOR=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
