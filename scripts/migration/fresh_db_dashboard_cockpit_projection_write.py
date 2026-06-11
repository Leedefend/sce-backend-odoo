#!/usr/bin/env python3
"""Project formal dashboard source rows into dashboard cockpit facts."""

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
output_json = artifact_root / "fresh_db_dashboard_cockpit_projection_write_result_v1.json"
currency_id = env.ref("base.CNY", raise_if_not_found=False).id  # noqa: F821

before = int(scalar("SELECT COUNT(*) FROM sc_dashboard_cockpit_fact") or 0)
fund_before = int(
    scalar(
        """
        SELECT COUNT(*)
          FROM sc_dashboard_cockpit_fact
         WHERE fact_type = 'fund_cockpit'
           AND source_model = 'sc.fund.daily.summary'
        """
    )
    or 0
)
cost_before = int(
    scalar(
        """
        SELECT COUNT(*)
          FROM sc_dashboard_cockpit_fact
         WHERE fact_type = 'cost_cockpit'
           AND source_model = 'construction.contract'
        """
    )
    or 0
)

env.cr.execute(  # noqa: F821
    """
    INSERT INTO sc_dashboard_cockpit_fact (
      name, document_no, fact_type, project_id, business_date, quantity,
      amount, currency_id, state, description, active, cockpit_scope,
      metric_period, metric_value, source_model, source_res_id,
      create_uid, write_uid, create_date, write_date
    )
    SELECT
      COALESCE(NULLIF(s.display_name, ''), '资金驾驶舱指标'),
      'FUND-DASH-' || s.id::text,
      'fund_cockpit',
      s.project_id,
      COALESCE(s.document_date, CURRENT_DATE),
      COALESCE(s.line_count, 0),
      COALESCE(s.net_amount, 0),
      %s,
      'done',
      concat_ws(E'\\n',
        NULLIF('账户名称: ' || COALESCE(s.account_name, ''), '账户名称: '),
        NULLIF('银行账号: ' || COALESCE(s.bank_account_no, ''), '银行账号: '),
        '当日收入: ' || COALESCE(s.daily_income, 0)::text,
        '当日支出: ' || COALESCE(s.daily_expense, 0)::text,
        '收支净额: ' || COALESCE(s.net_amount, 0)::text,
        '账面余额: ' || COALESCE(s.account_balance, 0)::text,
        '当前账面余额: ' || COALESCE(s.current_account_balance, 0)::text,
        '当前银行余额: ' || COALESCE(s.current_bank_balance, 0)::text,
        '账实差异: ' || COALESCE(s.bank_system_difference, 0)::text
      ),
      TRUE,
      CASE WHEN s.project_id IS NULL THEN 'company' ELSE 'project' END,
      'day',
      COALESCE(s.account_balance, s.current_account_balance, s.net_amount, 0),
      'sc.fund.daily.summary',
      s.id,
      1,
      1,
      NOW(),
      NOW()
    FROM sc_fund_daily_summary s
    ON CONFLICT (fact_type, source_model, source_res_id)
    DO UPDATE SET
      name = EXCLUDED.name,
      project_id = EXCLUDED.project_id,
      business_date = EXCLUDED.business_date,
      quantity = EXCLUDED.quantity,
      amount = EXCLUDED.amount,
      currency_id = EXCLUDED.currency_id,
      state = EXCLUDED.state,
      description = EXCLUDED.description,
      active = EXCLUDED.active,
      cockpit_scope = EXCLUDED.cockpit_scope,
      metric_period = EXCLUDED.metric_period,
      metric_value = EXCLUDED.metric_value,
      write_uid = 1,
      write_date = NOW()
    """,
    [currency_id],
)

