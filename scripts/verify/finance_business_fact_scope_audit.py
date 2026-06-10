# -*- coding: utf-8 -*-
"""Audit finance fact families that must be integrated into formal business handling.

Run inside Odoo shell:
    DB_NAME=sc_demo bash scripts/ops/odoo_shell_exec.sh < scripts/verify/finance_business_fact_scope_audit.py
"""

from __future__ import annotations

import json
import os
from collections import OrderedDict
from pathlib import Path


def artifact_root() -> Path:
    raw = os.getenv("MIGRATION_ARTIFACT_ROOT") or os.getenv("FINANCE_BUSINESS_FACT_ARTIFACT_ROOT")
    candidates = [Path(raw)] if raw else []
    candidates.extend([Path("/mnt/artifacts/backend"), Path(f"/tmp/finance_business_fact/{env.cr.dbname}")])  # noqa: F821
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


def rows(query, params=None):
    env.cr.execute(query, params or [])  # noqa: F821
    return env.cr.fetchall()  # noqa: F821


def one(query, params=None):
    data = rows(query, params)
    return data[0] if data else ()


def named(keys, query, params=None):
    return OrderedDict(zip(keys, one(query, params)))


def table(items):
    return [list(item) for item in items]


summary = OrderedDict()
findings = []

summary["arrival_settlement"] = named(
    ["count", "actual_fund_amount", "deducted_amount_total", "paid_amount_total"],
    """
    SELECT
        COUNT(*)::integer,
        COALESCE(SUM(actual_fund_amount), 0.0),
        COALESCE(SUM(deducted_amount_total), 0.0),
        COALESCE(SUM(paid_amount_total), 0.0)
      FROM sc_legacy_fund_confirmation_document
     WHERE active IS TRUE
    """,
)
summary["arrival_settlement_by_state"] = table(
    rows(
        """
        SELECT document_state, COUNT(*)::integer, COALESCE(SUM(actual_fund_amount), 0.0)
          FROM sc_legacy_fund_confirmation_document
         WHERE active IS TRUE
         GROUP BY document_state
         ORDER BY COUNT(*) DESC, document_state
        """
    )
)

summary["deduction_paid_formal"] = named(
    ["count", "amount", "approved_amount", "paid_amount"],
    """
    SELECT
        COUNT(*)::integer,
        COALESCE(SUM(amount), 0.0),
        COALESCE(SUM(approved_amount), 0.0),
        COALESCE(SUM(paid_amount), 0.0)
      FROM sc_expense_claim
     WHERE active IS TRUE
       AND legacy_source_model = 'online_old_scbs:T_KK_SJDJB:list897'
    """,
)
summary["deduction_refund_formal"] = named(
    ["count", "amount", "approved_amount", "paid_amount"],
    """
    SELECT
        COUNT(*)::integer,
        COALESCE(SUM(amount), 0.0),
        COALESCE(SUM(approved_amount), 0.0),
        COALESCE(SUM(paid_amount), 0.0)
      FROM sc_expense_claim
     WHERE active IS TRUE
       AND legacy_source_model = 'online_old_scbs:T_KK_SJTHB:list898'
    """,
)
summary["deduction_adjustment_raw"] = named(
    ["count", "planned_amount", "actual_amount"],
    """
    SELECT
        COUNT(*)::integer,
        COALESCE(SUM(current_planned_amount), 0.0),
        COALESCE(SUM(current_actual_amount), 0.0)
      FROM sc_legacy_deduction_adjustment_line
     WHERE active IS TRUE
    """,
)
summary["deduction_adjustment_by_item_returned"] = table(
    rows(
        """
        SELECT
            COALESCE(adjustment_item_name, ''),
            COALESCE(returned_flag, ''),
            COUNT(*)::integer,
            COALESCE(SUM(current_actual_amount), 0.0)
          FROM sc_legacy_deduction_adjustment_line
         WHERE active IS TRUE
         GROUP BY 1, 2
         ORDER BY COUNT(*) DESC, 1, 2
        """
    )
)
summary["deduction_refund_account_lines"] = table(
    rows(
        """
        SELECT
            COALESCE(category, ''),
            COUNT(*)::integer,
            COALESCE(SUM(amount), 0.0)
          FROM sc_legacy_account_transaction_line
         WHERE active IS TRUE
           AND source_table = 'T_KK_SJTHB_CB'
         GROUP BY category
         ORDER BY COUNT(*) DESC, category
        """
    )
)

summary["tax_deduction_formal"] = named(
    [
        "count",
        "invoice_amount_total",
        "invoice_tax_amount",
        "deduction_amount",
        "deduction_tax_amount",
        "deduction_surcharge_amount",
        "transfer_out_count",
    ],
    """
    SELECT
        COUNT(*)::integer,
        COALESCE(SUM(invoice_amount_total), 0.0),
        COALESCE(SUM(invoice_tax_amount), 0.0),
        COALESCE(SUM(deduction_amount), 0.0),
        COALESCE(SUM(deduction_tax_amount), 0.0),
        COALESCE(SUM(deduction_surcharge_amount), 0.0),
        COUNT(*) FILTER (WHERE is_transfer_out)::integer
      FROM sc_tax_deduction_registration
     WHERE active IS TRUE
    """,
)
summary["tax_deduction_by_state"] = table(
    rows(
        """
        SELECT state, COUNT(*)::integer, COALESCE(SUM(deduction_tax_amount), 0.0)
          FROM sc_tax_deduction_registration
         WHERE active IS TRUE
         GROUP BY state
         ORDER BY COUNT(*) DESC, state
        """
    )
)

