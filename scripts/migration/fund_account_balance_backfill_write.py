#!/usr/bin/env python3
"""Initialize formal fund account balances from legacy daily lines.

This is the current-database companion to the fresh DB fund account projection.
It only updates balance state on legacy-origin formal fund accounts and uses the
same matching policy as the read-only readiness audit.
"""

from __future__ import annotations

import json
import os
from pathlib import Path


def ensure_allowed_db() -> None:
    allowlist = {
        item.strip()
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_migration_fresh").split(",")
        if item.strip()
    }
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_balance_backfill": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def resolve_artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
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


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def fetchone_dict(query: str) -> dict[str, object]:
    env.cr.execute(query)  # noqa: F821
    columns = [column.name for column in env.cr.description]  # noqa: F821
    row = env.cr.fetchone()  # noqa: F821
    return dict(zip(columns, row)) if row else {}


def fetchall_dict(query: str) -> list[dict[str, object]]:
    env.cr.execute(query)  # noqa: F821
    columns = [column.name for column in env.cr.description]  # noqa: F821
    return [dict(zip(columns, row)) for row in env.cr.fetchall()]  # noqa: F821


MATCH_CTE = """
WITH formal_account AS (
    SELECT
        f.id,
        f.name,
        f.account_no,
        f.legacy_account_id,
        f.opening_balance,
        f.current_account_balance,
        f.current_bank_balance,
        f.current_balance_source,
        f.balance_as_of_date
    FROM sc_fund_account f
    WHERE f.active IS TRUE
      AND f.source_origin = 'legacy'
),
latest_daily AS (
    SELECT DISTINCT ON (f.id)
        f.id AS fund_account_id,
        l.id AS daily_line_id,
        l.legacy_line_id,
        l.document_date,
        l.current_account_balance AS daily_account_balance,
        l.current_bank_balance AS daily_bank_balance,
        CASE
            WHEN NULLIF(l.account_legacy_id, '') = NULLIF(f.legacy_account_id, '') THEN 'legacy_account_id'
            WHEN NULLIF(l.bank_account_no, '') = NULLIF(f.account_no, '') THEN 'account_no'
            WHEN lower(trim(NULLIF(l.account_name, ''))) = lower(trim(NULLIF(f.name, ''))) THEN 'account_name'
            ELSE 'none'
        END AS match_key
    FROM formal_account f
    JOIN sc_legacy_fund_daily_line l
      ON l.active IS TRUE
     AND (
            NULLIF(l.account_legacy_id, '') = NULLIF(f.legacy_account_id, '')
         OR NULLIF(l.bank_account_no, '') = NULLIF(f.account_no, '')
         OR lower(trim(NULLIF(l.account_name, ''))) = lower(trim(NULLIF(f.name, '')))
     )
    ORDER BY f.id, l.document_date DESC NULLS LAST, l.id DESC
),
expected AS (
    SELECT
        f.*,
        d.daily_line_id,
        d.legacy_line_id,
        d.document_date,
        d.daily_account_balance,
        d.daily_bank_balance,
        d.match_key,
        COALESCE(d.daily_account_balance, f.opening_balance, 0.0) AS expected_account_balance,
        COALESCE(d.daily_bank_balance, 0.0) AS expected_bank_balance,
        CASE WHEN d.daily_line_id IS NOT NULL THEN 'fund_daily_report' ELSE 'opening' END AS expected_balance_source
    FROM formal_account f
    LEFT JOIN latest_daily d ON d.fund_account_id = f.id
)
"""


def summary() -> dict[str, object]:
    return fetchone_dict(
        MATCH_CTE
        + """
        SELECT
            COUNT(*)::integer AS formal_legacy_account_count,
            COUNT(*) FILTER (WHERE daily_line_id IS NOT NULL)::integer AS latest_daily_matched_count,
            COUNT(*) FILTER (WHERE daily_line_id IS NULL)::integer AS latest_daily_missing_count,
            COUNT(*) FILTER (
                WHERE daily_line_id IS NULL
                  AND COALESCE(opening_balance, 0.0) = 0.0
            )::integer AS no_daily_no_opening_count,
            COUNT(*) FILTER (
                WHERE current_account_balance IS DISTINCT FROM expected_account_balance
                   OR current_balance_source IS DISTINCT FROM expected_balance_source
                   OR COALESCE(current_bank_balance, 0.0) IS DISTINCT FROM COALESCE(expected_bank_balance, 0.0)
                   OR balance_as_of_date IS DISTINCT FROM document_date
            )::integer AS current_state_mismatch_count,
            COALESCE(SUM(expected_account_balance), 0.0) AS expected_account_balance_total,
            COALESCE(SUM(expected_bank_balance), 0.0) AS expected_bank_balance_total
        FROM expected
        """
    )


def by_match_key() -> list[dict[str, object]]:
    return fetchall_dict(
        MATCH_CTE
        + """
        SELECT COALESCE(match_key, 'no_daily_match') AS match_key,
               COUNT(*)::integer AS account_count
          FROM expected
         GROUP BY COALESCE(match_key, 'no_daily_match')
         ORDER BY match_key
        """
    )


def apply_backfill() -> list[int]:
    env.cr.execute(  # noqa: F821
        MATCH_CTE
        + """
        , to_update AS (
            SELECT *
              FROM expected
             WHERE current_account_balance IS DISTINCT FROM expected_account_balance
                OR current_balance_source IS DISTINCT FROM expected_balance_source
                OR COALESCE(current_bank_balance, 0.0) IS DISTINCT FROM COALESCE(expected_bank_balance, 0.0)
                OR balance_as_of_date IS DISTINCT FROM document_date
        )
        UPDATE sc_fund_account account
           SET current_account_balance = to_update.expected_account_balance,
               current_bank_balance = to_update.expected_bank_balance,
               balance_as_of_date = to_update.document_date,
               current_balance_source = to_update.expected_balance_source,
               balance_source_operation_id = NULL,
               write_uid = 1,
               write_date = NOW()
          FROM to_update
         WHERE account.id = to_update.id
        RETURNING account.id
        """
    )
    return [row[0] for row in env.cr.fetchall()]  # noqa: F821


ensure_allowed_db()
artifact_root = resolve_artifact_root()
output_json = artifact_root / "fund_account_balance_backfill_write_result_v1.json"

before = summary()
match_key_before = by_match_key()
updated_account_ids = apply_backfill()
env.cr.commit()  # noqa: F821
after = summary()

failures = []
if int(after.get("current_state_mismatch_count") or 0) != 0:
    failures.append("current_state_mismatch_count_after=%s" % after.get("current_state_mismatch_count"))

payload = {
    "status": "PASS" if not failures else "FAIL",
    "mode": "fund_account_balance_backfill_write",
    "database": env.cr.dbname,  # noqa: F821
    "before": before,
    "after": after,
    "by_match_key_before": match_key_before,
    "updated_account_count": len(updated_account_ids),
    "updated_account_ids_sample": updated_account_ids[:50],
    "failures": failures,
    "policy": {
        "scope": "legacy-origin formal fund accounts only",
        "initialization_order": "latest fund daily line, then opening balance",
        "write_fields": "current_account_balance, current_bank_balance, balance_as_of_date, current_balance_source, balance_source_operation_id",
        "transfer_balance_policy": "do not enable transfer debit/credit until opening balance and historical account lines are confirmed",
    },
}
write_json(output_json, payload)
print("FUND_ACCOUNT_BALANCE_BACKFILL_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str))
if failures:
    raise SystemExit(1)
