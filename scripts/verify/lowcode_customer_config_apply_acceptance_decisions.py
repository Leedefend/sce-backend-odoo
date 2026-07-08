# -*- coding: utf-8 -*-
"""Apply reviewed customer low-code acceptance decisions to an asset candidate.

The default mode is dry-run and writes an artifacts/backend candidate only.
Set LOWCODE_CUSTOMER_CONFIG_APPLY_ACCEPTANCE=1 to overwrite the module asset.
"""

import json
import os
from pathlib import Path


DEFAULT_DRAFT_INPUT = "artifacts/backend/lowcode_customer_config_module_asset_draft.json"
DEFAULT_DECISIONS_INPUT = "artifacts/backend/lowcode_customer_config_acceptance_decisions_template.json"
DEFAULT_OUTPUT = "artifacts/backend/lowcode_customer_config_contracts_candidate.json"
MODULE_ASSET = "addons/smart_construction_custom/data/lowcode_customer_config_contracts_v1.json"
DRAFT_SCHEMA_VERSION = "lowcode_customer_config_module_asset_draft.v1"
DECISION_SCHEMA_VERSION = "lowcode_customer_config_acceptance_decisions.v1"
ASSET_SCHEMA_VERSION = "lowcode_customer_config_contracts.v1"
TARGET_MODULE = "smart_construction_custom"
ALLOWED_DECISIONS = {"pending", "accepted", "rejected"}


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


def _records_by_key(draft):
    records = draft.get("module_asset_records") if isinstance(draft.get("module_asset_records"), list) else []
    return {
        _text(record.get("contract_key")): record
        for record in records
        if isinstance(record, dict) and _text(record.get("contract_key"))
    }


def _decision_counts(decisions):
    counts = {"pending": 0, "accepted": 0, "rejected": 0}
    for row in decisions:
        decision = _text(row.get("decision"))
        if decision in counts:
            counts[decision] += 1
    return counts


def _validate_inputs(draft, decision_payload):
    errors = []
    if draft.get("schema_version") != DRAFT_SCHEMA_VERSION:
        errors.append("draft schema_version must be %s" % DRAFT_SCHEMA_VERSION)
    if draft.get("target_module") != TARGET_MODULE:
        errors.append("draft target_module must be %s" % TARGET_MODULE)
    if decision_payload.get("schema_version") != DECISION_SCHEMA_VERSION:
        errors.append("decisions schema_version must be %s" % DECISION_SCHEMA_VERSION)
    if decision_payload.get("source_draft_schema") != DRAFT_SCHEMA_VERSION:
        errors.append("decisions source_draft_schema must be %s" % DRAFT_SCHEMA_VERSION)
    if decision_payload.get("target_module") != TARGET_MODULE:
        errors.append("decisions target_module must be %s" % TARGET_MODULE)
    if not isinstance(decision_payload.get("decisions"), list):
        errors.append("decisions must be a list")
    if errors:
        raise SystemExit("; ".join(errors))


def _accepted_records(draft, decision_payload):
    records_by_key = _records_by_key(draft)
    accepted = []
    errors = []
    seen = set()
    for index, row in enumerate(decision_payload.get("decisions") or []):
        if not isinstance(row, dict):
            errors.append("decision #%s must be an object" % index)
            continue
        key = _text(row.get("contract_key"))
        decision = _text(row.get("decision"))
        if decision not in ALLOWED_DECISIONS:
            errors.append("decision %s has invalid decision %s" % (key or index, decision or "-"))
            continue
        if not key:
            errors.append("decision #%s must declare contract_key" % index)
            continue
        if key in seen:
            errors.append("duplicate decision contract_key %s" % key)
            continue
        seen.add(key)
        record = records_by_key.get(key)
        if not record:
            errors.append("decision %s does not match any draft record" % key)
            continue
        if decision != "accepted":
            continue
        reviewer = _text(row.get("reviewer"))
        review_note = _text(row.get("review_note"))
        if not reviewer or not review_note:
            errors.append("accepted decision %s must include reviewer and review_note" % key)
            continue
        if _text(row.get("payload_hash")) != _text(record.get("payload_hash")):
            errors.append("accepted decision %s payload_hash does not match draft record" % key)
            continue
        if _text(record.get("source_status")) != "tenant_runtime":
            errors.append("accepted decision %s must be tenant_runtime" % key)
            continue
        accepted_record = dict(record)
        accepted_record["accepted_by"] = reviewer
        accepted_record["acceptance_note"] = review_note
        accepted_record["acceptance_source"] = DECISION_SCHEMA_VERSION
        accepted.append(accepted_record)
    if errors:
        raise SystemExit("; ".join(errors))
    return accepted


