#!/usr/bin/env python3
"""Project legacy payment residual facts into runtime payment execution."""

from __future__ import annotations

import json
import os
from pathlib import Path


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


def scalar(sql: str) -> object:
    env.cr.execute(sql)  # noqa: F821
    row = env.cr.fetchone()  # noqa: F821
    return row[0] if row else None


allowlist = {item.strip() for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "").split(",") if item.strip()}
if allowlist and env.cr.dbname not in allowlist:  # noqa: F821
    raise RuntimeError({"db_name_not_allowed_for_replay": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821

artifact_root = resolve_artifact_root()
output_json = artifact_root / "fresh_db_payment_execution_projection_write_result_v1.json"
currency_id = env.company.currency_id.id  # noqa: F821
before = int(scalar("SELECT COUNT(*) FROM sc_payment_execution") or 0)

env.cr.execute(  # noqa: F821
    """
    INSERT INTO sc_payment_execution (
      name, source_origin, source_kind, state, project_id, partner_id, contract_id,
      date_payment, document_no, payment_family, payment_method, bank_account,
      handler_name, planned_amount, paid_amount, invoice_amount, currency_id,
      legacy_source_model, legacy_source_table, legacy_record_id,
      legacy_document_state, legacy_residual_reason, legacy_attachment_ref,
      note, active, create_uid, write_uid, create_date, write_date
    )
    SELECT
      COALESCE(NULLIF(r.document_no, ''), 'LEGACY-PAYMENT-' || r.legacy_record_id),
      'legacy',
      CASE WHEN r.payment_family = 'actual_outflow' THEN 'actual_outflow' ELSE 'outflow_request' END,
      CASE WHEN COALESCE(r.document_state, '') = '2' THEN 'legacy_confirmed' ELSE 'draft' END,
      r.project_id,
      r.partner_id,
      c.id,
      COALESCE(r.document_date, r.created_time::date, CURRENT_DATE),
      NULLIF(r.document_no, ''),
      NULLIF(r.payment_family, ''),
      NULLIF(r.payment_method, ''),
      NULLIF(r.bank_account, ''),
      NULLIF(r.handler_name, ''),
      GREATEST(COALESCE(r.planned_amount, 0), 0),
      GREATEST(COALESCE(r.paid_amount, 0), 0),
      GREATEST(COALESCE(r.invoice_amount, 0), 0),
      %s,
      'sc.legacy.payment.residual.fact',
      r.source_table,
      r.legacy_record_id,
      NULLIF(r.document_state, ''),
      NULLIF(r.residual_reason, ''),
      NULLIF(r.attachment_ref, ''),
      CONCAT_WS(E'\n',
        '[migration:payment_execution] legacy_record_id=' || r.legacy_record_id,
        NULLIF(r.residual_reason, ''),
        NULLIF(r.project_name, ''),
        NULLIF(r.partner_name, ''),
        NULLIF(r.note, '')
      ),
      r.active,
      1,
      1,
      NOW(),
      NOW()
    FROM sc_legacy_payment_residual_fact r
    LEFT JOIN (
      SELECT DISTINCT ON (legacy_contract_id) legacy_contract_id, id
      FROM construction_contract
      WHERE legacy_contract_id IS NOT NULL
      ORDER BY legacy_contract_id, id
    ) c ON c.legacy_contract_id = r.contract_legacy_id
    WHERE r.active
      AND r.project_id IS NOT NULL
      AND (GREATEST(COALESCE(r.planned_amount, 0), 0) > 0 OR GREATEST(COALESCE(r.paid_amount, 0), 0) > 0)
    ON CONFLICT (legacy_source_model, legacy_record_id)
    DO UPDATE SET
      source_kind = EXCLUDED.source_kind,
      state = EXCLUDED.state,
      project_id = EXCLUDED.project_id,
      partner_id = EXCLUDED.partner_id,
      contract_id = EXCLUDED.contract_id,
      date_payment = EXCLUDED.date_payment,
      document_no = EXCLUDED.document_no,
      payment_family = EXCLUDED.payment_family,
      payment_method = EXCLUDED.payment_method,
      bank_account = EXCLUDED.bank_account,
      handler_name = EXCLUDED.handler_name,
      planned_amount = EXCLUDED.planned_amount,
      paid_amount = EXCLUDED.paid_amount,
      invoice_amount = EXCLUDED.invoice_amount,
      legacy_document_state = EXCLUDED.legacy_document_state,
      legacy_residual_reason = EXCLUDED.legacy_residual_reason,
      legacy_attachment_ref = EXCLUDED.legacy_attachment_ref,
      note = EXCLUDED.note,
      active = EXCLUDED.active,
      write_uid = 1,
      write_date = NOW()
    """,
    [currency_id],
)

env.cr.commit()  # noqa: F821

after = int(scalar("SELECT COUNT(*) FROM sc_payment_execution") or 0)
payload = {
    "status": "PASS",
    "mode": "fresh_db_payment_execution_projection_write",
    "database": env.cr.dbname,  # noqa: F821
    "before": before,
    "after": after,
    "delta": after - before,
    "legacy_rows": int(scalar("SELECT COUNT(*) FROM sc_payment_execution WHERE source_origin = 'legacy'") or 0),
    "legacy_with_project": int(
        scalar("SELECT COUNT(*) FROM sc_payment_execution WHERE source_origin = 'legacy' AND project_id IS NOT NULL")
        or 0
    ),
    "legacy_with_partner": int(
        scalar("SELECT COUNT(*) FROM sc_payment_execution WHERE source_origin = 'legacy' AND partner_id IS NOT NULL")
        or 0
    ),
    "legacy_outflow_request": int(
        scalar("SELECT COUNT(*) FROM sc_payment_execution WHERE source_kind = 'outflow_request' AND source_origin = 'legacy'")
        or 0
    ),
    "legacy_actual_outflow": int(
        scalar("SELECT COUNT(*) FROM sc_payment_execution WHERE source_kind = 'actual_outflow' AND source_origin = 'legacy'")
        or 0
    ),
    "legacy_confirmed": int(
        scalar("SELECT COUNT(*) FROM sc_payment_execution WHERE source_origin = 'legacy' AND state = 'legacy_confirmed'")
        or 0
    ),
    "legacy_planned_amount_sum": float(
        scalar("SELECT COALESCE(SUM(planned_amount), 0) FROM sc_payment_execution WHERE source_origin = 'legacy'") or 0
    ),
    "legacy_paid_amount_sum": float(
        scalar("SELECT COALESCE(SUM(paid_amount), 0) FROM sc_payment_execution WHERE source_origin = 'legacy'") or 0
    ),
}
write_json(output_json, payload)
print("PAYMENT_EXECUTION_PROJECTION_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
