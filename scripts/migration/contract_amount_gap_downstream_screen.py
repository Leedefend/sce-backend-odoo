#!/usr/bin/env python3
"""Screen amount-less loadable contracts against downstream legacy facts."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import contract_line_summary_asset_generator as contract_line


REPO_ASSET_ROOT = Path("migration_assets")
CONTRACT_CSV = Path("tmp/raw/contract/contract.csv")
RECEIPT_CSV = Path("tmp/raw/receipt/receipt.csv")
LEGACY_OUTFLOW_CSV = Path("tmp/raw/payment/payment.csv")
RUNTIME_ROOT = Path(".runtime_artifacts/migration_assets/contract_amount_gap_downstream_screen")
OUTPUT_JSON = RUNTIME_ROOT / "contract_amount_gap_downstream_screen_v1.json"
OUTPUT_CSV = RUNTIME_ROOT / "contract_amount_gap_downstream_screen_rows_v1.csv"
OUTPUT_MD = Path("docs/migration_alignment/frozen/contract_amount_gap_downstream_screen_v1.md")
EXPECTED_AMOUNT_GAP_ROWS = 51


class ContractAmountGapScreenError(Exception):
    pass


def clean(value: object) -> str:
    return contract_line.clean(value)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractAmountGapScreenError(message)


def read_csv(path: Path) -> list[dict[str, str]]:
    require(path.exists(), f"missing csv file: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "legacy_contract_id",
        "contract_external_id",
        "contract_type",
        "subject",
        "legacy_project_id",
        "receipt_ref_count",
        "legacy_outflow_ref_count",
        "route",
        "decision_note",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def contract_manifest_map(asset_root: Path) -> dict[str, dict[str, str]]:
    manifest = contract_line.load_json(asset_root / "manifest/contract_external_id_manifest_v1.json")
    result: dict[str, dict[str, str]] = {}
    for row in manifest.get("records", []):
        legacy_id = clean(row.get("legacy_contract_id"))
        if legacy_id and row.get("status") == "loadable":
            result[legacy_id] = {
                "external_id": clean(row.get("external_id")),
                "contract_type": clean(row.get("contract_type")),
                "legacy_project_id": clean(row.get("legacy_project_id")),
            }
    require(result, "contract manifest map is empty")
    return result


def downstream_refs() -> tuple[dict[str, int], dict[str, int]]:
    receipt_refs: Counter[str] = Counter()
    for row in read_csv(RECEIPT_CSV):
        for field in ("SGHTID", "GLHTID", "HTID"):
            legacy_contract_id = clean(row.get(field))
            if legacy_contract_id:
                receipt_refs[legacy_contract_id] += 1

    outflow_refs: Counter[str] = Counter()
    if LEGACY_OUTFLOW_CSV.exists():
        for row in read_csv(LEGACY_OUTFLOW_CSV):
            for field in ("f_GYSHTID", "GLDJID", "Y_C_ZFSQGL_Id"):
                legacy_contract_id = clean(row.get(field))
                if legacy_contract_id:
                    outflow_refs[legacy_contract_id] += 1
    return dict(receipt_refs), dict(outflow_refs)


def route_for(receipt_count: int, outflow_count: int) -> tuple[str, str]:
    if receipt_count or outflow_count:
        return (
            "keep_header_without_summary_line_downstream_fact_exists",
            "target amount is not required; keep contract header because downstream business facts reference it",
        )
    return (
        "keep_header_without_summary_line_no_downstream_seen",
        "target amount is not required; amount is auxiliary missing information and no summary line should be fabricated",
    )


def render_markdown(payload: dict[str, Any]) -> str:
    route_rows = "\n".join(f"| {route} | {count} |" for route, count in payload["route_counts"].items())
    return f"""# Contract Amount Gap Downstream Screen v1

Status: `{payload["status"]}`

Target model judgment:

