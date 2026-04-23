#!/usr/bin/env python3
"""Screen old-system outflow request facts before asset generation."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import receipt_core_asset_generator as receipt_core


REPO_ASSET_ROOT = Path("migration_assets")
SOURCE_CSV = Path("tmp/raw/payment/payment.csv")
RUNTIME_ROOT = Path(".runtime_artifacts/migration_assets/legacy_outflow_fact_screen")
OUTPUT_JSON = RUNTIME_ROOT / "legacy_outflow_fact_screen_v1.json"
OUTPUT_CSV = RUNTIME_ROOT / "legacy_outflow_fact_screen_rows_v1.csv"
OUTPUT_MD = Path("docs/migration_alignment/frozen/legacy_outflow_fact_screen_v1.md")
EXPECTED_RAW_ROWS = 13646
AMOUNT_FIELDS = ("f_JHJE", "f_JHFKJE", "f_NEW_JHJE", "f_SFJE", "ZSJE", "YJJE")


class LegacyOutflowFactScreenError(Exception):
    pass


def clean(value: object) -> str:
    return receipt_core.clean(value)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise LegacyOutflowFactScreenError(message)


def read_csv(path: Path) -> list[dict[str, str]]:
    require(path.exists(), f"missing source csv: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def parse_amount(value: object) -> Decimal:
    try:
        return Decimal(clean(value) or "0")
    except InvalidOperation:
        return Decimal("0")


def best_amount(row: dict[str, str]) -> tuple[str, Decimal]:
    for field in AMOUNT_FIELDS:
        amount = parse_amount(row.get(field))
        if amount > 0:
            return field, amount
    return "", Decimal("0")


def is_deleted(row: dict[str, str]) -> bool:
    return clean(row.get("DEL")) == "1" or bool(clean(row.get("SCRID")) or clean(row.get("SCR")) or clean(row.get("SCRQ")))


def load_partner_map(asset_root: Path) -> dict[str, str]:
    return receipt_core.merge_partner_maps(
        receipt_core.build_partner_map(receipt_core.load_json(asset_root / "manifest/partner_external_id_manifest_v1.json")),
        receipt_core.build_partner_map(asset_root and receipt_core.load_json(asset_root / "manifest/receipt_counterparty_partner_external_id_manifest_v1.json")),
        receipt_core.build_partner_map(asset_root and receipt_core.load_json(asset_root / "manifest/contract_counterparty_partner_external_id_manifest_v1.json")),
    )


def load_contract_map(asset_root: Path) -> dict[str, dict[str, str]]:
    return receipt_core.build_contract_map(receipt_core.load_json(asset_root / "manifest/contract_external_id_manifest_v1.json"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "legacy_outflow_id",
        "legacy_project_id",
        "legacy_partner_id",
        "legacy_contract_id",
        "amount",
        "amount_source",
        "project_resolved",
        "partner_resolved",
        "contract_resolved",
        "route",
        "blockers",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def render_markdown(payload: dict[str, Any]) -> str:
    route_rows = "\n".join(f"| {route} | {count} |" for route, count in payload["route_counts"].items())
    blocker_rows = "\n".join(f"| {blocker} | {count} |" for blocker, count in payload["blocker_counts"].items())
    amount_rows = "\n".join(f"| {source} | {count} |" for source, count in payload["amount_source_counts"].items())
    return f"""# Legacy Outflow Fact Screen v1

Status: `{payload["status"]}`

This is a no-DB screen for old-system outflow request facts before any target
asset generation. The target carrier is `payment.request(type='pay')`, so this
lane remains high-risk until separately authorized for asset generation.

## Required Facts

- stable old row id
- project anchor
- partner anchor
- positive amount

Contract reference is optional.

## Result

- raw rows: `{payload["raw_rows"]}`
- loadable candidates: `{payload["loadable_candidate_rows"]}`
- blocked/discarded rows: `{payload["blocked_rows"]}`
- contract-linked candidate rows: `{payload["contract_linked_candidate_rows"]}`
- DB writes: `0`
- Odoo shell: `false`

## Routes

| Route | Rows |
|---|---:|
{route_rows}

## Blockers

| Blocker | Rows |
|---|---:|
{blocker_rows}

## Amount Sources

| Source | Rows |
|---|---:|
{amount_rows}

## Decision

`{payload["decision"]}`

## Next

