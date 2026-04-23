#!/usr/bin/env python3
"""Generate supplemental partner XML assets from legacy contract counterparties."""

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

import contract_header_asset_generator as contract_header


REPO_ASSET_ROOT = Path("migration_assets")
RUNTIME_ROOT = Path(".runtime_artifacts/migration_assets/contract_counterparty_partner_sc_v1")
SOURCE_CSV = Path("tmp/raw/contract/contract.csv")
XML_REL_PATH = Path("10_master/contract_counterparty_partner/contract_counterparty_partner_master_v1.xml")
EXTERNAL_REL_PATH = Path("manifest/contract_counterparty_partner_external_id_manifest_v1.json")
VALIDATION_REL_PATH = Path("manifest/contract_counterparty_partner_validation_manifest_v1.json")
ASSET_MANIFEST_REL_PATH = Path("manifest/contract_counterparty_partner_asset_manifest_v1.json")
ASSET_PACKAGE_ID = "contract_counterparty_partner_sc_v1"
LANE = "contract_counterparty_partner"
LAYER = "10_master"
TARGET_MODEL = "res.partner"


class ContractCounterpartyPartnerAssetError(Exception):
    pass


def clean(value: object) -> str:
    text = "" if value is None else str(value)
    text = text.replace("\u3000", " ").strip()
    return re.sub(r"\s+", " ", text)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractCounterpartyPartnerAssetError(message)


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
    require(path.exists(), f"missing contract csv: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def is_safe_enterprise_name(value: str) -> bool:
    text = clean(value)
    if len(text) < 4:
        return False
    if text.isdigit():
        return False
    if text in {"==请选择==", "请选择", "无", "测试"}:
        return False
    return True


def stable_external_id(normalized_name: str) -> str:
    digest = hashlib.sha1(normalized_name.encode("utf-8")).hexdigest()[:16]
    return f"legacy_contract_counterparty_sc_{digest}"


def representative_name(names: list[str]) -> str:
    counts = Counter(clean(name) for name in names if clean(name))
    require(bool(counts), "cannot choose representative name from empty names")
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))[0][0]


def current_partner_anchor(
    legacy_contract_id: str,
    counterparty: str,
    partner_exact: dict[str, list[dict[str, str]]],
    partner_normalized: dict[str, list[dict[str, str]]],
    receipt_single_counterparty: dict[str, str],
    partner_by_legacy_id: dict[str, str],
) -> tuple[str, str]:
    partner_external_id, partner_match_type = contract_header.resolve_partner(counterparty, partner_exact, partner_normalized)
    if not partner_external_id and legacy_contract_id:
        receipt_partner_id = receipt_single_counterparty.get(legacy_contract_id, "")
        receipt_partner_external_id = partner_by_legacy_id.get(receipt_partner_id, "")
        if receipt_partner_external_id:
            return receipt_partner_external_id, "receipt_single_counterparty"
    return partner_external_id, partner_match_type