summary["self_funding_raw"] = named(
    ["count", "income_amount", "refund_amount", "unreturned_amount"],
    """
    SELECT
        COUNT(*)::integer,
        COALESCE(SUM(self_funding_amount), 0.0),
        COALESCE(SUM(refund_amount), 0.0),
        COALESCE(SUM(unreturned_amount), 0.0)
      FROM sc_legacy_self_funding_fact
     WHERE active IS TRUE
       AND COALESCE(deleted_flag, '0') IN ('0', '')
    """,
)
summary["self_funding_by_type"] = table(
    rows(
        """
        SELECT
            line_type,
            COUNT(*)::integer,
            COALESCE(SUM(self_funding_amount), 0.0),
            COALESCE(SUM(refund_amount), 0.0),
            COALESCE(SUM(unreturned_amount), 0.0)
          FROM sc_legacy_self_funding_fact
         WHERE active IS TRUE
           AND COALESCE(deleted_flag, '0') IN ('0', '')
         GROUP BY line_type
         ORDER BY line_type
        """
    )
)
self_type_amounts = {row[0]: {"count": row[1], "income": float(row[2] or 0.0), "refund": float(row[3] or 0.0)} for row in summary["self_funding_by_type"]}
if abs(self_type_amounts.get("income", {}).get("income", 0.0) - self_type_amounts.get("income_visible", {}).get("income", 0.0)) < 200000:
    findings.append(
        {
            "severity": "policy_required",
            "key": "self_funding_income_duplicate_family",
            "message": "self_funding income and income_visible are near-duplicates; formal balance policy must choose one source family.",
        }
    )
if self_type_amounts.get("refund_visible", {}).get("count", 0) and not self_type_amounts.get("refund_visible", {}).get("refund", 0.0):
    findings.append(
        {
            "severity": "policy_required",
            "key": "self_funding_refund_visible_zero_amount",
            "message": "refund_visible rows exist but carry zero refund amount; refund balance must use refund rows or a proven join.",
        }
    )

summary["tender_guarantee_formal"] = named(
    ["count", "out_amount", "return_amount", "outstanding_amount"],
    """
    SELECT
        COUNT(*)::integer,
        COALESCE(SUM(CASE WHEN type = 'out' THEN amount ELSE 0 END), 0.0),
        COALESCE(SUM(CASE WHEN type = 'return' THEN amount ELSE 0 END), 0.0),
        COALESCE(SUM(CASE WHEN type = 'out' THEN amount ELSE -amount END), 0.0)
      FROM tender_guarantee
    """,
)
summary["tender_guarantee_by_state_type"] = table(
    rows(
        """
        SELECT state, type, COUNT(*)::integer, COALESCE(SUM(amount), 0.0)
          FROM tender_guarantee
         GROUP BY state, type
         ORDER BY state, type
        """
    )
)
summary["legacy_tender_guarantee_by_source"] = table(
    rows(
        """
        SELECT legacy_source_table, COUNT(*)::integer, COALESCE(SUM(source_amount), 0.0)
          FROM sc_legacy_tender_guarantee_report_fact
         GROUP BY legacy_source_table
         ORDER BY legacy_source_table
        """
    )
)

summary["existing_projection_totals"] = OrderedDict(
    [
        (
            "company_operation_summary",
            named(
                ["months", "income_amount", "expense_amount", "revenue_amount", "deduction_paid_amount", "deduction_refund_amount"],
                """
                SELECT
                    COUNT(*)::integer,
                    COALESCE(SUM(income_amount), 0.0),
                    COALESCE(SUM(expense_amount), 0.0),
                    COALESCE(SUM(revenue_amount), 0.0),
                    COALESCE(SUM(
                        deduction_management_fee_amount
                        + deduction_enterprise_income_tax_amount
                        + deduction_vat_surcharge_amount
                        + deduction_vat_surcharge_nonrefundable_amount
                    ), 0.0),
                    COALESCE(SUM(deduction_refund_surcharge_amount), 0.0)
                  FROM sc_company_operation_summary
                """,
            ),
        ),
        (
            "ar_ap_project_summary",
            named(
                ["rows", "deduction_tax_amount", "deduction_surcharge_amount", "self_funding_income_amount", "self_funding_refund_amount", "self_funding_unreturned_amount"],
                """
                SELECT
                    COUNT(*)::integer,
                    COALESCE(SUM(deduction_tax_amount), 0.0),
                    COALESCE(SUM(deduction_surcharge_amount), 0.0),
                    COALESCE(SUM(self_funding_income_amount), 0.0),
                    COALESCE(SUM(self_funding_refund_amount), 0.0),
                    COALESCE(SUM(self_funding_unreturned_amount), 0.0)
                  FROM sc_ar_ap_project_summary
                """,
            ),
        ),
    ]
)

business_domains = OrderedDict(
    [
        ("arrival_settlement", "工程款到账清算"),
        ("deduction_clearing", "扣款代缴与退回"),
        ("tax_deduction", "税务抵扣"),
        ("self_funding", "自筹垫资与退回"),
        ("guarantee_deposit", "保证金支出与退回"),
    ]
)

summary["business_domain_policy"] = business_domains
summary["findings"] = findings
summary["decision"] = "finance_fact_policy_required" if findings else "finance_fact_scope_ready"
summary["status"] = "WARN" if findings else "PASS"

out = artifact_root() / "finance_business_fact_scope_audit_v1.json"
out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

print(json.dumps(summary, ensure_ascii=False))
print(f"FINANCE_BUSINESS_FACT_SCOPE_AUDIT_RESULT: {summary['status']} decision={summary['decision']} output={out}")
