#!/usr/bin/env python3
"""Freeze target carrier boundaries for legacy actual outflow assets."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


MODEL_PATH = Path("addons/smart_construction_core/models/core/payment_request.py")
VIEW_PATH = Path("addons/smart_construction_core/views/core/payment_request_views.xml")
FACT_SCREEN_JSON = Path(
    ".runtime_artifacts/migration_assets/legacy_actual_outflow_fact_screen/"
    "legacy_actual_outflow_fact_screen_v1.json"
)
FACT_SCREEN_DOC = Path("docs/migration_alignment/frozen/legacy_actual_outflow_fact_screen_v1.md")
OUTPUT_JSON = Path(".runtime_artifacts/migration_assets/legacy_actual_outflow_carrier_screen_v1.json")
OUTPUT_MD = Path("docs/migration_alignment/frozen/legacy_actual_outflow_carrier_screen_v1.md")

REQUIRED_MODEL_MARKERS = {
    "target_model": '_name = "payment.request"',
    "type_default_pay": 'default="pay"',
    "project_required": "project_id = fields.Many2one",
    "partner_required": "partner_id = fields.Many2one",
    "amount_required": "amount = fields.Monetary",
    "state_default_draft": 'default="draft"',
    "state_write_guard": "allow_transition",
    "ledger_runtime_method": "_ensure_payment_ledger",
    "contract_optional_guard": "if rec.contract_id",
    "settlement_optional_guard": "if not rec.settlement_id",
}

ALLOWED_FIELDS = [
    "type",
    "project_id",
    "partner_id",
    "amount",
    "date_request",
    "note",
]

FORBIDDEN_FIELDS = [
    "state",
    "settlement_id",
    "ledger_line_ids",
    "paid_amount_total",
    "unpaid_amount",
    "is_fully_paid",
    "validation_status",
    "reviewer_id",
    "approved_by_id",
]


class CarrierScreenError(Exception):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise CarrierScreenError(message)


def load_text(path: Path) -> str:
    require(path.exists(), f"missing input: {path}")
    return path.read_text(encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    require(path.exists(), f"missing input: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def marker_status(text: str) -> dict[str, bool]:
    return {name: marker in text for name, marker in REQUIRED_MODEL_MARKERS.items()}


def build_payload() -> dict[str, Any]:
    model_text = load_text(MODEL_PATH)
    view_text = load_text(VIEW_PATH)
    fact_doc = load_text(FACT_SCREEN_DOC)
    fact_payload = load_json(FACT_SCREEN_JSON)
    markers = marker_status(model_text)
    missing = [name for name, present in markers.items() if not present]
    require(not missing, f"model marker drift: {', '.join(missing)}")
    require("loadable candidates" in fact_doc, "fact screen doc is not the expected actual outflow screen")

    loadable_rows = int(fact_payload.get("loadable_candidate_rows", 0))
    blocked_rows = int(fact_payload.get("blocked_rows", 0))
    raw_rows = int(fact_payload.get("raw_rows", 0))
    require(loadable_rows == 12463, f"loadable rows drifted: {loadable_rows} != 12463")
    require(blocked_rows == 1166, f"blocked rows drifted: {blocked_rows} != 1166")
    require(raw_rows == 13629, f"raw rows drifted: {raw_rows} != 13629")

    view_has_runtime_actions = "action_submit" in view_text and "action_done" in view_text
    require(view_has_runtime_actions, "view runtime action markers missing")

    return {
        "status": "PASS",
        "lane": "actual_outflow",
        "source_table": "T_FK_Supplier",
        "target_model": "payment.request",
        "carrier_decision": "draft_carrier",
        "source_fact_rows": {
            "raw_rows": raw_rows,
            "loadable_rows": loadable_rows,
            "blocked_rows": blocked_rows,
        },
        "required_legacy_facts": [
            "stable actual outflow source id",
            "project anchor",
            "partner anchor",
            "positive amount",
        ],
        "allowed_fields": ALLOWED_FIELDS,
        "forbidden_fields": FORBIDDEN_FIELDS,
        "boundary_markers": {
            **markers,
            "view_runtime_actions_present": view_has_runtime_actions,
            "state_not_written": True,
            "ledger_not_written": True,
            "settlement_not_written": True,
            "contract_not_required": True,
            "source_request_anchor_optional": True,
        },
        "field_policy": {
            "type": "always pay",
            "project_id": "required external id ref from project asset",
            "partner_id": "required external id ref from partner asset",
            "amount": "required positive source amount",
            "date_request": "source outflow date when present",
            "note": "source trace marker and optional original request reference",
            "state": "state_not_written; target default remains draft",
            "settlement_id": "settlement_not_written",
            "ledger_line_ids": "ledger_not_written",
        },
        "external_id_pattern": "legacy_actual_outflow_sc_<T_FK_Supplier.Id>",
        "decision": (
            "Use payment.request as a draft business-fact carrier only. Do not "
            "materialize paid/completed state, settlement, ledger, workflow, or "
            "accounting semantics in the XML asset lane."
        ),
        "next_step": (
            "Generate actual_outflow XML assets for the 12463 loadable rows using "
            "the allowed field set, then verify that no forbidden runtime fields "
            "appear in generated XML."
        ),
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def render_markdown(payload: dict[str, Any]) -> str:
    allowed_rows = "\n".join(f"- `{field}`" for field in payload["allowed_fields"])
    forbidden_rows = "\n".join(f"- `{field}`" for field in payload["forbidden_fields"])
    marker_rows = "\n".join(
        f"| {name} | `{value}` |" for name, value in payload["boundary_markers"].items()
    )
    return f"""# Legacy Actual Outflow Carrier Screen v1

