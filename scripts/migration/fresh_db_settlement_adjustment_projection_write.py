#!/usr/bin/env python3
"""Project legacy deduction adjustment facts into settlement adjustment runtime."""

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


def resolve_artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.append(repo_root() / "artifacts/migration")
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


def ensure_allowed_db() -> None:
    allowlist = {
        item.strip()
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_prod_sim,sc_migration_fresh").split(",")
        if item.strip()
    }
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_projection": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


ensure_allowed_db()
artifact_root = resolve_artifact_root()
output_json = artifact_root / "fresh_db_settlement_adjustment_projection_write_result_v1.json"
uid = env.uid  # noqa: F821
company = env.company  # noqa: F821
currency_id = company.currency_id.id

env.cr.execute("SELECT COUNT(*) FROM sc_settlement_adjustment")  # noqa: F821
before = env.cr.fetchone()[0]  # noqa: F821

env.cr.execute(  # noqa: F821
    """
    INSERT INTO sc_settlement_adjustment (
      name, source_origin, adjustment_type, state,
      project_id, settlement_id, contract_id, partner_id,
      date_adjustment, item_name, account_name,
      amount, signed_amount, currency_id,
      legacy_line_id, legacy_document_no, legacy_document_state,
      legacy_fund_confirmation_id, legacy_source_table, note, active,
      create_uid, create_date, write_uid, write_date
    )
    SELECT
      CONCAT('LEG-ADJ-', COALESCE(NULLIF(l.document_no, ''), l.legacy_line_id)),
      'legacy',
      CASE WHEN COALESCE(l.current_actual_amount, 0) < 0 THEN 'addition' ELSE 'deduction' END,
      CASE WHEN l.document_state = '2' THEN 'legacy_confirmed' ELSE 'draft' END,
      l.project_id,
      NULL,
      NULL,
      NULL,
      COALESCE(l.document_date::date, l.created_time::date, CURRENT_DATE),
      NULLIF(l.adjustment_item_name, ''),
      NULLIF(l.deduction_account, ''),
      ABS(COALESCE(NULLIF(l.current_actual_amount, 0), l.current_planned_amount, 0)),
      CASE
        WHEN COALESCE(l.current_actual_amount, 0) < 0
        THEN ABS(COALESCE(NULLIF(l.current_actual_amount, 0), l.current_planned_amount, 0))
        ELSE -ABS(COALESCE(NULLIF(l.current_actual_amount, 0), l.current_planned_amount, 0))
      END,
      %s,
      l.legacy_line_id,
      NULLIF(l.document_no, ''),
      NULLIF(l.document_state, ''),
      NULLIF(l.fund_confirmation_legacy_id, ''),
      l.source_table,
      CONCAT(
        '[migration:settlement_adjustment] legacy_line_id=', l.legacy_line_id,
        '; legacy_header_id=', COALESCE(l.legacy_header_id, ''),
        '; legacy_project_id=', COALESCE(l.project_legacy_id, ''),
        '; document_state=', COALESCE(l.document_state, ''),
        '; title=', COALESCE(l.title, ''),
        '; historical_runtime_projection=true'
      ),
      l.active,
      %s, NOW(), %s, NOW()
    FROM sc_legacy_deduction_adjustment_line l
    WHERE l.project_id IS NOT NULL
      AND ABS(COALESCE(NULLIF(l.current_actual_amount, 0), l.current_planned_amount, 0)) > 0
    ON CONFLICT (legacy_line_id) DO UPDATE SET
      name = EXCLUDED.name,
      source_origin = EXCLUDED.source_origin,
      adjustment_type = EXCLUDED.adjustment_type,
      state = EXCLUDED.state,
      project_id = EXCLUDED.project_id,
      date_adjustment = EXCLUDED.date_adjustment,
      item_name = EXCLUDED.item_name,
      account_name = EXCLUDED.account_name,
      amount = EXCLUDED.amount,
      signed_amount = EXCLUDED.signed_amount,
      currency_id = EXCLUDED.currency_id,
      legacy_document_no = EXCLUDED.legacy_document_no,
      legacy_document_state = EXCLUDED.legacy_document_state,
      legacy_fund_confirmation_id = EXCLUDED.legacy_fund_confirmation_id,
      legacy_source_table = EXCLUDED.legacy_source_table,
      note = EXCLUDED.note,
      active = EXCLUDED.active,
      write_uid = EXCLUDED.write_uid,
      write_date = NOW()
    """,
    [currency_id, uid, uid],
)
env.cr.commit()  # noqa: F821

env.cr.execute("SELECT COUNT(*) FROM sc_settlement_adjustment")  # noqa: F821
after = env.cr.fetchone()[0]  # noqa: F821
env.cr.execute("SELECT COUNT(*) FROM sc_settlement_adjustment WHERE source_origin = 'legacy'")  # noqa: F821
legacy_rows = env.cr.fetchone()[0]  # noqa: F821
env.cr.execute("SELECT COUNT(*) FROM sc_settlement_adjustment WHERE source_origin = 'legacy' AND project_id IS NOT NULL")  # noqa: F821
legacy_with_project = env.cr.fetchone()[0]  # noqa: F821
env.cr.execute("SELECT COUNT(*) FROM sc_settlement_adjustment WHERE source_origin = 'legacy' AND state = 'legacy_confirmed'")  # noqa: F821
legacy_confirmed = env.cr.fetchone()[0]  # noqa: F821
env.cr.execute("SELECT COALESCE(SUM(signed_amount), 0), COALESCE(SUM(amount), 0) FROM sc_settlement_adjustment WHERE source_origin = 'legacy'")  # noqa: F821
signed_sum, amount_sum = env.cr.fetchone()  # noqa: F821

payload = {
    "status": "PASS",
    "mode": "fresh_db_settlement_adjustment_projection_write",
    "database": env.cr.dbname,  # noqa: F821
    "before": before,
    "after": after,
    "delta": after - before,
    "legacy_rows": legacy_rows,
    "legacy_with_project": legacy_with_project,
    "legacy_confirmed": legacy_confirmed,
    "legacy_signed_amount_sum": float(signed_sum or 0),
    "legacy_amount_sum": float(amount_sum or 0),
    "db_writes": max(after - before, 0),
    "decision": "legacy_deduction_adjustments_projected_to_settlement_runtime",
}
write_json(output_json, payload)
print("FRESH_DB_SETTLEMENT_ADJUSTMENT_PROJECTION_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
