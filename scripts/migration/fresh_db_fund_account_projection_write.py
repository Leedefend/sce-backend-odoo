#!/usr/bin/env python3
"""Project legacy account master records into formal fund accounts."""

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
        raise RuntimeError({"db_name_not_allowed_for_replay": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


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


def scalar(sql: str, params: list[object] | None = None) -> object:
    env.cr.execute(sql, params or [])  # noqa: F821
    row = env.cr.fetchone()  # noqa: F821
    return row[0] if row else None


ensure_allowed_db()
artifact_root = resolve_artifact_root()
output_json = artifact_root / "fresh_db_fund_account_projection_write_result_v1.json"
currency_id = env.ref("base.CNY", raise_if_not_found=False).id  # noqa: F821
company_id = env.company.id  # noqa: F821

before = int(scalar("SELECT COUNT(*) FROM sc_fund_account") or 0)
legacy_before = int(scalar("SELECT COUNT(*) FROM sc_fund_account WHERE source_origin = 'legacy'") or 0)

env.cr.execute(  # noqa: F821
    """
    WITH source_account AS (
        SELECT
            a.*,
            latest.current_account_balance,
            latest.current_bank_balance,
            latest.document_date AS latest_balance_date,
            latest.legacy_line_id AS latest_balance_line_id
        FROM sc_legacy_account_master a
        LEFT JOIN LATERAL (
            SELECT
                l.current_account_balance,
                l.current_bank_balance,
                l.document_date,
                l.legacy_line_id
            FROM sc_legacy_fund_daily_line l
            WHERE l.active IS TRUE
              AND (
                    NULLIF(l.account_legacy_id, '') = NULLIF(a.legacy_account_id, '')
                 OR NULLIF(l.bank_account_no, '') = NULLIF(a.account_no, '')
                 OR lower(trim(NULLIF(l.account_name, ''))) = lower(trim(NULLIF(a.name, '')))
              )
            ORDER BY l.document_date DESC NULLS LAST, l.id DESC
            LIMIT 1
        ) latest ON TRUE
        WHERE a.legacy_account_id IS NOT NULL
          AND a.legacy_account_id <> ''
    )
    INSERT INTO sc_fund_account (
      name, account_no, account_type, bank_name, project_id, company_id,
      opening_balance, current_account_balance, current_bank_balance,
      balance_as_of_date, current_balance_source, currency_id,
      is_default, fixed_account, state, note,
      source_origin, legacy_source_model, legacy_source_table, legacy_record_id,
      legacy_account_id, legacy_state, legacy_project_id, active,
      create_uid, write_uid, create_date, write_date
    )
    SELECT
      COALESCE(NULLIF(a.name, ''), a.legacy_account_id),
      NULLIF(a.account_no, ''),
      NULLIF(a.account_type, ''),
      NULLIF(a.bank_name, ''),
      a.project_id,
      %s,
      COALESCE(a.opening_balance, 0),
      COALESCE(a.current_account_balance, a.opening_balance, 0),
      COALESCE(a.current_bank_balance, 0),
      a.latest_balance_date,
      CASE WHEN a.latest_balance_line_id IS NOT NULL THEN 'fund_daily_report' ELSE 'opening' END,
      %s,
      COALESCE(a.is_default, FALSE),
      COALESCE(a.fixed_account, FALSE),
      CASE WHEN COALESCE(a.active, TRUE) THEN 'active' ELSE 'inactive' END,
      NULLIF(a.note, ''),
      'legacy',
      'sc.legacy.account.master',
      a.source_table,
      a.legacy_account_id,
      a.legacy_account_id,
      NULLIF(a.legacy_state, ''),
      NULLIF(a.project_legacy_id, ''),
      a.active,
      1,
      1,
      NOW(),
      NOW()
    FROM source_account a
    ON CONFLICT (legacy_source_model, legacy_record_id)
    DO UPDATE SET
      name = EXCLUDED.name,
      account_no = EXCLUDED.account_no,
      account_type = EXCLUDED.account_type,
      bank_name = EXCLUDED.bank_name,
      project_id = EXCLUDED.project_id,
      company_id = EXCLUDED.company_id,
      opening_balance = EXCLUDED.opening_balance,
      current_account_balance = EXCLUDED.current_account_balance,
      current_bank_balance = EXCLUDED.current_bank_balance,
      balance_as_of_date = EXCLUDED.balance_as_of_date,
      current_balance_source = EXCLUDED.current_balance_source,
      currency_id = EXCLUDED.currency_id,
      is_default = EXCLUDED.is_default,
      fixed_account = EXCLUDED.fixed_account,
      state = EXCLUDED.state,
      note = EXCLUDED.note,
      legacy_source_table = EXCLUDED.legacy_source_table,
      legacy_account_id = EXCLUDED.legacy_account_id,
      legacy_state = EXCLUDED.legacy_state,
      legacy_project_id = EXCLUDED.legacy_project_id,
      active = EXCLUDED.active,
      write_uid = 1,
      write_date = NOW()
    """,
    [company_id, currency_id],
)

env.cr.commit()  # noqa: F821

after = int(scalar("SELECT COUNT(*) FROM sc_fund_account") or 0)
legacy_after = int(scalar("SELECT COUNT(*) FROM sc_fund_account WHERE source_origin = 'legacy'") or 0)
legacy_source = int(scalar("SELECT COUNT(*) FROM sc_legacy_account_master") or 0)
with_project = int(scalar("SELECT COUNT(*) FROM sc_fund_account WHERE source_origin = 'legacy' AND project_id IS NOT NULL") or 0)
payload = {
    "status": "PASS",
    "mode": "fresh_db_fund_account_projection_write",
    "database": env.cr.dbname,  # noqa: F821
    "before": before,
    "after": after,
    "delta": after - before,
    "legacy_before": legacy_before,
    "legacy_after": legacy_after,
    "legacy_delta": legacy_after - legacy_before,
    "legacy_source_rows": legacy_source,
    "legacy_with_project": with_project,
    "decision": "fund_account_projection_complete" if legacy_after >= legacy_source else "fund_account_projection_gap",
}
write_json(output_json, payload)
print("FUND_ACCOUNT_PROJECTION_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
