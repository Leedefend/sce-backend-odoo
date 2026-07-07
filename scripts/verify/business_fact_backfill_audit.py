#!/usr/bin/env python3
"""Audit user-facing business fact backfill quality in the active Odoo DB.

Run through scripts/ops/odoo_shell_exec.sh so the global ``env`` is provided.
The audit is intentionally read-only and writes a JSON report under artifacts.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path


DB_NAME = env.cr.dbname  # noqa: F821


def artifact_root() -> Path:
    root = Path(os.getenv("BUSINESS_FACT_AUDIT_ROOT") or f"/mnt/artifacts/business-fact-audit/{DB_NAME}")
    root.mkdir(parents=True, exist_ok=True)
    return root


def scalar(sql: str, params: list[object] | None = None) -> object:
    env.cr.execute(sql, params or [])  # noqa: F821
    row = env.cr.fetchone()  # noqa: F821
    return row[0] if row else None


def rows(sql: str, params: list[object] | None = None) -> list[dict[str, object]]:
    env.cr.execute(sql, params or [])  # noqa: F821
    columns = [desc[0] for desc in env.cr.description]  # noqa: F821
    return [dict(zip(columns, row)) for row in env.cr.fetchall()]  # noqa: F821


def table_exists(table_name: str) -> bool:
    return bool(scalar("SELECT to_regclass(%s)", [table_name]))


def column_exists(table_name: str, column_name: str) -> bool:
    if not table_exists(table_name):
        return False
    return bool(
        scalar(
            """
            SELECT 1
              FROM information_schema.columns
             WHERE table_name = %s
               AND column_name = %s
             LIMIT 1
            """,
            [table_name, column_name],
        )
    )


def count_table(table_name: str, where: str = "TRUE") -> int:
    if not table_exists(table_name):
        return 0
    return int(scalar(f"SELECT COUNT(*) FROM {table_name} WHERE {where}") or 0)


def count_query(sql: str) -> int:
    return int(scalar(f"SELECT COUNT(*) FROM ({sql}) AS audit_count_query") or 0)


def sample_query(sql: str, limit: int = 10) -> list[dict[str, object]]:
    return rows(f"SELECT * FROM ({sql}) AS audit_sample_query LIMIT {int(limit)}")


def write_csv(path: Path, csv_rows: list[dict[str, object]]) -> None:
    import csv

    if not csv_rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(csv_rows[0])
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(csv_rows)


def add_issue(
    issues: list[dict[str, object]],
    *,
    key: str,
    severity: str,
    count: int,
    message: str,
    sample_sql: str | None = None,
) -> None:
    if count <= 0:
        return
    issue: dict[str, object] = {
        "key": key,
        "severity": severity,
        "count": int(count),
        "message": message,
    }
    if sample_sql:
        issue["samples"] = sample_query(sample_sql)
    issues.append(issue)


def collect_counts() -> dict[str, int]:
    return {
        "partner_total": count_table("res_partner"),
        "customer_total": count_table("res_partner", "COALESCE(customer_rank, 0) > 0"),
        "supplier_total": count_table("res_partner", "COALESCE(supplier_rank, 0) > 0"),
        "supplier_with_type_rel": count_query(
            """
            SELECT DISTINCT partner_id
              FROM sc_res_partner_supplier_type_rel
            """
        )
        if table_exists("sc_res_partner_supplier_type_rel")
        else 0,
        "legacy_contract_total": count_table("construction_contract", "legacy_contract_id IS NOT NULL"),
        "contract_total": count_table("construction_contract"),
        "legacy_receipt_income": count_table("sc_legacy_receipt_income_fact"),
        "receipt_income_legacy": count_table("sc_receipt_income", "source_origin = 'legacy'"),
        "legacy_payment_residual": count_table("sc_legacy_payment_residual_fact"),
        "payment_execution_legacy": count_table("sc_payment_execution", "source_origin = 'legacy'"),
        "legacy_purchase_contract": count_table("sc_legacy_purchase_contract_fact"),
        "legacy_supplier_pricing": count_table("sc_legacy_supplier_contract_pricing_fact"),
        "general_contract_legacy": count_table("construction_contract", "legacy_contract_id IS NOT NULL"),
        "fund_account_legacy": count_table("sc_fund_account", "source_origin = 'legacy'"),
        "treasury_ledger": count_table("sc_treasury_ledger"),
        "expense_claim_legacy": count_table("sc_expense_claim", "source_origin = 'legacy'"),
        "invoice_registration_legacy": count_table("sc_invoice_registration", "source_origin = 'legacy'"),
    }


def collect_environment_boundary() -> dict[str, object]:
    demo_module_state = scalar("SELECT state FROM ir_module_module WHERE name = 'smart_construction_demo' LIMIT 1")
    contracts_without_legacy_id = count_table("construction_contract", "legacy_contract_id IS NULL")
    example_named_partners = count_table("res_partner", "name ILIKE '%示例%'")
    findings = []
    if demo_module_state == "installed":
        findings.append("smart_construction_demo_installed")
    if contracts_without_legacy_id:
        findings.append("construction_contract_without_legacy_id")
    if example_named_partners:
        findings.append("example_named_partner")
    return {
        "clean": not findings,
        "findings": findings,
        "smart_construction_demo_state": demo_module_state or "",
        "contracts_without_legacy_id": contracts_without_legacy_id,
        "example_named_partners": example_named_partners,
        "rule": "historical business fact acceptance must run on a no-demo database; mixed development databases are legacy-row-only provisional evidence.",
    }


def partner_semantic_counts() -> dict[str, int]:
    Partner = env["res.partner"].sudo().with_context(active_test=False)  # noqa: F821
    facts = Partner._sc_collect_partner_business_facts()
    customer_fact_ids = {partner_id for partner_id, data in facts.items() if data["customer"]}
    supplier_fact_ids = {
        partner_id
        for partner_id, data in facts.items()
        if data["supplier"] and Partner._sc_is_supplier_business_counterparty(Partner.browse(partner_id))
    }
    customer_rank_ids = set(Partner.search([("customer_rank", ">", 0)]).ids)
    supplier_rank_ids = set(Partner.search([("supplier_rank", ">", 0)]).ids)
    return {
        "customer_target": len(customer_fact_ids),
        "supplier_target": len(supplier_fact_ids),
        "customer_rank_mismatch": len(customer_fact_ids ^ customer_rank_ids),
        "supplier_rank_mismatch": len(supplier_fact_ids ^ supplier_rank_ids),
    }


def source_trace_issues() -> list[dict[str, object]]:
    configs = [
        ("sc_receipt_income", "收款登记"),
        ("sc_payment_execution", "付款登记"),
        ("sc_expense_claim", "费用报销"),
        ("sc_invoice_registration", "发票登记"),
        ("sc_financing_loan", "融资借款"),
        ("sc_fund_account", "资金账户"),
        ("sc_treasury_ledger", "资金台账"),
        ("sc_treasury_reconciliation", "资金对账"),
        ("sc_settlement_adjustment", "结算调整"),
        ("sc_general_contract", "通用合同"),
    ]
    issues: list[dict[str, object]] = []
    for table, label in configs:
        if not table_exists(table):
            continue
        legacy_where = "source_origin = 'legacy'" if column_exists(table, "source_origin") else "TRUE"
        source_model_col = "legacy_source_model" if column_exists(table, "legacy_source_model") else None
        source_table_col = "legacy_source_table" if column_exists(table, "legacy_source_table") else None
        record_col = "legacy_record_id" if column_exists(table, "legacy_record_id") else None
        if not record_col:
            continue
        source_expr = source_model_col or source_table_col
        if source_expr:
            missing_count = count_table(
                table,
                f"{legacy_where} AND (COALESCE({record_col}::text, '') = '' OR COALESCE({source_expr}::text, '') = '')",
            )
            add_issue(
                issues,
                key=f"{table}.missing_source_trace",
                severity="error",
                count=missing_count,
                message=f"{label}历史数据缺少来源模型/来源表或来源记录编号。",
                sample_sql=f"""
                    SELECT id, {record_col} AS legacy_record_id, {source_expr} AS legacy_source
                      FROM {table}
                     WHERE {legacy_where}
                       AND (COALESCE({record_col}::text, '') = '' OR COALESCE({source_expr}::text, '') = '')
                     ORDER BY id
                """,
            )
            duplicate_count = count_query(
                f"""
                SELECT {source_expr}, {record_col}
                  FROM {table}
                 WHERE {legacy_where}
                   AND COALESCE({record_col}::text, '') <> ''
                   AND COALESCE({source_expr}::text, '') <> ''
                 GROUP BY {source_expr}, {record_col}
                HAVING COUNT(*) > 1
                """
            )
            add_issue(
                issues,
                key=f"{table}.duplicate_source_trace",
                severity="error",
                count=duplicate_count,
                message=f"{label}历史来源键重复，回填不满足幂等唯一性。",
                sample_sql=f"""
                    SELECT {source_expr} AS legacy_source, {record_col} AS legacy_record_id, COUNT(*) AS duplicate_count
                      FROM {table}
                     WHERE {legacy_where}
                       AND COALESCE({record_col}::text, '') <> ''
                       AND COALESCE({source_expr}::text, '') <> ''
                     GROUP BY {source_expr}, {record_col}
                    HAVING COUNT(*) > 1
                     ORDER BY duplicate_count DESC
                """,
            )
    return issues


def collect_projection_followup_issues(semantic: dict[str, int]) -> list[dict[str, object]]:
    """Collect partner projection gaps that should not gate source fact replay.

    Customer/supplier ranks and partner source attribution are projections from
    business facts. They are useful acceptance follow-ups, but the primary audit
    pass should first complete deterministic old-database facts that have direct
    source fields.
    """

    issues: list[dict[str, object]] = []
    add_issue(
        issues,
        key="partner.supplier_type_missing",
        severity="info",
        count=count_table(
            "res_partner",
            "COALESCE(supplier_rank, 0) > 0 AND NOT EXISTS "
            "(SELECT 1 FROM sc_res_partner_supplier_type_rel rel WHERE rel.partner_id = res_partner.id)",
        ),
        message="供应商缺少多选供应商类型关系。",
        sample_sql="""
            SELECT id, name, sc_supplier_type, legacy_partner_id
              FROM res_partner
             WHERE COALESCE(supplier_rank, 0) > 0
               AND NOT EXISTS (
                    SELECT 1
                      FROM sc_res_partner_supplier_type_rel rel
                     WHERE rel.partner_id = res_partner.id
               )
             ORDER BY id
        """,
    )
    add_issue(
        issues,
        key="partner.business_source_creator_missing",
        severity="info",
        count=count_table(
            "res_partner",
            "(COALESCE(customer_rank, 0) > 0 OR COALESCE(supplier_rank, 0) > 0) "
            "AND COALESCE(sc_source_fact_count, 0) > 0 "
            "AND COALESCE(sc_source_created_by, '') = ''",
        ),
        message="有业务事实的客户/供应商缺少录入人回填。",
        sample_sql="""
            SELECT id, name, customer_rank, supplier_rank, sc_source_fact_count, sc_source_fact_source
              FROM res_partner
             WHERE (COALESCE(customer_rank, 0) > 0 OR COALESCE(supplier_rank, 0) > 0)
               AND COALESCE(sc_source_fact_count, 0) > 0
               AND COALESCE(sc_source_created_by, '') = ''
             ORDER BY sc_source_fact_count DESC, id
        """,
    )
    add_issue(
        issues,
        key="partner.business_source_time_missing",
        severity="info",
        count=count_table(
            "res_partner",
            "(COALESCE(customer_rank, 0) > 0 OR COALESCE(supplier_rank, 0) > 0) "
            "AND COALESCE(sc_source_fact_count, 0) > 0 "
            "AND COALESCE(sc_source_created_at, '') = ''",
        ),
        message="有业务事实的客户/供应商缺少录入时间回填。",
        sample_sql="""
            SELECT id, name, customer_rank, supplier_rank, sc_source_fact_count, sc_source_fact_source
              FROM res_partner
             WHERE (COALESCE(customer_rank, 0) > 0 OR COALESCE(supplier_rank, 0) > 0)
               AND COALESCE(sc_source_fact_count, 0) > 0
               AND COALESCE(sc_source_created_at, '') = ''
             ORDER BY sc_source_fact_count DESC, id
        """,
    )
    add_issue(
        issues,
        key="partner.creator_placeholder",
        severity="info",
        count=count_table(
            "res_partner",
            "LOWER(COALESCE(sc_source_created_by, '')) IN ('odoobot', 'false', 'admin', 'administrator')",
        ),
        message="客户/供应商录入人出现系统占位值，需追溯历史来源真实用户。",
        sample_sql="""
            SELECT id, name, sc_source_created_by, sc_source_created_at, sc_source_fact_source
              FROM res_partner
             WHERE LOWER(COALESCE(sc_source_created_by, '')) IN ('odoobot', 'false', 'admin', 'administrator')
             ORDER BY id
        """,
    )
    add_issue(
        issues,
        key="partner.customer_rank_mismatch",
        severity="info",
        count=semantic["customer_rank_mismatch"],
        message="客户身份与收入合同/收款事实不一致。",
    )
    add_issue(
        issues,
        key="partner.supplier_rank_mismatch",
        severity="info",
        count=semantic["supplier_rank_mismatch"],
        message="供应商身份与支出合同/付款事实不一致。",
    )
    return issues


def collect_issues(counts: dict[str, int]) -> list[dict[str, object]]:
    issues: list[dict[str, object]] = []
    supplier_contract_entry_missing = count_table(
        "construction_contract",
        "legacy_contract_id IS NOT NULL AND type = 'in' AND (COALESCE(entry_user_text, '') = '' OR entry_time IS NULL)",
    )
    add_issue(
        issues,
        key="contract.entry_user_missing",
        severity="warn",
        count=count_table(
            "construction_contract",
            "legacy_contract_id IS NOT NULL AND COALESCE(entry_user_text, '') = ''",
        ),
        message="历史合同缺少旧库直接对应的录入人。",
        sample_sql="""
            SELECT id, legacy_contract_id, legacy_document_no, subject, entry_user_text, entry_time
              FROM construction_contract
             WHERE legacy_contract_id IS NOT NULL
               AND COALESCE(entry_user_text, '') = ''
             ORDER BY id
        """,
    )
    add_issue(
        issues,
        key="contract.entry_time_missing",
        severity="warn",
        count=count_table(
            "construction_contract",
            "legacy_contract_id IS NOT NULL AND entry_time IS NULL",
        ),
        message="历史合同缺少旧库直接对应的录入时间。",
        sample_sql="""
            SELECT id, legacy_contract_id, legacy_document_no, subject, entry_user_text, entry_time
              FROM construction_contract
             WHERE legacy_contract_id IS NOT NULL
               AND entry_time IS NULL
             ORDER BY id
        """,
    )
    add_issue(
        issues,
        key="contract.supplier_entry_source_missing",
        severity="info",
        count=supplier_contract_entry_missing,
        message="供应商合同运行时载荷未携带历史来源录入人/录入时间；不能用 Odoo 创建人或导入时间替代。",
        sample_sql="""
            SELECT id, legacy_contract_id, legacy_document_no, legacy_contract_no, subject, note
              FROM construction_contract
             WHERE legacy_contract_id IS NOT NULL
               AND type = 'in'
               AND (COALESCE(entry_user_text, '') = '' OR entry_time IS NULL)
             ORDER BY id
        """,
    )
    add_issue(
        issues,
        key="contract.amount_missing",
        severity="warn",
        count=count_table(
            "construction_contract",
            "legacy_contract_id IS NOT NULL AND COALESCE(visible_contract_amount, 0) = 0 "
            "AND COALESCE(legacy_contract_amount_source, '') = ''",
        ),
        message="历史合同合同金额为空或为 0，且缺少旧库金额来源证据。",
        sample_sql="""
            SELECT id, legacy_contract_id, legacy_document_no, subject,
                   legacy_contract_amount, legacy_contract_amount_source, amount_untaxed, visible_contract_amount
              FROM construction_contract
             WHERE legacy_contract_id IS NOT NULL
               AND COALESCE(visible_contract_amount, 0) = 0
               AND COALESCE(legacy_contract_amount_source, '') = ''
             ORDER BY id
        """,
    )
    add_issue(
        issues,
        key="contract.receivable_balance_missing",
        severity="warn",
        count=count_table(
            "construction_contract",
            "type = 'out' AND legacy_contract_id IS NOT NULL AND COALESCE(visible_contract_amount, 0) <> 0 "
            "AND (visible_received_amount IS NULL OR visible_unreceived_amount IS NULL) "
            "AND (COALESCE(visible_received_amount_source, '') = '' OR COALESCE(visible_unreceived_amount_source, '') = '')",
        ),
        message="收入合同缺少历史来源累计收款/未收款余额来源证据，不能按合同金额倒推造数。",
        sample_sql="""
            SELECT id, legacy_contract_id, legacy_document_no, subject,
                   visible_contract_amount, visible_received_amount, visible_unreceived_amount,
                   visible_received_amount_source, visible_unreceived_amount_source
              FROM construction_contract
             WHERE type = 'out'
               AND legacy_contract_id IS NOT NULL
               AND COALESCE(visible_contract_amount, 0) <> 0
               AND (visible_received_amount IS NULL OR visible_unreceived_amount IS NULL)
               AND (COALESCE(visible_received_amount_source, '') = '' OR COALESCE(visible_unreceived_amount_source, '') = '')
             ORDER BY id
        """,
    )
    add_issue(
        issues,
        key="contract.receivable_formula_mismatch",
        severity="warn",
        count=count_table(
            "construction_contract",
            "type = 'out' AND visible_received_amount IS NOT NULL AND visible_unreceived_amount IS NOT NULL AND ABS(COALESCE(visible_contract_amount, 0) - COALESCE(visible_received_amount, 0) - COALESCE(visible_unreceived_amount, 0)) > 0.05",
        ),
        message="收入合同的合同金额、累计收款、未收款金额不平衡。",
        sample_sql="""
            SELECT id, legacy_contract_id, legacy_document_no, subject,
                   visible_contract_amount, visible_received_amount, visible_unreceived_amount
              FROM construction_contract
             WHERE type = 'out'
               AND visible_received_amount IS NOT NULL
               AND visible_unreceived_amount IS NOT NULL
               AND ABS(COALESCE(visible_contract_amount, 0) - COALESCE(visible_received_amount, 0) - COALESCE(visible_unreceived_amount, 0)) > 0.05
             ORDER BY id
        """,
    )
    issues.extend(source_trace_issues())
    return issues


def export_gap_details(root: Path) -> dict[str, object]:
    amount_rows = rows(
        """
        SELECT id AS contract_id,
               type,
               legacy_contract_id,
               legacy_document_no,
               legacy_contract_no,
               subject,
               legacy_contract_amount,
               legacy_contract_amount_source,
               amount_untaxed,
               visible_contract_amount,
               note
          FROM construction_contract
         WHERE legacy_contract_id IS NOT NULL
           AND COALESCE(visible_contract_amount, 0) = 0
           AND COALESCE(legacy_contract_amount_source, '') = ''
         ORDER BY type, legacy_document_no, id
        """
    )
    supplier_entry_rows = rows(
        """
        SELECT id AS contract_id,
               type,
               legacy_contract_id,
               legacy_document_no,
               legacy_contract_no,
               subject,
               note
          FROM construction_contract
         WHERE legacy_contract_id IS NOT NULL
           AND type = 'in'
           AND (COALESCE(entry_user_text, '') = '' OR entry_time IS NULL)
         ORDER BY legacy_document_no, id
        """
    )
    partner_creator_rows = rows(
        """
        SELECT p.id AS partner_id,
               p.name,
               p.customer_rank,
               p.supplier_rank,
               p.sc_source_fact_count,
               p.sc_source_fact_source
          FROM res_partner p
         WHERE (p.customer_rank > 0 OR p.supplier_rank > 0 OR COALESCE(p.sc_source_fact_count, 0) > 0)
           AND COALESCE(p.sc_source_created_by, '') = ''
         ORDER BY p.sc_source_fact_count DESC, p.id
        """
    )
    fact_creator_source_gap_rows = rows(
        """
        WITH fact_sources AS (
            SELECT partner_id,
                   'sc.receipt.income' AS runtime_model,
                   legacy_source_table,
                   legacy_record_id,
                   COALESCE(amount, 0) AS amount
              FROM sc_receipt_income
             WHERE source_origin = 'legacy'
               AND partner_id IS NOT NULL
            UNION ALL
            SELECT partner_id,
                   'sc.payment.execution' AS runtime_model,
                   legacy_source_table,
                   legacy_record_id,
                   COALESCE(paid_amount, 0) AS amount
              FROM sc_payment_execution
             WHERE source_origin = 'legacy'
               AND partner_id IS NOT NULL
            UNION ALL
            SELECT partner_id,
                   'sc.legacy.enterprise.business.fact' AS runtime_model,
                   legacy_source_table,
                   legacy_record_id,
                   COALESCE(amount_total, 0) AS amount
              FROM sc_legacy_enterprise_business_fact
             WHERE partner_id IS NOT NULL
        )
        SELECT p.id AS partner_id,
               p.name AS partner_name,
               f.runtime_model,
               f.legacy_source_table,
               COUNT(*) AS fact_rows,
               MIN(f.legacy_record_id) AS sample_legacy_record_id,
               SUM(f.amount) AS amount_total
          FROM res_partner p
          JOIN fact_sources f ON f.partner_id = p.id
         WHERE (p.customer_rank > 0 OR p.supplier_rank > 0 OR COALESCE(p.sc_source_fact_count, 0) > 0)
           AND COALESCE(p.sc_source_created_by, '') = ''
         GROUP BY p.id, p.name, f.runtime_model, f.legacy_source_table
         ORDER BY fact_rows DESC, p.id
        """
    )
    fact_creator_record_gap_rows = rows(
        """
        WITH fact_sources AS (
            SELECT partner_id,
                   'sc.receipt.income' AS runtime_model,
                   legacy_source_table,
                   legacy_record_id,
                   COALESCE(amount, 0) AS amount
              FROM sc_receipt_income
             WHERE source_origin = 'legacy'
               AND partner_id IS NOT NULL
            UNION ALL
            SELECT partner_id,
                   'sc.payment.execution' AS runtime_model,
                   legacy_source_table,
                   legacy_record_id,
                   COALESCE(paid_amount, 0) AS amount
              FROM sc_payment_execution
             WHERE source_origin = 'legacy'
               AND partner_id IS NOT NULL
            UNION ALL
            SELECT partner_id,
                   'sc.legacy.enterprise.business.fact' AS runtime_model,
                   legacy_source_table,
                   legacy_record_id,
                   COALESCE(amount_total, 0) AS amount
              FROM sc_legacy_enterprise_business_fact
             WHERE partner_id IS NOT NULL
        )
        SELECT p.id AS partner_id,
               p.name AS partner_name,
               f.runtime_model,
               f.legacy_source_table,
               f.legacy_record_id,
               f.amount
          FROM res_partner p
          JOIN fact_sources f ON f.partner_id = p.id
         WHERE (p.customer_rank > 0 OR p.supplier_rank > 0 OR COALESCE(p.sc_source_fact_count, 0) > 0)
           AND COALESCE(p.sc_source_created_by, '') = ''
         ORDER BY f.legacy_source_table, f.legacy_record_id, p.id
        """
    )
    fact_time_record_gap_rows = rows(
        """
        WITH fact_sources AS (
            SELECT partner_id,
                   'sc.receipt.income' AS runtime_model,
                   legacy_source_table,
                   legacy_record_id,
                   COALESCE(amount, 0) AS amount
              FROM sc_receipt_income
             WHERE source_origin = 'legacy'
               AND partner_id IS NOT NULL
            UNION ALL
            SELECT partner_id,
                   'sc.payment.execution' AS runtime_model,
                   legacy_source_table,
                   legacy_record_id,
                   COALESCE(paid_amount, 0) AS amount
              FROM sc_payment_execution
             WHERE source_origin = 'legacy'
               AND partner_id IS NOT NULL
            UNION ALL
            SELECT partner_id,
                   'sc.legacy.enterprise.business.fact' AS runtime_model,
                   legacy_source_table,
                   legacy_record_id,
                   COALESCE(amount_total, 0) AS amount
              FROM sc_legacy_enterprise_business_fact
             WHERE partner_id IS NOT NULL
        )
        SELECT p.id AS partner_id,
               p.name AS partner_name,
               f.runtime_model,
               f.legacy_source_table,
               f.legacy_record_id,
               f.amount
          FROM res_partner p
          JOIN fact_sources f ON f.partner_id = p.id
         WHERE (p.customer_rank > 0 OR p.supplier_rank > 0 OR COALESCE(p.sc_source_fact_count, 0) > 0)
           AND COALESCE(p.sc_source_created_at, '') = ''
         ORDER BY f.legacy_source_table, f.legacy_record_id, p.id
        """
    )
    balance_rows = rows(
        """
        SELECT id AS contract_id,
               legacy_contract_id,
               legacy_document_no,
               legacy_contract_no,
               subject,
               visible_contract_amount,
               visible_received_amount,
               visible_unreceived_amount,
               visible_invoice_amount_source,
               visible_received_amount_source,
               visible_unreceived_amount_source
         FROM construction_contract
         WHERE type = 'out'
           AND legacy_contract_id IS NOT NULL
           AND COALESCE(visible_contract_amount, 0) <> 0
           AND (visible_received_amount IS NULL OR visible_unreceived_amount IS NULL)
           AND (COALESCE(visible_received_amount_source, '') = '' OR COALESCE(visible_unreceived_amount_source, '') = '')
         ORDER BY legacy_document_no, id
        """
    )
    write_csv(root / "contract_amount_missing_rows_v1.csv", amount_rows)
    write_csv(root / "contract_supplier_entry_source_missing_rows_v1.csv", supplier_entry_rows)
    write_csv(root / "partner_source_creator_missing_rows_v1.csv", partner_creator_rows)
    write_csv(root / "partner_fact_creator_source_gap_rows_v1.csv", fact_creator_source_gap_rows)
    write_csv(root / "partner_fact_creator_record_gap_rows_v1.csv", fact_creator_record_gap_rows)
    write_csv(root / "partner_fact_time_record_gap_rows_v1.csv", fact_time_record_gap_rows)
    write_csv(root / "contract_receivable_balance_missing_rows_v1.csv", balance_rows)
    return {
        "contract_amount_missing_rows": len(amount_rows),
        "contract_supplier_entry_source_missing_rows": len(supplier_entry_rows),
        "partner_source_creator_missing_rows": len(partner_creator_rows),
        "partner_fact_creator_source_gap_rows": len(fact_creator_source_gap_rows),
        "partner_fact_creator_record_gap_rows": len(fact_creator_record_gap_rows),
        "partner_fact_time_record_gap_rows": len(fact_time_record_gap_rows),
        "contract_receivable_balance_missing_rows": len(balance_rows),
        "gap_artifact_root": str(root),
    }


counts = collect_counts()
environment_boundary = collect_environment_boundary()
semantic_counts = partner_semantic_counts()
issues = collect_issues(counts)
projection_followup_issues = collect_projection_followup_issues(semantic_counts)
error_count = sum(1 for issue in issues if issue["severity"] == "error")
warn_count = sum(1 for issue in issues if issue["severity"] == "warn")
environment_warn_count = 0 if environment_boundary["clean"] else 1
projection_warn_count = sum(1 for issue in projection_followup_issues if issue["severity"] == "warn")
root = artifact_root()
gap_exports = export_gap_details(root)
deterministic_fact_status = "FAIL" if error_count else ("WARN" if warn_count else "PASS")

payload = {
    "status": "FAIL" if error_count else ("WARN" if warn_count or environment_warn_count else "PASS"),
    "deterministic_fact_status": deterministic_fact_status,
    "database": DB_NAME,
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "mode": "business_fact_backfill_audit",
    "environment_boundary": environment_boundary,
    "counts": counts,
    "semantic_counts": semantic_counts,
    "issue_count": len(issues),
    "error_count": error_count,
    "warn_count": warn_count,
    "environment_warn_count": environment_warn_count,
    "issues": issues,
    "projection_followup_issue_count": len(projection_followup_issues),
    "projection_followup_warn_count": projection_warn_count,
    "projection_followup_issues": projection_followup_issues,
    "gap_exports": gap_exports,
    "audit_strategy": "deterministic_old_database_facts_first_then_partner_projection",
    "decision": "deterministic_fact_backfill_needs_remediation"
    if issues
    else ("deterministic_fact_audit_clean_environment_mixed" if environment_warn_count else "deterministic_fact_audit_clean"),
}

output = root / "business_fact_backfill_audit_v1.json"
output.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
print("BUSINESS_FACT_BACKFILL_AUDIT=" + json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str))
