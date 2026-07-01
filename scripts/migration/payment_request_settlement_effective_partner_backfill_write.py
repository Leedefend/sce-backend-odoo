#!/usr/bin/env python3
"""Align payment request partner anchors with settlement effective partner.

Run with:
  DB_NAME=sc_demo MIGRATION_REPLAY_DB_ALLOWLIST=sc_demo \
    scripts/ops/odoo_shell_exec.sh < scripts/migration/payment_request_settlement_effective_partner_backfill_write.py
"""

from __future__ import annotations

import json
import os
from pathlib import Path


def _artifact_path() -> Path:
    root = Path(os.getenv("MIGRATION_ARTIFACT_ROOT") or "/tmp")
    root.mkdir(parents=True, exist_ok=True)
    return root / "payment_request_settlement_effective_partner_backfill_result.json"


def _db_allowed() -> bool:
    raw = os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST") or os.getenv("DB_NAME") or ""
    allowed = {item.strip() for item in raw.split(",") if item.strip()}
    return env.cr.dbname in allowed  # noqa: F821


if not _db_allowed():
    raise SystemExit(f"database {env.cr.dbname} is not in MIGRATION_REPLAY_DB_ALLOWLIST")  # noqa: F821

env.cr.execute(  # noqa: F821
    """
    UPDATE payment_request AS r
       SET settlement_id = NULL
      FROM sc_settlement_order AS s
     WHERE s.id = r.settlement_id
       AND (
            (r.project_id IS NOT NULL AND s.project_id IS NOT NULL AND r.project_id <> s.project_id)
            OR (r.contract_id IS NOT NULL AND s.contract_id IS NOT NULL AND r.contract_id <> s.contract_id)
       )
    RETURNING r.id
    """
)
detached_rows = env.cr.fetchall()  # noqa: F821

env.cr.execute(  # noqa: F821
    """
    WITH candidates AS (
        SELECT r.id, COALESCE(s.settlement_unit_id, s.partner_id) AS effective_partner_id
          FROM payment_request AS r
          JOIN sc_settlement_order AS s ON s.id = r.settlement_id
         WHERE r.partner_id IS NOT NULL
           AND COALESCE(s.settlement_unit_id, s.partner_id) IS NOT NULL
           AND r.partner_id <> COALESCE(s.settlement_unit_id, s.partner_id)
           AND (r.project_id IS NULL OR s.project_id IS NULL OR r.project_id = s.project_id)
           AND (r.contract_id IS NULL OR s.contract_id IS NULL OR r.contract_id = s.contract_id)
    )
    UPDATE payment_request AS r
       SET partner_id = candidates.effective_partner_id
      FROM candidates
     WHERE r.id = candidates.id
    RETURNING r.id, r.partner_id
    """
)
rows = env.cr.fetchall()  # noqa: F821
updated = len(rows)
errors = []
env.cr.commit()  # noqa: F821

result = {
    "mode": "payment_request_settlement_effective_partner_backfill",
    "status": "ok" if not errors else "failed",
    "detached_scope_mismatch_count": len(detached_rows),
    "candidate_count": updated,
    "updated": updated,
    "error_count": len(errors),
    "errors": errors[:20],
}
output = _artifact_path()
output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, ensure_ascii=False, indent=2))
if errors:
    raise SystemExit(1)
