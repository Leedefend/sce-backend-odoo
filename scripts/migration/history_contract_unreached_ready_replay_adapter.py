#!/usr/bin/env python3
"""Build replay payload for unreached contract headers that are ready in current sc_demo."""

from __future__ import annotations

import csv
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
REASON_CSV = REPO_ROOT / "artifacts/migration/history_contract_unreached_reason_rows_v1.csv"
RAW_CONTRACT_CSV = REPO_ROOT / "tmp/raw/contract/contract.csv"
OUTPUT_CSV = REPO_ROOT / "artifacts/migration/history_contract_unreached_ready_replay_payload_v1.csv"
OUTPUT_JSON = REPO_ROOT / "artifacts/migration/history_contract_unreached_ready_replay_adapter_result_v1.json"
EXPECTED_ROWS = 56


def clean(value: object) -> str:
    return "" if value is None else str(value).replace("\r\n", "\n").replace("\r", "\n").strip()


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


def main() -> int:
    raw_by_id = {clean(row.get("Id")): row for row in read_csv(RAW_CONTRACT_CSV)}
    reason_rows = read_csv(REASON_CSV)
    ready = [row for row in reason_rows if not clean(row.get("blockers"))]
    if len(ready) != EXPECTED_ROWS:
        raise RuntimeError({"unexpected_ready_rows": len(ready), "expected": EXPECTED_ROWS})

    payload_rows = []
    for row in ready:
        legacy_contract_id = clean(row.get("legacy_contract_id"))
        raw = raw_by_id.get(legacy_contract_id)
        if not raw:
            raise RuntimeError({"missing_raw_contract_row": legacy_contract_id})
        payload_rows.append(
            {
                "legacy_contract_id": legacy_contract_id,
                "legacy_project_id": clean(raw.get("XMID")),
                "subject": clean(raw.get("HTBT")) or clean(raw.get("DJBH")) or clean(raw.get("HTBH")),
                "type": clean(row.get("direction")),
                "legacy_contract_no": clean(raw.get("HTBH")),
                "legacy_document_no": clean(raw.get("DJBH")),
                "legacy_external_contract_no": clean(raw.get("f_WBHTBH")) or clean(raw.get("WBHTBH")) or clean(raw.get("PID")),
                "legacy_status": clean(raw.get("DJZT")),
                "legacy_deleted_flag": clean(raw.get("DEL")),
                "legacy_counterparty_text": clean(row.get("counterparty_text")),
            }
        )

    fieldnames = [
        "legacy_contract_id",
        "legacy_project_id",
        "subject",
        "type",
        "legacy_contract_no",
        "legacy_document_no",
        "legacy_external_contract_no",
        "legacy_status",
        "legacy_deleted_flag",
        "legacy_counterparty_text",
    ]
    write_csv(OUTPUT_CSV, fieldnames, payload_rows)
    payload = {
        "status": "PASS",
        "mode": "history_contract_unreached_ready_replay_adapter",
        "source_rows": len(reason_rows),
        "ready_rows": len(ready),
        "replay_payload_rows": len(payload_rows),
        "payload_csv": str(OUTPUT_CSV),
        "next_step": "run history_contract_unreached_ready_replay_write.py",
    }
    write_json(OUTPUT_JSON, payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
