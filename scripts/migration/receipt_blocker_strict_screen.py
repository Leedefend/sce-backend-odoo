#!/usr/bin/env python3
"""Screen blocked receipt rows under strict business-fact rules."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

import receipt_core_asset_generator as receipt_core


REPO_ASSET_ROOT = Path("migration_assets")
SOURCE_CSV = Path("tmp/raw/receipt/receipt.csv")
RUNTIME_ROOT = Path(".runtime_artifacts/migration_assets/receipt_blocker_strict_screen")
OUTPUT_JSON = RUNTIME_ROOT / "receipt_blocker_strict_screen_v1.json"
OUTPUT_CSV = RUNTIME_ROOT / "receipt_blocker_strict_screen_rows_v1.csv"
OUTPUT_MD = Path("docs/migration_alignment/frozen/receipt_blocker_strict_screen_v1.md")
EXPECTED_BLOCKED_ROWS = 2057


class ReceiptBlockerStrictScreenError(Exception):
    pass


def clean(value: object) -> str:
    return receipt_core.clean(value)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ReceiptBlockerStrictScreenError(message)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "legacy_receipt_id",
        "legacy_contract_id",
        "legacy_project_id",
        "legacy_partner_id",
        "amount",
        "partner_name",
        "blockers",
        "strict_route",
        "decision_note",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def blocked_rows(asset_root: Path) -> tuple[list[dict[str, Any]], int]:
    _fields, source_rows = receipt_core.read_source(SOURCE_CSV)
    project_by_legacy = receipt_core.build_project_map(receipt_core.load_json(receipt_core.PROJECT_EXTERNAL_MANIFEST))
    partner_by_legacy = receipt_core.merge_partner_maps(
        receipt_core.build_partner_map(receipt_core.load_json(receipt_core.PARTNER_EXTERNAL_MANIFEST)),
        receipt_core.build_partner_map(receipt_core.load_json(receipt_core.RECEIPT_COUNTERPARTY_EXTERNAL_MANIFEST)),
    )
    contract_by_legacy = receipt_core.build_contract_map(receipt_core.load_json(receipt_core.CONTRACT_EXTERNAL_MANIFEST))

    blocked: list[dict[str, Any]] = []
    loadable_count = 0
    for row in source_rows:
        legacy_receipt_id = clean(row.get("Id"))
        amount = receipt_core.parse_amount(row.get("f_JE"))
        legacy_contract_id = receipt_core.first_nonempty(row, ["SGHTID", "GLHTID", "HTID"])
        row_legacy_project_id = receipt_core.first_nonempty(row, ["XMID", "LYXMID", "TSXMID"])
        legacy_partner_id = clean(row.get("WLDWID"))
        contract = contract_by_legacy.get(legacy_contract_id)
        partner_external_id = partner_by_legacy.get(legacy_partner_id)

        errors: list[str] = []
        if not legacy_receipt_id:
            errors.append("missing_legacy_receipt_id")
        if receipt_core.is_deleted(row.get("DEL")):
            errors.append("discard_deleted")
        if amount <= 0:
            errors.append("zero_or_negative_amount")
        if not legacy_partner_id:
            errors.append("missing_partner_ref")
        elif not partner_external_id:
            errors.append("partner_not_in_asset")

        project_external_id = contract["project_external_id"] if contract else project_by_legacy.get(row_legacy_project_id, "")
        legacy_project_id = contract["legacy_project_id"] if contract else row_legacy_project_id
        if not project_external_id:
            errors.append("project_not_in_asset")

        if errors:
            blocked.append(
                {
                    "source_row": row,
                    "legacy_receipt_id": legacy_receipt_id,
                    "legacy_contract_id": legacy_contract_id,
                    "legacy_project_id": legacy_project_id,
                    "legacy_partner_id": legacy_partner_id,
                    "amount": str(amount),
                    "partner_name": clean(row.get("WLDWMC")),
                    "blockers": errors,
                }
            )
            continue
        loadable_count += 1
    return blocked, loadable_count


def strict_route(blockers: list[str]) -> tuple[str, str]:
    blocker_set = set(blockers)
    if "discard_deleted" in blocker_set:
        return "discard_deleted_source", "deleted legacy receipt row"
    if "zero_or_negative_amount" in blocker_set:
        return "discard_non_positive_amount", "no positive receipt amount; not a core receipt fact"
    if "project_not_in_asset" in blocker_set:
        return "discard_project_anchor_missing", "owner decision: remaining project-missing receipt rows are invalid business data"
    if blocker_set & {"missing_partner_ref", "partner_not_in_asset"}:
        return "discard_incomplete_counterparty", "owner decision: remaining incomplete-counterparty receipt rows are invalid business data"
    if "missing_legacy_receipt_id" in blocker_set:
        return "discard_missing_legacy_receipt_id", "stable legacy receipt identity is missing"
    return "discard_invalid_business_data", "owner decision: remaining receipt blockers are invalid business data"


def render_markdown(payload: dict[str, Any]) -> str:
    route_rows = "\n".join(f"| {route} | {count} |" for route, count in payload["strict_route_counts"].items())
    blocker_rows = "\n".join(f"| {blocker} | {count} |" for blocker, count in payload["blocker_counts"].items())
    return f"""# Receipt Blocker Strict Screen v1

