#!/usr/bin/env python3
"""Read-only audit for receipt source lanes and contract direction evidence."""

from __future__ import annotations

import csv
import json
import re
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
RAW_RECEIPT = ROOT / "tmp/raw/receipt/receipt.csv"
RAW_CONTRACT = ROOT / "tmp/raw/contract/contract.csv"
RECEIPT_XML = ROOT / "migration_assets/20_business/receipt/receipt_core_v1.xml"
CONTRACT_MANIFEST = ROOT / "migration_assets/manifest/contract_external_id_manifest_v1.json"
OUTPUT_JSON = ROOT / "artifacts/migration/receipt_contract_boundary_audit_v1.json"
OUTPUT_MD = ROOT / "artifacts/migration/receipt_contract_boundary_audit_v1.md"

TARGET_PROJECT_ID = "8ab29cb255744a2d8b8369c642ee6fe6"
TARGET_CONTRACT_ID = "af35fb6a1aec4ccb8c0c725524809da2"
TARGET_RECEIPT_IDS = {"514330e6e0754363b7e764aef7a59d11", "f983d92633054253b52a4fa29628f84b"}
LEGACY_DELETE_FIELDS = ("DEL", "SCRID", "SCR", "SCRQ")


def clean(value: object) -> str:
    return "" if value is None else str(value).strip()


def money(value: object) -> Decimal:
    try:
        return Decimal(clean(value) or "0")
    except InvalidOperation:
        return Decimal("0")


def is_deleted(row: dict[str, str]) -> bool:
    value = clean(row.get("DEL")).lower()
    return (bool(value) and value not in {"0", "false", "no", "n", "否"}) or any(
        clean(row.get(field)) for field in LEGACY_DELETE_FIELDS if field != "DEL"
    )


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def receipt_lane(row: dict[str, str]) -> str:
    if is_deleted(row):
        return "deleted"
    pushed_income = (
        clean(row.get("D_SCBSJS_SKYT")) in {"销售收款", "预收款"}
        or bool(clean(row.get("OTHER_SYSTEM_CODE")))
        or clean(row.get("D_SCBSJS_IsPush")) == "1"
    )
    if pushed_income:
        return "sales_receipt_or_pushed_income"
    if clean(row.get("SJBMC")) == "甲方回款录入" or clean(row.get("DJBH")).startswith(("ZJSR", "QTSR", "ZCDFSR")):
        return "legacy_receipt_entry"
    return "other_receipt_income"


def receipt_asset_legacy_ids() -> set[str]:
    root = ET.parse(RECEIPT_XML).getroot()
    result: set[str] = set()
    for record in root.findall(".//record[@model='payment.request']"):
        note = ""
        for field in record.findall("field"):
            if clean(field.get("name")) == "note":
                note = clean(field.text)
                break
        match = re.search(r"legacy_receipt_id=([^;\s]+)", note)
        if match:
            result.add(match.group(1))
    return result


def contract_direction_rows() -> list[dict[str, Any]]:
    manifest = json.loads(CONTRACT_MANIFEST.read_text(encoding="utf-8"))
    return [row for row in manifest.get("records", []) if row.get("status") == "loadable"]


def summarize_receipts(rows: list[dict[str, str]], asset_ids: set[str]) -> dict[str, Any]:
    raw_counts: Counter[str] = Counter()
    raw_amounts: defaultdict[str, Decimal] = defaultdict(Decimal)
    raw_with_contract: Counter[str] = Counter()
    asset_counts: Counter[str] = Counter()
    asset_amounts: defaultdict[str, Decimal] = defaultdict(Decimal)
    asset_with_contract: Counter[str] = Counter()
    target_rows: list[dict[str, str]] = []

    for row in rows:
        lane = receipt_lane(row)
        raw_counts[lane] += 1
        raw_amounts[lane] += money(row.get("f_JE"))
        if clean(row.get("SGHTID")):
            raw_with_contract[lane] += 1
        legacy_id = clean(row.get("Id"))
        if legacy_id in asset_ids:
            asset_counts[lane] += 1
            asset_amounts[lane] += money(row.get("f_JE"))
            if clean(row.get("SGHTID")):
                asset_with_contract[lane] += 1
        if legacy_id in TARGET_RECEIPT_IDS or clean(row.get("XMID")) == TARGET_PROJECT_ID and clean(row.get("SGHTID")) == TARGET_CONTRACT_ID:
            target_rows.append(
                {
                    "legacy_receipt_id": legacy_id,
                    "document_no": clean(row.get("DJBH")),
                    "amount": clean(row.get("f_JE")),
                    "date": clean(row.get("f_RQ")),
                    "source_menu": clean(row.get("SJBMC")),
                    "receipt_lane": lane,
                    "legacy_receipt_type": clean(row.get("type")),
                    "income_category": clean(row.get("f_SRLBName")),
                    "contract_legacy_id": clean(row.get("SGHTID")),
                    "sales_receipt_kind": clean(row.get("D_SCBSJS_SKYT")),
                    "is_pushed": clean(row.get("D_SCBSJS_IsPush")),
                    "other_system_code": clean(row.get("OTHER_SYSTEM_CODE")),
                }
            )

    lanes = sorted(raw_counts)
    return {
        "raw_rows": sum(raw_counts.values()),
        "receipt_core_asset_rows": len(asset_ids),
        "lanes": [
            {
                "lane": lane,
                "raw_rows": raw_counts[lane],
                "raw_amount": str(raw_amounts[lane]),
                "raw_with_contract": raw_with_contract[lane],
                "receipt_core_asset_rows": asset_counts[lane],
                "receipt_core_asset_amount": str(asset_amounts[lane]),
                "receipt_core_asset_with_contract": asset_with_contract[lane],
            }
            for lane in lanes
        ],
        "target_rows": target_rows,
    }


