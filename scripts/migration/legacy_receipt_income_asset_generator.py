#!/usr/bin/env python3
"""Generate XML assets for legacy receipt and income residual facts."""

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

from legacy_receipt_income_residual_screen import clean, classify_row, load_existing_receipts, load_partner_refs, load_project_refs, parse_amount, parse_sql_rows, run_sql


RUNTIME_ROOT = Path(".runtime_artifacts/migration_assets/legacy_receipt_income_sc_v1")
XML_REL_PATH = Path("30_relation/legacy_receipt_income/legacy_receipt_income_v1.xml")
EXTERNAL_REL_PATH = Path("manifest/legacy_receipt_income_external_id_manifest_v1.json")
VALIDATION_REL_PATH = Path("manifest/legacy_receipt_income_validation_manifest_v1.json")
ASSET_MANIFEST_REL_PATH = Path("manifest/legacy_receipt_income_asset_manifest_v1.json")
CATALOG_REL_PATH = Path("manifest/migration_asset_catalog_v1.json")
ASSET_PACKAGE_ID = "legacy_receipt_income_sc_v1"
GENERATED_AT = "2026-04-15T18:45:00+00:00"
EXPECTED_RAW_ROWS = 14769
EXPECTED_LOADABLE_ROWS = 7220


class ReceiptIncomeAssetError(Exception):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ReceiptIncomeAssetError(message)


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


def project_map(asset_root: Path) -> dict[str, str]:
    manifest = load_json(asset_root / "manifest/project_external_id_manifest_v1.json")
    result: dict[str, str] = {}
    for row in manifest.get("records", []):
        if row.get("status") == "loadable":
            external_id = clean(row.get("external_id"))
            for value in (clean(row.get("legacy_key")), clean((row.get("target_lookup") or {}).get("value"))):
                if value and external_id:
                    result[value] = external_id
    require(result, "project map is empty")
    return result


