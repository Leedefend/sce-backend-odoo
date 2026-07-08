# -*- coding: utf-8 -*-
"""Build a review-only customer-module low-code asset draft.

This script consumes the runtime candidate export produced by
lowcode_customer_config_baseline_candidate.py and converts it into a structured
draft for smart_construction_custom promotion review. It intentionally does not
write module data.
"""

import hashlib
import json
import os
from pathlib import Path


DEFAULT_INPUT = "artifacts/backend/lowcode_customer_config_baseline_candidate.json"
DEFAULT_OUTPUT = "artifacts/backend/lowcode_customer_config_module_asset_draft.json"
TARGET_MODULE = "smart_construction_custom"
TARGET_ASSET = "addons/smart_construction_custom/data/lowcode_customer_config_contracts_v1.json"
SCHEMA_VERSION = "lowcode_customer_config_module_asset_draft.v1"
SOURCE_SCHEMA_VERSION = "lowcode_customer_config_baseline_candidate.v1"
REQUIRED_REVIEW_STATUSES = {"tenant_runtime"}


def _read_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")


def _text(value):
    return str(value or "").strip()


def _payload_hash(payload) -> str:
    return hashlib.sha256(
        json.dumps(payload if isinstance(payload, dict) else {}, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _iter_candidate_contracts(candidate):
    for surface in candidate.get("surfaces") or []:
        if not isinstance(surface, dict):
            continue
        surface_name = _text(surface.get("surface"))
        for contract in surface.get("contracts") or []:
            if isinstance(contract, dict):
                yield surface_name, contract


def _module_record(surface, contract):
    contract_json = contract.get("contract_json") if isinstance(contract.get("contract_json"), dict) else {}
    return {
        "contract_key": _text(contract.get("contract_key")),
        "surface": surface,
        "name": _text(contract.get("name")),
        "model": _text(contract.get("model")),
        "view_type": _text(contract.get("view_type")),
        "action_id": int(contract.get("action_id") or 0),
        "view_id": int(contract.get("view_id") or 0),
        "role_key": _text(contract.get("role_key")),
        "source_status": _text(contract.get("source_status")),
        "payload_hash": _text(contract.get("payload_hash")) or _payload_hash(contract_json),
        "contract_json": contract_json,
    }


def _surface_counts(records):
    counts = {}
    for record in records:
        surface = record["surface"]
        counts[surface] = counts.get(surface, 0) + 1
    return dict(sorted(counts.items()))


def _review_findings(records):
    findings = []
    invalid_statuses = sorted({record["source_status"] for record in records if record["source_status"] not in REQUIRED_REVIEW_STATUSES})
    if invalid_statuses:
        findings.append({
            "severity": "blocker",
            "code": "unexpected_source_status",
            "message": "Module asset draft may only include tenant_runtime contracts before manual promotion review.",
            "actual_source_statuses": invalid_statuses,
        })
    duplicate_keys = sorted(
        key for key in {record["contract_key"] for record in records}
        if key and sum(1 for item in records if item["contract_key"] == key) > 1
    )
    if duplicate_keys:
        findings.append({
            "severity": "blocker",
            "code": "duplicate_contract_key",
            "message": "Module asset draft contains duplicate replay keys.",
            "contract_keys": duplicate_keys,
        })
    return findings


def build_draft(candidate):
    if candidate.get("schema_version") != SOURCE_SCHEMA_VERSION:
        raise SystemExit("candidate schema_version must be %s" % SOURCE_SCHEMA_VERSION)
    if candidate.get("target_module") != TARGET_MODULE:
        raise SystemExit("candidate target_module must be %s" % TARGET_MODULE)
    records = sorted(
        (_module_record(surface, contract) for surface, contract in _iter_candidate_contracts(candidate)),
        key=lambda item: (item["surface"], item["model"], item["view_type"], item["action_id"], item["view_id"], item["role_key"], item["name"]),
    )
    findings = _review_findings(records)
    return {
        "schema_version": SCHEMA_VERSION,
        "source_candidate_schema": SOURCE_SCHEMA_VERSION,
        "target_module": TARGET_MODULE,
        "artifact_status": "review_required",
        "not_applied_to_module": True,
        "promotion_boundary": {
            "source": "ui.business.config.contract tenant_runtime rows",
            "target_asset": TARGET_ASSET,
            "rule": "This artifact is a module asset draft only. A reviewer must accept rows before adding an initializer, migration, or JSON module asset.",
        },
        "summary": {
            "candidate_contract_count": int(candidate.get("summary", {}).get("candidate_contract_count") or len(records)),
            "draft_contract_count": len(records),
            "draft_surface_counts": _surface_counts(records),
            "review_finding_count": len(findings),
        },
        "proposed_assets": [
            {
                "path": TARGET_ASSET,
                "schema_version": "lowcode_customer_config_contracts.v1",
                "status": "draft_not_committed",
                "record_count": len(records),
                "requires_initializer": "sc.user.preference.initialization must explicitly replay accepted records idempotently.",
            }
        ],
        "required_review": [
            "Confirm every record is customer-confirmed configuration, not product_release behavior.",
            "Choose whether accepted records live in smart_construction_custom or a dedicated customer module.",
            "Add an idempotent replay initializer only after review acceptance.",
            "Run the full low-code boundary and business configuration verification chain after promotion.",
        ],
        "review_findings": findings,
        "module_asset_records": records,
    }


def main():
    input_path = Path(os.getenv("LOWCODE_CUSTOMER_CONFIG_BASELINE_CANDIDATE_INPUT", DEFAULT_INPUT))
    output_path = Path(os.getenv("LOWCODE_CUSTOMER_CONFIG_MODULE_ASSET_DRAFT_PATH", DEFAULT_OUTPUT))
    if not input_path.exists():
        raise SystemExit("candidate artifact is missing: %s" % input_path)
    draft = build_draft(_read_json(input_path))
    _write_json(output_path, draft)
    print("[lowcode_customer_config_module_asset_draft] PASS %s" % json.dumps({
        "schema_version": draft["schema_version"],
        "target_module": draft["target_module"],
        "artifact_status": draft["artifact_status"],
        "draft_contract_count": draft["summary"]["draft_contract_count"],
        "draft_surface_counts": draft["summary"]["draft_surface_counts"],
        "review_finding_count": draft["summary"]["review_finding_count"],
        "output_path": str(output_path),
    }, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