Status: `{payload["status"]}`

This screen keeps the strict receipt fact policy:

- deleted source rows are discarded
- zero or negative amount rows are discarded
- project-missing rows are discarded by owner decision
- incomplete-counterparty rows are discarded by owner decision

## Result

- source rows: `{payload["raw_rows"]}`
- current loadable rows: `{payload["current_loadable_rows"]}`
- blocked rows screened: `{payload["blocked_rows"]}`
- recoverable candidate rows: `{payload["recoverable_candidate_rows"]}`
- discard rows: `{payload["discard_rows"]}`
- DB writes: `0`
- Odoo shell: `false`

## Strict Routes

| Route | Rows |
|---|---:|
{route_rows}

## Blockers

| Blocker | Rows |
|---|---:|
{blocker_rows}

## Decision

`{payload["decision"]}`

## Next

{payload["next_step"]}
"""


def build_screen(asset_root: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    blocked, loadable_count = blocked_rows(asset_root)
    require(len(blocked) == EXPECTED_BLOCKED_ROWS, f"blocked row count drifted: {len(blocked)} != {EXPECTED_BLOCKED_ROWS}")

    route_counts: Counter[str] = Counter()
    blocker_counts: Counter[str] = Counter()
    output_rows: list[dict[str, Any]] = []
    for row in blocked:
        for blocker in row["blockers"]:
            blocker_counts[blocker] += 1
        route, note = strict_route(row["blockers"])
        route_counts[route] += 1
        output_rows.append(
            {
                "legacy_receipt_id": row["legacy_receipt_id"],
                "legacy_contract_id": row["legacy_contract_id"],
                "legacy_project_id": row["legacy_project_id"],
                "legacy_partner_id": row["legacy_partner_id"],
                "amount": row["amount"],
                "partner_name": row["partner_name"],
                "blockers": ",".join(row["blockers"]),
                "strict_route": route,
                "decision_note": note,
            }
        )

    discard_rows = sum(route_counts.values())
    recoverable_candidate_rows = 0
    payload = {
        "status": "PASS",
        "mode": "receipt_blocker_strict_screen",
        "raw_rows": loadable_count + len(blocked),
        "current_loadable_rows": loadable_count,
        "blocked_rows": len(blocked),
        "discard_rows": discard_rows,
        "recoverable_candidate_rows": recoverable_candidate_rows,
        "strict_route_counts": dict(sorted(route_counts.items())),
        "blocker_counts": dict(sorted(blocker_counts.items())),
        "row_artifact": str(OUTPUT_CSV),
        "db_writes": 0,
        "odoo_shell": False,
        "decision": "remaining_receipt_blockers_discarded_as_invalid_business_data",
        "next_step": (
            "Receipt blocker recovery lane is closed; continue with contract amount-gap screening or the next business-fact lane."
        ),
    }
    return payload, output_rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Screen blocked receipt rows under strict business-fact rules.")
    parser.add_argument("--asset-root", default=str(REPO_ASSET_ROOT))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        payload, rows = build_screen(Path(args.asset_root))
        write_json(OUTPUT_JSON, payload)
        write_csv(OUTPUT_CSV, rows)
        OUTPUT_MD.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT_MD.write_text(render_markdown(payload), encoding="utf-8")
    except (ReceiptBlockerStrictScreenError, receipt_core.ReceiptAssetError, json.JSONDecodeError) as exc:
        result = {"status": "FAIL", "error": str(exc), "db_writes": 0, "odoo_shell": False}
        print("RECEIPT_BLOCKER_STRICT_SCREEN=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 1 if args.check else 0

    print(
        "RECEIPT_BLOCKER_STRICT_SCREEN="
        + json.dumps(
            {
                "status": payload["status"],
                "blocked_rows": payload["blocked_rows"],
                "discard_rows": payload["discard_rows"],
                "recoverable_candidate_rows": payload["recoverable_candidate_rows"],
                "strict_route_counts": payload["strict_route_counts"],
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
