#!/usr/bin/env python3
"""Audit remaining blocked contract headers for partner/direction recovery planning."""

from __future__ import annotations

import csv
import json
import re
from collections import Counter
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
REASON_CSV = REPO_ROOT / "artifacts/migration/history_contract_unreached_reason_rows_v1.csv"
RAW_CONTRACT_CSV = REPO_ROOT / "tmp/raw/contract/contract.csv"
OUTPUT_JSON = REPO_ROOT / "artifacts/migration/history_contract_partner_gap_audit_v1.json"
OUTPUT_CSV = REPO_ROOT / "artifacts/migration/history_contract_partner_gap_rows_v1.csv"

ASSET_FILES = {
    "partner_master": REPO_ROOT / "migration_assets/10_master/partner/partner_master_v1.xml",
    "contract_counterparty_partner": REPO_ROOT / "migration_assets/10_master/contract_counterparty_partner/contract_counterparty_partner_master_v1.xml",
    "receipt_counterparty_partner": REPO_ROOT / "migration_assets/10_master/receipt_counterparty_partner/receipt_counterparty_partner_master_v1.xml",
}
OWN_COMPANY_NAMES = {"四川保盛建设集团有限公司", "四川保感建设集团有限公司", "My Company"}
ORG_SUFFIXES = ("有限责任公司", "股份有限公司", "集团有限公司", "有限公司", "公司")


def clean(value: object) -> str:
    text = "" if value is None else str(value)
    text = text.replace("\u3000", " ").strip()
    return re.sub(r"\s+", " ", text)


def norm_name(value: object) -> str:
    text = re.sub(r"[（）()·,，.。/、\s\\-]", "", clean(value))
    for suffix in ORG_SUFFIXES:
        if text.endswith(suffix):
            text = text[: -len(suffix)]
            break
    return text


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def infer_direction_bucket(raw: dict[str, str]) -> str:
    fbf = clean(raw.get("FBF"))
    cbf = clean(raw.get("CBF"))
    fbf_own = fbf in OWN_COMPANY_NAMES
    cbf_own = cbf in OWN_COMPANY_NAMES
    if not fbf and not cbf:
        return "both_blank"
    if fbf and not cbf:
        return "fbf_only_non_own" if not fbf_own else "fbf_only_own"
    if cbf and not fbf:
        return "cbf_only_non_own" if not cbf_own else "cbf_only_own"
    if fbf_own and cbf_own:
        return "both_own"
    if not fbf_own and not cbf_own:
        return "both_non_own"
    return "mixed_own_non_own"


def main() -> int:
    reason_rows = read_csv(REASON_CSV)
    raw_by_id = {clean(row.get("Id")): row for row in read_csv(RAW_CONTRACT_CSV)}
    asset_text = {key: path.read_text(encoding="utf-8") for key, path in ASSET_FILES.items()}
    asset_text_norm = {key: norm_name(text) for key, text in asset_text.items()}

    blocked_rows = [row for row in reason_rows if clean(row.get("blockers"))]
    row_out: list[dict[str, object]] = []
    source_counts = Counter()
    direction_counts = Counter()

    for row in blocked_rows:
        legacy_contract_id = clean(row.get("legacy_contract_id"))
        blockers = clean(row.get("blockers"))
        counterparty = clean(row.get("counterparty_text"))
        raw = raw_by_id.get(legacy_contract_id, {})
        source_hits = []
        if "partner_unresolved" in blockers and counterparty:
            for source_key, text in asset_text.items():
                if counterparty in text:
                    source_hits.append(f"{source_key}:exact")
            if not source_hits:
                normalized_counterparty = norm_name(counterparty)
                if normalized_counterparty:
                    for source_key, text in asset_text_norm.items():
                        if normalized_counterparty in text:
                            source_hits.append(f"{source_key}:normalized")

        if not source_hits and "partner_unresolved" in blockers:
            source_bucket = "no_asset_source_in_current_packages"
        elif source_hits:
            first = source_hits[0]
            if first.startswith("partner_master"):
                source_bucket = "partner_master_recoverable"
            elif first.startswith("contract_counterparty_partner"):
                source_bucket = "contract_counterparty_recoverable"
            elif first.startswith("receipt_counterparty_partner"):
                source_bucket = "receipt_counterparty_recoverable"
            else:
                source_bucket = "other_asset_recoverable"
        else:
            source_bucket = ""

        direction_bucket = ""
        if "direction_defer" in blockers:
            direction_bucket = infer_direction_bucket(raw)
            direction_counts[direction_bucket] += 1

        if source_bucket:
            source_counts[source_bucket] += 1

        row_out.append(
            {
                "legacy_contract_id": legacy_contract_id,
                "blockers": blockers,
                "counterparty_text": counterparty,
                "partner_source_bucket": source_bucket,
                "partner_source_hits": "|".join(source_hits),
                "direction_bucket": direction_bucket,
                "fbf": clean(raw.get("FBF")),
                "cbf": clean(raw.get("CBF")),
                "subject": clean(raw.get("HTBT")) or clean(row.get("subject")),
                "legacy_contract_no": clean(raw.get("HTBH")),
            }
        )

    payload = {
        "status": "PASS",
        "mode": "history_contract_partner_gap_audit",
        "blocked_rows": len(blocked_rows),
        "partner_source_bucket_counts": dict(sorted(source_counts.items())),
        "direction_bucket_counts": dict(sorted(direction_counts.items())),
        "row_artifact": str(OUTPUT_CSV.relative_to(REPO_ROOT)),
        "sample_rows": row_out[:20],
    }
    write_csv(
        OUTPUT_CSV,
        [
            "legacy_contract_id",
            "blockers",
            "counterparty_text",
            "partner_source_bucket",
            "partner_source_hits",
            "direction_bucket",
            "fbf",
            "cbf",
            "subject",
            "legacy_contract_no",
        ],
        row_out,
    )
    write_json(OUTPUT_JSON, payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
