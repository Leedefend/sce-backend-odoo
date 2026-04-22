#!/usr/bin/env python3
"""Generate repository-trackable partner XML migration assets without DB access."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET


COMPANY_REQUIRED_COLUMNS = {"Id", "DWMC"}
SUPPLIER_REQUIRED_COLUMNS = {"ID", "f_SupplierName"}
TARGET_MODEL = "res.partner"
LANE = "partner"
LAYER = "10_master"
ASSET_PACKAGE_ID = "partner_sc_v1"


class PartnerAssetError(Exception):
    pass


def clean(value: object) -> str:
    text = "" if value is None else str(value)
    text = text.replace("\u3000", " ").strip()
    return re.sub(r"\s+", " ", text)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise PartnerAssetError(message)


def safe_token(value: str) -> str:
    token = re.sub(r"[^0-9A-Za-z_]+", "_", value.strip())
    token = re.sub(r"_+", "_", token).strip("_")
    return token or "missing"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    require(path.exists(), f"missing source csv: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), [dict(row) for row in reader]


def first_nonempty(*values: object) -> str:
    for value in values:
        text = clean(value)
        if text:
            return text
    return ""


def valid_tax(value: object) -> str:
    text = clean(value).upper()
    if not text or text in {"0", "1", "2", "3", "NULL", "NONE", "==请选择=="}:
        return ""
    return text if len(text) >= 8 else ""


def is_safe_enterprise_name(value: str) -> bool:
    text = clean(value)
    if len(text) < 4:
        return False
    if text.isdigit():
        return False
    if text in {"==请选择==", "请选择", "无", "测试"}:
        return False
    return True


def normalize_company(row: dict[str, str]) -> dict[str, Any]:
    return {
        "legacy_partner_id": clean(row.get("Id")),
        "legacy_partner_source": "cooperat_company",
        "legacy_partner_name": clean(row.get("DWMC")),
        "name": clean(row.get("DWMC")),
        "vat": first_nonempty(valid_tax(row.get("TYSHXYDM")), valid_tax(row.get("SH"))),
        "phone": clean(row.get("YWLXRHM")),
        "email": clean(row.get("YWLXRYX")).lower(),
        "legacy_credit_code": valid_tax(row.get("TYSHXYDM")),
        "legacy_tax_no": valid_tax(row.get("SH")),
        "legacy_source_evidence": "tmp/raw/partner/company.csv:T_Base_CooperatCompany",
        "source_roles": {"company"},
    }


def normalize_supplier(row: dict[str, str]) -> dict[str, Any]:
    return {
        "legacy_partner_id": clean(row.get("ID")),
        "legacy_partner_source": "supplier",
        "legacy_partner_name": clean(row.get("f_SupplierName")),
        "name": clean(row.get("f_SupplierName")),
        "vat": first_nonempty(
            valid_tax(row.get("SH")),
            valid_tax(row.get("SHXYDM")),
            valid_tax(row.get("NSRSBH")),
            valid_tax(row.get("TISHXYDM")),
        ),
        "phone": clean(row.get("f_Phone")),
        "email": clean(row.get("f_Email")).lower(),
        "legacy_credit_code": first_nonempty(valid_tax(row.get("SHXYDM")), valid_tax(row.get("TISHXYDM"))),
        "legacy_tax_no": first_nonempty(valid_tax(row.get("SH")), valid_tax(row.get("NSRSBH"))),
        "legacy_source_evidence": "tmp/raw/partner/supplier.csv:T_Base_SupplierInfo",
        "source_roles": {"supplier"},
    }


def merge_records(rows: list[dict[str, Any]]) -> tuple[dict[str, Any] | None, str]:
    names = sorted({clean(row.get("name")) for row in rows if clean(row.get("name"))})
    if not names:
        return None, "missing_partner_name"
    safe_names = [name for name in names if is_safe_enterprise_name(name)]
    if not safe_names:
        return None, "unsafe_partner_name"
    source_roles = set()
    for row in rows:
        source_roles.update(row.get("source_roles") or set())
    if source_roles == {"company", "supplier"}:
        source = "company_supplier"
    elif source_roles == {"supplier"}:
        source = "supplier"
    else:
        source = "cooperat_company"
    first = rows[0]
    merged = {
        "legacy_partner_id": clean(first.get("legacy_partner_id")),
        "legacy_partner_source": source,
        "legacy_partner_name": safe_names[0],
        "name": safe_names[0],
        "vat": first_nonempty(*(row.get("vat") for row in rows)),
        "phone": first_nonempty(*(row.get("phone") for row in rows)),
        "email": first_nonempty(*(row.get("email") for row in rows)),
        "legacy_credit_code": first_nonempty(*(row.get("legacy_credit_code") for row in rows)),
        "legacy_tax_no": first_nonempty(*(row.get("legacy_tax_no") for row in rows)),
        "legacy_source_evidence": ";".join(sorted({clean(row.get("legacy_source_evidence")) for row in rows})),
        "source_row_count": len(rows),
        "name_variant_count": len(names),
    }
    return merged, ""


def build_records(company_rows: list[dict[str, str]], supplier_rows: list[dict[str, str]]) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    raw_records = [normalize_company(row) for row in company_rows] + [normalize_supplier(row) for row in supplier_rows]
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    discard_rows: list[dict[str, str]] = []
    for record in raw_records:
        legacy_id = clean(record.get("legacy_partner_id"))
        if not legacy_id:
            discard_rows.append({"discard_reason": "missing_legacy_partner_id", "source": clean(record.get("legacy_partner_source")), "name": clean(record.get("name"))})
            continue
        grouped[legacy_id].append(record)

    output: list[dict[str, Any]] = []
    seen_external_ids: set[str] = set()
    for legacy_id, rows in sorted(grouped.items()):
        merged, discard_reason = merge_records(rows)
        if not merged:
            discard_rows.append({"discard_reason": discard_reason, "legacy_partner_id": legacy_id, "source": "mixed", "name": ""})
            continue
        external_id = f"legacy_partner_sc_{safe_token(legacy_id)}"
        if external_id in seen_external_ids:
            raise PartnerAssetError(f"duplicate external id: {external_id}")
        seen_external_ids.add(external_id)
        merged["external_id"] = external_id
        merged["legacy_identity_key"] = f"partner:sc:{legacy_id}"
        output.append(merged)
    return output, discard_rows


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def write_xml(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    root = ET.Element("odoo")
    data = ET.SubElement(root, "data", {"noupdate": "1"})
    xml_fields = [
        "name",
        "company_type",
        "is_company",
        "vat",
        "phone",
        "email",
        "legacy_partner_id",
        "legacy_partner_source",
        "legacy_partner_name",
        "legacy_credit_code",
        "legacy_tax_no",
        "legacy_source_evidence",
    ]
    for record in records:
        element = ET.SubElement(data, "record", {"id": record["external_id"], "model": TARGET_MODEL})
        payload = {
            "name": clean(record.get("name")),
            "company_type": "company",
            "is_company": "1",
            "vat": clean(record.get("vat")),
            "phone": clean(record.get("phone")),
            "email": clean(record.get("email")),
            "legacy_partner_id": clean(record.get("legacy_partner_id")),
            "legacy_partner_source": clean(record.get("legacy_partner_source")),
            "legacy_partner_name": clean(record.get("legacy_partner_name")),
            "legacy_credit_code": clean(record.get("legacy_credit_code")),
            "legacy_tax_no": clean(record.get("legacy_tax_no")),
            "legacy_source_evidence": clean(record.get("legacy_source_evidence")),
        }
        for field_name in xml_fields:
            field = ET.SubElement(element, "field", {"name": field_name})
            field.text = payload[field_name]
    ET.indent(root, space="  ")
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)


def manifest_payloads(
    asset_root: Path,
    records: list[dict[str, Any]],
    discard_rows: list[dict[str, str]],
    source: str,
    asset_version: str,
    raw_source_rows: int,
) -> dict[str, Any]:
    asset_manifest_path = asset_root / "manifest" / "partner_asset_manifest_v1.json"
    external_manifest_path = asset_root / "manifest" / "partner_external_id_manifest_v1.json"
    validation_manifest_path = asset_root / "manifest" / "partner_validation_manifest_v1.json"
    xml_path = asset_root / LAYER / LANE / "partner_master_v1.xml"
    csv_path = asset_root / LAYER / LANE / "partner_master_v1.csv"
    discard_path = asset_root / LAYER / LANE / "partner_discard_summary_v1.csv"
    generated_at = datetime.now(timezone.utc).isoformat()
    assets = [
        {
            "asset_id": "partner_master_xml_v1",
            "path": f"{LAYER}/{LANE}/partner_master_v1.xml",
            "format": "xml",
            "record_count": len(records),
            "required": True,
            "sha256": sha256_file(xml_path),
        },
        {
            "asset_id": "partner_external_id_manifest_v1",
            "path": "manifest/partner_external_id_manifest_v1.json",
            "format": "json",
            "record_count": len(records),
            "required": True,
            "sha256": sha256_file(external_manifest_path),
        },
        {
            "asset_id": "partner_validation_manifest_v1",
            "path": "manifest/partner_validation_manifest_v1.json",
            "format": "json",
            "record_count": 1,
            "required": True,
            "sha256": sha256_file(validation_manifest_path),
        },
    ]
    return {
        "asset_manifest": {
            "asset_manifest_version": "1.0",
            "asset_package_id": ASSET_PACKAGE_ID,
            "baseline_package": True,
            "generated_at": generated_at,
            "db_writes": 0,
            "odoo_shell": False,
            "lane": {
                "lane_id": LANE,
                "layer": LAYER,
                "business_priority": "core_master",
                "risk_class": "normal",
            },
            "target": {
                "model": TARGET_MODEL,
                "identity_field": "external_id",
                "load_strategy": "odoo_xml_external_id",
            },
            "source_snapshot": {
                "source_system": source,
                "extract_batch_id": f"partner_xml_baseline_{asset_version}",
                "source_tables": ["T_Base_CooperatCompany", "T_Base_SupplierInfo"],
            },
            "counts": {
                "raw_rows": raw_source_rows,
                "loadable_records": len(records),
                "discarded_records": len(discard_rows),
                "deferred_records": 0,
                "normalized_rows": len(records),
                "high_risk_excluded_records": 0,
            },
            "dependencies": [],
            "load_order": ["partner_master_xml_v1", "partner_external_id_manifest_v1", "partner_validation_manifest_v1"],
            "idempotency": {
                "mode": "odoo_xml_external_id",
                "duplicate_policy": "update_existing_same_external_id",
                "conflict_policy": "block_package",
            },
            "validation_gates": [
                "source_partner_files_exist",
                "required_source_headers_present",
                "legacy_partner_id_non_empty",
                "partner_name_safe",
                "external_id_unique",
                "garbage_rows_discarded",
                "no_partner_rank_fields",
                "no_high_risk_lane_leakage",
            ],
            "assets": assets,
        },
        "paths": {
            "asset_manifest": asset_manifest_path,
            "external_manifest": external_manifest_path,
            "validation_manifest": validation_manifest_path,
            "xml": xml_path,
            "csv": csv_path,
            "discard": discard_path,
        },
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_package(
    asset_root: Path,
    records: list[dict[str, Any]],
    discard_rows: list[dict[str, str]],
    source: str,
    asset_version: str,
    raw_source_rows: int,
    write_sidecars: bool = True,
) -> dict[str, Any]:
    fieldnames = [
        "external_id",
        "legacy_identity_key",
        "legacy_partner_id",
        "legacy_partner_source",
        "name",
        "vat",
        "phone",
        "email",
        "legacy_partner_name",
        "legacy_credit_code",
        "legacy_tax_no",
        "legacy_source_evidence",
        "source_row_count",
        "name_variant_count",
    ]
    xml_path = asset_root / LAYER / LANE / "partner_master_v1.xml"
    csv_path = asset_root / LAYER / LANE / "partner_master_v1.csv"
    discard_path = asset_root / LAYER / LANE / "partner_discard_summary_v1.csv"
    external_path = asset_root / "manifest" / "partner_external_id_manifest_v1.json"
    validation_path = asset_root / "manifest" / "partner_validation_manifest_v1.json"
    if write_sidecars:
        write_csv(csv_path, fieldnames, records)
        write_csv(discard_path, ["discard_reason", "legacy_partner_id", "source", "name"], discard_rows)
    write_xml(xml_path, records)
    external_manifest = {
        "asset_manifest_version": "1.0",
        "asset_package_id": ASSET_PACKAGE_ID,
        "summary": {
            "loadable": len(records),
            "discarded": len(discard_rows),
        },
        "records": [
            {
                "external_id": record["external_id"],
                "legacy_identity_key": record["legacy_identity_key"],
                "legacy_partner_id": record["legacy_partner_id"],
                "legacy_partner_source": record["legacy_partner_source"],
                "target_model": TARGET_MODEL,
                "target_lookup": {
                    "field": "xml_id",
                    "value": record["external_id"],
                },
                "status": "loadable",
            }
            for record in records
        ],
    }
    write_json(external_path, external_manifest)
    validation_manifest = {
        "asset_manifest_version": "1.0",
        "asset_package_id": ASSET_PACKAGE_ID,
        "baseline_package": True,
        "failure_policy": {
            "missing_source_file": "block_package",
            "missing_required_header": "block_package",
            "missing_legacy_partner_id": "discard_record",
            "unsafe_partner_name": "discard_record",
            "external_id_duplicate": "block_package",
            "partner_rank_field_requested": "block_package",
        },
        "validation_gates": {
            "generate_time": [
                "source_partner_files_exist",
                "required_source_headers_present",
                "legacy_partner_id_non_empty",
                "partner_name_safe",
                "external_id_unique",
                "garbage_rows_discarded",
                "no_partner_rank_fields",
                "no_high_risk_lane_leakage",
            ],
            "preload": ["asset_files_exist", "asset_hashes_match", "target_model_available"],
            "postload": ["target_count_matches_manifest", "external_id_resolves", "rerun_is_idempotent"],
        },
    }
    write_json(validation_path, validation_manifest)
    payloads = manifest_payloads(asset_root, records, discard_rows, source, asset_version, raw_source_rows)
    write_json(payloads["paths"]["asset_manifest"], payloads["asset_manifest"])
    return payloads["asset_manifest"]


def validate_records(records: list[dict[str, Any]]) -> None:
    external_ids = [record["external_id"] for record in records]
    require(len(external_ids) == len(set(external_ids)), "duplicate external ids")
    for record in records:
        require(record["external_id"].startswith("legacy_partner_sc_"), f"invalid external id: {record['external_id']}")
        require(clean(record.get("legacy_partner_id")), f"missing legacy partner id: {record}")
        require(is_safe_enterprise_name(clean(record.get("name"))), f"unsafe partner name: {record}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate partner XML migration asset package without DB access.")
    parser.add_argument("--company", default="tmp/raw/partner/company.csv", help="Legacy company CSV")
    parser.add_argument("--supplier", default="tmp/raw/partner/supplier.csv", help="Legacy supplier CSV")
    parser.add_argument("--out", default=".runtime_artifacts/migration_assets/partner_sc_v1", help="Runtime output root")
    parser.add_argument("--baseline-out", help="Optional repository baseline asset root")
    parser.add_argument("--source", default="sc", help="Source system code")
    parser.add_argument("--asset-version", default="v1", help="Asset version")
    parser.add_argument("--check", action="store_true", help="Fail non-zero on validation errors")
    args = parser.parse_args()

    try:
        company_columns, company_rows = read_csv(Path(args.company))
        supplier_columns, supplier_rows = read_csv(Path(args.supplier))
        missing_company = sorted(COMPANY_REQUIRED_COLUMNS - set(company_columns))
        missing_supplier = sorted(SUPPLIER_REQUIRED_COLUMNS - set(supplier_columns))
        require(not missing_company, f"missing company columns: {missing_company}")
        require(not missing_supplier, f"missing supplier columns: {missing_supplier}")
        records, discard_rows = build_records(company_rows, supplier_rows)
        validate_records(records)
        raw_source_rows = len(company_rows) + len(supplier_rows)
        runtime_manifest = write_package(
            Path(args.out),
            records,
            discard_rows,
            args.source,
            args.asset_version,
            raw_source_rows,
            write_sidecars=True,
        )
        baseline_manifest = None
        if args.baseline_out:
            baseline_manifest = write_package(
                Path(args.baseline_out),
                records,
                discard_rows,
                args.source,
                args.asset_version,
                raw_source_rows,
                write_sidecars=False,
            )
    except (PartnerAssetError, OSError, csv.Error) as exc:
        payload = {"status": "FAIL", "error": str(exc), "db_writes": 0, "odoo_shell": False}
        print("PARTNER_ASSET_GENERATOR=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 1 if args.check else 0

    source_counts = Counter(record["legacy_partner_source"] for record in records)
    payload = {
        "status": "PASS",
        "asset_package_id": ASSET_PACKAGE_ID,
        "runtime_out": args.out,
        "baseline_out": args.baseline_out or "",
        "raw_rows": len(company_rows) + len(supplier_rows),
        "loadable_records": len(records),
        "discarded_records": len(discard_rows),
        "source_counts": dict(sorted(source_counts.items())),
        "runtime_asset_manifest_hash": sha256_file(Path(args.out) / "manifest" / "partner_asset_manifest_v1.json"),
        "baseline_asset_manifest_hash": sha256_file(Path(args.baseline_out) / "manifest" / "partner_asset_manifest_v1.json") if args.baseline_out else "",
        "db_writes": 0,
        "odoo_shell": False,
    }
    print("PARTNER_ASSET_GENERATOR=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
