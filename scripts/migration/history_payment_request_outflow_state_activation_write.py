#!/usr/bin/env python3
"""Promote historical outflow-request carriers from draft to submit without live approval runtime."""

from __future__ import annotations

import csv
import json
import os
import re
from pathlib import Path


LEGACY_OUTFLOW_RE = re.compile(r"legacy_outflow_id=([^;]+)")


def repo_root() -> Path:
    env_root = os.getenv("MIGRATION_REPO_ROOT")
    candidates = []
    if env_root:
        candidates.append(Path(env_root))
    candidates.extend([Path("/mnt"), Path.cwd()])
    for candidate in candidates:
        if (candidate / "artifacts/migration/history_payment_request_outflow_state_activation_payload_v1.csv").exists():
            return candidate
    return Path.cwd()


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


def parse_legacy_outflow_id(note: str) -> str:
    matched = LEGACY_OUTFLOW_RE.search(clean(note))
    return clean(matched.group(1)) if matched else ""


REPO_ROOT = repo_root()
ARTIFACT_ROOT = resolve_artifact_root(REPO_ROOT)
PAYLOAD_CSV = REPO_ROOT / "artifacts/migration/history_payment_request_outflow_state_activation_payload_v1.csv"
OUTPUT_JSON = ARTIFACT_ROOT / "history_payment_request_outflow_state_activation_write_result_v1.json"
ROLLBACK_CSV = ARTIFACT_ROOT / "history_payment_request_outflow_state_activation_rollback_targets_v1.csv"
BLOCKED_CSV = ARTIFACT_ROOT / "history_payment_request_outflow_state_activation_blocked_rows_v1.csv"

ensure_allowed_db()

Request = env["payment.request"].sudo().with_context(active_test=False)  # noqa: F821

payload_rows = read_csv(PAYLOAD_CSV)
candidate_by_legacy = {clean(row.get("legacy_outflow_id")): row for row in payload_rows if clean(row.get("legacy_outflow_id"))}
if len(candidate_by_legacy) != len(payload_rows):
    raise RuntimeError({"duplicate_or_missing_legacy_outflow_ids": True, "payload_rows": len(payload_rows), "unique_ids": len(candidate_by_legacy)})

runtime_map: dict[str, object] = {}
duplicates: dict[str, list[int]] = {}
for rec in Request.search([("note", "ilike", "[migration:outflow_request_core]")]):
    legacy_outflow_id = parse_legacy_outflow_id(rec.note or "")
    if not legacy_outflow_id:
        continue
    existing = runtime_map.get(legacy_outflow_id)
    if existing:
        duplicates.setdefault(legacy_outflow_id, [existing.id]).append(rec.id)
        continue
    runtime_map[legacy_outflow_id] = rec

if duplicates:
    raise RuntimeError({"duplicate_runtime_outflow_requests": {key: value[:10] for key, value in list(duplicates.items())[:20]}})

missing_runtime = sorted(set(candidate_by_legacy) - set(runtime_map))
if missing_runtime:
    raise RuntimeError({"missing_runtime_requests": missing_runtime[:30], "missing_count": len(missing_runtime)})

promoted_rows: list[dict[str, object]] = []
skipped_non_draft = 0
promote_ids: list[int] = []
id_rows: list[tuple[int, dict[str, str], object]] = []

for legacy_outflow_id, row in sorted(candidate_by_legacy.items()):
    rec = runtime_map[legacy_outflow_id]
    if clean(rec.state) != "draft":
        skipped_non_draft += 1
        continue
    promote_ids.append(int(rec.id))
    id_rows.append((int(rec.id), row, rec))

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
            ["submit", env.user.id, batch_ids, "draft"],  # noqa: F821
        )
    env.invalidate_all()  # noqa: F821

for payment_request_id, row, rec in id_rows:
    refreshed = Request.browse(payment_request_id)
    promoted_rows.append(
        {
            "payment_request_id": payment_request_id,
            "legacy_outflow_id": clean(row.get("legacy_outflow_id")),
            "document_no": clean(row.get("document_no")),
            "workflow_row_count": clean(row.get("workflow_row_count")),
            "old_state": "draft",
            "new_state": clean(refreshed.state),
        }
    )

env.cr.commit()  # noqa: F821

write_csv(
    ROLLBACK_CSV,
    ["payment_request_id", "legacy_outflow_id", "document_no", "workflow_row_count", "old_state", "new_state"],
    promoted_rows,
)
write_csv(
    BLOCKED_CSV,
    ["payment_request_id", "legacy_outflow_id", "document_no", "workflow_row_count", "state", "reason"],
    [],
)

payload = {
    "status": "PASS",
    "mode": "history_payment_request_outflow_state_activation_write",
    "database": env.cr.dbname,  # noqa: F821
    "input_rows": len(payload_rows),
    "promoted_rows": len(promoted_rows),
    "skipped_non_draft": skipped_non_draft,
    "blocked_rows": 0,
    "blocked_reason_counts": {},
    "artifacts": {
        "rollback_csv": str(ROLLBACK_CSV),
        "blocked_csv": str(BLOCKED_CSV),
    },
    "decision": "outflow_request_state_activation_complete",
    "boundary": {
        "target_state": "submit",
        "tier_review_written": False,
        "validation_status_written": False,
        "runtime_callbacks_triggered": False,
        "funding_gate_enforced": False,
    },
}
write_json(OUTPUT_JSON, payload)
print(json.dumps(payload, ensure_ascii=False, indent=2))
