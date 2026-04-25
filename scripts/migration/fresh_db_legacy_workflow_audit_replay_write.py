#!/usr/bin/env python3
"""Replay legacy workflow audit facts into allowed replay databases."""

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
        if (candidate / "artifacts/migration/fresh_db_legacy_workflow_audit_replay_payload_v1.csv").exists():
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


REPO_ROOT = repo_root()
ARTIFACT_ROOT = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", str(REPO_ROOT / "artifacts/migration")))
INPUT_CSV = REPO_ROOT / "artifacts/migration/fresh_db_legacy_workflow_audit_replay_payload_v1.csv"
INPUT_JSON = REPO_ROOT / "artifacts/migration/fresh_db_legacy_workflow_audit_replay_adapter_result_v1.json"
OUTPUT_JSON = ARTIFACT_ROOT / "fresh_db_legacy_workflow_audit_replay_write_result_v1.json"

ensure_allowed_db()
adapter = json.loads(INPUT_JSON.read_text(encoding="utf-8"))
rows = read_csv(INPUT_CSV)
expected_rows = int(adapter["expected_rows"])

Model = env["sc.legacy.workflow.audit"].sudo().with_context(active_test=False)  # noqa: F821
existing_ids = {
    clean(rec["legacy_workflow_id"])
    for rec in Model.search_read([("legacy_workflow_id", "!=", False)], ["legacy_workflow_id"])
}

created = 0
skipped = 0
buffer: list[dict[str, object]] = []
batch_size = 1000
for row in rows:
    legacy_workflow_id = clean(row.get("legacy_workflow_id"))
    if legacy_workflow_id in existing_ids:
        skipped += 1
        continue
    vals = {
        "legacy_workflow_id": legacy_workflow_id,
        "legacy_pid": clean(row.get("legacy_pid")),
        "legacy_djid": clean(row.get("legacy_djid")),
        "legacy_business_id": clean(row.get("legacy_business_id")),
        "legacy_source_table": clean(row.get("legacy_source_table")),
        "legacy_detail_status_id": clean(row.get("legacy_detail_status_id")),
        "legacy_detail_step_id": clean(row.get("legacy_detail_step_id")),
        "legacy_setup_step_id": clean(row.get("legacy_setup_step_id")),
        "legacy_template_id": clean(row.get("legacy_template_id")),
        "legacy_step_name": clean(row.get("legacy_step_name")),
        "legacy_template_name": clean(row.get("legacy_template_name")),
        "target_model": clean(row.get("target_model")),
        "target_external_id": clean(row.get("target_external_id")),
        "target_lane": clean(row.get("target_lane")),
        "actor_legacy_user_id": clean(row.get("actor_legacy_user_id")),
        "actor_name": clean(row.get("actor_name")),
        "approved_at": clean(row.get("approved_at")) or False,
        "received_at": clean(row.get("received_at")) or False,
        "action_classification": clean(row.get("action_classification")),
        "legacy_status": clean(row.get("legacy_status")),
        "legacy_back_type": clean(row.get("legacy_back_type")),
        "legacy_approval_type": clean(row.get("legacy_approval_type")),
        "approval_note": clean(row.get("approval_note")),
        "import_batch": clean(row.get("import_batch")) or "legacy_workflow_audit_asset_v1",
    }
    buffer.append(vals)
    existing_ids.add(legacy_workflow_id)
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
    "mode": "fresh_db_legacy_workflow_audit_replay_write",
    "database": env.cr.dbname,  # noqa: F821
    "input_rows": len(rows),
    "created_rows": created,
    "skipped_existing": skipped,
    "db_writes": created,
    "decision": "legacy_workflow_audit_replay_write_complete" if status == "PASS" else "STOP_REVIEW_REQUIRED",
}
write_json(OUTPUT_JSON, payload)
print("FRESH_DB_LEGACY_WORKFLOW_AUDIT_REPLAY_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
