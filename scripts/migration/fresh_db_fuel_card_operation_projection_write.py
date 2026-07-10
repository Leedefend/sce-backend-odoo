#!/usr/bin/env python3
"""Project legacy fuel-card records into formal fund account operations."""

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


def artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.append(Path("/mnt/artifacts/migration"))
    candidates.append(Path(f"/tmp/history_continuity/{env.cr.dbname}/adhoc"))  # noqa: F821
    for root in candidates:
        try:
            root.mkdir(parents=True, exist_ok=True)
            probe = root / ".write_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return root
        except Exception:
            continue
    return Path(f"/tmp/history_continuity/{env.cr.dbname}/adhoc")  # noqa: F821


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def scalar(sql: str, params: list[object] | None = None) -> object:
    env.cr.execute(sql, params or [])  # noqa: F821
    row = env.cr.fetchone()  # noqa: F821
    return row[0] if row else None


ensure_allowed_db()
output_json = artifact_root() / "fresh_db_fuel_card_operation_projection_write_result_v1.json"
currency_id = env.ref("base.CNY", raise_if_not_found=False).id  # noqa: F821
company_id = env.company.id  # noqa: F821
uid = env.uid  # noqa: F821

before = int(scalar("SELECT COUNT(*) FROM sc_fund_account_operation") or 0)
source_card = int(scalar("SELECT COUNT(*) FROM sc_legacy_fuel_card_fact WHERE active") or 0)
source_recharge = int(scalar("SELECT COUNT(*) FROM sc_legacy_fuel_card_recharge_fact WHERE active") or 0)

env.cr.execute(  # noqa: F821
    """
    INSERT INTO sc_fund_account_operation (
      name, operation_type, operation_date, project_id, company_id, currency_id,
      amount, before_balance, after_balance, operation_reason, state, note,
      legacy_source_model, legacy_source_table, legacy_record_id,
      legacy_document_state, creator_name, created_time, active,
      create_uid, write_uid, create_date, write_date
    )
    SELECT
      COALESCE(NULLIF(card.document_no, ''), 'YKDJ-' || card.id::text),
      'balance_adjustment',
      COALESCE(card.document_date::date, card.created_time::date, CURRENT_DATE),
      card.project_id,
      %s,
      %s,
      COALESCE(card.initial_amount, 0),
      0,
      COALESCE(NULLIF(card.balance_amount, 0), NULLIF(card.initial_amount, 0), 0),
      CONCAT_WS(':', '油卡登记', NULLIF(card.card_no, ''), NULLIF(card.document_no, '')),
      CASE WHEN COALESCE(card.document_state, '') IN ('审核通过', '已审核', '完成', '已完成') THEN 'done' ELSE 'draft' END,
      CONCAT_WS(E'\n',
        NULLIF(card.note, ''),
        CASE WHEN COALESCE(card.attachment_ref, '') <> '' THEN '附件: ' || card.attachment_ref ELSE NULL END,
        CASE WHEN COALESCE(card.manager_name, '') <> '' THEN '主要管理人: ' || card.manager_name ELSE NULL END
      ),
      'sc.legacy.fuel.card.fact',
      'D_LYXM_BG_BX_YKDJ',
      card.legacy_record_id,
      NULLIF(card.document_state, ''),
      NULLIF(card.creator_name, ''),
      card.created_time,
      card.active,
      %s,
      %s,
      NOW(),
      NOW()
    FROM sc_legacy_fuel_card_fact card
    WHERE card.active
      AND COALESCE(card.legacy_record_id, '') <> ''
    ON CONFLICT (legacy_source_model, legacy_record_id)
    DO UPDATE SET
      name = EXCLUDED.name,
      operation_date = EXCLUDED.operation_date,
      project_id = EXCLUDED.project_id,
      amount = EXCLUDED.amount,
      before_balance = EXCLUDED.before_balance,
      after_balance = EXCLUDED.after_balance,
      operation_reason = EXCLUDED.operation_reason,
      state = EXCLUDED.state,
      note = EXCLUDED.note,
      legacy_source_table = EXCLUDED.legacy_source_table,
      legacy_document_state = EXCLUDED.legacy_document_state,
      creator_name = EXCLUDED.creator_name,
      created_time = EXCLUDED.created_time,
      active = EXCLUDED.active,
      write_uid = %s,
      write_date = NOW()
    """,
    [company_id, currency_id, uid, uid, uid],
)
card_upserted = env.cr.rowcount  # noqa: F821

