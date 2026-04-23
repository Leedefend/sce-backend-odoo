#!/usr/bin/env python3
"""Freeze policy classification for remaining receipt blockers."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any


RECEIPT_CSV = Path("tmp/raw/receipt/receipt.csv")
RECEIPT_EXTERNAL = Path("migration_assets/manifest/receipt_external_id_manifest_v1.json")
PROJECT_EXTERNAL = Path("migration_assets/manifest/project_external_id_manifest_v1.json")
PARTNER_EXTERNAL = Path("migration_assets/manifest/partner_external_id_manifest_v1.json")
OUTPUT_JSON = Path("migration_assets/manifest/receipt_blocker_policy_snapshot_v1.json")
OUTPUT_MD = Path("docs/migration_alignment/frozen/receipt_blocker_policy_snapshot_v1.md")
EXPECTED_BLOCKED = 4001
ORG_HINTS = ("公司", "有限", "集团", "厂", "局", "院", "中心", "委员会", "合作社")
PROJECT_LIKE_HINTS = ("项目", "项目部", "标包", "片区", "渠道", "维修", "工程")


class ReceiptBlockerPolicyError(Exception):
    pass


def clean(value: object) -> str:
    return re.sub(r"\s+", " ", ("" if value is None else str(value)).replace("\u3000", " ").strip())


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ReceiptBlockerPolicyError(message)


def load_json(path: Path) -> dict[str, Any]:
    require(path.exists(), f"missing json file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    require(path.exists(), f"missing csv file: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_amount(value: object) -> Decimal:
    try:
        return Decimal(clean(value) or "0")
    except InvalidOperation:
        return Decimal("0")


def is_deleted(value: object) -> bool:
    normalized = clean(value).lower()
    return bool(normalized) and normalized not in {"0", "false", "no", "n", "否"}


def first_nonempty(row: dict[str, str], fields: list[str]) -> str:
    for field in fields:
        value = clean(row.get(field))
        if value:
            return value
    return ""


def load_receipt_ids() -> set[str]:
    return {
        clean(row.get("legacy_receipt_id"))
        for row in load_json(RECEIPT_EXTERNAL).get("records", [])
        if row.get("status") == "loadable" and clean(row.get("legacy_receipt_id"))
    }


def load_project_ids() -> set[str]:
    return {
        clean(row.get("target_lookup", {}).get("value"))
        for row in load_json(PROJECT_EXTERNAL).get("records", [])
        if row.get("status") == "loadable" and clean(row.get("target_lookup", {}).get("value"))
    }


def load_partner_ids() -> set[str]:
    return {
        clean(row.get("legacy_partner_id"))
        for row in load_json(PARTNER_EXTERNAL).get("records", [])
        if row.get("status") == "loadable" and clean(row.get("legacy_partner_id"))
    }


def partner_name_policy(name: str) -> str:
    if not name or len(name) < 4 or name.isdigit():
        return "discard_non_enterprise_partner_text"
    if any(hint in name for hint in PROJECT_LIKE_HINTS):
        return "review_project_like_partner_text"
    if any(hint in name for hint in ORG_HINTS):
        return "review_possible_enterprise_partner_text"
    return "discard_non_enterprise_partner_text"


def build_snapshot() -> dict[str, Any]:
    loadable_receipts = load_receipt_ids()
    project_ids = load_project_ids()
    partner_ids = load_partner_ids()
    counters: Counter[str] = Counter()
    review_samples: list[dict[str, str]] = []

    for row in read_csv(RECEIPT_CSV):
        legacy_receipt_id = clean(row.get("Id"))
        if legacy_receipt_id in loadable_receipts:
            continue
        amount = parse_amount(row.get("f_JE"))
        legacy_project_id = first_nonempty(row, ["XMID", "LYXMID", "TSXMID"])
        legacy_partner_id = clean(row.get("WLDWID"))
        partner_name = clean(row.get("WLDWMC"))

        if is_deleted(row.get("DEL")):
            policy = "discard_deleted"
        elif amount <= 0:
            policy = "discard_zero_or_negative_amount"
        elif legacy_project_id not in project_ids:
            policy = "defer_project_anchor_missing"
        elif not legacy_partner_id or legacy_partner_id not in partner_ids:
            policy = partner_name_policy(partner_name)
        else:
            policy = "defer_other_unexpected_blocker"
        counters[policy] += 1
        if policy.startswith("review") and len(review_samples) < 20:
            review_samples.append(
                {
                    "legacy_receipt_id": legacy_receipt_id,
                    "legacy_partner_id": legacy_partner_id,
                    "partner_name": partner_name,
                    "policy": policy,
                }
            )

    total_blocked = sum(counters.values())
    require(total_blocked == EXPECTED_BLOCKED, f"blocked count drifted: {total_blocked} != {EXPECTED_BLOCKED}")
    return {
        "status": "PASS",
        "generated_at": "2026-04-15T09:05:00+00:00",
        "db_writes": 0,
        "odoo_shell": False,
        "receipt_loadable_records": len(loadable_receipts),
        "blocked_records": total_blocked,
        "policy_counts": dict(sorted(counters.items())),
        "review_samples": review_samples,
        "decision": "receipt_blockers_policy_classified_continue_mainline",
    }


def render_markdown(payload: dict[str, Any]) -> str:
    policy_rows = "\n".join(f"| {key} | {value} |" for key, value in payload["policy_counts"].items())
    return f"""# Receipt Blocker Policy Snapshot v1

Status: `{payload["status"]}`

Generated at: `{payload["generated_at"]}`

This snapshot classifies receipt rows that remain outside `receipt_sc_v1` after
contract-optional expansion. It performs no DB writes and does not create
settlement, ledger, payment-completion, or accounting facts.

## Counts

- receipt loadable records: `{payload["receipt_loadable_records"]}`
- remaining blocked records: `{payload["blocked_records"]}`
- DB writes: `0`
- Odoo shell: `false`

## Policy Counts

| Policy | Rows |
|---|---:|
{policy_rows}

## Decision

`{payload["decision"]}`

Rows classified as `discard_*` should not block the rebuild bus. Rows classified
as `review_*` require a separate owner review before partner supplementation.
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate receipt blocker policy snapshot.")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        payload = build_snapshot()
        write_json(OUTPUT_JSON, payload)
        OUTPUT_MD.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT_MD.write_text(render_markdown(payload), encoding="utf-8")
    except (ReceiptBlockerPolicyError, json.JSONDecodeError) as exc:
        result = {"status": "FAIL", "error": str(exc), "db_writes": 0, "odoo_shell": False}
        print("RECEIPT_BLOCKER_POLICY_SNAPSHOT=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 1 if args.check else 0
    print(
        "RECEIPT_BLOCKER_POLICY_SNAPSHOT="
        + json.dumps(
            {
                "status": payload["status"],
                "blocked_records": payload["blocked_records"],
                "policy_counts": payload["policy_counts"],
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
