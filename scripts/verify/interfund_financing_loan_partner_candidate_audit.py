# -*- coding: utf-8 -*-
"""Audit financing loan partner anchor candidates without writing records."""

from __future__ import annotations

import json
import os
from collections import OrderedDict
from pathlib import Path


def artifact_root() -> Path:
    raw = os.getenv("MIGRATION_ARTIFACT_ROOT") or os.getenv("INTERFUND_LOAN_PARTNER_ARTIFACT_ROOT")
    candidates = [Path(raw)] if raw else []
    candidates.extend([Path("/mnt/artifacts/backend"), Path(f"/tmp/interfund_loan_partner/{env.cr.dbname}")])  # noqa: F821
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return candidate
        except OSError:
            continue
    return Path("/tmp")


def sql_one(query, params=None):
    env.cr.execute(query, params or [])  # noqa: F821
    row = env.cr.fetchone()  # noqa: F821
    return row[0] if row else None


def sql_rows(query, params=None):
    env.cr.execute(query, params or [])  # noqa: F821
    names = [desc[0] for desc in env.cr.description]  # noqa: F821
    return [dict(zip(names, row)) for row in env.cr.fetchall()]  # noqa: F821


SAFE_CANDIDATE_CTE = """
    WITH partner_names AS (
        SELECT name, COUNT(*)::integer AS partner_count, MIN(id) AS partner_id
          FROM res_partner
         GROUP BY name
    ), candidate AS (
        SELECT l.id,
               l.loan_type,
               l.direction,
               l.amount,
               COALESCE(pc.partner_id, pv.partner_id) AS partner_id,
               COALESCE(
                   CASE WHEN pc.partner_id IS NOT NULL THEN l.legacy_counterparty_name END,
                   CASE WHEN pv.partner_id IS NOT NULL THEN l.legacy_visible_counterparty_name END
               ) AS matched_name,
               ARRAY_REMOVE(ARRAY[pc.partner_id, pv.partner_id], NULL) AS matched_partner_ids
          FROM sc_financing_loan l
          LEFT JOIN partner_names pc
            ON pc.name = l.legacy_counterparty_name
           AND pc.partner_count = 1
          LEFT JOIN partner_names pv
            ON pv.name = l.legacy_visible_counterparty_name
           AND pv.partner_count = 1
         WHERE l.active IS TRUE
           AND l.partner_id IS NULL
           AND COALESCE(l.legacy_counterparty_name, l.legacy_visible_counterparty_name, '') <> ''
    ), safe AS (
        SELECT *
          FROM candidate
         WHERE partner_id IS NOT NULL
           AND matched_name NOT IN ('admin', 'administrator', '系统管理员')
           AND NOT EXISTS (
                SELECT 1
                  FROM unnest(matched_partner_ids) AS mp(partner_id)
                 WHERE mp.partner_id <> candidate.partner_id
           )
    )
"""


summary = OrderedDict()
warnings = []

