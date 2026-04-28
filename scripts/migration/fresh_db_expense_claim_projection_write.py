#!/usr/bin/env python3
"""Project legacy expense reimbursement and deposit facts into runtime claims."""

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
output_json = artifact_root / "fresh_db_expense_claim_projection_write_result_v1.json"
uid = env.uid  # noqa: F821
currency_id = env.company.currency_id.id  # noqa: F821

env.cr.execute("SELECT COUNT(*) FROM sc_expense_claim")  # noqa: F821
before = env.cr.fetchone()[0]  # noqa: F821

env.cr.execute(  # noqa: F821
    """
    INSERT INTO sc_expense_claim (
      name, source_origin, claim_type, direction, state, project_id, partner_id,
      applicant_name, payee, payee_account, payee_bank, date_claim,
      expense_type, summary, amount, approved_amount, currency_id,
      legacy_source_model, legacy_source_table, legacy_record_id,
      legacy_document_no, legacy_document_state, note, active,
      create_uid, create_date, write_uid, write_date
    )
    SELECT
      CONCAT('LEG-EXP-', COALESCE(NULLIF(l.document_no, ''), l.legacy_line_id)),
      'legacy',
      'expense',
      'outflow',
      CASE WHEN l.document_state = '2' THEN 'legacy_confirmed' ELSE 'draft' END,
      l.project_id,
      NULL,
      NULLIF(l.applicant_name, ''),
      NULLIF(l.payee, ''),
      NULLIF(l.payee_account, ''),
      NULLIF(l.payee_bank, ''),
      COALESCE(NULLIF(l.document_date, '')::date, l.created_time::date, CURRENT_DATE),
      COALESCE(NULLIF(l.finance_type, ''), NULLIF(l.reimbursement_type, '')),
      NULLIF(l.summary, ''),
      ABS(COALESCE(NULLIF(l.approved_amount, 0), l.amount, 0)),
      ABS(COALESCE(NULLIF(l.approved_amount, 0), l.amount, 0)),
      %s,
      'sc.legacy.expense.reimbursement.line',
      l.source_table,
      l.legacy_line_id,
      NULLIF(l.document_no, ''),
      NULLIF(l.document_state, ''),
      CONCAT(
        '[migration:expense_claim] legacy_line_id=', l.legacy_line_id,
        '; legacy_header_id=', COALESCE(l.legacy_header_id, ''),
        '; legacy_project_id=', COALESCE(l.project_legacy_id, ''),
        '; reimbursement_type=', COALESCE(l.reimbursement_type, ''),
        '; historical_runtime_projection=true'
      ),
      l.active,
      %s, NOW(), %s, NOW()
    FROM sc_legacy_expense_reimbursement_line l
    WHERE l.project_id IS NOT NULL
      AND ABS(COALESCE(NULLIF(l.approved_amount, 0), l.amount, 0)) > 0
    ON CONFLICT (legacy_source_model, legacy_record_id) DO UPDATE SET
      name = EXCLUDED.name,
      state = EXCLUDED.state,
      project_id = EXCLUDED.project_id,
      applicant_name = EXCLUDED.applicant_name,
      payee = EXCLUDED.payee,
      payee_account = EXCLUDED.payee_account,
      payee_bank = EXCLUDED.payee_bank,
      date_claim = EXCLUDED.date_claim,
      expense_type = EXCLUDED.expense_type,
      summary = EXCLUDED.summary,
      amount = EXCLUDED.amount,
      approved_amount = EXCLUDED.approved_amount,
      legacy_document_no = EXCLUDED.legacy_document_no,
      legacy_document_state = EXCLUDED.legacy_document_state,
      note = EXCLUDED.note,
      active = EXCLUDED.active,
      write_uid = EXCLUDED.write_uid,
      write_date = NOW()
    """,
    [currency_id, uid, uid],
)

