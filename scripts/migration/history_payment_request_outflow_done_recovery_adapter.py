#!/usr/bin/env python3
"""Build done-state recovery payload for historical outflow requests."""

from __future__ import annotations

import csv
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
INPUT_CSV = REPO_ROOT / "artifacts/migration/legacy_payment_approval_downstream_fact_state_sync_snapshot_v1.csv"
OUTPUT_CSV = REPO_ROOT / "artifacts/migration/history_payment_request_outflow_done_recovery_payload_v1.csv"
OUTPUT_JSON = REPO_ROOT / "artifacts/migration/history_payment_request_outflow_done_recovery_adapter_result_v1.json"


def clean(value: object) -> str:
    return "" if value is None else str(value).strip()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_decimal(text: str) -> str:
    try:
        value = Decimal(clean(text) or "0")
    except InvalidOperation as exc:
        raise RuntimeError({"invalid_decimal": text}) from exc
    if value <= 0:
        raise RuntimeError({"non_positive_ledger_sum": text})
    return format(value, "f")


def main() -> int:
    rows = read_csv(INPUT_CSV)
    payload_rows: list[dict[str, object]] = []
    seen = set()
    for row in rows:
        external_id = clean(row.get("external_id"))
        if not external_id:
            raise RuntimeError({"missing_external_id": row})
        if external_id in seen:
            raise RuntimeError({"duplicate_external_id": external_id})
        seen.add(external_id)
        old_state = clean(row.get("old_state"))
        old_validation_status = clean(row.get("old_validation_status"))
        old_ledger_count = clean(row.get("old_ledger_count"))
        if old_state != "done" or old_validation_status != "validated" or old_ledger_count != "1":
            raise RuntimeError(
                {
                    "unexpected_done_snapshot_row": {
                        "external_id": external_id,
                        "old_state": old_state,
                        "old_validation_status": old_validation_status,
                        "old_ledger_count": old_ledger_count,
                    }
                }
            )
        payload_rows.append(
            {
                "external_id": external_id,
                "legacy_payment_request_id": clean(row.get("payment_request_id")),
                "name": clean(row.get("name")),
                "ledger_amount": parse_decimal(clean(row.get("old_ledger_sum"))),
                "actual_outflow_count": clean(row.get("actual_outflow_count")),
                "actual_outflow_amount": clean(row.get("actual_outflow_amount")),
                "sample_downstream_external_ids": clean(row.get("sample_downstream_external_ids")),
                "target_state": "done",
                "target_validation_status": "validated",
                "business_fact": "historical_paid_by_downstream_business_fact",
            }
        )

    fieldnames = [
        "external_id",
        "legacy_payment_request_id",
        "name",
        "ledger_amount",
        "actual_outflow_count",
        "actual_outflow_amount",
        "sample_downstream_external_ids",
        "target_state",
        "target_validation_status",
        "business_fact",
    ]
    write_csv(OUTPUT_CSV, fieldnames, payload_rows)
    payload = {
        "status": "PASS",
        "mode": "history_payment_request_outflow_done_recovery_adapter",
        "payload_rows": len(payload_rows),
        "fact_counts": {
            "historical_paid_by_downstream_business_fact": len(payload_rows),
        },
        "payload_csv": str(OUTPUT_CSV),
    }
    write_json(OUTPUT_JSON, payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
