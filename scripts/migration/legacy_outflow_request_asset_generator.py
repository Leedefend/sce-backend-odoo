#!/usr/bin/env python3
"""Generate repository XML assets for old-system outflow request facts."""

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

import receipt_core_asset_generator as receipt_core


REPO_ASSET_ROOT = Path("migration_assets")
RUNTIME_ROOT = Path(".runtime_artifacts/migration_assets/outflow_request_sc_v1")
SOURCE_CSV = Path("tmp/raw/payment/payment.csv")
XML_REL_PATH = Path("20_business/outflow/outflow_request_core_v1.xml")
EXTERNAL_REL_PATH = Path("manifest/outflow_request_external_id_manifest_v1.json")
VALIDATION_REL_PATH = Path("manifest/outflow_request_validation_manifest_v1.json")
ASSET_MANIFEST_REL_PATH = Path("manifest/outflow_request_asset_manifest_v1.json")
ASSET_PACKAGE_ID = "outflow_request_sc_v1"
GENERATED_AT = "2026-04-15T10:20:00+00:00"
EXPECTED_RAW_ROWS = 13646
AMOUNT_FIELDS = ("f_JHJE", "f_JHFKJE", "f_NEW_JHJE", "f_SFJE", "ZSJE", "YJJE")
REQUIRED_COLUMNS = {"Id", "f_XMID", "f_GYSID", "f_JHJE"}


class OutflowRequestAssetError(Exception):
    pass


