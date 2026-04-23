#!/usr/bin/env python3
"""Screen contract blockers for deterministic partner-anchor recovery."""

from __future__ import annotations

import argparse
import csv
import json
import re
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


CONTRACT_CSV = Path("tmp/raw/contract/contract.csv")
PROJECT_EXTERNAL = Path("migration_assets/manifest/project_external_id_manifest_v1.json")
CONTRACT_EXTERNAL = Path("migration_assets/manifest/contract_external_id_manifest_v1.json")
PARTNER_XML = Path("migration_assets/10_master/partner/partner_master_v1.xml")
OUTPUT_JSON = Path(".runtime_artifacts/migration_assets/contract_blocker_recovery_screen_v1.json")
OWN_COMPANY_NAMES = {"四川保盛建设集团有限公司", "My Company"}
ORG_SUFFIXES = ("有限责任公司", "股份有限公司", "集团有限公司", "有限公司", "公司")


class ContractBlockerScreenError(Exception):
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
        raise ContractBlockerScreenError(message)


def read_csv(path: Path) -> list[dict[str, str]]:
    require(path.exists(), f"missing csv file: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def load_json(path: Path) -> dict[str, Any]:
    require(path.exists(), f"missing json file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def project_ids() -> set[str]:
    return {
        clean(row.get("target_lookup", {}).get("value"))
        for row in load_json(PROJECT_EXTERNAL).get("records", [])
        if row.get("status") == "loadable" and clean(row.get("target_lookup", {}).get("value"))
    }


def loaded_contract_ids() -> set[str]:
    return {
        clean(row.get("legacy_contract_id"))
        for row in load_json(CONTRACT_EXTERNAL).get("records", [])
        if row.get("status") == "loadable" and clean(row.get("legacy_contract_id"))
    }


def partner_indexes() -> tuple[dict[str, list[dict[str, str]]], dict[str, list[dict[str, str]]]]:
    require(PARTNER_XML.exists(), f"missing partner xml: {PARTNER_XML}")
    exact: dict[str, list[dict[str, str]]] = defaultdict(list)
    normalized: dict[str, list[dict[str, str]]] = defaultdict(list)
    root = ET.parse(PARTNER_XML).getroot()
    for record in root.findall(".//record"):
        fields = {field.attrib.get("name", ""): clean(field.text) for field in record.findall("field")}
        item = {
            "external_id": clean(record.attrib.get("id")),
            "name": clean(fields.get("name")),
            "vat": clean(fields.get("vat")),
            "legacy_partner_id": clean(fields.get("legacy_partner_id")),
        }
        if item["external_id"] and item["name"]:
            exact[item["name"]].append(item)
            normalized[norm_name(item["name"])].append(item)
    return exact, normalized


def infer_direction(row: dict[str, str]) -> tuple[str, str]:
    fbf = clean(row.get("FBF"))
    cbf = clean(row.get("CBF"))
    if cbf in OWN_COMPANY_NAMES and fbf not in OWN_COMPANY_NAMES:
        return "out", fbf
    if fbf in OWN_COMPANY_NAMES and cbf not in OWN_COMPANY_NAMES:
        return "in", cbf
    return "defer", ""


def canonical_nonempty_vat(matches: list[dict[str, str]]) -> str:
    nonempty = [item for item in matches if item.get("vat")]
    if len(nonempty) == 1:
        return nonempty[0]["external_id"]
    vats = {item["vat"] for item in nonempty}
    if len(vats) == 1 and nonempty:
        return sorted(item["external_id"] for item in nonempty)[0]
    return ""


def screen() -> dict[str, Any]:
    projects = project_ids()
    loaded_contracts = loaded_contract_ids()
    exact_partner, normalized_partner = partner_indexes()
    counters: Counter[str] = Counter()
    recovery_samples: list[dict[str, str]] = []

    for row in read_csv(CONTRACT_CSV):
        legacy_contract_id = clean(row.get("Id"))
        if legacy_contract_id in loaded_contracts:
            continue
        legacy_project_id = clean(row.get("XMID"))
        subject = clean(row.get("HTBT")) or clean(row.get("DJBH")) or clean(row.get("HTBH"))
        deleted = clean(row.get("DEL")) == "1"
        direction, counterparty = infer_direction(row)
        blockers: list[str] = []
        if not legacy_contract_id:
            blockers.append("missing_legacy_contract_id")
        if deleted:
            blockers.append("deleted_flag")
        if direction not in {"out", "in"}:
            blockers.append("direction_defer")
        if not legacy_project_id or legacy_project_id not in projects:
            blockers.append("project_anchor_missing")
        if not subject:
            blockers.append("missing_subject")

        matches = (exact_partner.get(counterparty, []) or normalized_partner.get(norm_name(counterparty), [])) if counterparty else []
        if not matches:
            blockers.append("partner_anchor_missing")
        elif len(matches) > 1:
            canonical = canonical_nonempty_vat(matches)
            if blockers:
                blockers.append("partner_anchor_ambiguous")
            elif canonical:
                counters["recoverable_partner_unique_nonempty_vat"] += 1
                if len(recovery_samples) < 20:
                    recovery_samples.append(
                        {
                            "legacy_contract_id": legacy_contract_id,
                            "counterparty": counterparty,
                            "candidate_count": str(len(matches)),
                            "canonical_partner_external_id": canonical,
                        }
                    )
                continue
            else:
                blockers.append("partner_anchor_ambiguous")

        if not blockers:
            counters["unexpected_ready_not_loaded"] += 1
            continue
        if blockers == ["partner_anchor_ambiguous"]:
            counters["blocked_partner_ambiguous_no_deterministic_identity"] += 1
        elif blockers == ["partner_anchor_missing"]:
            counters["blocked_partner_missing"] += 1
        else:
            counters["blocked_other_or_multi_reason"] += 1

    payload = {
        "status": "PASS",
        "mode": "contract_blocker_recovery_screen",
        "db_writes": 0,
        "odoo_shell": False,
        "current_loaded_contracts": len(loaded_contracts),
        "recovery_route_counts": dict(sorted(counters.items())),
        "recovery_samples": recovery_samples,
        "decision": "deterministic_partner_recovery_candidates_found"
        if counters["recoverable_partner_unique_nonempty_vat"]
        else "no_deterministic_recovery_candidates",
        "next_step": "expand contract header asset with unique non-empty VAT canonical partner route"
        if counters["recoverable_partner_unique_nonempty_vat"]
        else "keep contract blockers deferred",
    }
    write_json(OUTPUT_JSON, payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Screen contract blocker recovery candidates.")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        payload = screen()
    except (ContractBlockerScreenError, json.JSONDecodeError, ET.ParseError) as exc:
        result = {"status": "FAIL", "error": str(exc), "db_writes": 0, "odoo_shell": False}
        print("CONTRACT_BLOCKER_RECOVERY_SCREEN=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 1 if args.check else 0
    print(
        "CONTRACT_BLOCKER_RECOVERY_SCREEN="
        + json.dumps(
            {
                "status": payload["status"],
                "recovery_route_counts": payload["recovery_route_counts"],
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
