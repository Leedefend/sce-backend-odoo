#!/usr/bin/env python3
"""Generate repository XML assets for anchored legacy contract headers."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


REPO_ASSET_ROOT = Path("migration_assets")
RUNTIME_ROOT = Path(".runtime_artifacts/migration_assets/contract_sc_v1")
SOURCE_CSV = Path("tmp/raw/contract/contract.csv")
RECEIPT_CSV = Path("tmp/raw/receipt/receipt.csv")
PROJECT_EXTERNAL_MANIFEST = REPO_ASSET_ROOT / "manifest/project_external_id_manifest_v1.json"
PARTNER_EXTERNAL_MANIFEST = REPO_ASSET_ROOT / "manifest/partner_external_id_manifest_v1.json"
CONTRACT_COUNTERPARTY_EXTERNAL_MANIFEST = REPO_ASSET_ROOT / "manifest/contract_counterparty_partner_external_id_manifest_v1.json"
PARTNER_XML = REPO_ASSET_ROOT / "10_master/partner/partner_master_v1.xml"
XML_REL_PATH = Path("20_business/contract/contract_header_v1.xml")
EXTERNAL_REL_PATH = Path("manifest/contract_external_id_manifest_v1.json")
VALIDATION_REL_PATH = Path("manifest/contract_validation_manifest_v1.json")
ASSET_MANIFEST_REL_PATH = Path("manifest/contract_asset_manifest_v1.json")
OWN_COMPANY_NAMES = {"四川保盛建设集团有限公司", "My Company"}
ORG_SUFFIXES = ("有限责任公司", "股份有限公司", "集团有限公司", "有限公司", "公司")
REQUIRED_COLUMNS = {"Id", "XMID", "FBF", "CBF"}
ASSET_PACKAGE_ID = "contract_sc_v1"
GENERATED_AT = "2026-04-15T07:45:00+00:00"


class ContractHeaderAssetError(Exception):
    pass


def clean(value: object) -> str:
    text = "" if value is None else str(value)
    text = text.replace("\u3000", " ").strip()
    return re.sub(r"\s+", " ", text)


def norm_name(value: object) -> str:
    text = re.sub(r"[（）()·,，.。/、\s\\-]", "", clean(value))
    for suffix in ORG_SUFFIXES:
        if text.endswith(suffix):
            text = text[: -len(suffix)]
            break
    return text


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractHeaderAssetError(message)


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
    require(path.exists(), f"missing contract csv: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = list(reader.fieldnames or [])
        rows = [dict(row) for row in reader]
    missing = sorted(REQUIRED_COLUMNS - set(fields))
    require(not missing, f"missing contract source columns: {missing}")
    return fields, rows


def project_map(manifest: dict[str, Any]) -> dict[str, str]:
    result: dict[str, str] = {}
    for row in manifest.get("records", []):
        legacy_id = clean(row.get("target_lookup", {}).get("value"))
        external_id = clean(row.get("external_id"))
        if legacy_id and external_id and row.get("status") == "loadable":
            result[legacy_id] = external_id
    require(result, "project external id map is empty")
    return result


def partner_legacy_map(manifest: dict[str, Any]) -> dict[str, str]:
    result: dict[str, str] = {}
    for row in manifest.get("records", []):
        legacy_id = clean(row.get("legacy_partner_id"))
        external_id = clean(row.get("external_id"))
        if legacy_id and external_id and row.get("status") == "loadable":
            result[legacy_id] = external_id
    require(result, "partner legacy id map is empty")
    return result


def supplemental_counterparty_map(manifest: dict[str, Any]) -> dict[str, str]:
    result: dict[str, str] = {}
    for row in manifest.get("records", []):
        normalized_name = clean(row.get("normalized_counterparty_name"))
        external_id = clean(row.get("external_id"))
        if normalized_name and external_id and row.get("status") == "loadable":
            result[normalized_name] = external_id
    require(result, "supplemental contract counterparty map is empty")
    return result


def partner_indexes(partner_xml: Path) -> tuple[dict[str, list[dict[str, str]]], dict[str, list[dict[str, str]]]]:
    require(partner_xml.exists(), f"missing partner xml: {partner_xml}")
    exact: dict[str, list[dict[str, str]]] = {}
    normalized: dict[str, list[dict[str, str]]] = {}
    root = ET.parse(partner_xml).getroot()
    for record in root.findall(".//record"):
        xml_id = clean(record.attrib.get("id"))
        fields = {field.attrib.get("name", ""): clean(field.text) for field in record.findall("field")}
        name = clean(fields.get("name"))
        if not xml_id or not name:
            continue
        item = {
            "external_id": xml_id,
            "name": name,
            "vat": clean(fields.get("vat")),
        }
        exact.setdefault(name, []).append(item)
        normalized.setdefault(norm_name(name), []).append(item)
    require(exact, "partner xml index is empty")
    return exact, normalized


def single_receipt_counterparty_map(receipt_csv: Path) -> dict[str, str]:
    require(receipt_csv.exists(), f"missing receipt evidence csv: {receipt_csv}")
    candidates: dict[str, set[str]] = {}
    with receipt_csv.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            contract_id = clean(row.get("SGHTID"))
            partner_id = clean(row.get("WLDWID"))
            if contract_id and partner_id:
                candidates.setdefault(contract_id, set()).add(partner_id)
    return {contract_id: next(iter(partner_ids)) for contract_id, partner_ids in candidates.items() if len(partner_ids) == 1}


def receipt_contract_evidence_map(receipt_csv: Path) -> dict[str, dict[str, str]]:
    require(receipt_csv.exists(), f"missing receipt evidence csv: {receipt_csv}")
    candidates: dict[str, list[dict[str, str]]] = {}
    with receipt_csv.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            for field in ("SGHTID", "GLHTID", "HTID"):
                contract_id = clean(row.get(field))
                if contract_id:
                    candidates.setdefault(contract_id, []).append(row)
    result: dict[str, dict[str, str]] = {}
    for contract_id, rows in candidates.items():
        partner_ids = {clean(row.get("WLDWID")) for row in rows if clean(row.get("WLDWID"))}
        partner_names = {clean(row.get("WLDWMC")) for row in rows if clean(row.get("WLDWMC"))}
        if len(partner_ids) == 1:
            result[contract_id] = {
                "receipt_reference_count": str(len(rows)),
                "receipt_partner_id": next(iter(partner_ids)),
                "receipt_partner_name": sorted(partner_names)[0] if partner_names else "",
            }
    return result


def infer_direction(row: dict[str, str]) -> tuple[str, str]:
    fbf = clean(row.get("FBF"))
    cbf = clean(row.get("CBF"))
    if cbf in OWN_COMPANY_NAMES and fbf not in OWN_COMPANY_NAMES:
        return "out", fbf
    if fbf in OWN_COMPANY_NAMES and cbf not in OWN_COMPANY_NAMES:
        return "in", cbf
    return "defer", ""


def parse_date(value: object) -> str:
    text = clean(value)
    if not text or text in {"/", "0"}:
        return ""
    for fmt in ("%m/%d/%Y %H:%M:%S", "%m/%d/%Y", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            continue
    return ""


def safe_external_suffix(value: str) -> str:
    suffix = re.sub(r"[^0-9A-Za-z_]+", "_", value).strip("_").lower()
    require(bool(suffix), "cannot build external id from blank legacy_contract_id")
    return suffix


def canonical_nonempty_vat(matches: list[dict[str, str]]) -> str:
    nonempty = [item for item in matches if item.get("vat")]
    if len(nonempty) == 1:
        return nonempty[0]["external_id"]
    vats = {item["vat"] for item in nonempty}
    if len(vats) == 1 and nonempty:
        return sorted(item["external_id"] for item in nonempty)[0]
    return ""


def resolve_partner(
    counterparty: str,
    exact: dict[str, list[dict[str, str]]],
    normalized: dict[str, list[dict[str, str]]],
) -> tuple[str, str]:
    exact_matches = exact.get(counterparty, []) if counterparty else []
    normalized_matches = normalized.get(norm_name(counterparty), []) if counterparty else []
    matches = exact_matches or normalized_matches
    if len(matches) == 1:
        return matches[0]["external_id"], "exact" if exact_matches else "normalized"
    if not matches:
        return "", "missing"
    canonical = canonical_nonempty_vat(matches)
    if canonical:
        return canonical, "canonical_nonempty_vat"
    return "", "ambiguous"


def add_text_field(record: ET.Element, name: str, value: object) -> None:
    text = clean(value)
    if not text:
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
        record = ET.SubElement(data, "record", {"id": row["external_id"], "model": "construction.contract"})
        add_text_field(record, "legacy_contract_id", row["legacy_contract_id"])
        add_text_field(record, "legacy_project_id", row["legacy_project_id"])
        add_text_field(record, "legacy_document_no", row["legacy_document_no"])
        add_text_field(record, "legacy_contract_no", row["legacy_contract_no"])
        add_text_field(record, "legacy_external_contract_no", row["legacy_external_contract_no"])
        add_text_field(record, "legacy_status", row["legacy_status"])
        add_text_field(record, "legacy_deleted_flag", row["legacy_deleted_flag"])
        add_text_field(record, "legacy_counterparty_text", row["legacy_counterparty_text"])
        add_text_field(record, "subject", row["subject"])
        add_text_field(record, "type", row["contract_type"])
        add_ref_field(record, "project_id", row["project_external_id"])
        add_ref_field(record, "partner_id", row["partner_external_id"])
        add_text_field(record, "name_short", row["name_short"])
        add_text_field(record, "date_contract", row["date_contract"])
        add_text_field(record, "date_start", row["date_start"])
        add_text_field(record, "date_end", row["date_end"])
    ET.indent(root, space="  ")
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)


def generate(asset_root: Path, runtime_root: Path, source_csv: Path, expected_ready: int) -> dict[str, Any]:
    _fields, source_rows = read_source(source_csv)
    project_external = project_map(load_json(PROJECT_EXTERNAL_MANIFEST))
    partner_by_legacy_id = partner_legacy_map(load_json(PARTNER_EXTERNAL_MANIFEST))
    supplemental_counterparty_by_name = supplemental_counterparty_map(load_json(CONTRACT_COUNTERPARTY_EXTERNAL_MANIFEST))
    partner_exact, partner_normalized = partner_indexes(PARTNER_XML)
    receipt_single_counterparty = single_receipt_counterparty_map(RECEIPT_CSV)
    receipt_contract_evidence = receipt_contract_evidence_map(RECEIPT_CSV)
    counters: Counter[str] = Counter()
    direction_counts: Counter[str] = Counter()
    partner_match_counts: Counter[str] = Counter()
    contract_ids: Counter[str] = Counter()
    loadable: list[dict[str, str]] = []
    blocked: list[dict[str, str]] = []

    for line_no, row in enumerate(source_rows, start=2):
        legacy_contract_id = clean(row.get("Id"))
        legacy_project_id = clean(row.get("XMID"))
        subject = clean(row.get("HTBT")) or clean(row.get("DJBH")) or clean(row.get("HTBH"))
        deleted = clean(row.get("DEL")) == "1"
        direction, counterparty = infer_direction(row)
        direction_source = "party_role"
        receipt_direction_evidence = receipt_contract_evidence.get(legacy_contract_id, {})
        if direction == "defer" and receipt_direction_evidence:
            direction = "in"
            direction_source = "receipt_contract_reference"
            counterparty = (
                clean(receipt_direction_evidence.get("receipt_partner_name"))
                or clean(row.get("FBF"))
                or clean(row.get("CBF"))
            )
        direction_counts[direction] += 1
        project_external_id = project_external.get(legacy_project_id)
        partner_external_id, partner_match_type = resolve_partner(counterparty, partner_exact, partner_normalized)
        receipt_partner_id = ""
        if not partner_external_id and legacy_contract_id:
            receipt_partner_id = receipt_single_counterparty.get(legacy_contract_id, "")
            receipt_partner_external_id = partner_by_legacy_id.get(receipt_partner_id, "")
            if receipt_partner_external_id:
                partner_external_id = receipt_partner_external_id
                partner_match_type = "receipt_single_counterparty"
        if not partner_external_id and counterparty:
            supplemental_partner_external_id = supplemental_counterparty_by_name.get(norm_name(counterparty), "")
            if supplemental_partner_external_id:
                partner_external_id = supplemental_partner_external_id
                partner_match_type = f"contract_counterparty_supplement_{partner_match_type}"
        partner_match_counts[partner_match_type] += 1

        blockers: list[str] = []
        if not legacy_contract_id:
            blockers.append("missing_legacy_contract_id")
        if deleted:
            blockers.append("deleted_flag")
        if direction not in {"out", "in"}:
            blockers.append("direction_defer")
        if not project_external_id:
            blockers.append("project_anchor_missing")
        if not partner_external_id:
            blockers.append("partner_anchor_missing" if partner_match_type == "missing" else "partner_anchor_ambiguous")
        if not subject:
            blockers.append("missing_subject")

        if blockers:
            for blocker in blockers:
                counters[blocker] += 1
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

        contract_ids[legacy_contract_id] += 1
        loadable.append(
            {
                "external_id": f"legacy_contract_sc_{safe_external_suffix(legacy_contract_id)}",
                "legacy_contract_id": legacy_contract_id,
                "legacy_project_id": legacy_project_id,
                "legacy_document_no": clean(row.get("DJBH")),
                "legacy_contract_no": clean(row.get("HTBH")),
                "legacy_external_contract_no": clean(row.get("f_WBHTBH")) or clean(row.get("PID")),
                "legacy_status": clean(row.get("DJZT")),
                "legacy_deleted_flag": clean(row.get("DEL")) or "0",
                "legacy_counterparty_text": counterparty,
                "subject": subject,
                "contract_type": direction,
                "project_external_id": project_external_id or "",
                "partner_external_id": partner_external_id,
                "partner_match_type": partner_match_type,
                "direction_source": direction_source,
                "receipt_direction_reference_count": receipt_direction_evidence.get("receipt_reference_count", ""),
                "receipt_counterparty_partner_id": receipt_partner_id,
                "name_short": clean(row.get("f_XMJC")),
                "date_contract": parse_date(row.get("f_HTDLRQ")) or parse_date(row.get("f_HTGDRQ")),
                "date_start": parse_date(row.get("f_GCKGRQ")),
                "date_end": parse_date(row.get("JGRQ")),
            }
        )

    duplicate_contract_ids = sorted(key for key, count in contract_ids.items() if count > 1)
    require(not duplicate_contract_ids, f"duplicate loadable contract ids: {duplicate_contract_ids[:10]}")
    require(len({row["external_id"] for row in loadable}) == len(loadable), "duplicate XML external ids")
    require(len(loadable) == expected_ready, f"ready contract count drifted: {len(loadable)} != {expected_ready}")
    loadable_partner_anchor_sources = Counter(row["partner_match_type"] for row in loadable)

    xml_path = asset_root / XML_REL_PATH
    external_path = asset_root / EXTERNAL_REL_PATH
    validation_path = asset_root / VALIDATION_REL_PATH
    asset_manifest_path = asset_root / ASSET_MANIFEST_REL_PATH
    write_xml(xml_path, loadable)

    external_manifest = {
        "asset_manifest_version": "1.0",
        "asset_package_id": ASSET_PACKAGE_ID,
        "external_id_rule": {
            "legacy_key_policy": "stable_legacy_contract_pk",
            "pattern": "legacy_contract_sc_<legacy_contract_id>",
            "source": "sc",
        },
        "lane_id": "contract",
        "records": [
            {
                "contract_type": row["contract_type"],
                "external_id": row["external_id"],
                "legacy_contract_id": row["legacy_contract_id"],
                "legacy_project_id": row["legacy_project_id"],
                "partner_external_id": row["partner_external_id"],
                "partner_anchor_source": row["partner_match_type"],
                "direction_source": row["direction_source"],
                "receipt_direction_reference_count": row["receipt_direction_reference_count"],
                "project_external_id": row["project_external_id"],
                "receipt_counterparty_partner_id": row["receipt_counterparty_partner_id"],
                "status": "loadable",
                "target_model": "construction.contract",
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
        "target_model": "construction.contract",
        "tax_policy": {
            "xml_tax_id": "omitted",
            "source_contract_tax_rows": 0,
            "target_default": "construction.contract.create_by_type",
        },
        "validation_gates": {
            "generate_time": [
                "legacy_contract_id_unique",
                "project_external_id_resolves",
                "partner_external_id_resolves",
                "contract_counterparty_supplement_resolves",
                "receipt_contract_reference_direction_resolves",
                "receipt_single_counterparty_anchor_resolves",
                "deleted_rows_excluded",
                "direction_resolved",
                "tax_id_omitted_target_default",
            ],
            "postload": ["xml_external_id_resolves", "project_id_ref_resolves", "partner_id_ref_resolves"],
        },
        "screen_profile": {
            "blocked_rows": len(blocked),
            "blocker_counts": dict(sorted(counters.items())),
            "direction_counts": dict(sorted(direction_counts.items())),
            "partner_match_counts": dict(sorted(partner_match_counts.items())),
            "ready_anchor_rows": len(loadable),
            "loadable_partner_anchor_sources": dict(sorted(loadable_partner_anchor_sources.items())),
            "receipt_direction_recovered_rows": sum(1 for row in loadable if row["direction_source"] == "receipt_contract_reference"),
            "receipt_evidence_recovered_rows": loadable_partner_anchor_sources["receipt_single_counterparty"],
        },
    }
    write_json(validation_path, validation_manifest)

    asset_manifest = {
        "asset_manifest_version": "1.0",
        "asset_package_id": ASSET_PACKAGE_ID,
        "assets": [
            {
                "asset_id": "contract_header_xml_v1",
                "format": "xml",
                "path": str(XML_REL_PATH),
                "record_count": len(loadable),
                "required": True,
                "sha256": sha256_file(xml_path),
            },
            {
                "asset_id": "contract_external_id_manifest_v1",
                "format": "json",
                "path": str(EXTERNAL_REL_PATH),
                "record_count": len(loadable),
                "required": True,
                "sha256": sha256_file(external_path),
            },
            {
                "asset_id": "contract_validation_manifest_v1",
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
        "dependencies": ["project_sc_v1", "partner_sc_v1", "contract_counterparty_partner_sc_v1"],
        "generated_at": GENERATED_AT,
        "idempotency": {
            "conflict_policy": "block_package",
            "duplicate_policy": "update_existing_same_external_id",
            "mode": "odoo_xml_external_id",
        },
        "lane": {
            "business_priority": "business_header_fact",
            "lane_id": "contract",
            "layer": "20_business",
            "risk_class": "anchored_subset",
        },
        "load_order": [
            "contract_header_xml_v1",
            "contract_external_id_manifest_v1",
            "contract_validation_manifest_v1",
        ],
        "odoo_shell": False,
        "source_snapshot": {
            "extract_batch_id": "contract_header_xml_baseline_v1",
            "source_system": "sc",
            "source_tables": ["T_ProjectContract_Out"],
        },
        "target": {
            "identity_field": "legacy_contract_id",
            "load_strategy": "odoo_xml_external_id",
            "model": "construction.contract",
        },
        "validation_gates": [
            "source_contract_file_exists",
            "required_source_headers_present",
            "legacy_contract_id_non_empty",
            "legacy_contract_id_unique",
            "project_anchor_resolves",
            "partner_anchor_resolves",
            "contract_counterparty_supplement_resolves",
            "receipt_contract_reference_direction_resolves",
            "receipt_single_counterparty_anchor_resolves",
            "tax_id_omitted_target_default",
        ],
    }
    write_json(asset_manifest_path, asset_manifest)

    runtime_root.mkdir(parents=True, exist_ok=True)
    write_json(runtime_root / "contract_blocked_v1.json", {"blocked": blocked, "blocker_counts": dict(counters)})
    return {
        "status": "PASS",
        "asset_package_id": ASSET_PACKAGE_ID,
        "db_writes": 0,
        "odoo_shell": False,
        "raw_rows": len(source_rows),
        "loadable_records": len(loadable),
        "blocked_records": len(blocked),
        "receipt_evidence_recovered_records": loadable_partner_anchor_sources["receipt_single_counterparty"],
        "asset_manifest_sha256": sha256_file(asset_manifest_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate contract header XML migration assets.")
    parser.add_argument("--asset-root", default=str(REPO_ASSET_ROOT))
    parser.add_argument("--runtime-root", default=str(RUNTIME_ROOT))
    parser.add_argument("--source", default=str(SOURCE_CSV))
    parser.add_argument("--expected-ready", type=int, default=1492)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    try:
        result = generate(Path(args.asset_root), Path(args.runtime_root), Path(args.source), args.expected_ready)
    except (ContractHeaderAssetError, ET.ParseError, json.JSONDecodeError) as exc:
        payload = {"status": "FAIL", "error": str(exc), "db_writes": 0, "odoo_shell": False}
        print("CONTRACT_HEADER_ASSET_GENERATOR=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 1 if args.check else 0

    print("CONTRACT_HEADER_ASSET_GENERATOR=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
