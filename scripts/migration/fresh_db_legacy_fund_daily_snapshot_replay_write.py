#!/usr/bin/env python3
"""Replay legacy fund daily snapshot facts into allowed replay databases."""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path


def repo_root() -> Path:
    env_root = os.getenv("MIGRATION_REPO_ROOT")
    candidates = []
    if env_root:
        candidates.append(Path(env_root))
    candidates.extend([Path("/mnt"), Path.cwd()])
    for candidate in candidates:
        if (candidate / "artifacts/migration/fresh_db_legacy_fund_daily_snapshot_replay_payload_v1.csv").exists():
            return candidate
    return Path.cwd()


def ensure_allowed_db() -> None:
    allowlist = {
        item.strip()
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_migration_fresh,sc_demo").split(",")
        if item.strip()
    }
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_replay": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def clean(value: object) -> str:
    return "" if value is None else str(value).strip()


def as_float(value: str) -> float:
    text = clean(value)
    return float(text) if text else 0.0


REPO_ROOT = repo_root()
ARTIFACT_ROOT = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", str(REPO_ROOT / "artifacts/migration")))
INPUT_CSV = REPO_ROOT / "artifacts/migration/fresh_db_legacy_fund_daily_snapshot_replay_payload_v1.csv"
INPUT_JSON = REPO_ROOT / "artifacts/migration/fresh_db_legacy_fund_daily_snapshot_replay_adapter_result_v1.json"
OUTPUT_JSON = ARTIFACT_ROOT / "fresh_db_legacy_fund_daily_snapshot_replay_write_result_v1.json"

ensure_allowed_db()
adapter = json.loads(INPUT_JSON.read_text(encoding="utf-8"))
rows = read_csv(INPUT_CSV)
expected_rows = int(adapter["expected_rows"])

Model = env["sc.legacy.fund.daily.snapshot.fact"].sudo().with_context(active_test=False)  # noqa: F821
Project = env["project.project"].sudo().with_context(active_test=False)  # noqa: F821

existing_keys = {
    (clean(rec["legacy_source_table"]), clean(rec["legacy_record_id"]))
    for rec in Model.search_read([("legacy_record_id", "!=", False)], ["legacy_source_table", "legacy_record_id"])
}
project_ids = sorted({clean(row.get("legacy_project_id")) for row in rows if clean(row.get("legacy_project_id"))})
project_map = {
    rec["legacy_project_id"]: rec["id"]
    for rec in Project.search_read([("legacy_project_id", "in", project_ids)], ["legacy_project_id"])
    if rec.get("legacy_project_id")
}

created = 0
skipped = 0
buffer: list[dict[str, object]] = []
batch_size = 500
for row in rows:
    key = (clean(row.get("legacy_source_table")), clean(row.get("legacy_record_id")))
    if key in existing_keys:
        skipped += 1
        continue
    legacy_project_id = clean(row.get("legacy_project_id"))
    project_id = project_map.get(legacy_project_id)
    if not project_id:
        raise RuntimeError({"missing_project_anchor": legacy_project_id, "external_id": row["external_id"]})
    buffer.append(
        {
            "legacy_source_table": clean(row.get("legacy_source_table")),
            "legacy_record_id": clean(row.get("legacy_record_id")),
            "legacy_pid": clean(row.get("legacy_pid")),
            "source_family": clean(row.get("source_family")),
            "document_no": clean(row.get("document_no")),
            "snapshot_date": clean(row.get("snapshot_date")) or False,
            "legacy_state": clean(row.get("legacy_state")),
            "subject": clean(row.get("subject")),
            "project_id": project_id,
            "legacy_project_id": legacy_project_id,
            "legacy_project_name": clean(row.get("legacy_project_name")),
            "source_account_balance_total": as_float(row.get("source_account_balance_total", "")),
            "source_bank_balance_total": as_float(row.get("source_bank_balance_total", "")),
            "source_bank_system_difference": as_float(row.get("source_bank_system_difference", "")),
            "note": clean(row.get("note")),
            "import_batch": clean(row.get("import_batch")) or "legacy_fund_daily_snapshot_asset_v1",
        }
    )
    existing_keys.add(key)
    if len(buffer) >= batch_size:
        Model.create(buffer)
        created += len(buffer)
        buffer = []

if buffer:
    Model.create(buffer)
    created += len(buffer)

env.cr.commit()  # noqa: F821
status = "PASS" if created + skipped == expected_rows else "FAIL"
payload = {
    "status": status,
    "mode": "fresh_db_legacy_fund_daily_snapshot_replay_write",
    "database": env.cr.dbname,  # noqa: F821
    "input_rows": len(rows),
    "created_rows": created,
    "skipped_existing": skipped,
    "db_writes": created,
    "decision": "legacy_fund_daily_snapshot_replay_write_complete" if status == "PASS" else "STOP_REVIEW_REQUIRED",
}
write_json(OUTPUT_JSON, payload)
print("FRESH_DB_LEGACY_FUND_DAILY_SNAPSHOT_REPLAY_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