def clean(value: object) -> str:
    return receipt_core.clean(value)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise OutflowRequestAssetError(message)


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
    require(path.exists(), f"missing outflow source csv: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = list(reader.fieldnames or [])
        rows = [dict(row) for row in reader]
    missing = sorted(REQUIRED_COLUMNS - set(fields))
    require(not missing, f"missing outflow source columns: {missing}")
    require(len(rows) == EXPECTED_RAW_ROWS, f"raw row count drifted: {len(rows)} != {EXPECTED_RAW_ROWS}")
    return fields, rows


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


def is_deleted(row: dict[str, str]) -> bool:
    return clean(row.get("DEL")) == "1" or bool(clean(row.get("SCRID")) or clean(row.get("SCR")) or clean(row.get("SCRQ")))


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
    require(bool(suffix), "cannot build external id from blank legacy outflow id")
    return suffix


def load_partner_map(asset_root: Path) -> dict[str, str]:
    return receipt_core.merge_partner_maps(
        receipt_core.build_partner_map(load_json(asset_root / "manifest/partner_external_id_manifest_v1.json")),
        receipt_core.build_partner_map(load_json(asset_root / "manifest/receipt_counterparty_partner_external_id_manifest_v1.json")),
        receipt_core.build_partner_map(load_json(asset_root / "manifest/contract_counterparty_partner_external_id_manifest_v1.json")),
    )


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
        add_text_field(record, "type", "pay", required=True)
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
    project_by_legacy = receipt_core.build_project_map(load_json(asset_root / "manifest/project_external_id_manifest_v1.json"))
    partner_by_legacy = load_partner_map(asset_root)
    contract_by_legacy = receipt_core.build_contract_map(load_json(asset_root / "manifest/contract_external_id_manifest_v1.json"))
    loadable: list[dict[str, str]] = []
    blocked: list[dict[str, str]] = []
    counters: Counter[str] = Counter()
    outflow_ids: Counter[str] = Counter()

    for line_no, row in enumerate(source_rows, start=2):
        legacy_outflow_id = clean(row.get("Id"))
        legacy_project_id = clean(row.get("f_XMID"))
        legacy_partner_id = clean(row.get("f_GYSID"))
        legacy_contract_id = clean(row.get("f_GYSHTID"))
        amount_source, amount = best_amount(row)
        project_external_id = project_by_legacy.get(legacy_project_id, "")
        partner_external_id = partner_by_legacy.get(legacy_partner_id, "")
        contract = contract_by_legacy.get(legacy_contract_id) if legacy_contract_id else None
        errors: list[str] = []
        if not legacy_outflow_id:
            errors.append("missing_legacy_outflow_id")
        if is_deleted(row):
            errors.append("discard_deleted")
        if amount <= 0:
            errors.append("zero_or_negative_amount")
        if not project_external_id:
            errors.append("project_not_in_asset")
        if not legacy_partner_id:
            errors.append("missing_partner_ref")
        elif not partner_external_id:
            errors.append("partner_not_in_asset")

        if errors:
            for error in errors:
                counters[error] += 1
            blocked.append(
                {
                    "line_no": str(line_no),
                    "legacy_outflow_id": legacy_outflow_id,
                    "legacy_project_id": legacy_project_id,
                    "legacy_partner_id": legacy_partner_id,
                    "legacy_contract_id": legacy_contract_id,
                    "errors": ",".join(errors),
                }
            )
            continue

        outflow_ids[legacy_outflow_id] += 1
        request_date = parse_date(first_nonempty(row, ["f_SQRQ", "f_LRSJ", "LRSJ"]))
        document_no = clean(row.get("DJBH"))
        loadable.append(
            {
                "external_id": f"legacy_outflow_sc_{safe_external_suffix(legacy_outflow_id)}",
                "legacy_outflow_id": legacy_outflow_id,
                "legacy_project_id": legacy_project_id,
                "legacy_partner_id": legacy_partner_id,
                "legacy_contract_id": legacy_contract_id,
                "project_external_id": project_external_id,
                "partner_external_id": partner_external_id,
                "contract_external_id": contract["contract_external_id"] if contract else "",
                "contract_link_policy": (
                    "contract_ref"
                    if contract
                    else ("contract_optional_unresolved" if legacy_contract_id else "contract_optional_empty")
                ),
                "amount": str(amount),
                "amount_source": amount_source,
                "date_request": request_date,
                "document_no": document_no,
                "note": (
                    "[migration:outflow_request_core] "
                    f"legacy_outflow_id={legacy_outflow_id}; "
                    f"legacy_project_id={legacy_project_id}; "
                    f"legacy_partner_id={legacy_partner_id}; "
                    f"legacy_contract_id={legacy_contract_id}; "
                    f"amount_source={amount_source}; "
                    f"document_no={document_no}"
                ),
            }
        )

    duplicate_outflow_ids = sorted(key for key, count in outflow_ids.items() if count > 1)
    require(not duplicate_outflow_ids, f"duplicate loadable outflow ids: {duplicate_outflow_ids[:10]}")
    require(len({row["external_id"] for row in loadable}) == len(loadable), "duplicate XML external ids")
    require(len(loadable) == expected_ready, f"ready outflow count drifted: {len(loadable)} != {expected_ready}")

    xml_path = asset_root / XML_REL_PATH
    external_path = asset_root / EXTERNAL_REL_PATH
    validation_path = asset_root / VALIDATION_REL_PATH
    asset_manifest_path = asset_root / ASSET_MANIFEST_REL_PATH
    write_xml(xml_path, loadable)

    external_manifest = {
        "asset_manifest_version": "1.0",
        "asset_package_id": ASSET_PACKAGE_ID,
        "external_id_rule": {
            "legacy_key_policy": "stable_legacy_outflow_pk",
            "pattern": "legacy_outflow_sc_<legacy_outflow_id>",
            "source": "sc",
        },
        "lane_id": "outflow",
        "records": [
            {
                "amount": row["amount"],
                "amount_source": row["amount_source"],
                "contract_external_id": row["contract_external_id"],
                "contract_link_policy": row["contract_link_policy"],
                "external_id": row["external_id"],
                "legacy_contract_id": row["legacy_contract_id"],
                "legacy_outflow_id": row["legacy_outflow_id"],
                "legacy_partner_id": row["legacy_partner_id"],
                "legacy_project_id": row["legacy_project_id"],
                "partner_external_id": row["partner_external_id"],
                "project_external_id": row["project_external_id"],
                "status": "loadable",
                "target_model": "payment.request",
                "target_type": "pay",
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
        "target_type": "pay",
        "business_boundary": {
            "state_replay": "excluded",
            "settlement_link": "excluded",
            "ledger": "excluded",
            "accounting": "excluded",
            "workflow": "excluded",
        },
        "validation_gates": {
            "generate_time": [
                "legacy_outflow_id_unique",
                "amount_positive",
                "project_external_id_resolves",
                "partner_external_id_resolves",
                "contract_id_optional_when_missing_in_legacy",
                "type_pay_only",
                "state_not_written",
                "settlement_not_written",
                "ledger_not_written",
                "accounting_not_written",
                "workflow_not_written",
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
                "asset_id": "outflow_request_core_xml_v1",
                "format": "xml",
                "path": str(XML_REL_PATH),
                "record_count": len(loadable),
                "required": True,
                "sha256": sha256_file(xml_path),
            },
            {
                "asset_id": "outflow_request_external_id_manifest_v1",
                "format": "json",
                "path": str(EXTERNAL_REL_PATH),
                "record_count": len(loadable),
                "required": True,
                "sha256": sha256_file(external_path),
            },
            {
                "asset_id": "outflow_request_validation_manifest_v1",
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
        "dependencies": [
            "project_sc_v1",
            "partner_sc_v1",
            "contract_counterparty_partner_sc_v1",
            "receipt_counterparty_partner_sc_v1",
            "contract_sc_v1",
        ],
        "generated_at": GENERATED_AT,
        "idempotency": {
            "conflict_policy": "block_package",
            "duplicate_policy": "update_existing_same_external_id",
            "mode": "odoo_xml_external_id",
        },
        "lane": {
            "business_priority": "outflow_request_core_fact",
            "lane_id": "outflow",
            "layer": "20_business",
            "risk_class": "authorized_outflow_request_core",
        },
        "load_order": [
            "outflow_request_core_xml_v1",
            "outflow_request_external_id_manifest_v1",
            "outflow_request_validation_manifest_v1",
        ],
        "odoo_shell": False,
        "source_snapshot": {
            "extract_batch_id": "outflow_request_core_xml_baseline_v1",
            "source_system": "sc",
            "source_tables": ["C_ZFSQGL"],
        },
        "target": {
            "identity_field": "legacy_outflow_id",
            "load_strategy": "odoo_xml_external_id",
            "model": "payment.request",
            "type": "pay",
        },
        "validation_gates": [
            "source_outflow_file_exists",
            "required_source_headers_present",
            "legacy_outflow_id_non_empty",
            "legacy_outflow_id_unique",
            "amount_positive",
            "project_anchor_resolves",
            "partner_anchor_resolves",
            "contract_id_optional_when_missing_in_legacy",
            "state_not_written",
            "settlement_not_written",
            "ledger_not_written",
            "accounting_not_written",
            "workflow_not_written",
        ],
    }
    write_json(asset_manifest_path, asset_manifest)

    runtime_root.mkdir(parents=True, exist_ok=True)
    write_json(runtime_root / "outflow_request_blocked_v1.json", {"blocked": blocked, "blocker_counts": dict(counters)})
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
    parser = argparse.ArgumentParser(description="Generate old-system outflow request XML migration assets.")
    parser.add_argument("--asset-root", default=str(REPO_ASSET_ROOT))
    parser.add_argument("--runtime-root", default=str(RUNTIME_ROOT))
    parser.add_argument("--source", default=str(SOURCE_CSV))
    parser.add_argument("--expected-ready", type=int, default=12284)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    try:
        result = generate(Path(args.asset_root), Path(args.runtime_root), Path(args.source), args.expected_ready)
    except (OutflowRequestAssetError, receipt_core.ReceiptAssetError, json.JSONDecodeError) as exc:
        payload = {"status": "FAIL", "error": str(exc), "db_writes": 0, "odoo_shell": False}
        print("OUTFLOW_REQUEST_ASSET_GENERATOR=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 1 if args.check else 0

    print("OUTFLOW_REQUEST_ASSET_GENERATOR=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
