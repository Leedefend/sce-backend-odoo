#!/usr/bin/env python3
"""Screen receipt partner supplement candidates from positive anchored receipts."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import receipt_core_asset_generator as receipt_core


REPO_ASSET_ROOT = Path("migration_assets")
SOURCE_CSV = Path("tmp/raw/receipt/receipt.csv")
RUNTIME_ROOT = Path(".runtime_artifacts/migration_assets/receipt_partner_supplement_screen")
OUTPUT_JSON = RUNTIME_ROOT / "receipt_partner_supplement_screen_v1.json"
OUTPUT_CSV = RUNTIME_ROOT / "receipt_partner_supplement_screen_rows_v1.csv"
OUTPUT_MD = Path("docs/migration_alignment/frozen/receipt_partner_supplement_screen_v1.md")
EXPECTED_PARTNER_ANCHOR_BLOCKED_ROWS = 1954
ENTERPRISE_TOKENS = ("公司", "厂", "集团", "中心", "合作社", "银行", "学校", "医院", "政府", "委员会", "项目部", "经营部")


class ReceiptPartnerSupplementScreenError(Exception):
    pass


def clean(value: object) -> str:
    return receipt_core.clean(value)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ReceiptPartnerSupplementScreenError(message)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "normalized_partner_name",
        "partner_name",
        "receipt_rows",
        "legacy_partner_ids",
        "sample_receipt_id",
        "route",
        "note",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def normalize_name(value: str) -> str:
    return re.sub(r"[（）()·,，.。/、\s\\-]", "", clean(value))


def is_enterprise_name(value: str) -> bool:
    text = clean(value)
    if len(text) < 4:
        return False
    if text.isdigit():
        return False
    if text in {"==请选择==", "请选择", "无", "测试"}:
        return False
    return any(token in text for token in ENTERPRISE_TOKENS)


def is_safe_counterparty_name(value: str) -> bool:
    text = clean(value)
    if len(text) < 2:
        return False
    if text.isdigit():
        return False
    if text in {"==请选择==", "请选择", "无", "测试"}:
        return False
    return True


def partner_anchor_blocked_rows(asset_root: Path) -> list[dict[str, str]]:
    _fields, source_rows = receipt_core.read_source(SOURCE_CSV)
    project_by_legacy = receipt_core.build_project_map(receipt_core.load_json(receipt_core.PROJECT_EXTERNAL_MANIFEST))
    partner_by_legacy = receipt_core.build_partner_map(receipt_core.load_json(receipt_core.PARTNER_EXTERNAL_MANIFEST))
    contract_by_legacy = receipt_core.build_contract_map(receipt_core.load_json(receipt_core.CONTRACT_EXTERNAL_MANIFEST))

    target_rows: list[dict[str, str]] = []
    for row in source_rows:
        legacy_receipt_id = clean(row.get("Id"))
        amount = receipt_core.parse_amount(row.get("f_JE"))
        legacy_contract_id = receipt_core.first_nonempty(row, ["SGHTID", "GLHTID", "HTID"])
        row_legacy_project_id = receipt_core.first_nonempty(row, ["XMID", "LYXMID", "TSXMID"])
        legacy_partner_id = clean(row.get("WLDWID"))
        contract = contract_by_legacy.get(legacy_contract_id)
        partner_external_id = partner_by_legacy.get(legacy_partner_id)
        project_external_id = contract["project_external_id"] if contract else project_by_legacy.get(row_legacy_project_id, "")
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
        if not project_external_id:
            errors.append("project_not_in_asset")
        if set(errors) <= {"partner_not_in_asset", "missing_partner_ref"} and errors:
            target_rows.append(row)
    return target_rows


def render_markdown(payload: dict[str, Any]) -> str:
    route_rows = "\n".join(f"| {route} | {count} |" for route, count in payload["route_counts"].items())
    return f"""# Receipt Partner Supplement Screen v1

Status: `{payload["status"]}`

This screen treats complete receipt counterparty records as recoverable partner
supplement candidates. Personal names are allowed because the target
`payment.request.partner_id` field points to `res.partner` and does not require
an enterprise company partner.

## Result

