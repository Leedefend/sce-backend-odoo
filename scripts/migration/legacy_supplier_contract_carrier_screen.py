#!/usr/bin/env python3
"""Freeze target carrier boundaries for legacy supplier contract assets."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


MODEL_PATH = Path("addons/smart_construction_core/models/support/contract_center.py")
FACT_SCREEN_JSON = Path(
    ".runtime_artifacts/migration_assets/legacy_supplier_contract_fact_screen/"
    "legacy_supplier_contract_fact_screen_v1.json"
)
FACT_SCREEN_DOC = Path("docs/migration_alignment/frozen/legacy_supplier_contract_fact_screen_v1.md")
OUTPUT_JSON = Path(".runtime_artifacts/migration_assets/legacy_supplier_contract_carrier_screen_v1.json")
OUTPUT_MD = Path("docs/migration_alignment/frozen/legacy_supplier_contract_carrier_screen_v1.md")

REQUIRED_MODEL_MARKERS = {
    "target_model": '_name = "construction.contract"',
    "type_out_income_label": '("out", "收入合同")',
    "type_in_expense_label": '("in", "支出合同")',
    "type_required": "required=True",
    "project_required": "project_id = fields.Many2one",
    "partner_required": "partner_id = fields.Many2one",
    "subject_required": 'subject = fields.Char(string="合同名称", required=True',
    "legacy_contract_id": "legacy_contract_id = fields.Char",
    "legacy_project_id": "legacy_project_id = fields.Char",
    "legacy_document_no": "legacy_document_no = fields.Char",
    "legacy_contract_no": "legacy_contract_no = fields.Char",
    "legacy_status": "legacy_status = fields.Char",
    "legacy_counterparty_text": "legacy_counterparty_text = fields.Char",
    "default_tax_for_type": "def _get_default_tax(self, contract_type)",
    "type_in_purchase_tax": 'return "sale" if contract_type == "out" else "purchase"',
    "amount_total_computed": "amount_total = fields.Monetary",
    "line_amount_total_computed": "line_amount_total = fields.Monetary",
    "create_sequence_default": "def create(self, vals_list)",
}

ALLOWED_FIELDS = [
    "legacy_contract_id",
    "legacy_project_id",
    "legacy_document_no",
    "legacy_contract_no",
    "legacy_status",
    "legacy_deleted_flag",
    "legacy_counterparty_text",
    "subject",
    "type",
    "project_id",
    "partner_id",
    "date_contract",
    "note",
]

FORBIDDEN_FIELDS = [
    "name",
    "tax_id",
    "amount_untaxed",
    "amount_tax",
    "amount_total",
    "line_amount_total",
    "amount_change",
    "amount_final",
    "state",
    "line_ids",
    "analytic_id",
    "budget_id",
    "payment_request_count",
    "settlement_count",
    "is_locked",
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
    fact_doc = load_text(FACT_SCREEN_DOC)
    fact_payload = load_json(FACT_SCREEN_JSON)
    markers = marker_status(model_text)
    missing = [name for name, present in markers.items() if not present]
    require(not missing, f"model marker drift: {', '.join(missing)}")
    require("supplier_contract" in fact_doc, "fact screen doc is not the expected supplier contract screen")

    loadable_rows = int(fact_payload.get("loadable_candidate_rows", 0))
    blocked_rows = int(fact_payload.get("blocked_rows", 0))
    raw_rows = int(fact_payload.get("raw_rows", 0))
    require(loadable_rows == 5301, f"loadable rows drifted: {loadable_rows} != 5301")
    require(blocked_rows == 234, f"blocked rows drifted: {blocked_rows} != 234")
    require(raw_rows == 5535, f"raw rows drifted: {raw_rows} != 5535")

    return {
        "status": "PASS",
        "lane": "supplier_contract",
        "source_table": "T_GYSHT_INFO",
        "target_model": "construction.contract",
        "carrier_decision": "type_in_supplier_expense",
        "source_fact_rows": {
            "raw_rows": raw_rows,
            "loadable_rows": loadable_rows,
            "blocked_rows": blocked_rows,
        },
        "required_legacy_facts": [
            "stable supplier contract source id",
            "contract identity",
            "project anchor",
            "partner anchor",
        ],
        "allowed_fields": ALLOWED_FIELDS,
        "forbidden_fields": FORBIDDEN_FIELDS,
        "boundary_markers": {
            **markers,
            "type_in_supplier_expense": True,
            "type_key_not_renamed": True,
            "amount_header_not_written": True,
            "tax_not_written": True,
            "state_not_written": True,
            "line_not_written": True,
        },
        "field_policy": {
            "type": "always in; existing model semantics mean supplier/purchase/expense contract",
            "subject": "source contract title/name/number fallback, required",
            "project_id": "required external id ref from project asset",
            "partner_id": "required external id ref from partner asset",
            "date_contract": "source signing date when present",
            "note": "source trace and optional amount trace",
            "name": "not written; target sequence creates official number",
            "tax_id": "not written; target model default tax for type=in applies",
            "amount_total": "not written; computed from lines in a separate lane",
            "state": "not written; target default remains draft",
        },
        "external_id_pattern": "legacy_supplier_contract_sc_<T_GYSHT_INFO.Id>",
        "decision": (
            "Use construction.contract as a draft supplier contract header carrier "
            "with type=in. Do not rename the selection key and do not write computed "
            "amount, tax, state, line, settlement, ledger, or accounting fields."
        ),
        "next_step": (
            "Generate supplier_contract XML assets for the 5301 loadable rows using "
            "the allowed field set, then verify that no forbidden computed/runtime "
            "fields appear in generated XML."
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
    return f"""# Legacy Supplier Contract Carrier Screen v1

