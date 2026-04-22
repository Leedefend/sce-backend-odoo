#!/usr/bin/env python3
"""Screen remaining blocked contract rows under strict business-fact rules."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import contract_header_asset_generator as contract_header


REPO_ASSET_ROOT = Path("migration_assets")
SOURCE_CSV = Path("tmp/raw/contract/contract.csv")
RECEIPT_CSV = Path("tmp/raw/receipt/receipt.csv")
PROJECT_CSV = Path("tmp/raw/project/project.csv")
RUNTIME_ROOT = Path(".runtime_artifacts/migration_assets/contract_remaining214_strict_screen")
OUTPUT_JSON = RUNTIME_ROOT / "contract_remaining214_strict_screen_v1.json"
OUTPUT_CSV = RUNTIME_ROOT / "contract_remaining214_strict_screen_rows_v1.csv"
OUTPUT_MD = Path("docs/migration_alignment/frozen/contract_remaining214_strict_screen_v1.md")
EXPECTED_BLOCKED_ROWS = 202


class ContractRemainingStrictScreenError(Exception):
    pass


def clean(value: object) -> str:
    return contract_header.clean(value)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractRemainingStrictScreenError(message)


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
        "legacy_project_id",
        "subject",
        "fbf",
        "cbf",
        "blockers",
        "strict_route",
        "receipt_reference_count",
        "alternate_project_ref_count",
        "decision_note",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def load_receipt_contract_refs(receipt_csv: Path) -> dict[str, int]:
    refs: Counter[str] = Counter()
    for row in read_csv(receipt_csv):
        for field in ("SGHTID", "GLHTID", "HTID"):
            legacy_contract_id = clean(row.get(field))
            if legacy_contract_id:
                refs[legacy_contract_id] += 1
    return dict(refs)


def project_source_indexes(project_csv: Path) -> dict[str, dict[str, list[dict[str, str]]]]:
    indexes: dict[str, dict[str, list[dict[str, str]]]] = {
        "ID": defaultdict(list),
        "OTHER_SYSTEM_ID": defaultdict(list),
        "OTHER_SYSTEM_CODE": defaultdict(list),
        "WBHTID": defaultdict(list),
        "PROJECT_CODE": defaultdict(list),
    }
    for row in read_csv(project_csv):
        for field, index in indexes.items():
            value = clean(row.get(field))
            if value:
                index[value].append(row)
    return indexes


def alternate_project_ref_count(row: dict[str, str], indexes: dict[str, dict[str, list[dict[str, str]]]]) -> int:
    candidate_values = [
        clean(row.get("f_GLZBGCID")),
        clean(row.get("GLZBXMID")),
        clean(row.get("GLZBGCID")),
        clean(row.get("ZFBHTID")),
        clean(row.get("GLYHTID")),
        clean(row.get("PID")),
        clean(row.get("XMBM")),
    ]
    total = 0
    for value in candidate_values:
        if not value or value == "0":
            continue
        total += sum(len(index.get(value, [])) for index in indexes.values())
    return total


def current_blocked_rows(asset_root: Path, source_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    project_external = contract_header.project_map(contract_header.load_json(contract_header.PROJECT_EXTERNAL_MANIFEST))
    partner_by_legacy_id = contract_header.partner_legacy_map(contract_header.load_json(contract_header.PARTNER_EXTERNAL_MANIFEST))
    supplemental_counterparty = contract_header.supplemental_counterparty_map(
        contract_header.load_json(contract_header.CONTRACT_COUNTERPARTY_EXTERNAL_MANIFEST)
    )
    partner_exact, partner_normalized = contract_header.partner_indexes(contract_header.PARTNER_XML)
    receipt_single_counterparty = contract_header.single_receipt_counterparty_map(contract_header.RECEIPT_CSV)
    receipt_contract_evidence = contract_header.receipt_contract_evidence_map(contract_header.RECEIPT_CSV)

    blocked: list[dict[str, Any]] = []
    for line_no, row in enumerate(source_rows, start=2):
        legacy_contract_id = clean(row.get("Id"))
        legacy_project_id = clean(row.get("XMID"))
        subject = clean(row.get("HTBT")) or clean(row.get("DJBH")) or clean(row.get("HTBH"))
        direction, counterparty = contract_header.infer_direction(row)
        if direction == "defer" and receipt_contract_evidence.get(legacy_contract_id):
            direction = "in"
            counterparty = (
                clean(receipt_contract_evidence[legacy_contract_id].get("receipt_partner_name"))
                or clean(row.get("FBF"))
                or clean(row.get("CBF"))
            )
        project_external_id = project_external.get(legacy_project_id, "")
        partner_external_id, partner_match_type = contract_header.resolve_partner(counterparty, partner_exact, partner_normalized)
        if not partner_external_id and legacy_contract_id:
            receipt_partner_id = receipt_single_counterparty.get(legacy_contract_id, "")
            receipt_partner_external_id = partner_by_legacy_id.get(receipt_partner_id, "")
            if receipt_partner_external_id:
                partner_external_id = receipt_partner_external_id
                partner_match_type = "receipt_single_counterparty"
        if not partner_external_id and counterparty:
            supplemental_partner_external_id = supplemental_counterparty.get(contract_header.norm_name(counterparty), "")
            if supplemental_partner_external_id:
                partner_external_id = supplemental_partner_external_id
                partner_match_type = f"contract_counterparty_supplement_{partner_match_type}"

        blockers: list[str] = []
        if not legacy_contract_id:
            blockers.append("missing_legacy_contract_id")
        if clean(row.get("DEL")) == "1":
            blockers.append("deleted_flag")
        if direction not in {"out", "in"}:
            blockers.append("direction_defer")
        if not project_external_id:
            blockers.append("project_anchor_missing")
        if not partner_external_id:
            blockers.append("partner_anchor_missing" if partner_match_type == "missing" else "partner_anchor_ambiguous")
        if not subject:
            blockers.append("missing_subject")
        if blockers:
            blocked.append(
                {
                    "line_no": line_no,
                    "source_row": row,
                    "legacy_contract_id": legacy_contract_id,
                    "legacy_project_id": legacy_project_id,
                    "subject": subject,
                    "fbf": clean(row.get("FBF")),
                    "cbf": clean(row.get("CBF")),
                    "blockers": blockers,
                }
            )
    return blocked


def strict_route(blockers: list[str], receipt_refs: int, alternate_project_refs: int) -> tuple[str, str]:
    blocker_set = set(blockers)
    if "deleted_flag" in blocker_set:
        return "discard_deleted_source", "deleted legacy contract row; do not load as core contract fact"
    if "project_anchor_missing" in blocker_set:
        if alternate_project_refs:
            return "review_project_anchor_external_reference", "alternate project-like reference exists but is not in project asset"
        return "block_project_anchor_missing", "project body anchor is missing; strict condition not met"
    if "direction_defer" in blocker_set:
        if receipt_refs and blocker_set <= {"direction_defer"}:
            return "candidate_recover_direction_from_receipt_income", "receipt rows reference this contract; income direction is explicit evidence candidate"
        return "block_direction_not_explicit", "income/expense direction is not explicit enough under current rules"
    if blocker_set & {"partner_anchor_missing", "partner_anchor_ambiguous"}:
        return "block_partner_anchor_unresolved", "partner anchor still unresolved after supplemental counterparty package"
    return "manual_review_hold", "unclassified blocker combination"


def render_markdown(payload: dict[str, Any]) -> str:
    route_rows = "\n".join(f"| {route} | {count} |" for route, count in payload["strict_route_counts"].items())
    blocker_rows = "\n".join(f"| {blocker} | {count} |" for blocker, count in payload["blocker_counts"].items())
    return f"""# Contract Remaining 214 Strict Screen v1