def build_asset(draft, decision_payload):
    _validate_inputs(draft, decision_payload)
    decisions = [row for row in decision_payload.get("decisions") or [] if isinstance(row, dict)]
    accepted = sorted(_accepted_records(draft, decision_payload), key=lambda row: _text(row.get("contract_key")))
    counts = _decision_counts(decisions)
    return {
        "schema_version": ASSET_SCHEMA_VERSION,
        "artifact_status": "accepted_module_asset",
        "source_draft_schema": DRAFT_SCHEMA_VERSION,
        "source_decision_schema": DECISION_SCHEMA_VERSION,
        "target_module": TARGET_MODULE,
        "promotion_boundary": {
            "source": "reviewed low-code customer acceptance decisions",
            "target_model": "ui.business.config.contract",
            "rule": "Only accepted decisions with reviewer, review_note, matching payload_hash, and tenant_runtime source_status are included.",
        },
        "summary": {
            "decision_count": len(decisions),
            "accepted_count": len(accepted),
            "pending_count": counts["pending"],
            "rejected_count": counts["rejected"],
        },
        "accepted_contracts": accepted,
        "acceptance": {
            "required_after_adding_records": [
                "make verify.lowcode_config.boundary.guard",
                "make verify.lowcode_config.runtime_boundary.guard",
                "make verify.lowcode_config.customer_module_asset.replay.guard",
                "make verify.business_config.unit",
                "make verify.business_config.snapshot",
            ],
        },
    }


def main():
    draft_path = Path(os.getenv("LOWCODE_CUSTOMER_CONFIG_MODULE_ASSET_DRAFT_INPUT", DEFAULT_DRAFT_INPUT))
    decisions_path = Path(os.getenv("LOWCODE_CUSTOMER_CONFIG_ACCEPTANCE_DECISIONS_INPUT", DEFAULT_DECISIONS_INPUT))
    output_path = Path(os.getenv("LOWCODE_CUSTOMER_CONFIG_ACCEPTED_ASSET_OUTPUT", DEFAULT_OUTPUT))
    apply_to_module = os.getenv("LOWCODE_CUSTOMER_CONFIG_APPLY_ACCEPTANCE") == "1"
    if apply_to_module:
        output_path = Path(MODULE_ASSET)
    if not draft_path.exists():
        raise SystemExit("module asset draft artifact is missing: %s" % draft_path)
    if not decisions_path.exists():
        raise SystemExit("acceptance decisions artifact is missing: %s" % decisions_path)
    asset = build_asset(_read_json(draft_path), _read_json(decisions_path))
    _write_json(output_path, asset)
    print("[lowcode_customer_config_apply_acceptance_decisions] PASS %s" % json.dumps({
        "schema_version": asset["schema_version"],
        "target_module": asset["target_module"],
        "artifact_status": asset["artifact_status"],
        "accepted_count": asset["summary"]["accepted_count"],
        "pending_count": asset["summary"]["pending_count"],
        "rejected_count": asset["summary"]["rejected_count"],
        "apply_to_module": apply_to_module,
        "output_path": str(output_path),
    }, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