Status: `{payload["status"]}`

This screen freezes how `supplier_contract` facts may enter the replayable
target asset bus. It is not an asset generation batch and performs no DB write.

## Carrier Decision

- source table: `{payload["source_table"]}`
- target model: `{payload["target_model"]}`
- carrier decision: `{payload["carrier_decision"]}`
- external id pattern: `{payload["external_id_pattern"]}`
- raw source rows: `{payload["source_fact_rows"]["raw_rows"]}`
- loadable source rows: `{payload["source_fact_rows"]["loadable_rows"]}`
- blocked source rows: `{payload["source_fact_rows"]["blocked_rows"]}`

The selected carrier is `type_in_supplier_expense`: the existing selection key
`in` means supplier/purchase/expense contract in this system. `type_key_not_renamed`
is intentional because changing the key would be a schema and semantic migration
outside the current assetization lane.

## Allowed Fields

{allowed_rows}

## Forbidden Computed Or Runtime Fields

{forbidden_rows}

Boundary markers:

| Marker | Value |
|---|---:|
{marker_rows}

## Hard Boundary

- `type_in_supplier_expense`: supplier contracts use `type="in"`.
- `type_key_not_renamed`: no model selection key change in this migration lane.
- `amount_header_not_written`: header computed amount fields are not written.
- `tax_not_written`: target default tax logic applies for `type="in"`.
- `state_not_written`: target default remains draft.
- `line_not_written`: amount/line materialization is a separate later lane.

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
        text = OUTPUT_MD.read_text(encoding="utf-8")
        for marker in [
            "type_in_supplier_expense",
            "type_key_not_renamed",
            "amount_header_not_written",
            "supplier_contract",
        ]:
            require(marker in text, f"missing marker in markdown: {marker}")
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail on any boundary drift")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        payload = run(check=args.check)
    except (CarrierScreenError, json.JSONDecodeError) as exc:
        result = {"status": "FAIL", "error": str(exc), "db_writes": 0, "odoo_shell": False}
        print("SUPPLIER_CONTRACT_CARRIER_SCREEN=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 1 if args.check else 0
    print(
        "SUPPLIER_CONTRACT_CARRIER_SCREEN="
        + json.dumps(
            {"status": payload["status"], "carrier_decision": payload["carrier_decision"]},
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
