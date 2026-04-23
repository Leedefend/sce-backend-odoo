#!/usr/bin/env python3
"""Generate repository XML assets for old-system core receipt facts."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any


REPO_ASSET_ROOT = Path("migration_assets")
RUNTIME_ROOT = Path(".runtime_artifacts/migration_assets/receipt_sc_v1")
SOURCE_CSV = Path("tmp/raw/receipt/receipt.csv")
PROJECT_EXTERNAL_MANIFEST = REPO_ASSET_ROOT / "manifest/project_external_id_manifest_v1.json"
PARTNER_EXTERNAL_MANIFEST = REPO_ASSET_ROOT / "manifest/partner_external_id_manifest_v1.json"
RECEIPT_COUNTERPARTY_EXTERNAL_MANIFEST = REPO_ASSET_ROOT / "manifest/receipt_counterparty_partner_external_id_manifest_v1.json"
CONTRACT_EXTERNAL_MANIFEST = REPO_ASSET_ROOT / "manifest/contract_external_id_manifest_v1.json"
XML_REL_PATH = Path("20_business/receipt/receipt_core_v1.xml")
EXTERNAL_REL_PATH = Path("manifest/receipt_external_id_manifest_v1.json")
VALIDATION_REL_PATH = Path("manifest/receipt_validation_manifest_v1.json")
ASSET_MANIFEST_REL_PATH = Path("manifest/receipt_asset_manifest_v1.json")
REQUIRED_COLUMNS = {"Id", "f_JE", "WLDWID"}
ASSET_PACKAGE_ID = "receipt_sc_v1"
GENERATED_AT = "2026-04-15T08:15:00+00:00"


class ReceiptAssetError(Exception):
    pass


def clean(value: object) -> str:
    return "" if value is None else str(value).strip()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ReceiptAssetError(message)


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
    require(path.exists(), f"missing receipt source csv: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = list(reader.fieldnames or [])
        rows = [dict(row) for row in reader]
    missing = sorted(REQUIRED_COLUMNS - set(fields))
    require(not missing, f"missing receipt source columns: {missing}")
    return fields, rows


def parse_amount(value: object) -> Decimal:
    try:
        return Decimal(clean(value) or "0")
    except InvalidOperation:
        return Decimal("0")


def is_deleted(value: object) -> bool:
    normalized = clean(value).lower()
    return bool(normalized) and normalized not in {"0", "false", "no", "n", "否"}


def first_nonempty(row: dict[str, str], fields: list[str]) -> str:
    for field in fields:
        value = clean(row.get(field))
        if value:
            return value
    return ""


def parse_date(value: object) -> str:
    raw = clean(value)
    if not raw:
        return ""
    for fmt in ("%m/%d/%Y %H:%M:%S", "%m/%d/%Y", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(raw, fmt).date().isoformat()
        except ValueError:
            continue
    return ""


def safe_external_suffix(value: str) -> str:
    suffix = re.sub(r"[^0-9A-Za-z_]+", "_", value).strip("_").lower()
    require(bool(suffix), "cannot build external id from blank legacy receipt id")
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


def build_partner_map(manifest: dict[str, Any]) -> dict[str, str]:
    result: dict[str, str] = {}
    for row in manifest.get("records", []):
        legacy_id = clean(row.get("legacy_partner_id"))
        external_id = clean(row.get("external_id"))
        if legacy_id and external_id and row.get("status") == "loadable":
            result[legacy_id] = external_id
    require(result, "partner external id map is empty")
    return result


def merge_partner_maps(*maps: dict[str, str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for mapping in maps:
        for legacy_id, external_id in mapping.items():
            if legacy_id not in result:
                result[legacy_id] = external_id
    require(result, "merged partner external id map is empty")
    return result


def build_contract_map(manifest: dict[str, Any]) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for row in manifest.get("records", []):
        legacy_id = clean(row.get("legacy_contract_id"))
        external_id = clean(row.get("external_id"))
        project_external_id = clean(row.get("project_external_id"))
        if legacy_id and external_id and project_external_id and row.get("status") == "loadable":
            result[legacy_id] = {
                "contract_external_id": external_id,
                "project_external_id": project_external_id,
                "legacy_project_id": clean(row.get("legacy_project_id")),
            }
    require(result, "contract external id map is empty")
    return result


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
        record = ET.SubElement(data, "record", {"id": row["external_id"], "model": "payment.request"})
        add_text_field(record, "type", "receive", required=True)
        add_ref_field(record, "project_id", row["project_external_id"])
        if row["contract_external_id"]:
            add_ref_field(record, "contract_id", row["contract_external_id"])
        add_ref_field(record, "partner_id", row["partner_external_id"])
        add_text_field(record, "amount", row["amount"], required=True)
        add_text_field(record, "date_request", row["date_request"])
        add_text_field(record, "note", row["note"], required=True)
    ET.indent(root, space="  ")
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)


def generate(asset_root: Path, runtime_root: Path, source_csv: Path, expected_ready: int) -> dict[str, Any]:
    _fields, source_rows = read_source(source_csv)
    project_by_legacy = build_project_map(load_json(PROJECT_EXTERNAL_MANIFEST))
    partner_by_legacy = merge_partner_maps(
        build_partner_map(load_json(PARTNER_EXTERNAL_MANIFEST)),
        build_partner_map(load_json(RECEIPT_COUNTERPARTY_EXTERNAL_MANIFEST)),
    )
    contract_by_legacy = build_contract_map(load_json(CONTRACT_EXTERNAL_MANIFEST))
    loadable: list[dict[str, str]] = []
    blocked: list[dict[str, str]] = []
    counters: Counter[str] = Counter()
    receipt_ids: Counter[str] = Counter()

    for line_no, row in enumerate(source_rows, start=2):
        legacy_receipt_id = clean(row.get("Id"))
        amount = parse_amount(row.get("f_JE"))
        legacy_contract_id = first_nonempty(row, ["SGHTID", "GLHTID", "HTID"])
        row_legacy_project_id = first_nonempty(row, ["XMID", "LYXMID", "TSXMID"])
        legacy_partner_id = clean(row.get("WLDWID"))
        contract = contract_by_legacy.get(legacy_contract_id)
        partner_external_id = partner_by_legacy.get(legacy_partner_id)
        errors: list[str] = []
        if not legacy_receipt_id:
            errors.append("missing_legacy_receipt_id")
        if is_deleted(row.get("DEL")):
            errors.append("discard_deleted")
        if amount <= 0:
            errors.append("zero_or_negative_amount")
        if not legacy_partner_id:
            errors.append("missing_partner_ref")
        elif not partner_external_id:
            errors.append("partner_not_in_asset")

        project_external_id = contract["project_external_id"] if contract else project_by_legacy.get(row_legacy_project_id, "")
        legacy_project_id = contract["legacy_project_id"] if contract else row_legacy_project_id
        if not project_external_id:
            errors.append("project_not_in_asset")

        if errors:
            for error in errors:
                counters[error] += 1
            blocked.append(
                {
                    "line_no": str(line_no),
                    "legacy_receipt_id": legacy_receipt_id,
                    "legacy_contract_id": legacy_contract_id,
                    "legacy_partner_id": legacy_partner_id,
                    "errors": ",".join(errors),
                }
            )
            continue

        receipt_ids[legacy_receipt_id] += 1
        document_no = clean(row.get("DJBH"))
        receipt_date = parse_date(first_nonempty(row, ["f_RQ", "LRSJ", "f_LRSJ"]))
        loadable.append(
            {
                "external_id": f"legacy_receipt_sc_{safe_external_suffix(legacy_receipt_id)}",
                "legacy_receipt_id": legacy_receipt_id,
                "legacy_contract_id": legacy_contract_id,
                "legacy_project_id": legacy_project_id,
                "legacy_partner_id": legacy_partner_id,
                "project_external_id": project_external_id,
                "contract_external_id": contract["contract_external_id"] if contract else "",
                "contract_link_policy": (
                    "contract_ref"
                    if contract
                    else ("contract_optional_unresolved" if legacy_contract_id else "contract_optional_empty")
                ),
                "partner_external_id": partner_external_id or "",
                "amount": str(amount),
                "date_request": receipt_date,
                "document_no": document_no,
                "note": (
                    "[migration:receipt_core] "
                    f"legacy_receipt_id={legacy_receipt_id}; "
                    f"legacy_contract_id={legacy_contract_id}; "
                    f"document_no={document_no}"
                ),
            }
        )

    duplicate_receipt_ids = sorted(key for key, count in receipt_ids.items() if count > 1)
    require(not duplicate_receipt_ids, f"duplicate loadable receipt ids: {duplicate_receipt_ids[:10]}")
    require(len({row["external_id"] for row in loadable}) == len(loadable), "duplicate XML external ids")
    require(len(loadable) == expected_ready, f"ready receipt count drifted: {len(loadable)} != {expected_ready}")

    xml_path = asset_root / XML_REL_PATH
    external_path = asset_root / EXTERNAL_REL_PATH
    validation_path = asset_root / VALIDATION_REL_PATH
    asset_manifest_path = asset_root / ASSET_MANIFEST_REL_PATH
    write_xml(xml_path, loadable)

    external_manifest = {
        "asset_manifest_version": "1.0",
        "asset_package_id": ASSET_PACKAGE_ID,
        "external_id_rule": {
            "legacy_key_policy": "stable_legacy_receipt_pk",
            "pattern": "legacy_receipt_sc_<legacy_receipt_id>",
            "source": "sc",
        },
        "lane_id": "receipt",
        "records": [
            {
                "amount": row["amount"],
                "contract_external_id": row["contract_external_id"],
                "contract_link_policy": row["contract_link_policy"],
                "external_id": row["external_id"],
                "legacy_contract_id": row["legacy_contract_id"],
                "legacy_partner_id": row["legacy_partner_id"],
                "legacy_project_id": row["legacy_project_id"],
                "legacy_receipt_id": row["legacy_receipt_id"],
                "partner_external_id": row["partner_external_id"],
                "project_external_id": row["project_external_id"],
                "status": "loadable",
                "target_model": "payment.request",
                "target_type": "receive",
            }
            for row in loadable
        ],
        "summary": {
            "blocked": len(blocked),
            "loadable": len(loadable),
            "raw_rows": len(source_rows),
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
        "target_model": "payment.request",
        "target_type": "receive",
        "business_boundary": {
            "state_replay": "excluded",
            "settlement_link": "excluded",
            "ledger": "excluded",
            "accounting": "excluded",
        },
        "validation_gates": {
            "generate_time": [
                "legacy_receipt_id_unique",
                "amount_positive",
                "project_external_id_resolves",
            "contract_external_id_resolves",
            "contract_id_optional_when_missing_in_legacy",
            "partner_external_id_resolves",
                "type_receive_only",
                "state_not_written",
                "settlement_not_written",
                "ledger_not_written",
                "accounting_not_written",
            ],
            "postload": ["xml_external_id_resolves", "draft_defaults_apply"],
        },
        "screen_profile": {
            "blocked_rows": len(blocked),
            "blocker_counts": dict(sorted(counters.items())),
            "ready_rows": len(loadable),
            "contract_optional_empty_rows": sum(1 for row in loadable if not row["contract_external_id"]),
        },
    }
    write_json(validation_path, validation_manifest)

    asset_manifest = {
        "asset_manifest_version": "1.0",
        "asset_package_id": ASSET_PACKAGE_ID,
        "assets": [
            {
                "asset_id": "receipt_core_xml_v1",
                "format": "xml",
                "path": str(XML_REL_PATH),
                "record_count": len(loadable),
                "required": True,
                "sha256": sha256_file(xml_path),
            },
            {
                "asset_id": "receipt_external_id_manifest_v1",
                "format": "json",
                "path": str(EXTERNAL_REL_PATH),
                "record_count": len(loadable),
                "required": True,
                "sha256": sha256_file(external_path),
            },
            {
                "asset_id": "receipt_validation_manifest_v1",
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
        "dependencies": ["project_sc_v1", "partner_sc_v1", "receipt_counterparty_partner_sc_v1", "contract_sc_v1"],
        "generated_at": GENERATED_AT,
        "idempotency": {
            "conflict_policy": "block_package",
            "duplicate_policy": "update_existing_same_external_id",
            "mode": "odoo_xml_external_id",
        },
        "lane": {
            "business_priority": "receipt_core_fact",
            "lane_id": "receipt",
            "layer": "20_business",
            "risk_class": "authorized_receipt_core",
        },
        "load_order": [
            "receipt_core_xml_v1",
            "receipt_external_id_manifest_v1",
            "receipt_validation_manifest_v1",
        ],
        "odoo_shell": False,
        "source_snapshot": {
            "extract_batch_id": "receipt_core_xml_baseline_v1",
            "source_system": "sc",
            "source_tables": ["C_JFHKLR"],
        },
        "target": {
            "identity_field": "legacy_receipt_id",
            "load_strategy": "odoo_xml_external_id",
            "model": "payment.request",
            "type": "receive",
        },
        "validation_gates": [
            "source_receipt_file_exists",
            "required_source_headers_present",
            "legacy_receipt_id_non_empty",
            "legacy_receipt_id_unique",
            "amount_positive",
            "project_anchor_resolves",
            "contract_anchor_resolves",
            "contract_id_optional_when_missing_in_legacy",
            "partner_anchor_resolves",
            "state_not_written",
            "settlement_not_written",
            "ledger_not_written",
            "accounting_not_written",
        ],
    }
    write_json(asset_manifest_path, asset_manifest)

    runtime_root.mkdir(parents=True, exist_ok=True)
    write_json(runtime_root / "receipt_blocked_v1.json", {"blocked": blocked, "blocker_counts": dict(counters)})
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
    parser = argparse.ArgumentParser(description="Generate receipt core XML migration assets.")
    parser.add_argument("--asset-root", default=str(REPO_ASSET_ROOT))
    parser.add_argument("--runtime-root", default=str(RUNTIME_ROOT))
    parser.add_argument("--source", default=str(SOURCE_CSV))
    parser.add_argument("--expected-ready", type=int, default=3411)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    try:
        result = generate(Path(args.asset_root), Path(args.runtime_root), Path(args.source), args.expected_ready)
    except (ReceiptAssetError, json.JSONDecodeError) as exc:
        payload = {"status": "FAIL", "error": str(exc), "db_writes": 0, "odoo_shell": False}
        print("RECEIPT_CORE_ASSET_GENERATOR=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 1 if args.check else 0

    print("RECEIPT_CORE_ASSET_GENERATOR=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
