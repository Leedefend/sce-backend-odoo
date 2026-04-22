#!/usr/bin/env python3
"""Generate XML assets for legacy invoice and tax facts."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from collections import Counter
from decimal import Decimal
from pathlib import Path
from typing import Any

from legacy_invoice_tax_fact_screen import clean, parse_amount, parse_sql_rows, run_sql


RUNTIME_ROOT = Path(".runtime_artifacts/migration_assets/legacy_invoice_tax_sc_v1")
XML_REL_PATH = Path("30_relation/legacy_invoice_tax/legacy_invoice_tax_v1.xml")
EXTERNAL_REL_PATH = Path("manifest/legacy_invoice_tax_external_id_manifest_v1.json")
VALIDATION_REL_PATH = Path("manifest/legacy_invoice_tax_validation_manifest_v1.json")
ASSET_MANIFEST_REL_PATH = Path("manifest/legacy_invoice_tax_asset_manifest_v1.json")
CATALOG_REL_PATH = Path("manifest/migration_asset_catalog_v1.json")
ASSET_PACKAGE_ID = "legacy_invoice_tax_sc_v1"
GENERATED_AT = "2026-04-15T18:10:00+00:00"
EXPECTED_RAW_ROWS = 21323
EXPECTED_LOADABLE_ROWS = 5920


class InvoiceTaxAssetError(Exception):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise InvoiceTaxAssetError(message)


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


def safe_external_suffix(source_table: str, legacy_id: str) -> str:
    suffix = re.sub(r"[^0-9A-Za-z_]+", "_", f"{source_table}_{legacy_id}").strip("_").lower()
    require(bool(suffix), "cannot build external id from blank invoice/tax key")
    return suffix


def normalize_date(value: str) -> str:
    text = clean(value)
    return text[:10] if text else ""


def decimal_text(value: Decimal) -> str:
    return format(value.quantize(Decimal("0.01")), "f")


def load_project_map(asset_root: Path) -> dict[str, str]:
    manifest = load_json(asset_root / "manifest/project_external_id_manifest_v1.json")
    refs: dict[str, str] = {}
    for row in manifest.get("records", []):
        if row.get("status") != "loadable":
            continue
        external_id = clean(row.get("external_id"))
        for value in (clean(row.get("legacy_key")), clean((row.get("target_lookup") or {}).get("value"))):
            if value and external_id:
                refs[value] = external_id
    require(refs, "project external id map is empty")
    return refs


def load_partner_map(asset_root: Path) -> dict[str, str]:
    manifest = load_json(asset_root / "manifest/partner_external_id_manifest_v1.json")
    return {
        clean(row.get("legacy_partner_id")): clean(row.get("external_id"))
        for row in manifest.get("records", [])
        if row.get("status") == "loadable" and clean(row.get("legacy_partner_id")) and clean(row.get("external_id"))
    }


def classify_row(row: dict[str, str], project_map: dict[str, str]) -> tuple[str, list[str]]:
    reasons: list[str] = []
    if not clean(row.get("legacy_id")):
        reasons.append("missing_legacy_id")
    if clean(row.get("deleted")) in {"1", "true", "True"}:
        reasons.append("deleted")
    project_id = clean(row.get("project_id"))
    if not project_id:
        reasons.append("missing_project_id")
    elif project_id not in project_map:
        reasons.append("project_not_assetized")
    if parse_amount(row.get("amount", "")) <= 0 and parse_amount(row.get("tax_amount", "")) <= 0:
        reasons.append("amount_and_tax_not_positive_or_missing")
    if not clean(row.get("partner_name")) and not clean(row.get("partner_tax_no")):
        reasons.append("missing_counterparty_evidence")
    return ("loadable" if not reasons else "blocked", reasons)


def add_text_field(record: ET.Element, name: str, value: object, *, required: bool = False) -> None:
    text = clean(value)
    if not text and not required:
        return
    field = ET.SubElement(record, "field", {"name": name})
    field.text = text


def add_ref_field(record: ET.Element, name: str, ref: str, *, required: bool = False) -> None:
    text = clean(ref)
    if not text and not required:
        return
    ET.SubElement(record, "field", {"name": name, "ref": text})


def write_xml(path: Path, records: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    root = ET.Element("odoo")
    data = ET.SubElement(root, "data", {"noupdate": "1"})
    for row in records:
        record = ET.SubElement(data, "record", {"id": row["external_id"], "model": "sc.legacy.invoice.tax.fact"})
        for field in (
            "legacy_source_table", "legacy_record_id", "legacy_pid", "source_family", "direction",
            "document_no", "document_date", "legacy_state", "invoice_type",
        ):
            add_text_field(record, field, row[field], required=field in {"legacy_source_table", "legacy_record_id", "source_family", "direction"})
        add_ref_field(record, "project_id", row["project_external_id"], required=True)
        add_text_field(record, "legacy_project_id", row["legacy_project_id"], required=True)
        add_text_field(record, "legacy_project_name", row["legacy_project_name"])
        add_ref_field(record, "partner_id", row["partner_external_id"])
        add_text_field(record, "legacy_partner_id", row["legacy_partner_id"])
        add_text_field(record, "legacy_partner_name", row["legacy_partner_name"])
        add_text_field(record, "legacy_partner_tax_no", row["legacy_partner_tax_no"])
        add_text_field(record, "source_amount", row["source_amount"])
        add_text_field(record, "source_tax_amount", row["source_tax_amount"])
        add_text_field(record, "source_amount_field", row["source_amount_field"], required=True)
        add_text_field(record, "note", row["note"])
        add_text_field(record, "import_batch", "legacy_invoice_tax_asset_v1", required=True)
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
        "business_priority": "legacy_invoice_tax_fact",
        "dependencies": ["project_sc_v1", "partner_sc_v1"],
        "layer": "30_relation",
        "load_phase": 30,
        "package_type": "legacy_invoice_tax_fact",
        "required": True,
        "risk_class": "historical_invoice_tax_fact",
        "target_model": "sc.legacy.invoice.tax.fact",
        "verification_command": "python3 scripts/migration/legacy_invoice_tax_asset_verify.py --asset-root migration_assets --lane legacy_invoice_tax --check",
    }
    catalog["package_order"] = [item for item in catalog.get("package_order", []) if item != ASSET_PACKAGE_ID]
    catalog["package_order"].append(ASSET_PACKAGE_ID)
    catalog["packages"] = [item for item in catalog.get("packages", []) if item.get("asset_package_id") != ASSET_PACKAGE_ID]
    catalog["packages"].append(package)
    catalog["generated_at"] = GENERATED_AT
    write_json(catalog_path, catalog)


def build_records(asset_root: Path) -> tuple[list[dict[str, str]], dict[str, Any]]:
    source_rows = parse_sql_rows(run_sql())
    require(len(source_rows) == EXPECTED_RAW_ROWS, f"raw row count drifted: {len(source_rows)} != {EXPECTED_RAW_ROWS}")
    project_map = load_project_map(asset_root)
    partner_map = load_partner_map(asset_root)
    records: list[dict[str, str]] = []
    reasons: Counter[str] = Counter()
    tables: Counter[str] = Counter()
    families: Counter[str] = Counter()
    directions: Counter[str] = Counter()
    partner_counts: Counter[str] = Counter()
    ids: Counter[str] = Counter()
    for row in source_rows:
        route, blocked_reasons = classify_row(row, project_map)
        table = clean(row.get("source_table"))
        tables[table] += 1
        for reason in blocked_reasons:
            reasons[reason] += 1
        if route != "loadable":
            continue
        legacy_id = clean(row.get("legacy_id"))
        project_id = clean(row.get("project_id"))
        partner_id = clean(row.get("partner_id"))
        external_id = "legacy_invoice_tax_sc_%s" % safe_external_suffix(table, legacy_id)
        ids[external_id] += 1
        partner_external_id = partner_map.get(partner_id, "")
        if partner_external_id:
            partner_counts["partner_ref"] += 1
        elif clean(row.get("partner_tax_no")):
            partner_counts["partner_tax_no_text"] += 1
        elif clean(row.get("partner_name")):
            partner_counts["partner_name_text"] += 1
        family = clean(row.get("family"))
        direction = clean(row.get("direction"))
        families[family] += 1
        directions[direction] += 1
        records.append({
            "external_id": external_id,
            "legacy_source_table": table,
            "legacy_record_id": legacy_id,
            "legacy_pid": clean(row.get("pid")),
            "source_family": family,
            "direction": direction,
            "document_no": clean(row.get("document_no")),
            "document_date": normalize_date(row.get("document_date", "")),
            "legacy_state": clean(row.get("state")),
            "invoice_type": clean(row.get("invoice_type")),
            "project_external_id": project_map[project_id],
            "legacy_project_id": project_id,
            "legacy_project_name": clean(row.get("project_name")),
            "partner_external_id": partner_external_id,
            "legacy_partner_id": partner_id,
            "legacy_partner_name": clean(row.get("partner_name")),
            "legacy_partner_tax_no": clean(row.get("partner_tax_no")),
            "source_amount": decimal_text(parse_amount(row.get("amount", ""))),
            "source_tax_amount": decimal_text(parse_amount(row.get("tax_amount", ""))),
            "source_amount_field": clean(row.get("amount_field")),
            "note": clean(row.get("note")),
        })
    require(len(records) == EXPECTED_LOADABLE_ROWS, f"loadable row count drifted: {len(records)} != {EXPECTED_LOADABLE_ROWS}")
    require(not [key for key, count in ids.items() if count > 1], "duplicate invoice/tax external ids")
    return records, {
        "raw_rows": len(source_rows),
        "loadable_records": len(records),
        "blocked_records": len(source_rows) - len(records),
        "blocked_reason_counts": dict(reasons.most_common()),
        "source_table_counts": dict(tables.most_common()),
        "family_counts": dict(families.most_common()),
        "direction_counts": dict(directions.most_common()),
        "partner_counts": dict(partner_counts.most_common()),
    }


def generate(asset_root: Path, runtime_root: Path) -> dict[str, Any]:
    records, summary = build_records(asset_root)
    xml_path = asset_root / XML_REL_PATH
    external_path = asset_root / EXTERNAL_REL_PATH
    validation_path = asset_root / VALIDATION_REL_PATH
    asset_manifest_path = asset_root / ASSET_MANIFEST_REL_PATH
    write_xml(xml_path, records)
    write_json(external_path, {
        "asset_manifest_version": "1.0",
        "asset_package_id": ASSET_PACKAGE_ID,
        "external_id_rule": "legacy_invoice_tax_sc_<source_table>_<legacy_id>",
        "lane_id": "legacy_invoice_tax",
        "records": [{"external_id": row["external_id"], "legacy_source_table": row["legacy_source_table"], "legacy_record_id": row["legacy_record_id"], "project_external_id": row["project_external_id"], "status": "loadable"} for row in records],
        "summary": {"loadable": len(records), "blocked": summary["blocked_records"], "raw_rows": summary["raw_rows"]},
    })
    write_json(validation_path, {
        "asset_manifest_version": "1.0",
        "asset_package_id": ASSET_PACKAGE_ID,
        "business_boundary": {"legacy_invoice_tax_fact": "included", "account_move": "excluded", "tax_ledger": "excluded", "payment_state": "excluded", "settlement_state": "excluded", "approval_runtime": "excluded"},
        "counts": summary,
        "validation_gates": {"generate_time": ["legacy_source_key_unique", "project_external_id_required_and_resolves", "counterparty_evidence_required", "source_amount_or_tax_positive", "no_account_move_records_generated", "no_tax_ledger_records_generated", "no_payment_or_settlement_records_generated", "no_runtime_approval_records_generated", "no_database_integer_ids_required"]},
    })
    asset_manifest = {
        "asset_manifest_version": "1.0",
        "asset_package_id": ASSET_PACKAGE_ID,
        "assets": [{"path": str(XML_REL_PATH), "sha256": sha256_file(xml_path), "type": "xml"}, {"path": str(EXTERNAL_REL_PATH), "sha256": sha256_file(external_path), "type": "external_id_manifest"}, {"path": str(VALIDATION_REL_PATH), "sha256": sha256_file(validation_path), "type": "validation_manifest"}],
        "baseline_package": True,
        "counts": summary,
        "db_writes": 0,
        "dependencies": ["project_sc_v1", "partner_sc_v1"],
        "generated_at": GENERATED_AT,
        "lane": {"lane_id": "legacy_invoice_tax", "layer": "30_relation", "load_phase": 30},
        "odoo_shell": False,
        "target": {"model": "sc.legacy.invoice.tax.fact", "source_tables": sorted(summary["source_table_counts"])},
    }
    write_json(asset_manifest_path, asset_manifest)
    update_catalog(asset_root, sha256_file(asset_manifest_path))
    payload = {"status": "PASS", "asset_package_id": ASSET_PACKAGE_ID, "xml_path": str(xml_path), "asset_manifest_path": str(asset_manifest_path), "counts": summary, "db_writes": 0, "odoo_shell": False}
    write_json(runtime_root / "legacy_invoice_tax_asset_generation_v1.json", payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate legacy invoice/tax XML assets.")
    parser.add_argument("--asset-root", default="migration_assets")
    parser.add_argument("--runtime-root", default=str(RUNTIME_ROOT))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        result = generate(Path(args.asset_root), Path(args.runtime_root))
    except (InvoiceTaxAssetError, json.JSONDecodeError, ET.ParseError) as exc:
        print("LEGACY_INVOICE_TAX_ASSET_GENERATE=" + json.dumps({"status": "FAIL", "error": str(exc), "db_writes": 0, "odoo_shell": False}, ensure_ascii=False, sort_keys=True))
        return 1 if args.check else 0
    print("LEGACY_INVOICE_TAX_ASSET_GENERATE=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
