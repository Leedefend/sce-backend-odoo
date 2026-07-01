#!/usr/bin/env python3
"""Backfill payment execution contract anchors from linked payment requests.

Run with:
  DB_NAME=sc_demo MIGRATION_REPLAY_DB_ALLOWLIST=sc_demo \
    scripts/ops/odoo_shell_exec.sh < scripts/migration/payment_execution_request_contract_backfill_write.py
"""

from __future__ import annotations

import json
import os
from pathlib import Path


def _artifact_path() -> Path:
    root = Path(os.getenv("MIGRATION_ARTIFACT_ROOT") or "/tmp")
    root.mkdir(parents=True, exist_ok=True)
    return root / "payment_execution_request_contract_backfill_result.json"


def _db_allowed() -> bool:
    raw = os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST") or os.getenv("DB_NAME") or ""
    allowed = {item.strip() for item in raw.split(",") if item.strip()}
    return env.cr.dbname in allowed  # noqa: F821


if not _db_allowed():
    raise SystemExit(f"database {env.cr.dbname} is not in MIGRATION_REPLAY_DB_ALLOWLIST")  # noqa: F821

env.cr.execute(  # noqa: F821
    """
    UPDATE sc_payment_execution AS e
       SET contract_id = r.contract_id
      FROM payment_request AS r
     WHERE r.id = e.payment_request_id
       AND e.contract_id IS NULL
       AND r.contract_id IS NOT NULL
       AND (e.project_id IS NULL OR r.project_id IS NULL OR e.project_id = r.project_id)
       AND (e.partner_id IS NULL OR r.partner_id IS NULL OR e.partner_id = r.partner_id)
    RETURNING e.id, e.contract_id
    """
)
rows = env.cr.fetchall()  # noqa: F821
env.cr.commit()  # noqa: F821

result = {
    "mode": "payment_execution_request_contract_backfill",
    "status": "ok",
    "updated": len(rows),
}
output = _artifact_path()
output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, ensure_ascii=False, indent=2))
