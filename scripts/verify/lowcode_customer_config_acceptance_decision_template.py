# -*- coding: utf-8 -*-
"""Generate a review decision template for customer low-code module assets."""

import json
import os
from pathlib import Path


DEFAULT_DRAFT_INPUT = "artifacts/backend/lowcode_customer_config_module_asset_draft.json"
DEFAULT_OUTPUT = "artifacts/backend/lowcode_customer_config_acceptance_decisions_template.json"
DRAFT_SCHEMA_VERSION = "lowcode_customer_config_module_asset_draft.v1"
DECISION_SCHEMA_VERSION = "lowcode_customer_config_acceptance_decisions.v1"
TARGET_MODULE = "smart_construction_custom"


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


def _decision_row(record):
    return {
        "contract_key": _text(record.get("contract_key")),
        "decision": "pending",
        "reviewer": "",
        "review_note": "",
        "surface": _text(record.get("surface")),
        "name": _text(record.get("name")),
        "model": _text(record.get("model")),
        "view_type": _text(record.get("view_type")),
        "source_status": _text(record.get("source_status")),
        "payload_hash": _text(record.get("payload_hash")),
    }


def build_template(draft):
    if draft.get("schema_version") != DRAFT_SCHEMA_VERSION:
        raise SystemExit("draft schema_version must be %s" % DRAFT_SCHEMA_VERSION)
    if draft.get("target_module") != TARGET_MODULE:
        raise SystemExit("draft target_module must be %s" % TARGET_MODULE)
    records = draft.get("module_asset_records") if isinstance(draft.get("module_asset_records"), list) else []
    decisions = [_decision_row(record) for record in records if isinstance(record, dict)]
    return {
        "schema_version": DECISION_SCHEMA_VERSION,
        "source_draft_schema": DRAFT_SCHEMA_VERSION,
        "source_draft_status": "review_required",
        "target_module": TARGET_MODULE,
        "artifact_status": "review_decision_template",
        "decision_policy": {
            "allowed_decisions": ["pending", "accepted", "rejected"],
            "default_decision": "pending",
            "rule": "Only rows explicitly changed to accepted with reviewer and review_note may be promoted into lowcode_customer_config_contracts.v1.",
        },
        "summary": {
            "decision_count": len(decisions),
            "pending_count": len(decisions),
            "accepted_count": 0,
            "rejected_count": 0,
        },
        "decisions": decisions,
    }


def main():
    draft_path = Path(os.getenv("LOWCODE_CUSTOMER_CONFIG_MODULE_ASSET_DRAFT_INPUT", DEFAULT_DRAFT_INPUT))
    output_path = Path(os.getenv("LOWCODE_CUSTOMER_CONFIG_ACCEPTANCE_DECISION_TEMPLATE_PATH", DEFAULT_OUTPUT))
    if not draft_path.exists():
        raise SystemExit("module asset draft artifact is missing: %s" % draft_path)
    template = build_template(_read_json(draft_path))
    _write_json(output_path, template)
    print("[lowcode_customer_config_acceptance_decision_template] PASS %s" % json.dumps({
        "schema_version": template["schema_version"],
        "target_module": template["target_module"],
        "artifact_status": template["artifact_status"],
        "decision_count": template["summary"]["decision_count"],
        "pending_count": template["summary"]["pending_count"],
        "output_path": str(output_path),
    }, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