summary["fund_account_operation_totals"] = sql_rows(
    """
    SELECT operation_type,
           COUNT(*)::integer AS total,
           COUNT(*) FILTER (WHERE source_account_id IS NULL)::integer AS missing_source_account,
           COUNT(*) FILTER (WHERE target_account_id IS NULL)::integer AS missing_target_account,
           COUNT(*) FILTER (WHERE fund_account_id IS NULL)::integer AS missing_single_account,
           COUNT(*) FILTER (WHERE NULLIF(legacy_visible_account_name, '') IS NOT NULL)::integer AS with_legacy_source_account_name,
           COUNT(*) FILTER (WHERE NULLIF(legacy_visible_counterparty_account_name, '') IS NOT NULL)::integer AS with_legacy_target_account_name
      FROM sc_fund_account_operation
     WHERE active IS TRUE
     GROUP BY operation_type
     ORDER BY operation_type
    """
)
summary["fund_account_master_totals"] = sql_rows(
    """
    SELECT source_origin,
           COUNT(*)::integer AS total,
           COUNT(*) FILTER (WHERE NULLIF(legacy_account_id, '') IS NOT NULL)::integer AS with_legacy_account_id,
           COUNT(DISTINCT legacy_account_id)::integer AS distinct_legacy_account_id,
           COUNT(*) FILTER (WHERE project_id IS NOT NULL)::integer AS with_project,
           COUNT(*) FILTER (WHERE NULLIF(account_no, '') IS NOT NULL)::integer AS with_account_no,
           COUNT(*) FILTER (WHERE state = 'active')::integer AS active_count
      FROM sc_fund_account
     GROUP BY source_origin
     ORDER BY source_origin
    """
)
summary["loan_totals"] = sql_rows(
    """
    SELECT loan_type,
           direction,
           COUNT(*)::integer AS total,
           COUNT(*) FILTER (WHERE partner_id IS NULL)::integer AS missing_partner,
           COUNT(*) FILTER (WHERE NULLIF(legacy_counterparty_name, '') IS NOT NULL)::integer AS with_counterparty_name,
           COUNT(*) FILTER (WHERE NULLIF(legacy_visible_counterparty_name, '') IS NOT NULL)::integer AS with_visible_counterparty_name,
           COUNT(*) FILTER (WHERE NULLIF(legacy_visible_payee, '') IS NOT NULL)::integer AS with_visible_payee,
           COUNT(*) FILTER (WHERE NULLIF(legacy_visible_receiver_unit, '') IS NOT NULL)::integer AS with_visible_receiver_unit,
           COALESCE(SUM(amount), 0.0) AS amount
      FROM sc_financing_loan
     WHERE active IS TRUE
     GROUP BY loan_type, direction
     ORDER BY loan_type, direction
    """
)
summary["counterparty_name_quality"] = sql_rows(
    """
    WITH source AS (
        SELECT 'legacy_counterparty_name' AS field_name, legacy_counterparty_name AS partner_name
          FROM sc_financing_loan
         WHERE active IS TRUE
           AND partner_id IS NULL
           AND NULLIF(legacy_counterparty_name, '') IS NOT NULL
        UNION ALL
        SELECT 'legacy_visible_counterparty_name', legacy_visible_counterparty_name
          FROM sc_financing_loan
         WHERE active IS TRUE
           AND partner_id IS NULL
           AND NULLIF(legacy_visible_counterparty_name, '') IS NOT NULL
    ), partner_names AS (
        SELECT name, COUNT(*)::integer AS partner_count
          FROM res_partner
         GROUP BY name
    )
    SELECT source.field_name,
           COUNT(*)::integer AS rows,
           COUNT(*) FILTER (WHERE partner_names.partner_count = 1)::integer AS unique_partner_match_rows,
           COUNT(*) FILTER (WHERE partner_names.partner_count > 1)::integer AS duplicate_partner_match_rows,
           COUNT(*) FILTER (WHERE partner_names.partner_count IS NULL)::integer AS no_partner_match_rows
      FROM source
      LEFT JOIN partner_names ON partner_names.name = source.partner_name
     GROUP BY source.field_name
     ORDER BY source.field_name
    """
)
summary["safe_counterparty_candidates"] = OrderedDict(
    [
        (
            "total",
            sql_one(
                SAFE_CANDIDATE_CTE
                + """
                SELECT COUNT(*)::integer
                  FROM safe
                """
            ),
        ),
        (
            "by_type",
            sql_rows(
                SAFE_CANDIDATE_CTE
                + """
                SELECT loan_type,
                       direction,
                       COUNT(*)::integer AS rows,
                       COALESCE(SUM(amount), 0.0) AS amount
                  FROM safe
                 GROUP BY loan_type, direction
                 ORDER BY loan_type, direction
                """
            ),
        ),
        (
            "samples",
            sql_rows(
                SAFE_CANDIDATE_CTE
                + """
                SELECT safe.id AS loan_id,
                       safe.loan_type,
                       safe.direction,
                       safe.amount,
                       safe.matched_name,
                       safe.partner_id,
                       p.name AS partner_name
                  FROM safe
                  JOIN res_partner p ON p.id = safe.partner_id
                 ORDER BY safe.id
                 LIMIT 30
                """
            ),
        ),
    ]
)
summary["high_risk_payee_or_receiver_only_matches"] = sql_rows(
    """
    WITH partner_names AS (
        SELECT name, COUNT(*)::integer AS partner_count, MIN(id) AS partner_id
          FROM res_partner
         GROUP BY name
    )
    SELECT l.id AS loan_id,
           l.loan_type,
           l.direction,
           l.amount,
           l.legacy_counterparty_name,
           l.legacy_visible_payee,
           l.legacy_visible_receiver_unit,
           COALESCE(pp.partner_id, pr.partner_id) AS matched_partner_id,
           p.name AS matched_partner_name
      FROM sc_financing_loan l
      LEFT JOIN partner_names pc ON pc.name = l.legacy_counterparty_name AND pc.partner_count = 1
      LEFT JOIN partner_names pv ON pv.name = l.legacy_visible_counterparty_name AND pv.partner_count = 1
      LEFT JOIN partner_names pp ON pp.name = l.legacy_visible_payee AND pp.partner_count = 1
      LEFT JOIN partner_names pr ON pr.name = l.legacy_visible_receiver_unit AND pr.partner_count = 1
      LEFT JOIN res_partner p ON p.id = COALESCE(pp.partner_id, pr.partner_id)
     WHERE l.active IS TRUE
       AND l.partner_id IS NULL
       AND pc.partner_id IS NULL
       AND pv.partner_id IS NULL
       AND COALESCE(pp.partner_id, pr.partner_id) IS NOT NULL
     ORDER BY l.id
     LIMIT 50
    """
)
if summary["high_risk_payee_or_receiver_only_matches"]:
    warnings.append(
        {
            "key": "payee_or_receiver_unit_not_used_for_partner_anchor",
            "policy": "收款人/收款单位可能是代收对象或账户对象，不能直接定义为借款责任往来方；必须在线核实或人工确认后再落正式关系。",
        }
    )

result = OrderedDict(
    [
        ("status", "PASS"),
        ("database", env.cr.dbname),  # noqa: F821
        (
            "policy",
            "只读审计，不写入历史融资/借款单据。自动候选仅来自历史往来方字段，不使用收款人、收款单位、账户字段推断责任主体。",
        ),
        ("summary", summary),
        ("warnings", warnings),
    ]
)

target = artifact_root() / f"interfund_financing_loan_partner_candidate_audit_{env.cr.dbname}.json"  # noqa: F821
target.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