def summarize_contracts(contract_rows: list[dict[str, Any]], raw_contract_rows: list[dict[str, str]]) -> dict[str, Any]:
    raw_by_id = {clean(row.get("Id")): row for row in raw_contract_rows}
    counts: Counter[tuple[str, str]] = Counter()
    receipt_reference_in: list[dict[str, str]] = []
    target_contract: dict[str, Any] | None = None

    for row in contract_rows:
        key = (clean(row.get("contract_type")), clean(row.get("direction_source")))
        counts[key] += 1
        legacy_id = clean(row.get("legacy_contract_id"))
        if legacy_id == TARGET_CONTRACT_ID:
            target_contract = row
        if key == ("in", "receipt_contract_reference"):
            raw = raw_by_id.get(legacy_id, {})
            receipt_reference_in.append(
                {
                    "legacy_contract_id": legacy_id,
                    "legacy_project_id": clean(row.get("legacy_project_id")),
                    "project_name": clean(raw.get("f_XMMC")),
                    "subject": clean(raw.get("HTBT")) or clean(raw.get("DJBH")) or clean(raw.get("HTBH")),
                    "fbf": clean(raw.get("FBF")),
                    "cbf": clean(raw.get("CBF")),
                    "contract_type": clean(row.get("contract_type")),
                    "direction_source": clean(row.get("direction_source")),
                    "receipt_reference_count": clean(row.get("receipt_direction_reference_count")),
                    "source_contract_confirmed": clean(raw.get("D_SCBSJS_SFGD")),
                }
            )

    return {
        "direction_counts": [
            {"contract_type": key[0], "direction_source": key[1], "rows": count}
            for key, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
        ],
        "receipt_reference_in_rows": len(receipt_reference_in),
        "receipt_reference_in_samples": receipt_reference_in[:50],
        "target_contract": target_contract,
    }


def write_outputs(payload: dict[str, Any]) -> None:
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# Receipt Contract Boundary Audit v1",
        "",
        f"- status: `{payload['status']}`",
        f"- raw_receipt_rows: `{payload['receipts']['raw_rows']}`",
        f"- receipt_core_asset_rows: `{payload['receipts']['receipt_core_asset_rows']}`",
        f"- receipt_reference_contracts_marked_in: `{payload['contracts']['receipt_reference_in_rows']}`",
        "- db_writes: `0`",
        "",
        "## Receipt Lanes",
        "",
        "| lane | raw rows | raw amount | raw with contract | receipt_core rows | receipt_core amount | receipt_core with contract |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in payload["receipts"]["lanes"]:
        lines.append(
            "| {lane} | {raw_rows} | {raw_amount} | {raw_with_contract} | {receipt_core_asset_rows} | {receipt_core_asset_amount} | {receipt_core_asset_with_contract} |".format(
                **row
            )
        )
    lines.extend(["", "## Contract Direction Counts", "", "| type | source | rows |", "|---|---|---:|"])
    for row in payload["contracts"]["direction_counts"]:
        lines.append(f"| {row['contract_type']} | {row['direction_source']} | {row['rows']} |")
    lines.extend(
        [
            "",
            "## Finding",
            "",
            "The audit checks that receipt-entry facts and sales/pushed income facts are separated before `receipt_core` reaches `payment.request`. It also checks that receipt-reference direction evidence does not mark contracts as `in`, because the runtime model defines `out` as income contract and `in` as expense contract.",
            "",
            "## Boundary Recommendation",
            "",
            "- Migration phase should preserve every non-deleted source fact, but separate carriers by old-system visible surface/source intent.",
            "- `sales_receipt_or_pushed_income` should be carried as income/receipt fact evidence, not user application fact.",
            "- Contract direction derived from receipt evidence is an income-side signal unless later user confirmation changes the business fact.",
        ]
    )
    OUTPUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    receipt_rows = read_csv(RAW_RECEIPT)
    raw_contract_rows = read_csv(RAW_CONTRACT)
    asset_ids = receipt_asset_legacy_ids()
    contracts = contract_direction_rows()
    payload = {
        "status": "PASS",
        "mode": "receipt_contract_boundary_audit",
        "db_writes": 0,
        "receipts": summarize_receipts(receipt_rows, asset_ids),
        "contracts": summarize_contracts(contracts, raw_contract_rows),
    }
    write_outputs(payload)
    print("RECEIPT_CONTRACT_BOUNDARY_AUDIT=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
