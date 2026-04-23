#!/usr/bin/env python3
"""Build a no-DB replay payload for 12 contract-dependent partner anchors."""

from __future__ import annotations

import csv
import json
from pathlib import Path


REPO_ROOT = Path.cwd()
INPUT_CSV = REPO_ROOT / "artifacts/migration/contract_partner_source_12_anchor_design_rows_v1.csv"
OUTPUT_JSON = REPO_ROOT / "artifacts/migration/fresh_db_contract_partner_12_anchor_replay_adapter_result_v1.json"
OUTPUT_CSV = REPO_ROOT / "artifacts/migration/fresh_db_contract_partner_12_anchor_replay_payload_v1.csv"
OUTPUT_REPORT = REPO_ROOT / "docs/migration_alignment/fresh_db_contract_partner_12_anchor_replay_adapter_report_v1.md"

PAYLOAD_FIELDS = [
    "counterparty_text",
    "name",
    "partner_kind",
    "legacy_partner_source_type",
    "dependent_contract_rows",
    "sample_legacy_contract_id",
    "sample_contract_subject",
    "idempotency_key",
    "replay_action",
    "current_db_partner_id",
    "evidence_file",
]


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


def write_report(payload: dict[str, object]) -> None:
    text = f"""# Fresh DB Contract Partner 12 Anchor Replay Adapter Report v1

Status: {payload["status"]}

Task: `ITER-2026-04-15-FRESH-DB-REPLAY-CONTRACT-PARTNER-12-ANCHOR-ADAPTER`

## Scope

Build a no-DB replay payload for the 12 company anchors required by 57
recoverable contract rows. This batch does not execute partner or contract
write scripts and does not touch a database.

## Result

- input anchor rows: `{payload["input_anchor_rows"]}`
- replay payload rows: `{payload["replay_payload_rows"]}`
- dependent contract rows: `{payload["dependent_contract_rows"]}`
- duplicate replay identities: `{payload["duplicate_replay_identities"]}`
- blank counterparty anchors: `{payload["blank_counterparty_anchors"]}`
- non-company anchors: `{payload["non_company_anchors"]}`
- DB writes: `0`

## Decision

`{payload["decision"]}`

## Next

{payload["next_step"]}
"""
    OUTPUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_REPORT.write_text(text, encoding="utf-8")


def main() -> int:
    if not INPUT_CSV.exists():
        raise RuntimeError({"missing_input_csv": str(INPUT_CSV)})

    input_rows = read_csv(INPUT_CSV)
    payload_rows: list[dict[str, object]] = []
    seen: set[str] = set()
    duplicates: list[str] = []
    blank_counterparties: list[dict[str, str]] = []
    non_company_anchors: list[dict[str, str]] = []

    for row in input_rows:
        counterparty = clean(row.get("counterparty_text"))
        source_type = clean(row.get("legacy_partner_source_type"))
        idempotency_key = clean(row.get("idempotency_key")) or f"company::{counterparty}"
        if not counterparty:
            blank_counterparties.append({"sample_legacy_contract_id": clean(row.get("sample_legacy_contract_id"))})
            continue
        if idempotency_key in seen:
            duplicates.append(idempotency_key)
            continue
        seen.add(idempotency_key)
        if source_type != "company":
            non_company_anchors.append({"counterparty_text": counterparty, "legacy_partner_source_type": source_type})
        payload_rows.append(
            {
                "counterparty_text": counterparty,
                "name": counterparty,
                "partner_kind": "company",
                "legacy_partner_source_type": source_type,
                "dependent_contract_rows": clean(row.get("dependent_contract_rows")),
                "sample_legacy_contract_id": clean(row.get("sample_legacy_contract_id")),
                "sample_contract_subject": clean(row.get("sample_contract_subject")),
                "idempotency_key": idempotency_key,
                "replay_action": "create_if_missing_for_contract_retry",
                "current_db_partner_id": "",
                "evidence_file": str(INPUT_CSV.relative_to(REPO_ROOT)),
            }
        )

    dependent_contract_rows = sum(int(clean(row.get("dependent_contract_rows")) or "0") for row in payload_rows)
    status = (
        "PASS"
        if len(input_rows) == 12
        and len(payload_rows) == 12
        and dependent_contract_rows == 57
        and not duplicates
        and not blank_counterparties
        and not non_company_anchors
        else "FAIL"
    )
    payload = {
        "status": status,
        "mode": "fresh_db_contract_partner_12_anchor_replay_adapter",
        "db_writes": 0,
        "database_operations": 0,
        "write_scripts_executed": 0,
        "input_artifact": str(INPUT_CSV),
        "input_anchor_rows": len(input_rows),
        "replay_payload_rows": len(payload_rows),
        "dependent_contract_rows": dependent_contract_rows,
        "duplicate_replay_identities": len(duplicates),
        "duplicate_samples": duplicates[:20],
        "blank_counterparty_anchors": len(blank_counterparties),
        "blank_counterparty_samples": blank_counterparties[:20],
        "non_company_anchors": len(non_company_anchors),
        "non_company_anchor_samples": non_company_anchors[:20],
        "row_artifact": str(OUTPUT_CSV),
        "decision": "contract_partner_12_anchor_replay_payload_ready" if status == "PASS" else "STOP_REVIEW_REQUIRED",
        "next_step": "retry the 57 dependent contract rows after these 12 partner anchors are written in the fresh database replay",
    }
    write_csv(OUTPUT_CSV, PAYLOAD_FIELDS, payload_rows)
    write_json(OUTPUT_JSON, payload)
    write_report(payload)
    print(
        "FRESH_DB_CONTRACT_PARTNER_12_ANCHOR_REPLAY_ADAPTER="
        + json.dumps(
            {
                "status": status,
                "input_anchor_rows": len(input_rows),
                "replay_payload_rows": len(payload_rows),
                "dependent_contract_rows": dependent_contract_rows,
                "duplicates": len(duplicates),
                "blank_counterparties": len(blank_counterparties),
                "db_writes": 0,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
