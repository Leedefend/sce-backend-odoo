#!/usr/bin/env python3
"""Project legacy actual outflow and receipt requests into treasury ledger."""

from __future__ import annotations

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
        if (candidate / "addons/smart_construction_core/__manifest__.py").exists():
            return candidate
    return Path.cwd()


def ensure_allowed_db() -> None:
    allowlist = {
        item.strip()
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_migration_fresh,sc_demo").split(",")
        if item.strip()
    }
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_treasury_projection": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def scalar(sql: str, params: list[object] | None = None) -> int:
    env.cr.execute(sql, params or [])  # noqa: F821
    return int(env.cr.fetchone()[0] or 0)  # noqa: F821


REPO_ROOT = repo_root()
ARTIFACT_ROOT = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", str(REPO_ROOT / "artifacts/migration")))
OUTPUT_JSON = ARTIFACT_ROOT / "fresh_db_treasury_ledger_projection_write_result_v1.json"

ensure_allowed_db()
uid = env.uid  # noqa: F821

before = scalar("SELECT COUNT(*) FROM sc_treasury_ledger")
candidates = scalar(
    """
    SELECT COUNT(*)
    FROM payment_request
    WHERE amount > 0
      AND (
        note LIKE '%%[migration:actual_outflow_core]%%'
        OR note LIKE '%%[migration:receipt_core]%%'
      )
    """
)
nonpositive = scalar(
    """
    SELECT COUNT(*)
    FROM payment_request
    WHERE amount <= 0
      AND (
        note LIKE '%%[migration:actual_outflow_core]%%'
        OR note LIKE '%%[migration:receipt_core]%%'
      )
    """
)

env.cr.execute(  # noqa: F821
    """
    INSERT INTO sc_treasury_ledger (
      name, date, project_id, partner_id, settlement_id, payment_request_id,
      direction, amount, currency_id, state, note, source_kind,
      legacy_record_id, legacy_source_ref,
      create_uid, create_date, write_uid, write_date
    )
    SELECT
      'HIST-TL-' || pr.id::text AS name,
      COALESCE(pr.date_request, pr.create_date::date, CURRENT_DATE) AS date,
      pr.project_id,
      pr.partner_id,
      pr.settlement_id,
      pr.id AS payment_request_id,
      CASE WHEN pr.type = 'receive' THEN 'in' ELSE 'out' END AS direction,
      pr.amount,
      pr.currency_id,
      'posted' AS state,
      pr.note,
      CASE
        WHEN pr.note LIKE '%%[migration:receipt_core]%%' THEN 'legacy_receipt'
        ELSE 'legacy_actual_outflow'
      END AS source_kind,
      CASE
        WHEN pr.note LIKE '%%legacy_receipt_id=%%'
          THEN substring(pr.note from 'legacy_receipt_id=([^;[:space:]]+)')
        WHEN pr.note LIKE '%%legacy_actual_outflow_id=%%'
          THEN substring(pr.note from 'legacy_actual_outflow_id=([^;[:space:]]+)')
        ELSE NULL
      END AS legacy_record_id,
      CASE
        WHEN pr.note LIKE '%%legacy_receipt_id=%%' THEN 'legacy_receipt_id'
        WHEN pr.note LIKE '%%legacy_actual_outflow_id=%%' THEN 'legacy_actual_outflow_id'
        ELSE NULL
      END AS legacy_source_ref,
      %s, NOW(), %s, NOW()
    FROM payment_request pr
    WHERE pr.amount > 0
      AND pr.project_id IS NOT NULL
      AND pr.partner_id IS NOT NULL
      AND (
        pr.note LIKE '%%[migration:actual_outflow_core]%%'
        OR pr.note LIKE '%%[migration:receipt_core]%%'
      )
    ON CONFLICT (payment_request_id) DO UPDATE SET
      name = EXCLUDED.name,
      date = EXCLUDED.date,
      project_id = EXCLUDED.project_id,
      partner_id = EXCLUDED.partner_id,
      settlement_id = EXCLUDED.settlement_id,
      direction = EXCLUDED.direction,
      amount = EXCLUDED.amount,
      currency_id = EXCLUDED.currency_id,
      state = EXCLUDED.state,
      note = EXCLUDED.note,
      source_kind = EXCLUDED.source_kind,
      legacy_record_id = EXCLUDED.legacy_record_id,
      legacy_source_ref = EXCLUDED.legacy_source_ref,
      write_uid = EXCLUDED.write_uid,
      write_date = NOW()
    """,
    [uid, uid],
)

env.cr.commit()  # noqa: F821

after = scalar("SELECT COUNT(*) FROM sc_treasury_ledger")
state_counts = {}
env.cr.execute("SELECT source_kind, direction, COUNT(*) FROM sc_treasury_ledger GROUP BY source_kind, direction ORDER BY source_kind, direction")  # noqa: F821
for source_kind, direction, count in env.cr.fetchall():  # noqa: F821
    state_counts[f"{source_kind or '__empty__'}:{direction or '__empty__'}"] = int(count)

payload = {
    "status": "PASS" if after >= candidates else "FAIL",
    "mode": "fresh_db_treasury_ledger_projection_write",
    "database": env.cr.dbname,  # noqa: F821
    "before_rows": before,
    "after_rows": after,
    "candidate_cash_requests": candidates,
    "nonpositive_cash_requests_skipped": nonpositive,
    "created_rows": max(after - before, 0),
    "updated_or_existing_rows": min(before, candidates),
    "source_direction_counts": state_counts,
    "db_writes": candidates,
    "decision": "treasury_ledger_projection_complete" if after >= candidates else "STOP_REVIEW_REQUIRED",
}
write_json(OUTPUT_JSON, payload)
print("FRESH_DB_TREASURY_LEDGER_PROJECTION_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
