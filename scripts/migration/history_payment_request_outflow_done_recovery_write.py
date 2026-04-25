#!/usr/bin/env python3
"""Promote historical outflow requests from approved to done using business-paid facts."""

from __future__ import annotations

import csv
import json
import os
import re
from datetime import datetime, time, timezone
from decimal import Decimal
from pathlib import Path


LEGACY_OUTFLOW_RE = re.compile(r"legacy_outflow_id=([^;]+)")


def repo_root() -> Path:
    env_root = os.getenv("MIGRATION_REPO_ROOT")
    candidates = []
    if env_root:
        candidates.append(Path(env_root))
    candidates.extend([Path("/mnt"), Path.cwd()])
    for candidate in candidates:
        if (candidate / "artifacts/migration/history_payment_request_outflow_done_recovery_payload_v1.csv").exists():
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


def parse_legacy_outflow_id(note: str) -> str:
    matched = LEGACY_OUTFLOW_RE.search(clean(note))
    return clean(matched.group(1)) if matched else ""


def ledger_paid_at(rec) -> datetime:
    if rec.date_request:
        return datetime.combine(rec.date_request, time(12, 0), tzinfo=timezone.utc)
    return datetime.now(timezone.utc)


REPO_ROOT = repo_root()
ARTIFACT_ROOT = resolve_artifact_root(REPO_ROOT)
PAYLOAD_CSV = REPO_ROOT / "artifacts/migration/history_payment_request_outflow_done_recovery_payload_v1.csv"
OUTPUT_JSON = ARTIFACT_ROOT / "history_payment_request_outflow_done_recovery_write_result_v1.json"
ROLLBACK_CSV = ARTIFACT_ROOT / "history_payment_request_outflow_done_recovery_rollback_targets_v1.csv"
BLOCKED_CSV = ARTIFACT_ROOT / "history_payment_request_outflow_done_recovery_blocked_rows_v1.csv"

ensure_allowed_db()

Request = env["payment.request"].sudo().with_context(active_test=False)  # noqa: F821
Ledger = env["payment.ledger"].sudo().with_context(active_test=False)  # noqa: F821
payload_rows = read_csv(PAYLOAD_CSV)
runtime_map = {}
for rec in Request.search([("note", "ilike", "[migration:outflow_request_core]")]):
    legacy_outflow_id = parse_legacy_outflow_id(rec.note or "")
    if legacy_outflow_id:
        runtime_map[f"legacy_outflow_sc_{legacy_outflow_id}"] = rec

missing_runtime = [row["external_id"] for row in payload_rows if row["external_id"] not in runtime_map]
if missing_runtime:
    raise RuntimeError({"missing_runtime_requests": missing_runtime[:20], "missing_count": len(missing_runtime)})

existing_ledger_map = {}
for ledger in Ledger.search([("payment_request_id", "in", [runtime_map[row["external_id"]].id for row in payload_rows])]):
    existing_ledger_map[int(ledger.payment_request_id.id)] = ledger

update_ids: list[int] = []
ledger_rows: list[tuple[int, str, datetime, str, str]] = []
rollback_rows: list[dict[str, object]] = []
blocked_rows: list[dict[str, object]] = []
already_done = 0
already_has_ledger = 0

for row in payload_rows:
    rec = runtime_map[row["external_id"]]
    ledger_amount = str(Decimal(clean(row["ledger_amount"])))
    if clean(rec.state) not in {"approved", "done"}:
        blocked_rows.append(
            {
                "payment_request_id": rec.id,
                "external_id": row["external_id"],
                "state": clean(rec.state),
                "validation_status": clean(rec.validation_status),
                "reason": "state_not_promotable_to_done",
            }
        )
        continue
    if int(rec.id) in existing_ledger_map:
        already_has_ledger += 1
    else:
        paid_at = ledger_paid_at(rec)
        ledger_rows.append(
            (
                int(rec.id),
                ledger_amount,
                paid_at,
                clean(row["sample_downstream_external_ids"])[:128],
                (
                    "[migration:outflow_done_recovery] "
                    f"external_id={clean(row['external_id'])}; "
                    f"business_fact={clean(row['business_fact'])}; "
                    "runtime_ledger_materialized=true"
                ),
            )
        )
    if clean(rec.state) == "done" and clean(rec.validation_status) == "validated":
        already_done += 1
        continue
    update_ids.append(int(rec.id))
    rollback_rows.append(
        {
            "payment_request_id": rec.id,
            "external_id": row["external_id"],
            "old_state": clean(rec.state),
            "new_state": "done",
            "old_validation_status": clean(rec.validation_status),
            "new_validation_status": "validated",
            "ledger_amount": ledger_amount,
            "business_fact": clean(row["business_fact"]),
        }
    )

if ledger_rows:
    env.cr.executemany(  # noqa: F821
        """
        INSERT INTO payment_ledger
            (payment_request_id, amount, paid_at, ref, note, create_uid, write_uid, create_date, write_date)
        VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        ON CONFLICT (payment_request_id) DO NOTHING
        """,
        [row + (env.user.id, env.user.id) for row in ledger_rows],  # noqa: F821
    )
if update_ids:
    env.cr.execute(  # noqa: F821
        """
        UPDATE payment_request
           SET state = %s,
               validation_status = %s,
               write_uid = %s,
               write_date = NOW()
         WHERE id = ANY(%s)
           AND state IN (%s, %s)
        """,
        ["done", "validated", env.user.id, update_ids, "approved", "done"],  # noqa: F821
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
        "old_validation_status",
        "new_validation_status",
        "ledger_amount",
        "business_fact",
    ],
    rollback_rows,
)
write_csv(
    BLOCKED_CSV,
    ["payment_request_id", "external_id", "state", "validation_status", "reason"],
    blocked_rows,
)
payload = {
    "status": "PASS",
    "mode": "history_payment_request_outflow_done_recovery_write",
    "database": env.cr.dbname,  # noqa: F821
    "input_rows": len(payload_rows),
    "promoted_rows": len(rollback_rows),
    "ledger_rows_created_attempted": len(ledger_rows),
    "already_done_rows": already_done,
    "already_has_ledger_rows": already_has_ledger,
    "blocked_rows": len(blocked_rows),
    "artifacts": {
        "rollback_csv": str(ROLLBACK_CSV),
        "blocked_csv": str(BLOCKED_CSV),
    },
    "boundary": {
        "target_state": "done",
        "target_validation_status": "validated",
        "tier_review_written": False,
        "settlement_written": False,
        "runtime_callbacks_triggered": False,
        "ledger_write_mode": "historical_business_fact_materialization",
    },
    "decision": "outflow_request_done_recovery_complete",
}
write_json(OUTPUT_JSON, payload)
print(json.dumps(payload, ensure_ascii=False, indent=2))
