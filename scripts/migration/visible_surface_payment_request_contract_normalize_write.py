#!/usr/bin/env python3
"""Backfill payment request header contract from unique line contract facts."""

from __future__ import annotations

import json
import os
from pathlib import Path


def artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT") or os.getenv("ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.append(Path("/mnt/artifacts/migration"))
    candidates.append(Path(f"/tmp/history_continuity/{env.cr.dbname}/adhoc"))  # noqa: F821
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return candidate
        except Exception:
            continue
    return Path(f"/tmp/history_continuity/{env.cr.dbname}/adhoc")  # noqa: F821


def scalar(sql: str) -> int:
    env.cr.execute(sql)  # noqa: F821
    row = env.cr.fetchone()  # noqa: F821
    return int(row[0] or 0) if row else 0


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


allowlist = {item.strip() for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "").split(",") if item.strip()}
if allowlist and env.cr.dbname not in allowlist:  # noqa: F821
    raise RuntimeError({"db_name_not_allowed_for_visible_surface_write": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821

pay_total = scalar("SELECT COUNT(*) FROM payment_request WHERE type = 'pay'")
before_with_contract = scalar("SELECT COUNT(*) FROM payment_request WHERE type = 'pay' AND contract_id IS NOT NULL")
backfillable_before = scalar(
    """
    WITH line_contract AS (
        SELECT request_id
          FROM payment_request_line
         WHERE contract_id IS NOT NULL
         GROUP BY request_id
        HAVING COUNT(DISTINCT contract_id) = 1
    )
    SELECT COUNT(*)
      FROM payment_request AS request
      JOIN line_contract AS line ON line.request_id = request.id
     WHERE request.type = 'pay'
       AND request.contract_id IS NULL
    """
)
multi_contract_skipped = scalar(
    """
    WITH line_contract AS (
        SELECT request_id
          FROM payment_request_line
         WHERE contract_id IS NOT NULL
         GROUP BY request_id
        HAVING COUNT(DISTINCT contract_id) > 1
    )
    SELECT COUNT(*)
      FROM payment_request AS request
      JOIN line_contract AS line ON line.request_id = request.id
     WHERE request.type = 'pay'
       AND request.contract_id IS NULL
    """
)

env.cr.execute(  # noqa: F821
    """
    WITH line_contract AS (
        SELECT request_id, MIN(contract_id) AS contract_id
          FROM payment_request_line
         WHERE contract_id IS NOT NULL
         GROUP BY request_id
        HAVING COUNT(DISTINCT contract_id) = 1
    )
    UPDATE payment_request AS request
       SET contract_id = line.contract_id,
           write_uid = 1,
           write_date = NOW()
      FROM line_contract AS line
     WHERE request.id = line.request_id
       AND request.type = 'pay'
       AND request.contract_id IS NULL
    """
)
updated = env.cr.rowcount  # noqa: F821
env.cr.commit()  # noqa: F821

after_with_contract = scalar("SELECT COUNT(*) FROM payment_request WHERE type = 'pay' AND contract_id IS NOT NULL")
after_without_contract = scalar("SELECT COUNT(*) FROM payment_request WHERE type = 'pay' AND contract_id IS NULL")
payload = {
    "status": "PASS",
    "mode": "visible_surface_payment_request_contract_normalize_write",
    "database": env.cr.dbname,  # noqa: F821
    "pay_request_total": pay_total,
    "before_with_contract": before_with_contract,
    "after_with_contract": after_with_contract,
    "after_without_contract": after_without_contract,
    "backfillable_before": backfillable_before,
    "updated_rows": updated,
    "multi_contract_skipped": multi_contract_skipped,
    "decision": "payment_request_header_contract_backfilled_only_when_detail_lines_have_one_unique_contract",
}
write_json(artifact_root() / "visible_surface_payment_request_contract_normalize_write_result_v1.json", payload)
print("VISIBLE_SURFACE_PAYMENT_REQUEST_CONTRACT_NORMALIZE_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