env.cr.execute(  # noqa: F821
    """
    INSERT INTO sc_fund_account_operation (
      name, operation_type, operation_date, project_id, company_id, currency_id,
      amount, before_balance, after_balance, operation_reason, state, note,
      legacy_source_model, legacy_source_table, legacy_record_id,
      legacy_document_state, creator_name, created_time, active,
      create_uid, write_uid, create_date, write_date
    )
    SELECT
      COALESCE(NULLIF(recharge.document_no, ''), 'YKCZ-' || recharge.id::text),
      'balance_adjustment',
      COALESCE(recharge.document_date::date, recharge.created_time::date, CURRENT_DATE),
      recharge.project_id,
      %s,
      %s,
      COALESCE(recharge.recharge_amount, 0),
      COALESCE(recharge.used_amount, 0),
      COALESCE(NULLIF(recharge.balance_amount, 0), NULLIF(recharge.total_recharge_amount, 0), NULLIF(recharge.recharge_amount, 0), 0),
      CONCAT_WS(':', '充值登记', NULLIF(recharge.card_no, ''), NULLIF(recharge.document_no, '')),
      CASE WHEN COALESCE(recharge.document_state, '') IN ('审核通过', '已审核', '完成', '已完成') THEN 'done' ELSE 'draft' END,
      CONCAT_WS(E'\n',
        NULLIF(recharge.note, ''),
        CASE WHEN COALESCE(recharge.attachment_ref, '') <> '' THEN '附件: ' || recharge.attachment_ref ELSE NULL END,
        CASE WHEN COALESCE(recharge.related_document_no, '') <> '' THEN '关联报销单: ' || recharge.related_document_no ELSE NULL END,
        CASE WHEN COALESCE(recharge.handler_name, '') <> '' THEN '充值人: ' || recharge.handler_name ELSE NULL END
      ),
      'sc.legacy.fuel.card.recharge.fact',
      'D_LYXM_BG_BX_CZDJ',
      recharge.legacy_record_id,
      NULLIF(recharge.document_state, ''),
      NULLIF(recharge.creator_name, ''),
      recharge.created_time,
      recharge.active,
      %s,
      %s,
      NOW(),
      NOW()
    FROM sc_legacy_fuel_card_recharge_fact recharge
    WHERE recharge.active
      AND COALESCE(recharge.legacy_record_id, '') <> ''
    ON CONFLICT (legacy_source_model, legacy_record_id)
    DO UPDATE SET
      name = EXCLUDED.name,
      operation_date = EXCLUDED.operation_date,
      project_id = EXCLUDED.project_id,
      amount = EXCLUDED.amount,
      before_balance = EXCLUDED.before_balance,
      after_balance = EXCLUDED.after_balance,
      operation_reason = EXCLUDED.operation_reason,
      state = EXCLUDED.state,
      note = EXCLUDED.note,
      legacy_source_table = EXCLUDED.legacy_source_table,
      legacy_document_state = EXCLUDED.legacy_document_state,
      creator_name = EXCLUDED.creator_name,
      created_time = EXCLUDED.created_time,
      active = EXCLUDED.active,
      write_uid = %s,
      write_date = NOW()
    """,
    [company_id, currency_id, uid, uid, uid],
)
recharge_upserted = env.cr.rowcount  # noqa: F821

env.cr.commit()  # noqa: F821

after = int(scalar("SELECT COUNT(*) FROM sc_fund_account_operation") or 0)
projected_card = int(
    scalar("SELECT COUNT(*) FROM sc_fund_account_operation WHERE legacy_source_model = 'sc.legacy.fuel.card.fact' AND active")
    or 0
)
projected_recharge = int(
    scalar(
        "SELECT COUNT(*) FROM sc_fund_account_operation WHERE legacy_source_model = 'sc.legacy.fuel.card.recharge.fact' AND active"
    )
    or 0
)
payload = {
    "status": "PASS" if projected_card >= source_card and projected_recharge >= source_recharge else "FAIL",
    "mode": "fresh_db_fuel_card_operation_projection_write",
    "database": env.cr.dbname,  # noqa: F821
    "before": before,
    "after": after,
    "delta": after - before,
    "source_card": source_card,
    "source_recharge": source_recharge,
    "projected_card": projected_card,
    "projected_recharge": projected_recharge,
    "card_upserted": card_upserted,
    "recharge_upserted": recharge_upserted,
}
write_json(output_json, payload)
print("FUEL_CARD_OPERATION_PROJECTION_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
