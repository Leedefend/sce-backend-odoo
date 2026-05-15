#!/usr/bin/env python3
"""Project runtime business facts into project cost ledger rows."""

from __future__ import annotations

import json
import os
from pathlib import Path


def repo_root() -> Path:
    env_root = os.getenv("MIGRATION_REPO_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.extend([Path("/mnt"), Path.cwd()])
    for candidate in candidates:
        if (candidate / "addons/smart_construction_core/__manifest__.py").exists():
            return candidate
    return Path.cwd()


def resolve_artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.append(Path("/mnt/artifacts/migration"))
    candidates.append(repo_root() / "artifacts/migration")
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


def ensure_allowed_db() -> None:
    allowlist = {
        item.strip()
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "").split(",")
        if item.strip()
    }
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_cost_ledger_projection": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def scalar(sql: str, params: list[object] | None = None) -> object:
    env.cr.execute(sql, params or [])  # noqa: F821
    row = env.cr.fetchone()  # noqa: F821
    return row[0] if row else None


def ensure_cost_code(code: str, name: str, cost_type: str, note: str) -> int:
    CostCode = env["project.cost.code"].sudo().with_context(active_test=False)  # noqa: F821
    record = CostCode.search([("code", "=", code)], limit=1)
    vals = {"name": name, "type": cost_type, "note": note, "active": True}
    if record:
        record.write(vals)
    else:
        record = CostCode.create({"code": code, **vals})
    return record.id


ensure_allowed_db()
artifact_root = resolve_artifact_root()
output_json = artifact_root / "project_cost_ledger_projection_write_result_v1.json"
uid = env.uid  # noqa: F821
currency_id = env.company.currency_id.id  # noqa: F821

code_ids = {
    "payment": ensure_cost_code("SC-COST-PAYMENT", "付款执行", "other", "由付款执行业务事实投影生成"),
    "expense": ensure_cost_code("SC-COST-EXPENSE", "费用与保证金", "other", "由费用/保证金业务事实投影生成"),
    "labor": ensure_cost_code("SC-COST-LABOR", "劳务结算", "labor", "由劳务结算业务事实投影生成"),
    "equipment": ensure_cost_code("SC-COST-EQUIPMENT", "机械结算", "machine", "由机械结算业务事实投影生成"),
    "subcontract": ensure_cost_code("SC-COST-SUBCONTRACT", "分包结算", "subcontract", "由分包结算业务事实投影生成"),
    "settlement": ensure_cost_code("SC-COST-SETTLEMENT", "支出结算", "other", "由支出结算业务事实投影生成"),
}

before = int(scalar("SELECT COUNT(*) FROM project_cost_ledger") or 0)

env.cr.execute("DROP TABLE IF EXISTS tmp_project_cost_ledger_projection")  # noqa: F821
env.cr.execute(  # noqa: F821
    """
    CREATE TEMP TABLE tmp_project_cost_ledger_projection (
      source_model text NOT NULL,
      source_id integer NOT NULL,
      source_line_id integer NOT NULL,
      project_id integer NOT NULL,
      cost_code_id integer NOT NULL,
      date date NOT NULL,
      period text NOT NULL,
      amount numeric NOT NULL,
      currency_id integer NOT NULL,
      partner_id integer,
      note text
    ) ON COMMIT DROP
    """
)

env.cr.execute(  # noqa: F821
    """
    INSERT INTO tmp_project_cost_ledger_projection
    SELECT
      'sc.payment.execution',
      p.id,
      p.id,
      p.project_id,
      %s,
      COALESCE(p.date_payment, CURRENT_DATE),
      TO_CHAR(COALESCE(p.date_payment, CURRENT_DATE), 'YYYY-MM'),
      GREATEST(COALESCE(p.paid_amount, 0), 0),
      COALESCE(p.currency_id, %s),
      p.partner_id,
      LEFT(CONCAT_WS(' | ', NULLIF(p.name, ''), NULLIF(p.document_no, ''), NULLIF(p.payment_family, ''), '成本台账投影:付款执行'), 250)
    FROM sc_payment_execution p
    WHERE p.active
      AND p.project_id IS NOT NULL
      AND GREATEST(COALESCE(p.paid_amount, 0), 0) > 0
      AND COALESCE(p.state, '') NOT IN ('draft', 'cancel')
    """,
    [code_ids["payment"], currency_id],
)