def partner_map(asset_root: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for rel_path in ("manifest/partner_external_id_manifest_v1.json", "manifest/receipt_counterparty_partner_external_id_manifest_v1.json"):
        path = asset_root / rel_path
        if not path.exists():
            continue
        manifest = load_json(path)
        for row in manifest.get("records", []):
            if row.get("status") == "loadable":
                legacy_id = clean(row.get("legacy_partner_id"))
                external_id = clean(row.get("external_id"))
                if legacy_id and external_id and legacy_id not in result:
                    result[legacy_id] = external_id
    return result


def safe_suffix(source_table: str, legacy_id: str) -> str:
    suffix = re.sub(r"[^0-9A-Za-z_]+", "_", f"{source_table}_{legacy_id}").strip("_").lower()
    require(bool(suffix), "cannot build external id")
    return suffix


def date_text(value: str) -> str:
    text = clean(value)
    return text[:10] if text else ""


def money(value: Decimal) -> str:
    return format(value.quantize(Decimal("0.01")), "f")


def add_text(record: ET.Element, name: str, value: object, required: bool = False) -> None:
    text = clean(value)
    if not text and not required:
        return
    field = ET.SubElement(record, "field", {"name": name})
    field.text = text


def add_ref(record: ET.Element, name: str, ref: str, required: bool = False) -> None:
    text = clean(ref)
    if not text and not required:
        return
    ET.SubElement(record, "field", {"name": name, "ref": text})


def write_xml(path: Path, records: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    root = ET.Element("odoo")
    data = ET.SubElement(root, "data", {"noupdate": "1"})
    for row in records:
        record = ET.SubElement(data, "record", {"id": row["external_id"], "model": "sc.legacy.receipt.income.fact"})
        for field in ("legacy_source_table", "legacy_record_id", "legacy_pid", "source_family", "direction", "document_no", "document_date", "legacy_state", "income_category"):
            add_text(record, field, row[field], field in {"legacy_source_table", "legacy_record_id", "source_family", "direction"})
        add_ref(record, "project_id", row["project_external_id"], True)
        add_text(record, "legacy_project_id", row["legacy_project_id"], True)
        add_text(record, "legacy_project_name", row["legacy_project_name"])
        add_ref(record, "partner_id", row["partner_external_id"])
        add_text(record, "legacy_partner_id", row["legacy_partner_id"])
        add_text(record, "legacy_partner_name", row["legacy_partner_name"])
        add_text(record, "source_amount", row["source_amount"], True)
        add_text(record, "note", row["note"])
        add_text(record, "import_batch", "legacy_receipt_income_asset_v1", True)
    ET.indent(root, space="  ")
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)


def update_catalog(asset_root: Path, manifest_hash: str) -> None:
    path = asset_root / CATALOG_REL_PATH
    catalog = load_json(path)
    package = {
        "asset_manifest_path": str(ASSET_MANIFEST_REL_PATH),
        "asset_manifest_sha256": manifest_hash,
        "asset_package_id": ASSET_PACKAGE_ID,
        "baseline_package": True,
        "business_priority": "legacy_receipt_income_fact",
        "dependencies": ["project_sc_v1", "partner_sc_v1"],
        "layer": "30_relation",
        "load_phase": 30,
        "package_type": "legacy_receipt_income_fact",
        "required": True,
        "risk_class": "historical_income_fact",
        "target_model": "sc.legacy.receipt.income.fact",
        "verification_command": "python3 scripts/migration/legacy_receipt_income_asset_verify.py --asset-root migration_assets --lane legacy_receipt_income --check",
    }
    catalog["package_order"] = [item for item in catalog.get("package_order", []) if item != ASSET_PACKAGE_ID]
    catalog["package_order"].append(ASSET_PACKAGE_ID)
    catalog["packages"] = [item for item in catalog.get("packages", []) if item.get("asset_package_id") != ASSET_PACKAGE_ID]
    catalog["packages"].append(package)
    catalog["generated_at"] = GENERATED_AT
    write_json(path, catalog)


def build_records(asset_root: Path) -> tuple[list[dict[str, str]], dict[str, Any]]:
    rows = parse_sql_rows(run_sql())
    require(len(rows) == EXPECTED_RAW_ROWS, f"raw row count drifted: {len(rows)} != {EXPECTED_RAW_ROWS}")
    pmap = project_map(asset_root)
    pref = load_project_refs(asset_root)
    existing = load_existing_receipts(asset_root)
    partner_refs = load_partner_refs(asset_root)
    partmap = partner_map(asset_root)
    records: list[dict[str, str]] = []
    route_counts: Counter[str] = Counter()
    reasons: Counter[str] = Counter()
    tables: Counter[str] = Counter()
    families: Counter[str] = Counter()
    partner_counts: Counter[str] = Counter()
    ids: Counter[str] = Counter()
    for row in rows:
        route, blocked = classify_row(row, pref, existing)
        route_counts[route] += 1
        table = clean(row.get("source_table"))
        tables[table] += 1
        for reason in blocked:
            reasons[reason] += 1
        if route != "residual_loadable_candidate":
            continue
        legacy_id = clean(row.get("legacy_id"))
        project_id = clean(row.get("project_id"))
        partner_id = clean(row.get("partner_id"))
        external_id = "legacy_receipt_income_sc_%s" % safe_suffix(table, legacy_id)
        ids[external_id] += 1
        partner_external_id = partmap.get(partner_id, "")
        if partner_external_id:
            partner_counts["partner_ref"] += 1
        elif partner_id:
            partner_counts["partner_text_id"] += 1
        elif clean(row.get("partner_name")):
            partner_counts["partner_name_text"] += 1
        else:
            partner_counts["partner_missing"] += 1
        family = clean(row.get("family"))
        families[family] += 1
        records.append({
            "external_id": external_id,
            "legacy_source_table": table,
            "legacy_record_id": legacy_id,
            "legacy_pid": clean(row.get("pid")),
            "source_family": family,
            "direction": clean(row.get("direction")) or "inflow",
            "document_no": clean(row.get("document_no")),
            "document_date": date_text(row.get("document_date", "")),
            "legacy_state": clean(row.get("state")),
            "income_category": clean(row.get("income_category")),
            "project_external_id": pmap[project_id],
            "legacy_project_id": project_id,
            "legacy_project_name": clean(row.get("project_name")),
            "partner_external_id": partner_external_id,
            "legacy_partner_id": partner_id,
            "legacy_partner_name": clean(row.get("partner_name")),
            "source_amount": money(parse_amount(row.get("amount", ""))),
            "note": clean(row.get("note")),
        })
    require(len(records) == EXPECTED_LOADABLE_ROWS, f"loadable row count drifted: {len(records)} != {EXPECTED_LOADABLE_ROWS}")
    require(not [key for key, count in ids.items() if count > 1], "duplicate external ids")
    return records, {"raw_rows": len(rows), "already_assetized_rows": route_counts["already_assetized_receipt"], "loadable_records": len(records), "blocked_records": route_counts["blocked"], "blocked_reason_counts": dict(reasons.most_common()), "source_table_counts": dict(tables.most_common()), "family_counts": dict(families.most_common()), "partner_counts": dict(partner_counts.most_common())}


def generate(asset_root: Path, runtime_root: Path) -> dict[str, Any]:
    records, summary = build_records(asset_root)
    xml_path = asset_root / XML_REL_PATH
    external_path = asset_root / EXTERNAL_REL_PATH
    validation_path = asset_root / VALIDATION_REL_PATH
    manifest_path = asset_root / ASSET_MANIFEST_REL_PATH
    write_xml(xml_path, records)
    write_json(external_path, {"asset_manifest_version": "1.0", "asset_package_id": ASSET_PACKAGE_ID, "external_id_rule": "legacy_receipt_income_sc_<source_table>_<legacy_id>", "lane_id": "legacy_receipt_income", "records": [{"external_id": row["external_id"], "legacy_source_table": row["legacy_source_table"], "legacy_record_id": row["legacy_record_id"], "project_external_id": row["project_external_id"], "status": "loadable"} for row in records], "summary": {"loadable": len(records), "already_assetized": summary["already_assetized_rows"], "blocked": summary["blocked_records"], "raw_rows": summary["raw_rows"]}})
    write_json(validation_path, {"asset_manifest_version": "1.0", "asset_package_id": ASSET_PACKAGE_ID, "business_boundary": {"legacy_receipt_income_fact": "included", "payment_request": "excluded", "account_move": "excluded", "settlement_state": "excluded", "approval_runtime": "excluded"}, "counts": summary, "validation_gates": {"generate_time": ["legacy_source_key_unique", "project_external_id_required_and_resolves", "source_amount_positive", "already_assetized_receipt_excluded", "no_payment_request_records_generated", "no_account_move_records_generated", "no_settlement_records_generated", "no_runtime_approval_records_generated"]}})
    asset_manifest = {"asset_manifest_version": "1.0", "asset_package_id": ASSET_PACKAGE_ID, "assets": [{"path": str(XML_REL_PATH), "sha256": sha256_file(xml_path), "type": "xml"}, {"path": str(EXTERNAL_REL_PATH), "sha256": sha256_file(external_path), "type": "external_id_manifest"}, {"path": str(VALIDATION_REL_PATH), "sha256": sha256_file(validation_path), "type": "validation_manifest"}], "baseline_package": True, "counts": summary, "db_writes": 0, "dependencies": ["project_sc_v1", "partner_sc_v1"], "generated_at": GENERATED_AT, "lane": {"lane_id": "legacy_receipt_income", "layer": "30_relation", "load_phase": 30}, "odoo_shell": False, "target": {"model": "sc.legacy.receipt.income.fact", "source_tables": sorted(summary["source_table_counts"])}}
    write_json(manifest_path, asset_manifest)
    update_catalog(asset_root, sha256_file(manifest_path))
    payload = {"status": "PASS", "asset_package_id": ASSET_PACKAGE_ID, "xml_path": str(xml_path), "asset_manifest_path": str(manifest_path), "counts": summary, "db_writes": 0, "odoo_shell": False}
    write_json(runtime_root / "legacy_receipt_income_asset_generation_v1.json", payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate legacy receipt/income XML assets.")
    parser.add_argument("--asset-root", default="migration_assets")
    parser.add_argument("--runtime-root", default=str(RUNTIME_ROOT))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        result = generate(Path(args.asset_root), Path(args.runtime_root))
    except (ReceiptIncomeAssetError, json.JSONDecodeError, ET.ParseError, KeyError) as exc:
        print("LEGACY_RECEIPT_INCOME_ASSET_GENERATE=" + json.dumps({"status": "FAIL", "error": str(exc), "db_writes": 0, "odoo_shell": False}, ensure_ascii=False, sort_keys=True))
        return 1 if args.check else 0
    print("LEGACY_RECEIPT_INCOME_ASSET_GENERATE=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
