#!/usr/bin/env python3
"""Generate contract summary-line XML assets from legacy header amounts."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from collections import Counter
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any


REPO_ASSET_ROOT = Path("migration_assets")
RUNTIME_ROOT = Path(".runtime_artifacts/migration_assets/contract_line_sc_v1")
SOURCE_CSV = Path("tmp/raw/contract/contract.csv")
CONTRACT_EXTERNAL_MANIFEST = REPO_ASSET_ROOT / "manifest/contract_external_id_manifest_v1.json"
XML_REL_PATH = Path("20_business/contract_line/contract_line_summary_v1.xml")
EXTERNAL_REL_PATH = Path("manifest/contract_line_external_id_manifest_v1.json")
VALIDATION_REL_PATH = Path("manifest/contract_line_validation_manifest_v1.json")
ASSET_MANIFEST_REL_PATH = Path("manifest/contract_line_asset_manifest_v1.json")
ASSET_PACKAGE_ID = "contract_line_sc_v1"
GENERATED_AT = "2026-04-15T08:35:00+00:00"
AMOUNT_FIELDS = [
    "GCYSZJ",
    "D_SCBSJS_QYHTJ",
    "D_SCBSJS_JSJE",
    "GCJSZJ",
    "CLHGCSBZGJJE",
    "ZYGCZGJJE",
    "ZLJE",
    "AQWMSGF",
    "NMGBZJ",
    "YFK",
    "ZLBZJ",
]


class ContractLineAssetError(Exception):
    pass


def clean(value: object) -> str:
    return "" if value is None else str(value).strip()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractLineAssetError(message)


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


def read_source(path: Path) -> list[dict[str, str]]:
    require(path.exists(), f"missing contract source csv: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def parse_amount(value: object) -> Decimal:
    try:
        return Decimal(clean(value) or "0")
    except InvalidOperation:
        return Decimal("0")


def best_amount(row: dict[str, str]) -> tuple[str, Decimal]:
    for field in AMOUNT_FIELDS:
        amount = parse_amount(row.get(field))
        if amount > 0:
            return field, amount
    return "", Decimal("0")


def safe_external_suffix(value: str) -> str:
    suffix = re.sub(r"[^0-9A-Za-z_]+", "_", value).strip("_").lower()
    require(bool(suffix), "cannot build external id from blank legacy contract id")
    return suffix


def build_contract_map(manifest: dict[str, Any]) -> dict[str, str]:
    result: dict[str, str] = {}
    for row in manifest.get("records", []):
        legacy_id = clean(row.get("legacy_contract_id"))
        external_id = clean(row.get("external_id"))
        if legacy_id and external_id and row.get("status") == "loadable":
            result[legacy_id] = external_id
    require(result, "contract external id map is empty")
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
        record = ET.SubElement(data, "record", {"id": row["external_id"], "model": "construction.contract.line"})
        add_ref_field(record, "contract_id", row["contract_external_id"])
        add_text_field(record, "sequence", "10")
        add_text_field(record, "qty_contract", "1.0")
        add_text_field(record, "price_contract", row["amount"])
        add_text_field(record, "note", row["note"])
    ET.indent(root, space="  ")
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)


def generate(asset_root: Path, runtime_root: Path, source_csv: Path, expected_ready: int) -> dict[str, Any]:
    source_rows = read_source(source_csv)
    contract_by_legacy = build_contract_map(load_json(CONTRACT_EXTERNAL_MANIFEST))
    loadable: list[dict[str, str]] = []
    blocked: list[dict[str, str]] = []
    counters: Counter[str] = Counter()
    amount_sources: Counter[str] = Counter()

    for line_no, row in enumerate(source_rows, start=2):
        legacy_contract_id = clean(row.get("Id"))
        contract_external_id = contract_by_legacy.get(legacy_contract_id)
        amount_source, amount = best_amount(row)
        errors: list[str] = []
        if not legacy_contract_id:
            errors.append("missing_legacy_contract_id")
        elif not contract_external_id:
            errors.append("contract_not_in_asset")
        if amount <= 0:
            errors.append("no_positive_amount")
        if errors:
            for error in errors:
                counters[error] += 1
            if contract_external_id:
                blocked.append(
                    {
                        "line_no": str(line_no),
                        "legacy_contract_id": legacy_contract_id,
                        "errors": ",".join(errors),
                    }
                )
            continue

        amount_sources[amount_source] += 1
        loadable.append(
            {
                "external_id": f"legacy_contract_line_summary_sc_{safe_external_suffix(legacy_contract_id)}",
                "legacy_contract_id": legacy_contract_id,
                "contract_external_id": contract_external_id or "",
                "amount": str(amount),
                "amount_source": amount_source,
                "note": (
                    "summary line from legacy contract header amount; "
                    f"legacy_contract_id={legacy_contract_id}; amount_source={amount_source}; "
                    "not a reconstructed BOQ detail"
                ),
            }
        )

    require(len({row["external_id"] for row in loadable}) == len(loadable), "duplicate XML external ids")
    require(len(loadable) == expected_ready, f"ready contract line count drifted: {len(loadable)} != {expected_ready}")

    xml_path = asset_root / XML_REL_PATH
    external_path = asset_root / EXTERNAL_REL_PATH
    validation_path = asset_root / VALIDATION_REL_PATH
    asset_manifest_path = asset_root / ASSET_MANIFEST_REL_PATH
    write_xml(xml_path, loadable)

    external_manifest = {
        "asset_manifest_version": "1.0",
        "asset_package_id": ASSET_PACKAGE_ID,
        "external_id_rule": {
            "legacy_key_policy": "stable_legacy_contract_pk_summary_line",
            "pattern": "legacy_contract_line_summary_sc_<legacy_contract_id>",
            "source": "sc",
        },
        "lane_id": "contract_line",
        "records": [
            {
                "amount": row["amount"],
                "amount_source": row["amount_source"],
                "contract_external_id": row["contract_external_id"],
                "external_id": row["external_id"],
                "legacy_contract_id": row["legacy_contract_id"],
                "status": "loadable",
                "target_model": "construction.contract.line",
                "target_semantic": "summary_line_only",
            }
            for row in loadable
        ],
        "summary": {
            "blocked": len(blocked),
            "loadable": len(loadable),
            "raw_contract_rows": len(source_rows),
        },
    }
    write_json(external_path, external_manifest)

    validation_manifest = {
        "asset_manifest_version": "1.0",
        "asset_package_id": ASSET_PACKAGE_ID,
        "db_writes": 0,
        "generated_at": GENERATED_AT,
        "odoo_shell": False,
        "source": str(source_csv),
        "target_model": "construction.contract.line",
        "business_boundary": {
            "boq_detail_reconstruction": "excluded",
            "summary_line_policy": "one_line_per_contract_from_header_amount",
        },
        "validation_gates": {
            "generate_time": [
                "contract_external_id_resolves",
                "amount_positive",
                "one_summary_line_per_contract",
                "boq_detail_not_fabricated",
            ],
            "postload": ["xml_external_id_resolves", "contract_id_ref_resolves"],
        },
        "screen_profile": {
            "amount_source_counts": dict(sorted(amount_sources.items())),
            "blocked_rows": len(blocked),
            "blocker_counts": dict(sorted(counters.items())),
            "ready_rows": len(loadable),
        },
    }
    write_json(validation_path, validation_manifest)

    asset_manifest = {
        "asset_manifest_version": "1.0",
        "asset_package_id": ASSET_PACKAGE_ID,
        "assets": [
            {
                "asset_id": "contract_line_summary_xml_v1",
                "format": "xml",
                "path": str(XML_REL_PATH),
                "record_count": len(loadable),
                "required": True,
                "sha256": sha256_file(xml_path),
            },
            {
                "asset_id": "contract_line_external_id_manifest_v1",
                "format": "json",
                "path": str(EXTERNAL_REL_PATH),
                "record_count": len(loadable),
                "required": True,
                "sha256": sha256_file(external_path),
            },
            {
                "asset_id": "contract_line_validation_manifest_v1",
                "format": "json",
                "path": str(VALIDATION_REL_PATH),
                "record_count": 1,
                "required": True,
                "sha256": sha256_file(validation_path),
            },
        ],
        "baseline_package": True,
        "counts": {
            "blocked_records": len(blocked),
            "loadable_records": len(loadable),
            "raw_rows": len(source_rows),
        },
        "db_writes": 0,
        "dependencies": ["contract_sc_v1"],
        "generated_at": GENERATED_AT,
        "idempotency": {
            "conflict_policy": "block_package",
            "duplicate_policy": "update_existing_same_external_id",
            "mode": "odoo_xml_external_id",
        },
        "lane": {
            "business_priority": "contract_amount_fact",
            "lane_id": "contract_line",
            "layer": "20_business",
            "risk_class": "summary_fact",
        },
        "load_order": [
            "contract_line_summary_xml_v1",
            "contract_line_external_id_manifest_v1",
            "contract_line_validation_manifest_v1",
        ],
        "odoo_shell": False,
        "source_snapshot": {
            "extract_batch_id": "contract_line_summary_xml_baseline_v1",
            "source_system": "sc",
            "source_tables": ["T_ProjectContract_Out"],
        },
        "target": {
            "identity_field": "legacy_contract_id",
            "load_strategy": "odoo_xml_external_id",
            "model": "construction.contract.line",
            "semantic": "summary_line_only",
        },
        "validation_gates": [
            "source_contract_file_exists",
            "contract_anchor_resolves",
            "amount_positive",
            "one_summary_line_per_contract",
            "boq_detail_not_fabricated",
        ],
    }
    write_json(asset_manifest_path, asset_manifest)

    runtime_root.mkdir(parents=True, exist_ok=True)
    write_json(runtime_root / "contract_line_blocked_v1.json", {"blocked": blocked, "blocker_counts": dict(counters)})
    return {
        "status": "PASS",
        "asset_package_id": ASSET_PACKAGE_ID,
        "db_writes": 0,
        "odoo_shell": False,
        "raw_rows": len(source_rows),
        "loadable_records": len(loadable),
        "blocked_records": len(blocked),
        "asset_manifest_sha256": sha256_file(asset_manifest_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate contract summary-line XML migration assets.")
    parser.add_argument("--asset-root", default=str(REPO_ASSET_ROOT))
    parser.add_argument("--runtime-root", default=str(RUNTIME_ROOT))
    parser.add_argument("--source", default=str(SOURCE_CSV))
    parser.add_argument("--expected-ready", type=int, default=919)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    try:
        result = generate(Path(args.asset_root), Path(args.runtime_root), Path(args.source), args.expected_ready)
    except (ContractLineAssetError, json.JSONDecodeError) as exc:
        payload = {"status": "FAIL", "error": str(exc), "db_writes": 0, "odoo_shell": False}
        print("CONTRACT_LINE_SUMMARY_ASSET_GENERATOR=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 1 if args.check else 0

    print("CONTRACT_LINE_SUMMARY_ASSET_GENERATOR=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