- partner-anchor blocked receipt rows: `{payload["partner_anchor_blocked_rows"]}`
- complete counterparty candidate receipt rows: `{payload["complete_counterparty_candidate_receipt_rows"]}`
- complete counterparty candidate partner records: `{payload["complete_counterparty_candidate_partner_records"]}`
- incomplete/unsafe receipt rows: `{payload["incomplete_or_unsafe_rows"]}`
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
    rows = partner_anchor_blocked_rows(asset_root)
    require(
        len(rows) == EXPECTED_PARTNER_ANCHOR_BLOCKED_ROWS,
        f"partner-anchor blocked row count drifted: {len(rows)} != {EXPECTED_PARTNER_ANCHOR_BLOCKED_ROWS}",
    )

    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    route_counts: Counter[str] = Counter()
    for row in rows:
        name = clean(row.get("WLDWMC"))
        normalized = normalize_name(name)
        legacy_partner_id = clean(row.get("WLDWID"))
        if legacy_partner_id and name and is_safe_counterparty_name(name):
            grouped[legacy_partner_id].append(row)
            route_counts["complete_counterparty_supplement_candidate"] += 1
        else:
            route_counts["block_incomplete_or_unsafe_counterparty_record"] += 1

    output_rows: list[dict[str, Any]] = []
    for legacy_partner_id, group in sorted(grouped.items()):
        names = Counter(clean(row.get("WLDWMC")) for row in group if clean(row.get("WLDWMC")))
        partner_name = sorted(names.items(), key=lambda item: (-item[1], item[0]))[0][0]
        output_rows.append(
            {
                "normalized_partner_name": normalize_name(partner_name),
                "partner_name": partner_name,
                "receipt_rows": len(group),
                "legacy_partner_ids": legacy_partner_id,
                "sample_receipt_id": clean(group[0].get("Id")),
                "route": "complete_counterparty_supplement_candidate",
                "note": "positive non-deleted project-anchored receipt with complete counterparty id and safe name",
            }
        )

    payload = {
        "status": "PASS",
        "mode": "receipt_partner_supplement_screen",
        "partner_anchor_blocked_rows": len(rows),
        "complete_counterparty_candidate_receipt_rows": route_counts["complete_counterparty_supplement_candidate"],
        "complete_counterparty_candidate_partner_records": len(output_rows),
        "incomplete_or_unsafe_rows": route_counts["block_incomplete_or_unsafe_counterparty_record"],
        "route_counts": dict(sorted(route_counts.items())),
        "row_artifact": str(OUTPUT_CSV),
        "db_writes": 0,
        "odoo_shell": False,
        "decision": "receipt_partner_person_or_enterprise_supplement_candidates_screened",
        "next_step": (
            "Materialize complete personal or enterprise counterparties as supplemental partner assets; "
            "keep rows with missing counterparty ids blocked."
        ),
    }
    return payload, output_rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Screen receipt partner supplement candidates.")
    parser.add_argument("--asset-root", default=str(REPO_ASSET_ROOT))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        payload, rows = build_screen(Path(args.asset_root))
        write_json(OUTPUT_JSON, payload)
        write_csv(OUTPUT_CSV, rows)
        OUTPUT_MD.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT_MD.write_text(render_markdown(payload), encoding="utf-8")
    except (ReceiptPartnerSupplementScreenError, receipt_core.ReceiptAssetError, json.JSONDecodeError) as exc:
        result = {"status": "FAIL", "error": str(exc), "db_writes": 0, "odoo_shell": False}
        print("RECEIPT_PARTNER_SUPPLEMENT_SCREEN=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 1 if args.check else 0

    print(
        "RECEIPT_PARTNER_SUPPLEMENT_SCREEN="
        + json.dumps(
            {
                "status": payload["status"],
                "partner_anchor_blocked_rows": payload["partner_anchor_blocked_rows"],
                "complete_counterparty_candidate_receipt_rows": payload["complete_counterparty_candidate_receipt_rows"],
                "complete_counterparty_candidate_partner_records": payload["complete_counterparty_candidate_partner_records"],
                "incomplete_or_unsafe_rows": payload["incomplete_or_unsafe_rows"],
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
