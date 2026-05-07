#!/usr/bin/env python3
"""Generate no-DB business-fit res.partner.bank replay assets."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ASSET_PACKAGE_ID = "partner_bank_business_fit_v1"
TARGET_MODEL = "res.partner.bank"
LOADABLE_FIELDS = [
    "external_id",
    "partner_external_id",
    "partner_legacy_partner_source",
    "partner_legacy_partner_id",
    "partner_name",
    "acc_number",
    "acc_holder_name",
    "bank_name",
    "source_evidence",
    "gate_action",
    "review_flags",
]
DISCARD_FIELDS = [
    "discard_reason",
    "partner_legacy_partner_source",
    "partner_legacy_partner_id",
    "partner_name",
    "acc_number",
    "bank_name",
    "gate_action",
    "review_flags",
]


class PartnerBankAssetError(Exception):
    pass


def clean(value: object) -> str:
    text = "" if value is None else str(value)
    text = text.replace("\u3000", " ").strip()
    return re.sub(r"\s+", " ", text)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise PartnerBankAssetError(message)


def sha1_token(value: str, prefix: str) -> str:
    return f"{prefix}_{hashlib.sha1(value.encode('utf-8')).hexdigest()[:20]}"


def stable_partner_external_id(value: str) -> str:
    return sha1_token(value, "legacy_partner_business")


def stable_bank_external_id(partner_external_id: str, acc_number: str) -> str:
    return sha1_token(f"{partner_external_id}::{acc_number}", "legacy_partner_bank")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    require(path.exists(), f"missing source csv: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), [dict(row) for row in reader]


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_assets(rows: list[dict[str, str]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, int]]:
    records: list[dict[str, Any]] = []
    discard_rows: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()
    seen_keys: set[tuple[str, str]] = set()
    for row in rows:
        gate_action = clean(row.get("gate_action"))
        counts[gate_action or "ungated"] += 1
        partner_legacy_id = clean(row.get("legacy_partner_id"))
        partner_source = clean(row.get("legacy_partner_source")) or "xlsx_business_aligned_partner"
        partner_name = clean(row.get("name"))
        acc_number = clean(row.get("sc_bank_account"))
        bank_name = clean(row.get("sc_bank_name"))
        review_flags = clean(row.get("review_flags"))
        if gate_action == "blocked_review":
            discard_rows.append(
                {
                    "discard_reason": "blocked_partner_review",
                    "partner_legacy_partner_source": partner_source,
                    "partner_legacy_partner_id": partner_legacy_id,
                    "partner_name": partner_name,
                    "acc_number": acc_number,
                    "bank_name": bank_name,
                    "gate_action": gate_action,
                    "review_flags": review_flags,
                }
            )
            continue
        if not acc_number:
            discard_rows.append(
                {
                    "discard_reason": "missing_bank_account",
                    "partner_legacy_partner_source": partner_source,
                    "partner_legacy_partner_id": partner_legacy_id,
                    "partner_name": partner_name,
                    "acc_number": "",
                    "bank_name": bank_name,
                    "gate_action": gate_action,
                    "review_flags": review_flags,
                }
            )
            continue
        partner_external_id = stable_partner_external_id(partner_legacy_id or clean(row.get("partner_key")) or partner_name)
        key = (partner_external_id, acc_number)
        if key in seen_keys:
            discard_rows.append(
                {
                    "discard_reason": "duplicate_partner_bank_account",
                    "partner_legacy_partner_source": partner_source,
                    "partner_legacy_partner_id": partner_legacy_id,
                    "partner_name": partner_name,
                    "acc_number": acc_number,
                    "bank_name": bank_name,
                    "gate_action": gate_action,
                    "review_flags": review_flags,
                }
            )
            continue
        seen_keys.add(key)
        records.append(
            {
                "external_id": stable_bank_external_id(partner_external_id, acc_number),
                "partner_external_id": partner_external_id,
                "partner_legacy_partner_source": partner_source,
                "partner_legacy_partner_id": partner_legacy_id,
                "partner_name": partner_name,
                "acc_number": acc_number,
                "acc_holder_name": clean(row.get("sc_account_name")) or partner_name,
                "bank_name": bank_name,
                "source_evidence": clean(row.get("legacy_source_evidence")),
                "gate_action": gate_action,
                "review_flags": review_flags,
            }
        )
    return records, discard_rows, dict(sorted(counts.items()))


def write_package(out: Path, records: list[dict[str, Any]], discard_rows: list[dict[str, Any]], gate_counts: dict[str, int]) -> dict[str, Any]:
    asset_csv = out / "10_master" / "partner_bank" / "partner_bank_master_v1.csv"
    discard_csv = out / "10_master" / "partner_bank" / "partner_bank_discard_summary_v1.csv"
    manifest_path = out / "manifest" / "partner_bank_asset_manifest_v1.json"
    write_csv(asset_csv, LOADABLE_FIELDS, records)
    write_csv(discard_csv, DISCARD_FIELDS, discard_rows)
    manifest = {
        "asset_manifest_version": "1.0",
        "asset_package_id": ASSET_PACKAGE_ID,
        "baseline_package": False,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "db_writes": 0,
        "odoo_shell": False,
        "lane": {
            "lane_id": "partner_bank",
            "layer": "10_master",
            "business_priority": "core_master_child",
            "risk_class": "normal",
        },
        "target": {
            "model": TARGET_MODEL,
            "parent_model": "res.partner",
            "parent_lookup": "partner_external_id",
            "load_strategy": "csv_replay_write",
        },
        "counts": {
            "loadable_records": len(records),
            "discarded_records": len(discard_rows),
            "gate_rows": sum(gate_counts.values()),
            "gate_counts": gate_counts,
        },
        "validation_gates": [
            "partner_business_gate_exists",
            "partner_parent_external_id_present",
            "bank_account_non_empty",
            "external_id_unique",
            "duplicate_partner_bank_account_discarded",
            "blocked_partner_rows_discarded",
        ],
        "assets": [
            {
                "asset_id": "partner_bank_master_csv_v1",
                "path": "10_master/partner_bank/partner_bank_master_v1.csv",
                "format": "csv",
                "record_count": len(records),
                "required": True,
                "sha256": sha256_file(asset_csv),
            },
            {
                "asset_id": "partner_bank_discard_summary_v1",
                "path": "10_master/partner_bank/partner_bank_discard_summary_v1.csv",
                "format": "csv",
                "record_count": len(discard_rows),
                "required": True,
                "sha256": sha256_file(discard_csv),
            },
        ],
    }
    write_json(manifest_path, manifest)
    return manifest


def validate(records: list[dict[str, Any]]) -> None:
    external_ids = [clean(row.get("external_id")) for row in records]
    require(len(external_ids) == len(set(external_ids)), "duplicate bank external ids")
    for row in records:
        require(clean(row.get("external_id")).startswith("legacy_partner_bank_"), f"invalid bank external id: {row}")
        require(clean(row.get("partner_external_id")).startswith("legacy_partner_business_"), f"invalid partner external id: {row}")
        require(clean(row.get("acc_number")), f"missing bank account: {row}")
        require(clean(row.get("acc_holder_name")), f"missing account holder: {row}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate business-fit res.partner.bank replay assets without DB access.")
    parser.add_argument(
        "--business-gate",
        default="artifacts/migration/partner_business_aligned_rebuild_v1/fact_based_partner_rebuild_business_aligned_gate_v1.csv",
        help="Business-aligned gated partner CSV",
    )
    parser.add_argument("--out", default=".runtime_artifacts/migration_assets/partner_bank_business_fit_v1", help="Runtime output root")
    parser.add_argument("--check", action="store_true", help="Fail non-zero on generation errors")
    args = parser.parse_args()

    try:
        columns, rows = read_csv(Path(args.business_gate))
        required = {"legacy_partner_id", "legacy_partner_source", "name", "sc_account_name", "sc_bank_name", "sc_bank_account", "gate_action"}
        missing = sorted(required - set(columns))
        require(not missing, f"missing business gate columns: {missing}")
        records, discard_rows, gate_counts = build_assets(rows)
        validate(records)
        manifest = write_package(Path(args.out), records, discard_rows, gate_counts)
    except (PartnerBankAssetError, OSError, csv.Error) as exc:
        payload = {"status": "FAIL", "error": str(exc), "db_writes": 0, "odoo_shell": False}
        print("PARTNER_BANK_ASSET_GENERATOR=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 1 if args.check else 0

    payload = {
        "status": "PASS",
        "asset_package_id": ASSET_PACKAGE_ID,
        "runtime_out": args.out,
        "loadable_records": manifest["counts"]["loadable_records"],
        "discarded_records": manifest["counts"]["discarded_records"],
        "gate_counts": manifest["counts"]["gate_counts"],
        "db_writes": 0,
        "odoo_shell": False,
    }
    print("PARTNER_BANK_ASSET_GENERATOR=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
