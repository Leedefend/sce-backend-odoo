#!/usr/bin/env python3
"""Project actual-outflow line facts into contract-linked payment executions."""

from __future__ import annotations

import json
import os
from pathlib import Path


def ensure_allowed_db() -> None:
    allowlist = {
        item.strip()
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_partner_acceptance,sc_migration_fresh,sc_demo").split(",")
        if item.strip()
    }
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_projection": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def artifact_root() -> Path:
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
output_json = artifact_root() / "fresh_db_actual_outflow_line_payment_execution_projection_write_result_v1.json"
uid = env.uid  # noqa: F821
currency_id = env.ref("base.CNY", raise_if_not_found=False).id  # noqa: F821

env.cr.execute(  # noqa: F821
    """
    UPDATE payment_request_line
       SET current_pay_amount = amount,
           write_uid = %s,
           write_date = NOW()
     WHERE legacy_line_id LIKE 'actual_outflow_line:%%'
       AND contract_id IS NOT NULL
       AND COALESCE(current_pay_amount, 0) = 0
       AND COALESCE(amount, 0) > 0
    """,
    [uid],
)
actual_outflow_line_amount_repairs = env.cr.rowcount  # noqa: F821
env.cr.commit()  # noqa: F821

before = int(scalar("SELECT COUNT(*) FROM sc_payment_execution") or 0)
candidate_lines = int(
    scalar(
        """
        SELECT COUNT(*)
          FROM payment_request_line l
         WHERE l.legacy_line_id LIKE 'actual_outflow_line:%'
           AND l.contract_id IS NOT NULL
           AND l.project_id IS NOT NULL
           AND COALESCE(NULLIF(l.current_pay_amount, 0), l.amount, 0) > 0
        """
    )
    or 0
)

env.cr.execute(  # noqa: F821
    """
    INSERT INTO sc_payment_execution (
      name, source_origin, source_kind, state,
      project_id, partner_id, contract_id, payment_request_id,
      date_payment, document_no, payment_family, planned_amount, paid_amount,
      currency_id, legacy_source_model, legacy_source_table, legacy_record_id,
      legacy_residual_reason, creator_legacy_user_id, creator_name, created_time, note, active,
      create_uid, create_date, write_uid, write_date
    )
    SELECT
      CONCAT('LEG-PAY-', REPLACE(l.legacy_line_id, ':', '-')),
      'legacy',
      'actual_outflow',
      'legacy_confirmed',
      l.project_id,
      l.partner_id,
      l.contract_id,
      l.request_id,
      COALESCE(r.date_request, CURRENT_DATE),
      COALESCE(NULLIF(l.source_document_no, ''), r.name),
      COALESCE(NULLIF(l.source_line_type, ''), 'actual_outflow_line'),
      COALESCE(NULLIF(l.amount, 0), l.current_pay_amount, 0),
      COALESCE(NULLIF(l.current_pay_amount, 0), l.amount, 0),
      %s,
      'payment.request.line',
      'T_FK_Supplier_CB',
      l.legacy_line_id,
      'actual_outflow_line_projected_to_payment_execution',
      NULLIF(r.creator_legacy_user_id, ''),
      NULLIF(r.creator_name, ''),
      r.created_time,
      CONCAT(
        '[migration:actual_outflow_line_payment_execution] legacy_line_id=', l.legacy_line_id,
        '; legacy_parent_id=', COALESCE(l.legacy_parent_id, ''),
        '; source_document_no=', COALESCE(l.source_document_no, ''),
        '; source_contract_no=', COALESCE(l.source_contract_no, ''),
        '; historical_runtime_projection=true'
      ),
      l.active,
      %s, NOW(), %s, NOW()
    FROM payment_request_line l
    JOIN payment_request r ON r.id = l.request_id
    WHERE l.legacy_line_id LIKE 'actual_outflow_line:%%'
      AND l.contract_id IS NOT NULL
      AND l.project_id IS NOT NULL
      AND COALESCE(NULLIF(l.current_pay_amount, 0), l.amount, 0) > 0
    ON CONFLICT (legacy_source_model, legacy_record_id) DO UPDATE SET
      source_origin = EXCLUDED.source_origin,
      source_kind = EXCLUDED.source_kind,
      state = EXCLUDED.state,
      project_id = EXCLUDED.project_id,
      partner_id = EXCLUDED.partner_id,
      contract_id = EXCLUDED.contract_id,
      payment_request_id = EXCLUDED.payment_request_id,
      date_payment = EXCLUDED.date_payment,
      document_no = EXCLUDED.document_no,
      payment_family = EXCLUDED.payment_family,
      planned_amount = EXCLUDED.planned_amount,
      paid_amount = EXCLUDED.paid_amount,
      currency_id = EXCLUDED.currency_id,
      legacy_source_table = EXCLUDED.legacy_source_table,
      legacy_residual_reason = EXCLUDED.legacy_residual_reason,
      creator_legacy_user_id = EXCLUDED.creator_legacy_user_id,
      creator_name = EXCLUDED.creator_name,
      created_time = EXCLUDED.created_time,
      note = EXCLUDED.note,
      active = EXCLUDED.active,
      write_uid = EXCLUDED.write_uid,
      write_date = NOW()
    """,
    [currency_id, uid, uid],
)
env.cr.commit()  # noqa: F821

after = int(scalar("SELECT COUNT(*) FROM sc_payment_execution") or 0)
legacy_actual_rows = int(
    scalar(
        """
        SELECT COUNT(*)
          FROM sc_payment_execution
         WHERE source_origin = 'legacy'
           AND source_kind = 'actual_outflow'
           AND legacy_source_model = 'payment.request.line'
        """
    )
    or 0
)
legacy_actual_with_contract = int(
    scalar(
        """
        SELECT COUNT(*)
          FROM sc_payment_execution
         WHERE source_origin = 'legacy'
           AND source_kind = 'actual_outflow'
           AND legacy_source_model = 'payment.request.line'
           AND contract_id IS NOT NULL
        """
    )
    or 0
)
linked_contracts = int(
    scalar(
        """
        SELECT COUNT(DISTINCT contract_id)
          FROM sc_payment_execution
         WHERE source_origin = 'legacy'
           AND source_kind = 'actual_outflow'
           AND legacy_source_model = 'payment.request.line'
           AND contract_id IS NOT NULL
        """
    )
    or 0
)
paid_sum = float(
    scalar(
        """
        SELECT COALESCE(SUM(paid_amount), 0)
          FROM sc_payment_execution
         WHERE source_origin = 'legacy'
           AND source_kind = 'actual_outflow'
           AND legacy_source_model = 'payment.request.line'
        """
    )
    or 0
)

payload = {
    "status": "PASS",
    "mode": "fresh_db_actual_outflow_line_payment_execution_projection_write",
    "database": env.cr.dbname,  # noqa: F821
    "candidate_actual_outflow_lines": candidate_lines,
    "actual_outflow_line_amount_repairs": actual_outflow_line_amount_repairs,
    "before": before,
    "after": after,
    "delta": after - before,
    "legacy_actual_outflow_line_execution_rows": legacy_actual_rows,
    "legacy_actual_outflow_line_execution_with_contract": legacy_actual_with_contract,
    "linked_contract_count": linked_contracts,
    "legacy_actual_outflow_line_paid_amount_sum": paid_sum,
    "db_writes": max(after - before, 0),
    "decision": "actual_outflow_line_payments_projected_to_contract_visible_execution",
}
write_json(output_json, payload)
print("FRESH_DB_ACTUAL_OUTFLOW_LINE_PAYMENT_EXECUTION_PROJECTION_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