Status: `{payload["status"]}`

This screen freezes how `actual_outflow` facts may enter the replayable target
asset bus. It is not an asset generation batch and performs no DB write.

## Carrier Decision

- source table: `{payload["source_table"]}`
- target model: `{payload["target_model"]}`
- carrier decision: `{payload["carrier_decision"]}`
- external id pattern: `{payload["external_id_pattern"]}`
- raw source rows: `{payload["source_fact_rows"]["raw_rows"]}`
- loadable source rows: `{payload["source_fact_rows"]["loadable_rows"]}`
- blocked source rows: `{payload["source_fact_rows"]["blocked_rows"]}`

The selected carrier is `draft_carrier`: source-backed actual outflow rows may
be replayed as draft target records that preserve project, counterparty, amount,
date, and source trace facts. This lane does not assert target runtime payment
completion.

## Allowed Fields

{allowed_rows}

## Forbidden Runtime Fields

{forbidden_rows}

Boundary markers:

| Marker | Value |
|---|---:|
{marker_rows}

## Hard Boundary

- `state_not_written`: target default remains draft.
- `ledger_not_written`: no payment ledger or accounting runtime data is created.
- `settlement_not_written`: no settlement relation is created.
- contract reference remains optional.
- original outflow request anchor remains optional and may be kept in note or manifest trace.

## Decision

{payload["decision"]}

## Next

{payload["next_step"]}
"""


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_markdown(payload), encoding="utf-8")


def run(check: bool) -> dict[str, Any]:
    payload = build_payload()
    write_json(OUTPUT_JSON, payload)
    write_markdown(OUTPUT_MD, payload)
    if check:
        require(OUTPUT_JSON.exists(), f"missing output: {OUTPUT_JSON}")
        require(OUTPUT_MD.exists(), f"missing output: {OUTPUT_MD}")
        text = OUTPUT_MD.read_text(encoding="utf-8")
        for marker in [
            "draft_carrier",
            "state_not_written",
            "ledger_not_written",
            "settlement_not_written",
            "actual_outflow",
        ]:
            require(marker in text, f"missing marker in markdown: {marker}")
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail on any boundary drift")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = run(check=args.check)
    print(json.dumps({"status": payload["status"], "carrier_decision": payload["carrier_decision"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
