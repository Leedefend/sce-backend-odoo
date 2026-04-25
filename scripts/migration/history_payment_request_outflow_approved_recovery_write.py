#!/usr/bin/env python3
"""Promote historical outflow requests from submit to approved without live approval runtime."""

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
        if (candidate / "artifacts/migration/history_payment_request_outflow_approved_recovery_payload_v1.csv").exists():
            return candidate
    return Path.cwd()


def clean(value: object) -> str:
    return "" if value is None else str(value).strip()


def resolve_artifact_root(repo_root_path: Path) -> Path:
    env_root = clean(os.getenv("MIGRATION_ARTIFACT_ROOT"))
    candidates = []
    if env_root:
        candidates.append(Path(env_root))
    candidates.extend(
        [
            repo_root_path / "artifacts/migration",
            Path(f"/tmp/history_continuity/{env.cr.dbname}/adhoc"),  # noqa: F821
        ]
    )
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_test"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink()
            return candidate
        except OSError:
            continue
    raise RuntimeError({"artifact_root_not_writable": [str(item) for item in candidates]})


def ensure_allowed_db() -> None:
    allowlist = {
        item.strip()
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_demo").split(",")
        if item.strip()
    }
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_replay": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


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


REPO_ROOT = repo_root()
ARTIFACT_ROOT = resolve_artifact_root(REPO_ROOT)
PAYLOAD_CSV = REPO_ROOT / "artifacts/migration/history_payment_request_outflow_approved_recovery_payload_v1.csv"
OUTPUT_JSON = ARTIFACT_ROOT / "history_payment_request_outflow_approved_recovery_write_result_v1.json"
ROLLBACK_CSV = ARTIFACT_ROOT / "history_payment_request_outflow_approved_recovery_rollback_targets_v1.csv"
BLOCKED_CSV = ARTIFACT_ROOT / "history_payment_request_outflow_approved_recovery_blocked_rows_v1.csv"

ensure_allowed_db()

Request = env["payment.request"].sudo().with_context(active_test=False)  # noqa: F821
payload_rows = read_csv(PAYLOAD_CSV)
runtime_map = {}
for rec in Request.search([("note", "ilike", "[migration:outflow_request_core]")]):
    note = clean(rec.note)
    marker = "[migration:outflow_request_core] "
    if marker not in note:
        continue
    legacy_marker = clean(note.split("legacy_outflow_id=", 1)[1].split(";", 1)[0]) if "legacy_outflow_id=" in note else ""
    if legacy_marker:
        runtime_map[f"legacy_outflow_sc_{legacy_marker}"] = rec

missing_runtime = [row["external_id"] for row in payload_rows if row["external_id"] not in runtime_map]
if missing_runtime:
    raise RuntimeError({"missing_runtime_requests": missing_runtime[:20], "missing_count": len(missing_runtime)})

promote_ids = []
rollback_rows = []
blocked_rows = []
skipped_non_submit = 0
for row in payload_rows:
    rec = runtime_map[row["external_id"]]
    if clean(rec.state) != "submit":
        skipped_non_submit += 1
        continue
    promote_ids.append(int(rec.id))
    rollback_rows.append(
        {
            "payment_request_id": rec.id,
            "external_id": row["external_id"],
            "old_state": "submit",
            "new_state": "approved",
            "final_approval_fact": row["final_approval_fact"],
            "actual_outflow_count": row["actual_outflow_count"],
            "actual_outflow_amount": row["actual_outflow_amount"],
            "sample_downstream_external_ids": row["sample_downstream_external_ids"],
        }
    )

if promote_ids:
    batch_size = 1000
    for start in range(0, len(promote_ids), batch_size):
        batch_ids = promote_ids[start : start + batch_size]
        env.cr.execute(  # noqa: F821
            """
            UPDATE payment_request
               SET state = %s,
                   write_uid = %s,
                   write_date = NOW()
             WHERE id = ANY(%s)
               AND state = %s
            """,
            ["approved", env.user.id, batch_ids, "submit"],  # noqa: F821
        )
    env.invalidate_all()  # noqa: F821

env.cr.commit()  # noqa: F821

write_csv(
    ROLLBACK_CSV,
    [
        "payment_request_id",
        "external_id",
        "old_state",
        "new_state",
        "final_approval_fact",
        "actual_outflow_count",
        "actual_outflow_amount",
        "sample_downstream_external_ids",
    ],
    rollback_rows,
)
write_csv(
    BLOCKED_CSV,
    ["payment_request_id", "external_id", "state", "reason"],
    blocked_rows,
)
payload = {
    "status": "PASS",
    "mode": "history_payment_request_outflow_approved_recovery_write",
    "database": env.cr.dbname,  # noqa: F821
    "input_rows": len(payload_rows),
    "promoted_rows": len(rollback_rows),
    "skipped_non_submit": skipped_non_submit,
    "blocked_rows": 0,
    "artifacts": {
        "rollback_csv": str(ROLLBACK_CSV),
        "blocked_csv": str(BLOCKED_CSV),
    },
    "boundary": {
        "target_state": "approved",
        "tier_review_written": False,
        "validation_status_written": False,
        "runtime_callbacks_triggered": False,
    },
    "decision": "outflow_request_approved_recovery_complete",
}
write_json(OUTPUT_JSON, payload)
print(json.dumps(payload, ensure_ascii=False, indent=2))