env.cr.execute(  # noqa: F821
    """
    INSERT INTO sc_expense_claim (
      name, source_origin, claim_type, direction, state, project_id, partner_id,
      applicant_name, payee, payee_account, payee_bank, date_claim,
      expense_type, summary, amount, approved_amount, currency_id,
      legacy_source_model, legacy_source_table, legacy_record_id,
      legacy_document_no, legacy_document_state, note, active,
      create_uid, create_date, write_uid, write_date
    )
    SELECT
      CONCAT('LEG-DEP-', COALESCE(NULLIF(f.document_no, ''), f.legacy_record_id)),
      'legacy',
      CASE
        WHEN f.source_family = 'expense_reimbursement' THEN 'expense'
        WHEN f.direction = 'outflow' THEN 'deposit_pay'
        WHEN f.direction = 'inflow' THEN 'deposit_receive'
        ELSE 'deposit_refund'
      END,
      CASE WHEN f.direction = 'outflow' THEN 'outflow' ELSE 'inflow' END,
      'legacy_confirmed',
      f.project_id,
      f.partner_id,
      NULL,
      NULLIF(f.legacy_partner_name, ''),
      NULL,
      NULL,
      COALESCE(f.document_date, CURRENT_DATE),
      NULLIF(f.source_family, ''),
      NULLIF(f.note, ''),
      ABS(COALESCE(f.source_amount, 0)),
      ABS(COALESCE(f.source_amount, 0)),
      %s,
      'sc.legacy.expense.deposit.fact',
      f.legacy_source_table,
      f.legacy_record_id,
      NULLIF(f.document_no, ''),
      NULLIF(f.legacy_state, ''),
      CONCAT(
        '[migration:expense_claim] legacy_record_id=', f.legacy_record_id,
        '; legacy_project_id=', COALESCE(f.legacy_project_id, ''),
        '; source_family=', COALESCE(f.source_family, ''),
        '; direction=', COALESCE(f.direction, ''),
        '; historical_runtime_projection=true'
      ),
      TRUE,
      %s, NOW(), %s, NOW()
    FROM sc_legacy_expense_deposit_fact f
    WHERE f.project_id IS NOT NULL
      AND ABS(COALESCE(f.source_amount, 0)) > 0
      AND NOT EXISTS (
        SELECT 1 FROM sc_expense_claim existing
        WHERE existing.legacy_source_model = 'sc.legacy.expense.reimbursement.line'
          AND existing.legacy_document_no IS NOT NULL
          AND existing.legacy_document_no = f.document_no
          AND f.source_family = 'expense_reimbursement'
      )
    ON CONFLICT (legacy_source_model, legacy_record_id) DO UPDATE SET
      name = EXCLUDED.name,
      claim_type = EXCLUDED.claim_type,
      direction = EXCLUDED.direction,
      state = EXCLUDED.state,
      project_id = EXCLUDED.project_id,
      partner_id = EXCLUDED.partner_id,
      payee = EXCLUDED.payee,
      date_claim = EXCLUDED.date_claim,
      expense_type = EXCLUDED.expense_type,
      summary = EXCLUDED.summary,
      amount = EXCLUDED.amount,
      approved_amount = EXCLUDED.approved_amount,
      legacy_document_no = EXCLUDED.legacy_document_no,
      legacy_document_state = EXCLUDED.legacy_document_state,
      note = EXCLUDED.note,
      active = EXCLUDED.active,
      write_uid = EXCLUDED.write_uid,
      write_date = NOW()
    """,
    [currency_id, uid, uid],
)

env.cr.commit()  # noqa: F821

def scalar(sql: str):
    env.cr.execute(sql)  # noqa: F821
    return env.cr.fetchone()[0]  # noqa: F821


after = scalar("SELECT COUNT(*) FROM sc_expense_claim")
payload = {
    "status": "PASS",
    "mode": "fresh_db_expense_claim_projection_write",
    "database": env.cr.dbname,  # noqa: F821
    "before": before,
    "after": after,
    "delta": after - before,
    "legacy_rows": scalar("SELECT COUNT(*) FROM sc_expense_claim WHERE source_origin = 'legacy'"),
    "legacy_expense_rows": scalar("SELECT COUNT(*) FROM sc_expense_claim WHERE legacy_source_model = 'sc.legacy.expense.reimbursement.line'"),
    "legacy_deposit_rows": scalar("SELECT COUNT(*) FROM sc_expense_claim WHERE legacy_source_model = 'sc.legacy.expense.deposit.fact'"),
    "legacy_confirmed": scalar("SELECT COUNT(*) FROM sc_expense_claim WHERE source_origin = 'legacy' AND state = 'legacy_confirmed'"),
    "legacy_with_project": scalar("SELECT COUNT(*) FROM sc_expense_claim WHERE source_origin = 'legacy' AND project_id IS NOT NULL"),
    "legacy_amount_sum": float(scalar("SELECT COALESCE(SUM(amount), 0) FROM sc_expense_claim WHERE source_origin = 'legacy'") or 0),
    "db_writes": max(after - before, 0),
    "decision": "legacy_expense_deposit_projected_to_runtime_claims",
}
write_json(output_json, payload)
print("FRESH_DB_EXPENSE_CLAIM_PROJECTION_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