Status: `{payload["status"]}`

This screen keeps the strict contract fact policy:

- deleted source rows are not migrated
- income/expense direction must have explicit old-database evidence
- project body anchor must exist before a contract fact can load

## Result

- screened blocked rows: `{payload["blocked_rows"]}`
- recoverable candidates without weakening conditions: `{payload["recoverable_candidate_rows"]}`
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

## Evidence

- receipt-direction candidates: `{payload["receipt_direction_candidate_rows"]}`
- alternate project-reference hits: `{payload["alternate_project_reference_hit_rows"]}`

## Decision

`{payload["decision"]}`

## Next

{payload["next_step"]}
"""


def build_screen(asset_root: Path) -> dict[str, Any]:
    source_rows = read_csv(SOURCE_CSV)
    blocked = current_blocked_rows(asset_root, source_rows)
    require(len(blocked) == EXPECTED_BLOCKED_ROWS, f"blocked row count drifted: {len(blocked)} != {EXPECTED_BLOCKED_ROWS}")
    receipt_refs = load_receipt_contract_refs(RECEIPT_CSV)
    project_indexes = project_source_indexes(PROJECT_CSV)

    output_rows: list[dict[str, Any]] = []
    blocker_counts: Counter[str] = Counter()
    route_counts: Counter[str] = Counter()
    receipt_direction_candidate_rows = 0
    alternate_project_hit_rows = 0

    for row in blocked:
        for blocker in row["blockers"]:
            blocker_counts[blocker] += 1
        receipt_ref_count = receipt_refs.get(row["legacy_contract_id"], 0)
        alt_project_refs = alternate_project_ref_count(row["source_row"], project_indexes)
        if alt_project_refs:
            alternate_project_hit_rows += 1
        route, note = strict_route(row["blockers"], receipt_ref_count, alt_project_refs)
        route_counts[route] += 1
        if route == "candidate_recover_direction_from_receipt_income":
            receipt_direction_candidate_rows += 1
        output_rows.append(
            {
                "legacy_contract_id": row["legacy_contract_id"],
                "legacy_project_id": row["legacy_project_id"],
                "subject": row["subject"],
                "fbf": row["fbf"],
                "cbf": row["cbf"],
                "blockers": ",".join(row["blockers"]),
                "strict_route": route,
                "receipt_reference_count": receipt_ref_count,
                "alternate_project_ref_count": alt_project_refs,
                "decision_note": note,
            }
        )

    recoverable_candidate_rows = receipt_direction_candidate_rows
    if recoverable_candidate_rows:
        decision = "strict_screen_pass_recover_receipt_direction_candidates_only"
        next_step = (
            "Open a separate asset-expansion task for receipt-direction candidates; "
            "keep deleted, project-missing, and direction-without-explicit-evidence rows blocked."
        )
    else:
        decision = "strict_screen_pass_no_recoverable_contract_candidates"
        next_step = (
            "Keep remaining contract rows blocked under the strict policy; move to receipt blocker "
            "classification or contract amount-gap screening."
        )
    payload = {
        "status": "PASS",
        "mode": "contract_remaining214_strict_screen",
        "asset_root": str(asset_root),
        "blocked_rows": len(blocked),
        "blocker_counts": dict(sorted(blocker_counts.items())),
        "strict_route_counts": dict(sorted(route_counts.items())),
        "receipt_direction_candidate_rows": receipt_direction_candidate_rows,
        "alternate_project_reference_hit_rows": alternate_project_hit_rows,
        "recoverable_candidate_rows": recoverable_candidate_rows,
        "row_artifact": str(OUTPUT_CSV),
        "db_writes": 0,
        "odoo_shell": False,
        "decision": decision,
        "next_step": next_step,
    }
    return payload, output_rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Screen remaining contract blockers under strict rules.")
    parser.add_argument("--asset-root", default=str(REPO_ASSET_ROOT))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        payload, rows = build_screen(Path(args.asset_root))
        write_json(OUTPUT_JSON, payload)
        write_csv(OUTPUT_CSV, rows)
        OUTPUT_MD.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT_MD.write_text(render_markdown(payload), encoding="utf-8")
    except (ContractRemainingStrictScreenError, contract_header.ContractHeaderAssetError, json.JSONDecodeError) as exc:
        result = {"status": "FAIL", "error": str(exc), "db_writes": 0, "odoo_shell": False}
        print("CONTRACT_REMAINING214_STRICT_SCREEN=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 1 if args.check else 0

    print(
        "CONTRACT_REMAINING214_STRICT_SCREEN="
        + json.dumps(
            {
                "status": payload["status"],
                "blocked_rows": payload["blocked_rows"],
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
