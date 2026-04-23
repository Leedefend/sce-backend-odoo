#!/usr/bin/env python3
"""Freeze carrier decision for legacy outflow request line facts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REQUEST_MODEL_PATH = Path("addons/smart_construction_core/models/core/payment_request.py")
EVIDENCE_MODEL_PATH = Path("addons/smart_construction_core/models/support/business_evidence.py")
SCREEN_JSON = Path(
    ".runtime_artifacts/migration_assets/legacy_outflow_request_line_screen/"
    "legacy_outflow_request_line_screen_v1.json"
)
SCREEN_DOC = Path("docs/migration_alignment/frozen/legacy_outflow_request_line_screen_v1.md")
OUTPUT_JSON = Path(".runtime_artifacts/migration_assets/legacy_outflow_request_line_carrier_screen_v1.json")
OUTPUT_MD = Path("docs/migration_alignment/frozen/legacy_outflow_request_line_carrier_screen_v1.md")


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


def build_payload() -> dict[str, Any]:
    request_text = load_text(REQUEST_MODEL_PATH)
    evidence_text = load_text(EVIDENCE_MODEL_PATH)
    screen_doc = load_text(SCREEN_DOC)
    screen_payload = load_json(SCREEN_JSON)
    require('_name = "payment.request"' in request_text, "payment.request marker missing")
    require("ledger_line_ids = fields.One2many" in request_text, "payment.request runtime ledger marker missing")
    require('"payment.ledger"' in request_text, "ledger relation marker missing")
    require('note = fields.Text(string="备注")' in request_text, "payment.request note marker missing")
    require('_name = "sc.business.evidence"' in evidence_text, "business evidence marker missing")
    require("allow_evidence_mutation" in evidence_text, "business evidence immutability marker missing")
    require("business_id = fields.Integer(required=True" in evidence_text, "business evidence runtime id marker missing")
    require("line_fact" in screen_doc, "line screen doc marker missing")

    raw_rows = int(screen_payload.get("raw_rows", 0))
    loadable_rows = int(screen_payload.get("loadable_candidate_rows", 0))
    blocked_rows = int(screen_payload.get("blocked_rows", 0))
    require(raw_rows == 17413, f"raw rows drifted: {raw_rows} != 17413")
    require(loadable_rows == 15917, f"loadable rows drifted: {loadable_rows} != 15917")
    require(blocked_rows == 1496, f"blocked rows drifted: {blocked_rows} != 1496")

    return {
        "status": "PASS_WITH_STOP",
        "lane": "outflow_request_line",
        "source_table": "C_ZFSQGL_CB",
        "source_fact_rows": {
            "raw_rows": raw_rows,
            "loadable_rows": loadable_rows,
            "blocked_rows": blocked_rows,
        },
        "carrier_decision": "no_safe_existing_xml_carrier",
        "candidate_models": {
            "payment.request": {
                "decision": "rejected",
                "reason": "parent request has no line fact one2many; note is not a structured replayable line carrier",
            },
            "payment.ledger": {
                "decision": "rejected",
                "reason": "ledger is runtime payment evidence and would fabricate payment/paid semantics",
            },
            "sc.business.evidence": {
                "decision": "rejected",
                "reason": "requires runtime business_id and allow_evidence_mutation context; not safe as XML carrier",
            },
        },
        "boundary_markers": {
            "no_safe_existing_xml_carrier": True,
            "parent_note_not_used": True,
            "ledger_not_used": True,
            "business_evidence_not_used": True,
            "neutral_staging_required": True,
            "line_fact_preserved": True,
        },
        "decision": (
            "Do not generate XML assets for outflow_request_line against existing "
            "models. A dedicated neutral staging carrier or explicit target line "
            "model is required before assetization."
        ),
        "next_step": (
            "Open a dedicated model-carrier design task for outflow request line "
            "facts, or switch to receipt_invoice line screen while this carrier "
            "decision is handled."
        ),
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def render_markdown(payload: dict[str, Any]) -> str:
    candidate_rows = "\n".join(
        f"| {model} | {info['decision']} | {info['reason']} |"
        for model, info in payload["candidate_models"].items()
    )
    marker_rows = "\n".join(
        f"| {name} | `{value}` |" for name, value in payload["boundary_markers"].items()
    )
    return f"""# Legacy Outflow Request Line Carrier Screen v1

Status: `{payload["status"]}`

This screen freezes the target-carrier decision for outflow request `line_fact`
rows. It performs no DB write and does not generate XML assets.

## Source Facts

- source table: `{payload["source_table"]}`
- raw rows: `{payload["source_fact_rows"]["raw_rows"]}`
- loadable line facts from screen: `{payload["source_fact_rows"]["loadable_rows"]}`
- blocked/discarded rows: `{payload["source_fact_rows"]["blocked_rows"]}`

## Carrier Decision

`{payload["carrier_decision"]}`

| Candidate model | Decision | Reason |
|---|---|---|
{candidate_rows}

## Boundary Markers

| Marker | Value |
|---|---:|
{marker_rows}

## Hard Boundary

- `parent_note_not_used`: line facts must not be collapsed into parent request notes.
- `ledger_not_used`: line facts must not fabricate paid/ledger semantics.
- `business_evidence_not_used`: XML cannot safely populate runtime `business_id` evidence.
- `neutral_staging_required`: a dedicated neutral carrier is required before XML assetization.

## Decision

{payload["decision"]}

## Next

{payload["next_step"]}
"""


def run(check: bool) -> dict[str, Any]:
    payload = build_payload()
    write_json(OUTPUT_JSON, payload)
    OUTPUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_MD.write_text(render_markdown(payload), encoding="utf-8")
    if check:
        text = OUTPUT_MD.read_text(encoding="utf-8")
        for marker in [
            "no_safe_existing_xml_carrier",
            "parent_note_not_used",
            "neutral_staging_required",
            "line_fact",
        ]:
            require(marker in text, f"missing marker in markdown: {marker}")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail on carrier drift")
    args = parser.parse_args()
    try:
        payload = run(check=args.check)
    except (CarrierScreenError, json.JSONDecodeError) as exc:
        result = {"status": "FAIL", "error": str(exc), "db_writes": 0, "odoo_shell": False}
        print("OUTFLOW_REQUEST_LINE_CARRIER_SCREEN=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 1 if args.check else 0
    print(
        "OUTFLOW_REQUEST_LINE_CARRIER_SCREEN="
        + json.dumps(
            {"status": payload["status"], "carrier_decision": payload["carrier_decision"]},
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