env.cr.execute(  # noqa: F821
    """
    INSERT INTO tmp_project_cost_ledger_projection
    SELECT
      'sc.expense.claim',
      e.id,
      e.id,
      e.project_id,
      %s,
      COALESCE(e.date_claim, e.fill_date, CURRENT_DATE),
      TO_CHAR(COALESCE(e.date_claim, e.fill_date, CURRENT_DATE), 'YYYY-MM'),
      GREATEST(COALESCE(NULLIF(e.approved_amount, 0), e.amount, 0), 0),
      COALESCE(e.currency_id, %s),
      e.partner_id,
      LEFT(CONCAT_WS(' | ', NULLIF(e.name, ''), NULLIF(e.expense_type, ''), NULLIF(e.summary, ''), '成本台账投影:费用与保证金'), 250)
    FROM sc_expense_claim e
    WHERE e.active
      AND e.project_id IS NOT NULL
      AND COALESCE(e.direction, 'outflow') = 'outflow'
      AND GREATEST(COALESCE(NULLIF(e.approved_amount, 0), e.amount, 0), 0) > 0
      AND COALESCE(e.state, '') NOT IN ('draft', 'cancel')
    """,
    [code_ids["expense"], currency_id],
)

for table, model, code_key, partner_field, date_field, label in [
    ("sc_labor_settlement", "sc.labor.settlement", "labor", "contractor_id", "settlement_date", "劳务结算"),
    ("sc_equipment_settlement", "sc.equipment.settlement", "equipment", "supplier_id", "settlement_date", "机械结算"),
    ("sc_subcontract_settlement", "sc.subcontract.settlement", "subcontract", "subcontractor_id", "settlement_date", "分包结算"),
]:
    env.cr.execute(  # noqa: F821
        f"""
        INSERT INTO tmp_project_cost_ledger_projection
        SELECT
          %s,
          s.id,
          s.id,
          s.project_id,
          %s,
          COALESCE(s.{date_field}, CURRENT_DATE),
          TO_CHAR(COALESCE(s.{date_field}, CURRENT_DATE), 'YYYY-MM'),
          GREATEST(COALESCE(s.amount_total, 0), 0),
          COALESCE(s.currency_id, %s),
          s.{partner_field},
          LEFT(CONCAT_WS(' | ', NULLIF(s.name, ''), %s), 250)
        FROM {table} s
        WHERE s.project_id IS NOT NULL
          AND GREATEST(COALESCE(s.amount_total, 0), 0) > 0
          AND COALESCE(s.state, '') NOT IN ('draft', 'cancel')
        """,
        [model, code_ids[code_key], currency_id, f"成本台账投影:{label}"],
    )

env.cr.execute(  # noqa: F821
    """
    INSERT INTO tmp_project_cost_ledger_projection
    SELECT
      'sc.settlement.order',
      s.id,
      s.id,
      s.project_id,
      %s,
      COALESCE(s.date_settlement, s.document_date, CURRENT_DATE),
      TO_CHAR(COALESCE(s.date_settlement, s.document_date, CURRENT_DATE), 'YYYY-MM'),
      GREATEST(COALESCE(s.amount_total, 0), 0),
      COALESCE(s.currency_id, %s),
      COALESCE(s.settlement_unit_id, s.partner_id),
      LEFT(CONCAT_WS(' | ', NULLIF(s.name, ''), NULLIF(s.title, ''), '成本台账投影:支出结算'), 250)
    FROM sc_settlement_order s
    WHERE s.project_id IS NOT NULL
      AND s.settlement_type = 'out'
      AND GREATEST(COALESCE(s.amount_total, 0), 0) > 0
      AND COALESCE(s.state, '') NOT IN ('draft', 'cancel')
    """,
    [code_ids["settlement"], currency_id],
)

