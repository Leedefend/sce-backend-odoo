#!/usr/bin/env python3
"""Generate supplemental res.partner assets from receipt counterparties."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import receipt_core_asset_generator as receipt_core


REPO_ASSET_ROOT = Path("migration_assets")
RUNTIME_ROOT = Path(".runtime_artifacts/migration_assets/receipt_counterparty_partner_sc_v1")
SOURCE_CSV = Path("tmp/raw/receipt/receipt.csv")
XML_REL_PATH = Path("10_master/receipt_counterparty_partner/receipt_counterparty_partner_master_v1.xml")
EXTERNAL_REL_PATH = Path("manifest/receipt_counterparty_partner_external_id_manifest_v1.json")
VALIDATION_REL_PATH = Path("manifest/receipt_counterparty_partner_validation_manifest_v1.json")
ASSET_MANIFEST_REL_PATH = Path("manifest/receipt_counterparty_partner_asset_manifest_v1.json")
ASSET_PACKAGE_ID = "receipt_counterparty_partner_sc_v1"
LANE = "receipt_counterparty_partner"
TARGET_MODEL = "res.partner"
ENTERPRISE_TOKENS = ("公司", "厂", "集团", "中心", "合作社", "银行", "学校", "医院", "政府", "委员会", "项目部", "经营部")


class ReceiptCounterpartyPartnerAssetError(Exception):
    pass


def clean(value: object) -> str:
    text = "" if value is None else str(value)
    text = text.replace("\u3000", " ").strip()
    return re.sub(r"\s+", " ", text)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ReceiptCounterpartyPartnerAssetError(message)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def normalize_name(value: str) -> str:
    return re.sub(r"[（）()·,，.。/、\s\\-]", "", clean(value))


def is_safe_name(value: str) -> bool:
    text = clean(value)
    if len(text) < 2 or text.isdigit():
        return False
    return text not in {"==请选择==", "请选择", "无", "测试"}


def is_enterprise_name(value: str) -> bool:
    return any(token in clean(value) for token in ENTERPRISE_TOKENS)


def safe_external_suffix(value: str) -> str:
    suffix = re.sub(r"[^0-9A-Za-z_]+", "_", value).strip("_").lower()
    if suffix:
        return suffix
    return hashlib.sha1(value.encode("utf-8")).hexdigest()[:16]


def read_source(path: Path) -> list[dict[str, str]]:
    require(path.exists(), f"missing receipt csv: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def build_records(asset_root: Path, source_rows: list[dict[str, str]]) -> tuple[list[dict[str, Any]], list[dict[str, str]], Counter[str]]:
    project_by_legacy = receipt_core.build_project_map(receipt_core.load_json(receipt_core.PROJECT_EXTERNAL_MANIFEST))
    partner_by_legacy = receipt_core.build_partner_map(receipt_core.load_json(receipt_core.PARTNER_EXTERNAL_MANIFEST))
    contract_by_legacy = receipt_core.build_contract_map(receipt_core.load_json(receipt_core.CONTRACT_EXTERNAL_MANIFEST))
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    blocked: list[dict[str, str]] = []
    route_counts: Counter[str] = Counter()

    for row in source_rows:
        legacy_receipt_id = clean(row.get("Id"))
        amount = receipt_core.parse_amount(row.get("f_JE"))
        legacy_contract_id = receipt_core.first_nonempty(row, ["SGHTID", "GLHTID", "HTID"])
        row_legacy_project_id = receipt_core.first_nonempty(row, ["XMID", "LYXMID", "TSXMID"])
        legacy_partner_id = clean(row.get("WLDWID"))
        partner_name = clean(row.get("WLDWMC"))
        contract = contract_by_legacy.get(legacy_contract_id)
        partner_external_id = partner_by_legacy.get(legacy_partner_id)
        project_external_id = contract["project_external_id"] if contract else project_by_legacy.get(row_legacy_project_id, "")

        blockers: list[str] = []
        if not legacy_receipt_id:
            blockers.append("missing_legacy_receipt_id")
        if receipt_core.is_deleted(row.get("DEL")):
            blockers.append("discard_deleted")
        if amount <= 0:
            blockers.append("zero_or_negative_amount")
        if not project_external_id:
            blockers.append("project_not_in_asset")
        if not legacy_partner_id:
            blockers.append("missing_partner_ref")
        elif partner_external_id:
            blockers.append("partner_already_in_asset")
        if not partner_name or not is_safe_name(partner_name):
            blockers.append("unsafe_partner_name")

        if blockers:
            for blocker in blockers:
                route_counts[blocker] += 1
            blocked.append(
                {
                    "legacy_receipt_id": legacy_receipt_id,
                    "legacy_partner_id": legacy_partner_id,
                    "partner_name": partner_name,
                    "blockers": ",".join(blockers),
                }
            )
            continue
        route_counts["supplement_candidate"] += 1
        grouped[legacy_partner_id].append(row)

    records: list[dict[str, Any]] = []
    seen_external_ids: set[str] = set()
    for legacy_partner_id, rows in sorted(grouped.items()):
        names = Counter(clean(row.get("WLDWMC")) for row in rows if clean(row.get("WLDWMC")))
        name = sorted(names.items(), key=lambda item: (-item[1], item[0]))[0][0]
        external_id = f"legacy_receipt_counterparty_sc_{safe_external_suffix(legacy_partner_id)}"
        require(external_id not in seen_external_ids, f"duplicate external id: {external_id}")
        seen_external_ids.add(external_id)
        enterprise = is_enterprise_name(name)
        records.append(
            {
                "external_id": external_id,
                "legacy_partner_id": legacy_partner_id,
                "legacy_identity_key": f"receipt_counterparty:sc:{legacy_partner_id}",
                "legacy_partner_source": "receipt_counterparty",
                "legacy_partner_name": name,
                "name": name,
                "company_type": "company" if enterprise else "person",
                "is_company": "1" if enterprise else "0",
                "normalized_partner_name": normalize_name(name),
                "source_receipt_count": len(rows),
                "legacy_source_evidence": "tmp/raw/receipt/receipt.csv:WLDWID/WLDWMC",
            }
        )
    return records, blocked, route_counts


def add_text_field(record: ET.Element, name: str, value: object) -> None:
    field = ET.SubElement(record, "field", {"name": name})
    field.text = clean(value)


def write_xml(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    root = ET.Element("odoo")
    data = ET.SubElement(root, "data", {"noupdate": "1"})
    for row in records:
        record = ET.SubElement(data, "record", {"id": row["external_id"], "model": TARGET_MODEL})
        for field_name in (
            "name",
            "company_type",
            "is_company",
            "legacy_partner_id",
            "legacy_partner_source",
            "legacy_partner_name",
            "legacy_source_evidence",
        ):
            add_text_field(record, field_name, row[field_name])
    ET.indent(root, space="  ")
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)


def generate(asset_root: Path, runtime_root: Path, source_csv: Path, expected_ready: int) -> dict[str, Any]:
    source_rows = read_source(source_csv)
    records, blocked, route_counts = build_records(asset_root, source_rows)
    require(len(records) == expected_ready, f"ready receipt counterparty partner count drifted: {len(records)} != {expected_ready}")
    xml_path = asset_root / XML_REL_PATH
    external_path = asset_root / EXTERNAL_REL_PATH
    validation_path = asset_root / VALIDATION_REL_PATH
    asset_manifest_path = asset_root / ASSET_MANIFEST_REL_PATH
    write_xml(xml_path, records)

    external_manifest = {
        "asset_manifest_version": "1.0",
        "asset_package_id": ASSET_PACKAGE_ID,
        "lane_id": LANE,
        "external_id_rule": {
            "legacy_key_policy": "stable_receipt_counterparty_wldwid",
            "pattern": "legacy_receipt_counterparty_sc_<WLDWID>",
            "source": "sc",
        },
        "records": [
            {
                "external_id": row["external_id"],
                "legacy_identity_key": row["legacy_identity_key"],
                "legacy_partner_id": row["legacy_partner_id"],
                "legacy_partner_source": row["legacy_partner_source"],
                "name": row["name"],
                "company_type": row["company_type"],
                "status": "loadable",
                "target_model": TARGET_MODEL,
                "target_lookup": {"field": "xml_id", "value": row["external_id"]},
            }
            for row in records
        ],
        "summary": {"loadable": len(records), "candidate_receipt_rows": route_counts["supplement_candidate"]},
    }
    write_json(external_path, external_manifest)

    validation_manifest = {
        "asset_manifest_version": "1.0",
        "asset_package_id": ASSET_PACKAGE_ID,
        "baseline_package": True,
        "db_writes": 0,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "odoo_shell": False,
        "source": str(source_csv),
        "target_model": TARGET_MODEL,
        "business_boundary": {
            "personal_counterparty_policy": "allowed_for_receipt_partner_id",
            "target_model_capacity": "payment.request.partner_id is res.partner and does not require company",
        },
        "screen_profile": {
            "blocked_source_rows": len(blocked),
            "route_counts": dict(sorted(route_counts.items())),
            "ready_partner_records": len(records),
        },
        "validation_gates": {
            "generate_time": [
                "positive_amount_required",
                "deleted_rows_excluded",
                "project_anchor_resolves",
                "legacy_counterparty_id_required",
                "legacy_counterparty_name_safe",
                "personal_partner_supported",
                "external_id_unique",
                "no_db_writes",
            ],
            "postload": ["xml_external_id_resolves"],
        },
    }
    write_json(validation_path, validation_manifest)

    asset_manifest = {
        "asset_manifest_version": "1.0",
        "asset_package_id": ASSET_PACKAGE_ID,
        "assets": [
            {
                "asset_id": "receipt_counterparty_partner_master_xml_v1",
                "format": "xml",
                "path": str(XML_REL_PATH),
                "record_count": len(records),
                "required": True,
                "sha256": sha256_file(xml_path),
            },
            {
                "asset_id": "receipt_counterparty_partner_external_id_manifest_v1",
                "format": "json",
                "path": str(EXTERNAL_REL_PATH),
                "record_count": len(records),
                "required": True,
                "sha256": sha256_file(external_path),
            },
            {
                "asset_id": "receipt_counterparty_partner_validation_manifest_v1",
                "format": "json",
                "path": str(VALIDATION_REL_PATH),
                "record_count": 1,
                "required": True,
                "sha256": sha256_file(validation_path),
            },
        ],
        "baseline_package": True,
        "counts": {
            "candidate_receipt_rows": route_counts["supplement_candidate"],
            "discarded_records": 0,
            "loadable_records": len(records),
            "raw_rows": len(records),
        },
        "db_writes": 0,
        "dependencies": ["partner_sc_v1"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "idempotency": {"mode": "odoo_xml_external_id", "duplicate_policy": "update_existing_same_external_id", "conflict_policy": "block_package"},
        "lane": {
            "business_priority": "receipt_counterparty_anchor_master",
            "lane_id": LANE,
            "layer": "10_master",
            "risk_class": "supplemental_master_data",
        },
        "load_order": [
            "receipt_counterparty_partner_master_xml_v1",
            "receipt_counterparty_partner_external_id_manifest_v1",
            "receipt_counterparty_partner_validation_manifest_v1",
        ],
        "odoo_shell": False,
        "source_snapshot": {"extract_batch_id": "receipt_counterparty_partner_xml_baseline_v1", "source_system": "sc", "source_tables": ["T_ProjectIncome"]},
        "target": {"identity_field": "legacy_partner_id", "load_strategy": "odoo_xml_external_id", "model": TARGET_MODEL},
        "validation_gates": [
            "positive_amount_required",
            "deleted_rows_excluded",
            "project_anchor_resolves",
            "legacy_counterparty_id_required",
            "legacy_counterparty_name_safe",
            "personal_partner_supported",
            "no_db_writes",
        ],
    }
    write_json(asset_manifest_path, asset_manifest)
    runtime_root.mkdir(parents=True, exist_ok=True)
    write_json(runtime_root / "receipt_counterparty_partner_blocked_v1.json", {"blocked": blocked[:200], "route_counts": dict(route_counts)})
    return {
        "status": "PASS",
        "asset_package_id": ASSET_PACKAGE_ID,
        "candidate_receipt_rows": route_counts["supplement_candidate"],
        "loadable_records": len(records),
        "asset_manifest_sha256": sha256_file(asset_manifest_path),
        "db_writes": 0,
        "odoo_shell": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate receipt counterparty supplemental partner assets.")
    parser.add_argument("--asset-root", default=str(REPO_ASSET_ROOT))
    parser.add_argument("--runtime-root", default=str(RUNTIME_ROOT))
    parser.add_argument("--source", default=str(SOURCE_CSV))
    parser.add_argument("--expected-ready", type=int, default=250)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        result = generate(Path(args.asset_root), Path(args.runtime_root), Path(args.source), args.expected_ready)
    except (ReceiptCounterpartyPartnerAssetError, receipt_core.ReceiptAssetError, ET.ParseError, json.JSONDecodeError) as exc:
        payload = {"status": "FAIL", "error": str(exc), "db_writes": 0, "odoo_shell": False}
        print("RECEIPT_COUNTERPARTY_PARTNER_ASSET_GENERATOR=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 1 if args.check else 0
    print("RECEIPT_COUNTERPARTY_PARTNER_ASSET_GENERATOR=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