{payload["next_step"]}
"""


def build_screen(asset_root: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    source_rows = read_csv(SOURCE_CSV)
    require(len(source_rows) == EXPECTED_RAW_ROWS, f"raw row count drifted: {len(source_rows)} != {EXPECTED_RAW_ROWS}")
    project_by_legacy = receipt_core.build_project_map(receipt_core.load_json(asset_root / "manifest/project_external_id_manifest_v1.json"))
    partner_by_legacy = load_partner_map(asset_root)
    contract_by_legacy = load_contract_map(asset_root)

    route_counts: Counter[str] = Counter()
    blocker_counts: Counter[str] = Counter()
    amount_source_counts: Counter[str] = Counter()
    output_rows: list[dict[str, Any]] = []
    contract_linked_candidate_rows = 0

    for row in source_rows:
        legacy_id = clean(row.get("Id"))
        legacy_project_id = clean(row.get("f_XMID"))
        legacy_partner_id = clean(row.get("f_GYSID"))
        legacy_contract_id = clean(row.get("f_GYSHTID"))
        amount_source, amount = best_amount(row)
        project_resolved = bool(project_by_legacy.get(legacy_project_id))
        partner_resolved = bool(partner_by_legacy.get(legacy_partner_id))
        contract_resolved = bool(contract_by_legacy.get(legacy_contract_id)) if legacy_contract_id else False

        blockers: list[str] = []
        if not legacy_id:
            blockers.append("missing_legacy_outflow_id")
        if is_deleted(row):
            blockers.append("discard_deleted")
        if amount <= 0:
            blockers.append("zero_or_negative_amount")
        if not project_resolved:
            blockers.append("project_not_in_asset")
        if not legacy_partner_id:
            blockers.append("missing_partner_ref")
        elif not partner_resolved:
            blockers.append("partner_not_in_asset")

        if blockers:
            for blocker in blockers:
                blocker_counts[blocker] += 1
            if "discard_deleted" in blockers:
                route = "discard_deleted_source"
            elif "zero_or_negative_amount" in blockers:
                route = "discard_non_positive_amount"
            elif "project_not_in_asset" in blockers:
                route = "block_project_anchor_missing"
            elif "missing_partner_ref" in blockers or "partner_not_in_asset" in blockers:
                route = "block_partner_anchor_missing"
            else:
                route = "manual_review_hold"
            route_counts[route] += 1
        else:
            route = "loadable_candidate_contract_optional"
            route_counts[route] += 1
            amount_source_counts[amount_source] += 1
            if contract_resolved:
                contract_linked_candidate_rows += 1

        output_rows.append(
            {
                "legacy_outflow_id": legacy_id,
                "legacy_project_id": legacy_project_id,
                "legacy_partner_id": legacy_partner_id,
                "legacy_contract_id": legacy_contract_id,
                "amount": str(amount),
                "amount_source": amount_source,
                "project_resolved": "1" if project_resolved else "0",
                "partner_resolved": "1" if partner_resolved else "0",
                "contract_resolved": "1" if contract_resolved else "0",
                "route": route,
                "blockers": ",".join(blockers),
            }
        )

    loadable_candidates = route_counts["loadable_candidate_contract_optional"]
    payload = {
        "status": "PASS",
        "mode": "legacy_outflow_fact_screen",
        "raw_rows": len(source_rows),
        "loadable_candidate_rows": loadable_candidates,
        "blocked_rows": len(source_rows) - loadable_candidates,
        "contract_linked_candidate_rows": contract_linked_candidate_rows,
        "route_counts": dict(sorted(route_counts.items())),
        "blocker_counts": dict(sorted(blocker_counts.items())),
        "amount_source_counts": dict(sorted(amount_source_counts.items())),
        "row_artifact": str(OUTPUT_CSV),
        "db_writes": 0,
        "odoo_shell": False,
        "decision": "outflow_fact_screen_pass_asset_generation_requires_dedicated_authorization",
        "next_step": "Open a dedicated outflow asset generation task only after confirming high-risk financial lane authorization.",
    }
    return payload, output_rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Screen old-system outflow request facts.")
    parser.add_argument("--asset-root", default=str(REPO_ASSET_ROOT))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        payload, rows = build_screen(Path(args.asset_root))
        write_json(OUTPUT_JSON, payload)
        write_csv(OUTPUT_CSV, rows)
        OUTPUT_MD.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT_MD.write_text(render_markdown(payload), encoding="utf-8")
    except (LegacyOutflowFactScreenError, receipt_core.ReceiptAssetError, json.JSONDecodeError) as exc:
        result = {"status": "FAIL", "error": str(exc), "db_writes": 0, "odoo_shell": False}
        print("LEGACY_OUTFLOW_FACT_SCREEN=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 1 if args.check else 0

    print(
        "LEGACY_OUTFLOW_FACT_SCREEN="
        + json.dumps(
            {
                "status": payload["status"],
                "raw_rows": payload["raw_rows"],
                "loadable_candidate_rows": payload["loadable_candidate_rows"],
                "blocked_rows": payload["blocked_rows"],
                "contract_linked_candidate_rows": payload["contract_linked_candidate_rows"],
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
