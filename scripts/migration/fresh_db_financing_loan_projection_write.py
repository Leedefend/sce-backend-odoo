#!/usr/bin/env python3
"""Project legacy financing and borrowing facts into runtime financing loans."""

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
output_json = artifact_root / "fresh_db_financing_loan_projection_write_result_v1.json"
currency_id = env.company.currency_id.id  # noqa: F821
before = int(scalar("SELECT COUNT(*) FROM sc_financing_loan") or 0)

env.cr.execute(  # noqa: F821
    """
    INSERT INTO sc_financing_loan (
      name, source_origin, loan_type, direction, state, project_id, partner_id,
      document_no, document_date, due_date, amount, currency_id, purpose,
      rate_label, extra_ref, extra_label, legacy_source_model,
      legacy_source_table, legacy_record_id, legacy_document_state,
      legacy_counterparty_id, legacy_counterparty_name, legacy_amount_field,
      note, active, create_uid, write_uid, create_date, write_date
    )
    SELECT
      COALESCE(NULLIF(f.document_no, ''), 'LEGACY-FINANCING-' || f.legacy_record_id),
      'legacy',
      CASE WHEN f.source_family = 'borrowing_request' THEN 'borrowing_request' ELSE 'loan_registration' END,
      CASE WHEN f.source_direction = 'borrowed_fund' THEN 'borrowed_fund' ELSE 'financing_in' END,
      CASE WHEN COALESCE(f.legacy_state, '') = '2' THEN 'legacy_confirmed' ELSE 'draft' END,
      f.project_id,
      f.partner_id,
      NULLIF(f.document_no, ''),
      COALESCE(f.document_date, CURRENT_DATE),
      f.due_date,
      GREATEST(COALESCE(f.source_amount, 0), 0),
      %s,
      NULLIF(f.purpose, ''),
      NULLIF(f.source_type_label, ''),
      NULLIF(f.source_extra_ref, ''),
      NULLIF(f.source_extra_label, ''),
      'sc.legacy.financing.loan.fact',
      f.legacy_source_table,
      f.legacy_record_id,
      NULLIF(f.legacy_state, ''),
      NULLIF(f.legacy_counterparty_id, ''),
      NULLIF(f.legacy_counterparty_name, ''),
      NULLIF(f.source_amount_field, ''),
      CONCAT_WS(E'\n',
        '[migration:financing_loan] legacy_record_id=' || f.legacy_record_id,
        NULLIF(f.source_family, ''),
        NULLIF(f.source_direction, ''),
        NULLIF(f.legacy_project_name, ''),
        NULLIF(f.legacy_counterparty_name, ''),
        NULLIF(f.note, '')
      ),
      TRUE,
      1,
      1,
      NOW(),
      NOW()
    FROM sc_legacy_financing_loan_fact f
    WHERE f.project_id IS NOT NULL
      AND GREATEST(COALESCE(f.source_amount, 0), 0) > 0
    ON CONFLICT (legacy_source_model, legacy_record_id)
    DO UPDATE SET
      loan_type = EXCLUDED.loan_type,
      direction = EXCLUDED.direction,
      state = EXCLUDED.state,
      project_id = EXCLUDED.project_id,
      partner_id = EXCLUDED.partner_id,
      document_no = EXCLUDED.document_no,
      document_date = EXCLUDED.document_date,
      due_date = EXCLUDED.due_date,
      amount = EXCLUDED.amount,
      purpose = EXCLUDED.purpose,
      rate_label = EXCLUDED.rate_label,
      extra_ref = EXCLUDED.extra_ref,
      extra_label = EXCLUDED.extra_label,
      legacy_document_state = EXCLUDED.legacy_document_state,
      legacy_counterparty_id = EXCLUDED.legacy_counterparty_id,
      legacy_counterparty_name = EXCLUDED.legacy_counterparty_name,
      legacy_amount_field = EXCLUDED.legacy_amount_field,
      note = EXCLUDED.note,
      active = EXCLUDED.active,
      write_uid = 1,
      write_date = NOW()
    """,
    [currency_id],
)

env.cr.commit()  # noqa: F821

after = int(scalar("SELECT COUNT(*) FROM sc_financing_loan") or 0)
payload = {
    "status": "PASS",
    "mode": "fresh_db_financing_loan_projection_write",
    "database": env.cr.dbname,  # noqa: F821
    "before": before,
    "after": after,
    "delta": after - before,
    "legacy_rows": int(scalar("SELECT COUNT(*) FROM sc_financing_loan WHERE source_origin = 'legacy'") or 0),
    "legacy_with_project": int(
        scalar("SELECT COUNT(*) FROM sc_financing_loan WHERE source_origin = 'legacy' AND project_id IS NOT NULL") or 0
    ),
    "legacy_with_partner": int(
        scalar("SELECT COUNT(*) FROM sc_financing_loan WHERE source_origin = 'legacy' AND partner_id IS NOT NULL") or 0
    ),
    "legacy_loan_registration": int(
        scalar("SELECT COUNT(*) FROM sc_financing_loan WHERE source_origin = 'legacy' AND loan_type = 'loan_registration'")
        or 0
    ),
    "legacy_borrowing_request": int(
        scalar("SELECT COUNT(*) FROM sc_financing_loan WHERE source_origin = 'legacy' AND loan_type = 'borrowing_request'")
        or 0
    ),
    "legacy_confirmed": int(
        scalar("SELECT COUNT(*) FROM sc_financing_loan WHERE source_origin = 'legacy' AND state = 'legacy_confirmed'") or 0
    ),
    "legacy_amount_sum": float(
        scalar("SELECT COALESCE(SUM(amount), 0) FROM sc_financing_loan WHERE source_origin = 'legacy'") or 0
    ),
}
write_json(output_json, payload)
print("FINANCING_LOAN_PROJECTION_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
