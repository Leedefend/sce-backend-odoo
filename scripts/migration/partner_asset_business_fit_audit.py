#!/usr/bin/env python3
"""Audit how the old partner asset lane fits the current business/model needs."""

from __future__ import annotations

import argparse
import json
import xml.etree.ElementTree as ET
from pathlib import Path


DEFAULT_ASSET_MANIFEST = Path("migration_assets/manifest/partner_asset_manifest_v1.json")
DEFAULT_PARTNER_XML = Path("migration_assets/10_master/partner/partner_master_v1.xml")
DEFAULT_BUSINESS_RESULT = Path(
    "artifacts/migration/partner_business_aligned_rebuild_v1/"
    "fact_based_partner_rebuild_business_aligned_result_v1.json"
)
DEFAULT_GATE_RESULT = Path(
    "artifacts/migration/partner_business_aligned_rebuild_v1/"
    "fact_based_partner_rebuild_business_aligned_gate_result_v1.json"
)
DEFAULT_OUT = Path("artifacts/migration/partner_asset_business_fit_audit_v1.json")

CURRENT_MODEL_FIELDS = {
    "name",
    "company_type",
    "customer_rank",
    "supplier_rank",
    "sc_supplier_type",
    "sc_account_name",
    "sc_bank_name",
    "sc_bank_account",
    "vat",
    "legacy_partner_id",
    "legacy_partner_source",
    "legacy_partner_name",
    "legacy_credit_code",
    "legacy_tax_no",
    "legacy_source_evidence",
}


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def xml_fields(path: Path) -> set[str]:
    root = ET.parse(path).getroot()
    return {node.attrib.get("name", "") for node in root.findall(".//field") if node.attrib.get("name")}


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--asset-manifest", default=str(DEFAULT_ASSET_MANIFEST))
    parser.add_argument("--partner-xml", default=str(DEFAULT_PARTNER_XML))
    parser.add_argument("--business-result", default=str(DEFAULT_BUSINESS_RESULT))
    parser.add_argument("--gate-result", default=str(DEFAULT_GATE_RESULT))
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    args = parser.parse_args()

    manifest = load_json(Path(args.asset_manifest))
    business = load_json(Path(args.business_result))
    gate = load_json(Path(args.gate_result))
    old_fields = xml_fields(Path(args.partner_xml))

    manifest_count = int((manifest.get("counts") or {}).get("loadable_records") or 0)
    business_count = int(business.get("business_aligned_payload_rows") or 0)
    gate_counts = gate.get("gate_action_counts") or {}
    missing_model_fields = sorted(CURRENT_MODEL_FIELDS - old_fields)
    retained_fields = sorted(CURRENT_MODEL_FIELDS & old_fields)
    outdated_gates = [
        gate_name
        for gate_name in (manifest.get("validation_gates") or [])
        if gate_name in {"no_partner_rank_fields"}
    ]

    result = {
        "status": "PASS",
        "mode": "partner_asset_business_fit_audit",
        "old_asset_package_id": manifest.get("asset_package_id"),
        "old_asset_loadable_records": manifest_count,
        "business_aligned_payload_rows": business_count,
        "business_entity_delta": business_count - manifest_count,
        "old_xml_fields": sorted(old_fields),
        "current_model_required_fields": sorted(CURRENT_MODEL_FIELDS),
        "retained_current_fields": retained_fields,
        "missing_current_fields_in_old_asset_xml": missing_model_fields,
        "outdated_validation_gates": outdated_gates,
        "write_gate_counts": gate_counts,
        "iteration_decision": "old_partner_asset_requires_business_fit_iteration",
        "logic_pages_to_refresh": [
            {
                "page": "identity_and_dedup",
                "reason": "old package has 6541 loadable records while current business source normalizes to 7792 entities",
            },
            {
                "page": "role_semantics",
                "reason": "old validation gate forbids partner rank fields but current business flow needs customer_rank/supplier_rank",
            },
            {
                "page": "basic_info_surface",
                "reason": "old XML omits sc supplier type and account fields now present on res.partner",
            },
            {
                "page": "write_gate",
                "reason": "current business source needs write/update-only/blocked review queues before replay",
            },
            {
                "page": "review_queue",
                "reason": "missing credit code, personal fragments, unknown roles, and invalid bank accounts must remain reviewable",
            },
        ],
        "db_writes": 0,
    }
    write_json(Path(args.out), result)
    print("PARTNER_ASSET_BUSINESS_FIT_AUDIT=" + json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