source_counts = {}
env.cr.execute(  # noqa: F821
    """
    SELECT source_model, COUNT(*)::integer, COALESCE(SUM(amount), 0)
    FROM tmp_project_cost_ledger_projection
    GROUP BY source_model
    ORDER BY source_model
    """
)
for source_model, count, amount_sum in env.cr.fetchall():  # noqa: F821
    source_counts[source_model] = {"count": int(count), "amount_sum": float(amount_sum or 0)}

env.cr.execute(  # noqa: F821
    """
    INSERT INTO project_cost_period (
      project_id, period, locked, create_uid, create_date, write_uid, write_date
    )
    SELECT DISTINCT s.project_id, s.period, FALSE, %s, NOW(), %s, NOW()
    FROM tmp_project_cost_ledger_projection s
    ON CONFLICT (project_id, period) DO NOTHING
    """,
    [uid, uid],
)
periods_created = env.cr.rowcount  # noqa: F821

env.cr.execute(  # noqa: F821
    """
    UPDATE project_cost_ledger ledger
       SET project_id = s.project_id,
           cost_code_id = s.cost_code_id,
           date = s.date,
           period = s.period,
           period_id = period.id,
           amount = s.amount,
           currency_id = s.currency_id,
           partner_id = s.partner_id,
           note = s.note,
           source_id = s.source_id,
           write_uid = %s,
           write_date = NOW()
      FROM tmp_project_cost_ledger_projection s
      JOIN project_cost_period period
        ON period.project_id = s.project_id
       AND period.period = s.period
     WHERE ledger.source_model = s.source_model
       AND ledger.source_line_id = s.source_line_id
    """,
    [uid],
)
updated = env.cr.rowcount  # noqa: F821

env.cr.execute(  # noqa: F821
    """
    INSERT INTO project_cost_ledger (
      project_id, cost_code_id, date, period, period_id, amount, currency_id,
      partner_id, source_model, source_id, source_line_id, note,
      create_uid, create_date, write_uid, write_date
    )
    SELECT
      s.project_id,
      s.cost_code_id,
      s.date,
      s.period,
      period.id,
      s.amount,
      s.currency_id,
      s.partner_id,
      s.source_model,
      s.source_id,
      s.source_line_id,
      s.note,
      %s,
      NOW(),
      %s,
      NOW()
    FROM tmp_project_cost_ledger_projection s
    JOIN project_cost_period period
      ON period.project_id = s.project_id
     AND period.period = s.period
    WHERE NOT EXISTS (
      SELECT 1
      FROM project_cost_ledger ledger
      WHERE ledger.source_model = s.source_model
        AND ledger.source_line_id = s.source_line_id
    )
    """,
    [uid, uid],
)
inserted = env.cr.rowcount  # noqa: F821

env.cr.commit()  # noqa: F821

after = int(scalar("SELECT COUNT(*) FROM project_cost_ledger") or 0)
payload = {
    "status": "PASS",
    "mode": "project_cost_ledger_projection_write",
    "database": env.cr.dbname,  # noqa: F821
    "before": before,
    "after": after,
    "delta": after - before,
    "inserted": int(inserted),
    "updated": int(updated),
    "periods_created": int(periods_created),
    "cost_code_ids": code_ids,
    "source_counts": source_counts,
    "ledger_amount_sum": float(scalar("SELECT COALESCE(SUM(amount), 0) FROM project_cost_ledger") or 0),
}
write_json(output_json, payload)
print("PROJECT_COST_LEDGER_PROJECTION_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