def build_records(asset_root: Path, source_rows: list[dict[str, str]]) -> tuple[list[dict[str, Any]], list[dict[str, str]], Counter[str], Counter[str]]:
    project_external = contract_header.project_map(load_json(contract_header.PROJECT_EXTERNAL_MANIFEST))
    partner_by_legacy_id = contract_header.partner_legacy_map(load_json(contract_header.PARTNER_EXTERNAL_MANIFEST))
    partner_exact, partner_normalized = contract_header.partner_indexes(contract_header.PARTNER_XML)
    receipt_single_counterparty = contract_header.single_receipt_counterparty_map(contract_header.RECEIPT_CSV)

    candidates: dict[str, list[dict[str, str]]] = defaultdict(list)
    blocked: list[dict[str, str]] = []
    blocker_counts: Counter[str] = Counter()
    match_type_counts: Counter[str] = Counter()

    for line_no, row in enumerate(source_rows, start=2):
        legacy_contract_id = clean(row.get("Id"))
        legacy_project_id = clean(row.get("XMID"))
        subject = clean(row.get("HTBT")) or clean(row.get("DJBH")) or clean(row.get("HTBH"))
        deleted = clean(row.get("DEL")) == "1"
        direction, counterparty = contract_header.infer_direction(row)
        project_external_id = project_external.get(legacy_project_id, "")
        partner_external_id, partner_match_type = current_partner_anchor(
            legacy_contract_id,
            counterparty,
            partner_exact,
            partner_normalized,
            receipt_single_counterparty,
            partner_by_legacy_id,
        )

        blockers: list[str] = []
        if not legacy_contract_id:
            blockers.append("missing_legacy_contract_id")
        if deleted:
            blockers.append("deleted_flag")
        if direction not in {"out", "in"}:
            blockers.append("direction_defer")
        if not project_external_id:
            blockers.append("project_anchor_missing")
        if not subject:
            blockers.append("missing_subject")
        if partner_external_id:
            blockers.append("partner_anchor_already_resolved")
        if not counterparty or not is_safe_enterprise_name(counterparty):
            blockers.append("unsafe_counterparty_name")

        if blockers:
            for blocker in blockers:
                blocker_counts[blocker] += 1
            blocked.append(
                {
                    "line_no": str(line_no),
                    "legacy_contract_id": legacy_contract_id,
                    "legacy_project_id": legacy_project_id,
                    "counterparty": counterparty,
                    "blockers": ",".join(blockers),
                }
            )
            continue

        normalized_name = contract_header.norm_name(counterparty)
        require(bool(normalized_name), f"empty normalized counterparty for contract {legacy_contract_id}")
        match_type_counts[partner_match_type] += 1
        candidates[normalized_name].append(
            {
                "legacy_contract_id": legacy_contract_id,
                "legacy_project_id": legacy_project_id,
                "counterparty": counterparty,
                "direction": direction,
                "partner_match_type": partner_match_type,
                "line_no": str(line_no),
            }
        )

    records: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for normalized_name, rows in sorted(candidates.items()):
        external_id = stable_external_id(normalized_name)
        require(external_id not in seen_ids, f"duplicate supplemental partner external id: {external_id}")
        seen_ids.add(external_id)
        names = [row["counterparty"] for row in rows]
        record = {
            "external_id": external_id,
            "legacy_identity_key": f"contract_counterparty:sc:{hashlib.sha1(normalized_name.encode('utf-8')).hexdigest()}",
            "legacy_partner_id": f"contract_counterparty:{hashlib.sha1(normalized_name.encode('utf-8')).hexdigest()[:16]}",
            "legacy_partner_source": "contract_counterparty",
            "legacy_partner_name": representative_name(names),
            "name": representative_name(names),
            "normalized_counterparty_name": normalized_name,
            "source_contract_count": len(rows),
            "source_contract_ids": sorted({row["legacy_contract_id"] for row in rows}),
            "source_project_ids": sorted({row["legacy_project_id"] for row in rows}),
            "source_direction_counts": dict(sorted(Counter(row["direction"] for row in rows).items())),
            "current_partner_match_types": dict(sorted(Counter(row["partner_match_type"] for row in rows).items())),
            "legacy_source_evidence": "tmp/raw/contract/contract.csv:T_ProjectContract_Out.FBF/CBF",
        }
        records.append(record)

    return records, blocked, blocker_counts, match_type_counts


def add_text_field(record: ET.Element, name: str, value: object) -> None:
    field = ET.SubElement(record, "field", {"name": name})
    field.text = clean(value)


def write_xml(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    root = ET.Element("odoo")
    data = ET.SubElement(root, "data", {"noupdate": "1"})
    for row in records:
        record = ET.SubElement(data, "record", {"id": row["external_id"], "model": TARGET_MODEL})
        add_text_field(record, "name", row["name"])
        add_text_field(record, "company_type", "company")
        add_text_field(record, "is_company", "1")
        add_text_field(record, "legacy_partner_id", row["legacy_partner_id"])
        add_text_field(record, "legacy_partner_source", row["legacy_partner_source"])
        add_text_field(record, "legacy_partner_name", row["legacy_partner_name"])
        add_text_field(record, "legacy_source_evidence", row["legacy_source_evidence"])
    ET.indent(root, space="  ")
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)