env.cr.execute(  # noqa: F821
    """
    INSERT INTO sc_dashboard_cockpit_fact (
      name, document_no, fact_type, project_id, partner_id, requester_id,
      handler_id, business_date, quantity, amount, tax_amount, currency_id, state, description, active,
      cockpit_scope, metric_period, metric_value, source_model, source_res_id,
      create_uid, write_uid, create_date, write_date
    )
    SELECT
      COALESCE(NULLIF(c.subject, ''), NULLIF(c.name, ''), '成本驾驶舱指标'),
      'COST-DASH-' || c.id::text,
      'cost_cockpit',
      c.project_id,
      c.partner_id,
      c.handler_id,
      c.handler_id,
      COALESCE(c.date_contract, CURRENT_DATE),
      1,
      COALESCE(NULLIF(c.amount_final, 0), c.amount_total, 0),
      COALESCE(c.amount_tax, 0),
      COALESCE(c.currency_id, %s),
      CASE
        WHEN c.state IN ('cancel', 'cancelled') THEN 'cancel'
        WHEN c.state IN ('confirmed', 'running', 'closed', 'done') THEN 'done'
        ELSE 'in_progress'
      END,
      concat_ws(E'\\n',
        NULLIF('合同编号: ' || COALESCE(c.name, ''), '合同编号: '),
        NULLIF('合同名称: ' || COALESCE(c.subject, ''), '合同名称: '),
        NULLIF('合同状态: ' || COALESCE(c.state, ''), '合同状态: '),
        '不含税金额: ' || COALESCE(c.amount_untaxed, 0)::text,
        '税额: ' || COALESCE(c.amount_tax, 0)::text,
        '含税金额: ' || COALESCE(c.amount_total, 0)::text,
        '最终合同价: ' || COALESCE(c.amount_final, 0)::text
      ),
      TRUE,
      CASE WHEN c.project_id IS NULL THEN 'company' ELSE 'project' END,
      'month',
      COALESCE(NULLIF(c.amount_final, 0), c.amount_total, 0),
      'construction.contract',
      c.id,
      1,
      1,
      NOW(),
      NOW()
    FROM construction_contract c
    WHERE c.type = 'in'
      AND COALESCE(NULLIF(c.amount_final, 0), c.amount_total, 0) >= 0
    ON CONFLICT (fact_type, source_model, source_res_id)
    DO UPDATE SET
      name = EXCLUDED.name,
      project_id = EXCLUDED.project_id,
      partner_id = EXCLUDED.partner_id,
      requester_id = EXCLUDED.requester_id,
      handler_id = EXCLUDED.handler_id,
      business_date = EXCLUDED.business_date,
      quantity = EXCLUDED.quantity,
      amount = EXCLUDED.amount,
      tax_amount = EXCLUDED.tax_amount,
      currency_id = EXCLUDED.currency_id,
      state = EXCLUDED.state,
      description = EXCLUDED.description,
      active = EXCLUDED.active,
      cockpit_scope = EXCLUDED.cockpit_scope,
      metric_period = EXCLUDED.metric_period,
      metric_value = EXCLUDED.metric_value,
      write_uid = 1,
      write_date = NOW()
    """,
    [currency_id],
)

env.cr.commit()  # noqa: F821

after = int(scalar("SELECT COUNT(*) FROM sc_dashboard_cockpit_fact") or 0)
fund_after = int(
    scalar(
        """
        SELECT COUNT(*)
          FROM sc_dashboard_cockpit_fact
         WHERE fact_type = 'fund_cockpit'
           AND source_model = 'sc.fund.daily.summary'
        """
    )
    or 0
)
cost_after = int(
    scalar(
        """
        SELECT COUNT(*)
          FROM sc_dashboard_cockpit_fact
         WHERE fact_type = 'cost_cockpit'
           AND source_model = 'construction.contract'
        """
    )
    or 0
)
source_rows = int(scalar("SELECT COUNT(*) FROM sc_fund_daily_summary") or 0)
cost_source_rows = int(scalar("SELECT COUNT(*) FROM construction_contract WHERE type = 'in'") or 0)
with_project = int(
    scalar(
        """
        SELECT COUNT(*)
          FROM sc_dashboard_cockpit_fact
         WHERE fact_type = 'fund_cockpit'
           AND source_model = 'sc.fund.daily.summary'
           AND project_id IS NOT NULL
        """
    )
    or 0
)
cost_with_project = int(
    scalar(
        """
        SELECT COUNT(*)
          FROM sc_dashboard_cockpit_fact
         WHERE fact_type = 'cost_cockpit'
           AND source_model = 'construction.contract'
           AND project_id IS NOT NULL
        """
    )
    or 0
)
payload = {
    "status": "PASS",
    "mode": "fresh_db_dashboard_cockpit_projection_write",
    "database": env.cr.dbname,  # noqa: F821
    "before": before,
    "after": after,
    "delta": after - before,
    "fund_before": fund_before,
    "fund_after": fund_after,
    "fund_delta": fund_after - fund_before,
    "source_rows": source_rows,
    "fund_with_project": with_project,
    "cost_before": cost_before,
    "cost_after": cost_after,
    "cost_delta": cost_after - cost_before,
    "cost_source_rows": cost_source_rows,
    "cost_with_project": cost_with_project,
    "decision": (
        "dashboard_projection_complete"
        if fund_after >= source_rows and cost_after >= cost_source_rows
        else "dashboard_projection_gap"
    ),
}
write_json(output_json, payload)
print("DASHBOARD_COCKPIT_PROJECTION_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
