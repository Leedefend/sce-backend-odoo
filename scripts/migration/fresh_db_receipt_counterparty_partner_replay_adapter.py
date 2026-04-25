#!/usr/bin/env python3
"""Build replay payload for receipt counterparty partner supplemental anchors."""

from __future__ import annotations

import csv
import json
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path


REPO_ROOT = Path.cwd()
INPUT_XML = REPO_ROOT / "migration_assets/10_master/receipt_counterparty_partner/receipt_counterparty_partner_master_v1.xml"
INPUT_MANIFEST = REPO_ROOT / "migration_assets/manifest/receipt_counterparty_partner_asset_manifest_v1.json"
OUTPUT_JSON = REPO_ROOT / "artifacts/migration/fresh_db_receipt_counterparty_partner_replay_adapter_result_v1.json"
OUTPUT_CSV = REPO_ROOT / "artifacts/migration/fresh_db_receipt_counterparty_partner_replay_payload_v1.csv"


def clean(value: object) -> str:
    return "" if value is None else str(value).strip()


def parse_xml(path: Path) -> list[dict[str, str]]:
    root = ET.parse(path).getroot()
    rows: list[dict[str, str]] = []
    for record in root.findall(".//record"):
        fields = {field.attrib.get("name", ""): clean(field.text) for field in record.findall("field")}
        rows.append({"external_id": clean(record.attrib.get("id")), "model": clean(record.attrib.get("model")), **fields})
    return rows


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


asset_manifest = json.loads(INPUT_MANIFEST.read_text(encoding="utf-8"))
rows = parse_xml(INPUT_XML)
expected_rows = int(asset_manifest["counts"]["loadable_records"])
identity_counts = Counter((row["legacy_partner_source"], row["legacy_partner_id"]) for row in rows)
duplicates = [identity for identity, count in identity_counts.items() if count > 1]

payload_rows = [
    {
        "external_id": row["external_id"],
        "legacy_partner_source": row["legacy_partner_source"],
        "legacy_partner_id": row["legacy_partner_id"],
        "name": row["name"],
        "company_type": row["company_type"],
        "is_company": row.get("is_company", ""),
        "legacy_partner_name": row["legacy_partner_name"],
        "legacy_source_evidence": row["legacy_source_evidence"],
        "idempotency_key": f"{row['legacy_partner_source']}::{row['legacy_partner_id']}",
        "replay_action": "create_if_missing",
    }
    for row in rows
]

status = "PASS" if len(rows) == expected_rows and not duplicates else "FAIL"
payload = {
    "status": status,
    "mode": "fresh_db_receipt_counterparty_partner_replay_adapter",
    "db_writes": 0,
    "database_operations": 0,
    "asset_package_id": asset_manifest["asset_package_id"],
    "candidate_receipt_rows": asset_manifest["counts"].get("candidate_receipt_rows"),
    "replay_payload_rows": len(payload_rows),
    "expected_rows": expected_rows,
    "duplicate_replay_identities": len(duplicates),
    "duplicate_samples": duplicates[:20],
    "row_artifact": str(OUTPUT_CSV),
    "decision": "receipt_counterparty_partner_replay_payload_ready" if status == "PASS" else "STOP_REVIEW_REQUIRED",
    "next_step": "write receipt counterparty supplemental anchors into allowed replay db",
}
write_csv(
    OUTPUT_CSV,
    [
        "external_id",
        "legacy_partner_source",
        "legacy_partner_id",
        "name",
        "company_type",
        "is_company",
        "legacy_partner_name",
        "legacy_source_evidence",
        "idempotency_key",
        "replay_action",
    ],
    payload_rows,
)
write_json(OUTPUT_JSON, payload)
print(
    "FRESH_DB_RECEIPT_COUNTERPARTY_PARTNER_REPLAY_ADAPTER="
    + json.dumps(
        {
            "status": status,
            "replay_payload_rows": len(payload_rows),
            "expected_rows": expected_rows,
            "duplicate_replay_identities": len(duplicates),
            "db_writes": 0,
        },
        ensure_ascii=False,
        sort_keys=True,
    )
)
