#!/usr/bin/env python3
"""Screen contract rows against repository rebuild anchors without DB access."""

from __future__ import annotations

import argparse
import csv
import json
import re
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from typing import Any


OWN_COMPANY_NAMES = {"四川保盛建设集团有限公司", "My Company"}
ORG_SUFFIXES = ("有限责任公司", "股份有限公司", "集团有限公司", "有限公司", "公司")
REQUIRED_COLUMNS = {"Id", "XMID", "FBF", "CBF"}


class ContractScreenError(Exception):
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
        raise ContractScreenError(message)


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    require(path.exists(), f"missing contract csv: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), [dict(row) for row in reader]


def load_json(path: Path) -> dict[str, Any]:
    require(path.exists(), f"missing json file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def project_ids(project_manifest: dict[str, Any]) -> set[str]:
    records = project_manifest.get("records", [])
    require(isinstance(records, list), "project external manifest records must be a list")
    return {clean(row.get("target_lookup", {}).get("value")) for row in records if clean(row.get("target_lookup", {}).get("value"))}


def partner_indexes(partner_xml: Path) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    require(partner_xml.exists(), f"missing partner xml: {partner_xml}")
    exact: dict[str, list[str]] = {}
    normalized: dict[str, list[str]] = {}
    root = ET.parse(partner_xml).getroot()
    for record in root.findall(".//record"):
        xml_id = clean(record.attrib.get("id"))
        fields = {field.attrib.get("name", ""): clean(field.text) for field in record.findall("field")}
        name = clean(fields.get("name"))
        if not xml_id or not name:
            continue
        exact.setdefault(name, []).append(xml_id)
        normalized.setdefault(norm_name(name), []).append(xml_id)
    return exact, normalized


def infer_direction(row: dict[str, str]) -> tuple[str, str]:
    fbf = clean(row.get("FBF"))
    cbf = clean(row.get("CBF"))
    if cbf in OWN_COMPANY_NAMES and fbf not in OWN_COMPANY_NAMES:
        return "out", fbf
    if fbf in OWN_COMPANY_NAMES and cbf not in OWN_COMPANY_NAMES:
        return "in", cbf
    return "defer", ""


def screen(contract_path: Path, project_external_path: Path, partner_xml: Path, out_path: Path | None) -> dict[str, Any]:
    columns, rows = read_csv(contract_path)
    missing_columns = sorted(REQUIRED_COLUMNS - set(columns))
    require(not missing_columns, f"missing contract columns: {missing_columns}")
    project_anchor_ids = project_ids(load_json(project_external_path))
    exact_partner, normalized_partner = partner_indexes(partner_xml)

    counters: Counter[str] = Counter()
    direction_counts: Counter[str] = Counter()
    partner_match_counts: Counter[str] = Counter()
    project_match_counts: Counter[str] = Counter()
    ready_anchor_rows = 0
    duplicate_contract_ids = 0
    contract_id_counts: Counter[str] = Counter()

    for row in rows:
        legacy_contract_id = clean(row.get("Id"))
        if legacy_contract_id:
            contract_id_counts[legacy_contract_id] += 1
        legacy_project_id = clean(row.get("XMID"))
        subject = clean(row.get("HTBT")) or clean(row.get("DJBH")) or clean(row.get("HTBH"))
        deleted = clean(row.get("DEL")) == "1"
        direction, counterparty = infer_direction(row)
        direction_counts[direction] += 1

        project_ok = bool(legacy_project_id and legacy_project_id in project_anchor_ids)
        project_match_counts["ready" if project_ok else "missing"] += 1

        exact_matches = exact_partner.get(counterparty, []) if counterparty else []
        normalized_matches = normalized_partner.get(norm_name(counterparty), []) if counterparty else []
        partner_matches = exact_matches or normalized_matches
        if len(partner_matches) == 1:
            partner_match_type = "ready_exact" if exact_matches else "ready_normalized"
        elif not partner_matches:
            partner_match_type = "missing"
        else:
            partner_match_type = "ambiguous"
        partner_match_counts[partner_match_type] += 1

        blockers = []
        if not legacy_contract_id:
            blockers.append("missing_legacy_contract_id")
        if deleted:
            blockers.append("deleted_flag")
        if direction not in {"out", "in"}:
            blockers.append("direction_defer")
        if not project_ok:
            blockers.append("project_anchor_missing")
        if len(partner_matches) != 1:
            blockers.append("partner_anchor_missing" if not partner_matches else "partner_anchor_ambiguous")
        if not subject:
            blockers.append("missing_subject")
        for blocker in blockers:
            counters[blocker] += 1
        if not blockers:
            ready_anchor_rows += 1

    duplicate_contract_ids = sum(1 for count in contract_id_counts.values() if count > 1)
    payload = {
        "status": "PASS",
        "mode": "contract_asset_screen",
        "db_writes": 0,
        "odoo_shell": False,
        "source_rows": len(rows),
        "target_model": "construction.contract",
        "target_asset_layer": "20_business",
        "ready_anchor_rows": ready_anchor_rows,
        "blocked_rows": len(rows) - ready_anchor_rows,
        "distinct_legacy_contract_ids": len(contract_id_counts),
        "duplicate_legacy_contract_id_keys": duplicate_contract_ids,
        "direction_counts": dict(sorted(direction_counts.items())),
        "project_match_counts": dict(sorted(project_match_counts.items())),
        "partner_match_counts": dict(sorted(partner_match_counts.items())),
        "blocker_counts": dict(sorted(counters.items())),
        "contract_xml_generation": "blocked_until_tax_master_policy",
        "next_required_asset": {
            "asset_package_id": "tax_policy_or_seed_v1",
            "reason": "construction.contract requires tax_id; contract XML must not fabricate tax master references.",
        },
        "dependency_order": ["project_sc_v1", "partner_sc_v1", "tax_policy_or_seed_v1", "contract_sc_v1"],
    }
    if out_path:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Screen contract asset readiness without DB access.")
    parser.add_argument("--contract", default="tmp/raw/contract/contract.csv", help="Legacy contract CSV")
    parser.add_argument(
        "--project-external",
        default="migration_assets/manifest/project_external_id_manifest_v1.json",
        help="Project external id manifest",
    )
    parser.add_argument(
        "--partner-xml",
        default="migration_assets/10_master/partner/partner_master_v1.xml",
        help="Partner XML asset",
    )
    parser.add_argument("--out", help="Optional runtime JSON output path")
    parser.add_argument("--check", action="store_true", help="Fail non-zero on screen errors")
    args = parser.parse_args()

    try:
        payload = screen(
            Path(args.contract),
            Path(args.project_external),
            Path(args.partner_xml),
            Path(args.out) if args.out else None,
        )
    except (ContractScreenError, ET.ParseError, json.JSONDecodeError) as exc:
        result = {"status": "FAIL", "error": str(exc), "db_writes": 0, "odoo_shell": False}
        print("CONTRACT_ASSET_SCREEN=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 1 if args.check else 0

    print(
        "CONTRACT_ASSET_SCREEN="
        + json.dumps(
            {
                "status": payload["status"],
                "source_rows": payload["source_rows"],
                "ready_anchor_rows": payload["ready_anchor_rows"],
                "blocked_rows": payload["blocked_rows"],
                "contract_xml_generation": payload["contract_xml_generation"],
                "db_writes": 0,
                "odoo_shell": False,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