- `construction.contract` does not require a direct amount field.
- Amount totals are computed from optional `construction.contract.line` records.
- Missing old contract amount must not be fabricated into a summary line.

## Result

- amount-gap contracts screened: `{payload["amount_gap_rows"]}`
- with downstream references: `{payload["downstream_referenced_rows"]}`
- without downstream references: `{payload["no_downstream_reference_rows"]}`
- DB writes: `0`
- Odoo shell: `false`

## Routes

| Route | Rows |
|---|---:|
{route_rows}

## Decision

`{payload["decision"]}`

## Next

{payload["next_step"]}
"""


def build_screen(asset_root: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    contract_by_legacy = contract_manifest_map(asset_root)
    receipt_refs, outflow_refs = downstream_refs()
    rows: list[dict[str, Any]] = []
    route_counts: Counter[str] = Counter()

    for source_row in read_csv(CONTRACT_CSV):
        legacy_contract_id = clean(source_row.get("Id"))
        contract = contract_by_legacy.get(legacy_contract_id)
        if not contract:
            continue
        _amount_source, amount = contract_line.best_amount(source_row)
        if amount > 0:
            continue
        receipt_count = receipt_refs.get(legacy_contract_id, 0)
        outflow_count = outflow_refs.get(legacy_contract_id, 0)
        route, note = route_for(receipt_count, outflow_count)
        route_counts[route] += 1
        rows.append(
            {
                "legacy_contract_id": legacy_contract_id,
                "contract_external_id": contract["external_id"],
                "contract_type": contract["contract_type"],
                "subject": clean(source_row.get("HTBT")) or clean(source_row.get("DJBH")) or clean(source_row.get("HTBH")),
                "legacy_project_id": contract["legacy_project_id"],
                "receipt_ref_count": receipt_count,
                "legacy_outflow_ref_count": outflow_count,
                "route": route,
                "decision_note": note,
            }
        )

    require(len(rows) == EXPECTED_AMOUNT_GAP_ROWS, f"amount gap row count drifted: {len(rows)} != {EXPECTED_AMOUNT_GAP_ROWS}")
    downstream_rows = sum(1 for row in rows if int(row["receipt_ref_count"]) or int(row["legacy_outflow_ref_count"]))
    payload = {
        "status": "PASS",
        "mode": "contract_amount_gap_downstream_screen",
        "amount_gap_rows": len(rows),
        "downstream_referenced_rows": downstream_rows,
        "no_downstream_reference_rows": len(rows) - downstream_rows,
        "route_counts": dict(sorted(route_counts.items())),
        "row_artifact": str(OUTPUT_CSV),
        "db_writes": 0,
        "odoo_shell": False,
        "decision": "amount_gap_contract_headers_kept_without_fabricated_summary_lines",
        "next_step": "Do not generate summary lines for amount-gap contracts; continue with the next business-fact lane.",
    }
    return payload, rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Screen contract amount gaps against downstream facts.")
    parser.add_argument("--asset-root", default=str(REPO_ASSET_ROOT))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        payload, rows = build_screen(Path(args.asset_root))
        write_json(OUTPUT_JSON, payload)
        write_csv(OUTPUT_CSV, rows)
        OUTPUT_MD.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT_MD.write_text(render_markdown(payload), encoding="utf-8")
    except (ContractAmountGapScreenError, contract_line.ContractLineAssetError, json.JSONDecodeError) as exc:
        result = {"status": "FAIL", "error": str(exc), "db_writes": 0, "odoo_shell": False}
        print("CONTRACT_AMOUNT_GAP_DOWNSTREAM_SCREEN=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 1 if args.check else 0

    print(
        "CONTRACT_AMOUNT_GAP_DOWNSTREAM_SCREEN="
        + json.dumps(
            {
                "status": payload["status"],
                "amount_gap_rows": payload["amount_gap_rows"],
                "downstream_referenced_rows": payload["downstream_referenced_rows"],
                "no_downstream_reference_rows": payload["no_downstream_reference_rows"],
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
