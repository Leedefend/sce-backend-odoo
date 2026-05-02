#!/usr/bin/env python3
"""Build approved-state recovery payload for historical outflow requests."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
INPUT_CSV = REPO_ROOT / "artifacts/migration/legacy_payment_approval_downstream_fact_screen_rows_v1.csv"
STATE_ACTIVATION_CSV = REPO_ROOT / "artifacts/migration/history_payment_request_outflow_state_activation_payload_v1.csv"
ACTUAL_OUTFLOW_CSV = REPO_ROOT / "artifacts/migration/fresh_db_actual_outflow_replay_payload_v1.csv"
OUTPUT_CSV = REPO_ROOT / "artifacts/migration/history_payment_request_outflow_approved_recovery_payload_v1.csv"
OUTPUT_JSON = REPO_ROOT / "artifacts/migration/history_payment_request_outflow_approved_recovery_adapter_result_v1.json"
ALLOWED_FACTS = {"historical_approved_by_downstream_business_fact", "historical_approved"}


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


def parse_amount(text: object) -> Decimal:
    try:
        return Decimal(clean(text) or "0")
    except InvalidOperation as exc:
        raise RuntimeError({"invalid_amount": text}) from exc


def actual_outflow_facts() -> dict[str, dict[str, object]]:
    facts: dict[str, dict[str, object]] = defaultdict(lambda: {"count": 0, "amount": Decimal("0"), "sample": []})
    if not ACTUAL_OUTFLOW_CSV.exists():
        return facts
    for row in read_csv(ACTUAL_OUTFLOW_CSV):
        request_external_id = clean(row.get("request_external_id"))
        if not request_external_id:
            continue
        fact = facts[request_external_id]
        fact["count"] = int(fact["count"]) + 1
        fact["amount"] = Decimal(fact["amount"]) + parse_amount(row.get("amount"))
        sample = fact["sample"]
        if isinstance(sample, list) and len(sample) < 5:
            sample.append(clean(row.get("external_id")))
    return facts


def build_from_downstream_snapshot(rows: list[dict[str, str]]) -> tuple[list[dict[str, object]], str]:
    payload_rows: list[dict[str, object]] = []
    seen = set()
    for row in rows:
        if clean(row.get("target_lane")) != "outflow_request":
            continue
        fact = clean(row.get("final_approval_fact"))
        if fact not in ALLOWED_FACTS:
            continue
        external_id = clean(row.get("target_external_id"))
        if not external_id:
            raise RuntimeError({"missing_target_external_id": row})
        if external_id in seen:
            raise RuntimeError({"duplicate_target_external_id": external_id})
        seen.add(external_id)
        payload_rows.append(
            {
                "external_id": external_id,
                "final_approval_fact": fact,
                "audit_semantic": clean(row.get("audit_semantic")),
                "workflow_trace_rows": clean(row.get("workflow_trace_rows")),
                "actual_outflow_count": clean(row.get("actual_outflow_count")),
                "actual_outflow_amount": clean(row.get("actual_outflow_amount")),
                "sample_downstream_external_ids": clean(row.get("sample_downstream_external_ids")),
                "activation_target_state": "approved",
            }
        )
    return payload_rows, "legacy_payment_approval_downstream_fact_screen_rows"


def build_from_packaged_assets() -> tuple[list[dict[str, object]], str]:
    if not STATE_ACTIVATION_CSV.exists():
        raise RuntimeError({"missing_state_activation_payload": str(STATE_ACTIVATION_CSV)})
    actual_facts = actual_outflow_facts()
    payload_rows: list[dict[str, object]] = []
    seen = set()
    for row in read_csv(STATE_ACTIVATION_CSV):
        external_id = clean(row.get("external_id"))
        if not external_id:
            raise RuntimeError({"missing_external_id": row})
        if external_id in seen:
            raise RuntimeError({"duplicate_external_id": external_id})
        seen.add(external_id)
        downstream = actual_facts.get(external_id, {"count": 0, "amount": Decimal("0"), "sample": []})
        actual_count = int(downstream["count"])
        final_fact = "historical_approved_by_downstream_business_fact" if actual_count else "historical_approved"
        payload_rows.append(
            {
                "external_id": external_id,
                "final_approval_fact": final_fact,
                "audit_semantic": "derived_from_packaged_workflow_and_payment_assets",
                "workflow_trace_rows": clean(row.get("workflow_row_count")),
                "actual_outflow_count": actual_count,
                "actual_outflow_amount": format(Decimal(downstream["amount"]), "f"),
                "sample_downstream_external_ids": "|".join(downstream["sample"]),
                "activation_target_state": "approved",
            }
        )
    return payload_rows, "packaged_workflow_and_payment_assets"


def main() -> int:
    if INPUT_CSV.exists():
        payload_rows, source_mode = build_from_downstream_snapshot(read_csv(INPUT_CSV))
    else:
        payload_rows, source_mode = build_from_packaged_assets()
    fieldnames = [
        "external_id",
        "final_approval_fact",
        "audit_semantic",
        "workflow_trace_rows",
        "actual_outflow_count",
        "actual_outflow_amount",
        "sample_downstream_external_ids",
        "activation_target_state",
    ]
    write_csv(OUTPUT_CSV, fieldnames, payload_rows)
    payload = {
        "status": "PASS",
        "mode": "history_payment_request_outflow_approved_recovery_adapter",
        "source_mode": source_mode,
        "payload_rows": len(payload_rows),
        "fact_counts": {
            "historical_approved_by_downstream_business_fact": sum(
                1 for row in payload_rows if row["final_approval_fact"] == "historical_approved_by_downstream_business_fact"
            ),
            "historical_approved": sum(1 for row in payload_rows if row["final_approval_fact"] == "historical_approved"),
        },
        "payload_csv": str(OUTPUT_CSV),
    }
    write_json(OUTPUT_JSON, payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