def generate(asset_root: Path, runtime_root: Path, source_csv: Path, expected_ready: int) -> dict[str, Any]:
    source_rows = read_source(source_csv)
    records, blocked, blocker_counts, match_type_counts = build_records(asset_root, source_rows)
    require(len(records) == expected_ready, f"ready supplemental partner count drifted: {len(records)} != {expected_ready}")

    xml_path = asset_root / XML_REL_PATH
    external_path = asset_root / EXTERNAL_REL_PATH
    validation_path = asset_root / VALIDATION_REL_PATH
    asset_manifest_path = asset_root / ASSET_MANIFEST_REL_PATH
    write_xml(xml_path, records)

    external_manifest = {
        "asset_manifest_version": "1.0",
        "asset_package_id": ASSET_PACKAGE_ID,
        "external_id_rule": {
            "legacy_key_policy": "stable_normalized_contract_counterparty_name",
            "pattern": "legacy_contract_counterparty_sc_<sha1_16_normalized_name>",
            "source": "sc",
        },
        "lane_id": LANE,
        "records": [
            {
                "external_id": row["external_id"],
                "legacy_identity_key": row["legacy_identity_key"],
                "legacy_partner_id": row["legacy_partner_id"],
                "legacy_partner_source": row["legacy_partner_source"],
                "name": row["name"],
                "normalized_counterparty_name": row["normalized_counterparty_name"],
                "source_contract_count": row["source_contract_count"],
                "source_contract_ids": row["source_contract_ids"],
                "status": "loadable",
                "target_model": TARGET_MODEL,
                "target_lookup": {"field": "xml_id", "value": row["external_id"]},
            }
            for row in records
        ],
        "summary": {
            "candidate_contract_rows": sum(int(row["source_contract_count"]) for row in records),
            "discarded_contract_rows": len(blocked),
            "loadable": len(records),
        },
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
            "counterparty_anchor_policy": "materialize_unresolved_contract_counterparty_text_only",
            "contract_inclusion_policy": "explicit_income_or_expense_and_project_anchor_required",
            "financial_semantics": "not_changed",
        },
        "screen_profile": {
            "blocked_contract_rows": len(blocked),
            "blocker_counts": dict(sorted(blocker_counts.items())),
            "candidate_contract_rows": sum(int(row["source_contract_count"]) for row in records),
            "candidate_current_partner_match_types": dict(sorted(match_type_counts.items())),
            "ready_partner_records": len(records),
        },
        "validation_gates": {
            "generate_time": [
                "contract_direction_explicit",
                "project_external_id_resolves",
                "subject_present",
                "counterparty_name_safe",
                "external_id_unique",
                "supplement_source_explicit",
                "no_partner_rank_fields",
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
                "asset_id": "contract_counterparty_partner_master_xml_v1",
                "format": "xml",
                "path": str(XML_REL_PATH),
                "record_count": len(records),
                "required": True,
                "sha256": sha256_file(xml_path),
            },
            {
                "asset_id": "contract_counterparty_partner_external_id_manifest_v1",
                "format": "json",
                "path": str(EXTERNAL_REL_PATH),
                "record_count": len(records),
                "required": True,
                "sha256": sha256_file(external_path),
            },
            {
                "asset_id": "contract_counterparty_partner_validation_manifest_v1",
                "format": "json",
                "path": str(VALIDATION_REL_PATH),
                "record_count": 1,
                "required": True,
                "sha256": sha256_file(validation_path),
            },
        ],
        "baseline_package": True,
        "counts": {
            "candidate_contract_rows": sum(int(row["source_contract_count"]) for row in records),
            "discarded_records": 0,
            "loadable_records": len(records),
            "raw_rows": len(records),
        },
        "db_writes": 0,
        "dependencies": ["partner_sc_v1"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "idempotency": {
            "conflict_policy": "update_existing_same_external_id",
            "duplicate_policy": "update_existing_same_external_id",
            "mode": "odoo_xml_external_id",
        },
        "lane": {
            "business_priority": "contract_counterparty_anchor_master",
            "lane_id": LANE,
            "layer": LAYER,
            "risk_class": "supplemental_master_data",
        },
        "load_order": [
            "contract_counterparty_partner_master_xml_v1",
            "contract_counterparty_partner_external_id_manifest_v1",
            "contract_counterparty_partner_validation_manifest_v1",
        ],
        "odoo_shell": False,
        "source_snapshot": {
            "extract_batch_id": "contract_counterparty_partner_xml_baseline_v1",
            "source_system": "sc",
            "source_tables": ["T_ProjectContract_Out"],
        },
        "target": {
            "identity_field": "external_id",
            "load_strategy": "odoo_xml_external_id",
            "model": TARGET_MODEL,
        },
        "validation_gates": [
            "contract_direction_explicit",
            "project_external_id_resolves",
            "subject_present",
            "counterparty_name_safe",
            "external_id_unique",
            "supplement_source_explicit",
            "no_db_writes",
        ],
    }
    write_json(asset_manifest_path, asset_manifest)

    runtime_root.mkdir(parents=True, exist_ok=True)
    write_json(runtime_root / "contract_counterparty_partner_blocked_v1.json", {"blocked": blocked, "blocker_counts": dict(blocker_counts)})
    return {
        "status": "PASS",
        "asset_package_id": ASSET_PACKAGE_ID,
        "candidate_contract_rows": sum(int(row["source_contract_count"]) for row in records),
        "loadable_records": len(records),
        "discarded_contract_rows": len(blocked),
        "asset_manifest_sha256": sha256_file(asset_manifest_path),
        "db_writes": 0,
        "odoo_shell": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate supplemental contract counterparty partner XML assets.")
    parser.add_argument("--asset-root", default=str(REPO_ASSET_ROOT))
    parser.add_argument("--runtime-root", default=str(RUNTIME_ROOT))
    parser.add_argument("--source", default=str(SOURCE_CSV))
    parser.add_argument("--expected-ready", type=int, default=88)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    try:
        result = generate(Path(args.asset_root), Path(args.runtime_root), Path(args.source), args.expected_ready)
    except (ContractCounterpartyPartnerAssetError, contract_header.ContractHeaderAssetError, ET.ParseError, json.JSONDecodeError) as exc:
        payload = {"status": "FAIL", "error": str(exc), "db_writes": 0, "odoo_shell": False}
        print("CONTRACT_COUNTERPARTY_PARTNER_ASSET_GENERATOR=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 1 if args.check else 0

    print("CONTRACT_COUNTERPARTY_PARTNER_ASSET_GENERATOR=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
