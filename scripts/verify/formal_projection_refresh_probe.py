#!/usr/bin/env python3
"""Verify formal projection tables after upgrade/demo uninstall refresh."""

from __future__ import annotations

import json
import os
from pathlib import Path


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


def scalar(sql: str, params: list[object] | None = None) -> object:
    env.cr.execute(sql, params or [])  # noqa: F821
    row = env.cr.fetchone()  # noqa: F821
    return row[0] if row else None


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
    return int(scalar(f"SELECT COUNT(*) FROM ({sql}) AS probe_count_query") or 0)


def count_legacy_or_all(table_name: str) -> int:
    if column_exists(table_name, "source_origin"):
        return count_table(table_name, "source_origin = 'legacy'")
    return count_table(table_name)


def partner_business_role_counts() -> dict[str, int]:
    Partner = env["res.partner"].sudo().with_context(active_test=False)  # noqa: F821
    facts = Partner._sc_collect_partner_business_facts()
    customer_ids = {partner_id for partner_id, data in facts.items() if data and data["customer"]}
    supplier_ids = {
        partner_id
        for partner_id, data in facts.items()
        if data and data["supplier"] and Partner._sc_is_supplier_business_counterparty(Partner.browse(partner_id))
    }
    customer_rank_ids = set(Partner.search([("customer_rank", ">", 0)]).ids)
    supplier_rank_ids = set(Partner.search([("supplier_rank", ">", 0)]).ids)
    return {
        "partner_semantic_customer_target": len(customer_ids),
        "partner_semantic_supplier_target": len(supplier_ids),
        "partner_semantic_customer_rank_mismatch": len(customer_ids ^ customer_rank_ids),
        "partner_semantic_supplier_rank_mismatch": len(supplier_ids ^ supplier_rank_ids),
    }


def add_gap(gaps: list[dict[str, object]], key: str, source: int, target: int, detail: str) -> None:
    if source > 0 and target <= 0:
        gaps.append({"key": key, "source": source, "target": target, "detail": detail})


partner_role_counts = partner_business_role_counts()

counts = {
    "legacy_account_master": count_table("sc_legacy_account_master"),
    "fund_account_legacy": count_table("sc_fund_account", "source_origin = 'legacy'"),
    "history_todo": count_table("sc_history_todo"),
    "workbench_todo": count_table(
        "sc_workbench_item",
        "fact_type = 'my_todo' AND source_model = 'sc.history.todo'",
    ),
    "workbench_approval": count_table(
        "sc_workbench_item",
        "fact_type = 'my_approval' AND source_model = 'sc.history.todo'",
    ),
    "fund_daily_summary": count_table("sc_fund_daily_summary"),
    "dashboard_fund": count_table(
        "sc_dashboard_cockpit_fact",
        "fact_type = 'fund_cockpit' AND source_model = 'sc.fund.daily.summary'",
    ),
    "cost_contracts": count_table("construction_contract", "type = 'in'"),
    "dashboard_cost": count_table(
        "sc_dashboard_cockpit_fact",
        "fact_type = 'cost_cockpit' AND source_model = 'construction.contract'",
    ),
    "legacy_material_category": count_table("sc_legacy_material_category"),
    "product_category_legacy": count_table("product_category", "legacy_material_category_id IS NOT NULL"),
    "legacy_material_detail": count_table("sc_legacy_material_detail"),
    "material_catalog_legacy": count_table("sc_material_catalog", "legacy_material_detail_id IS NOT NULL"),
    "material_catalog_with_category": count_table(
        "sc_material_catalog",
        "legacy_material_detail_id IS NOT NULL AND category_id IS NOT NULL",
    ),
    "material_catalog_with_project": count_table(
        "sc_material_catalog",
        "legacy_material_detail_id IS NOT NULL AND project_id IS NOT NULL",
    ),
    "legacy_receipt_income": count_table("sc_legacy_receipt_income_fact"),
    "receipt_income": count_table("sc_receipt_income", "source_origin = 'legacy'"),
    "legacy_payment_residual": count_table("sc_legacy_payment_residual_fact"),
    "payment_execution": count_table("sc_payment_execution", "source_origin = 'legacy'"),
    "legacy_expense_deposit": count_table("sc_legacy_expense_deposit_fact"),
    "legacy_expense_reimbursement": count_table("sc_legacy_expense_reimbursement_line"),
    "expense_claim": count_table("sc_expense_claim", "source_origin = 'legacy'"),
    "legacy_invoice_registration": count_table("sc_legacy_invoice_registration_line"),
    "legacy_invoice_tax": count_table("sc_legacy_invoice_tax_fact"),
    "invoice_registration": count_table("sc_invoice_registration", "source_origin = 'legacy'"),
    "legacy_tax_deduction": count_table("sc_legacy_tax_deduction_fact"),
    "tax_deduction_registration": count_table("sc_tax_deduction_registration", "source_origin = 'legacy'"),
    "legacy_financing_loan": count_table("sc_legacy_financing_loan_fact"),
    "financing_loan": count_table("sc_financing_loan", "source_origin = 'legacy'"),
    "legacy_purchase_contract": count_table("sc_legacy_purchase_contract_fact"),
    "legacy_supplier_pricing": count_table("sc_legacy_supplier_contract_pricing_fact"),
    "general_contract_legacy": count_table("construction_contract", "legacy_contract_id IS NOT NULL"),
    "legacy_construction_diary": count_table("sc_legacy_construction_diary_line"),
    "construction_diary": count_table("sc_construction_diary", "source_origin = 'legacy'"),
    "legacy_deduction_adjustment": count_table("sc_legacy_deduction_adjustment_line"),
    "settlement_adjustment": count_table("sc_settlement_adjustment", "source_origin = 'legacy'"),
    "legacy_fund_confirmation": count_table("sc_legacy_fund_confirmation_line"),
    "legacy_fund_daily_line": count_table("sc_legacy_fund_daily_line"),
    "treasury_reconciliation": count_table("sc_treasury_reconciliation", "source_origin = 'legacy'"),
    "account_transaction_line": count_table("sc_legacy_account_transaction_line"),
    "treasury_ledger": count_legacy_or_all("sc_treasury_ledger"),
    **partner_role_counts,
}

gaps: list[dict[str, object]] = []
add_gap(gaps, "fund_account", counts["legacy_account_master"], counts["fund_account_legacy"], "账户管理正式模型为空")
add_gap(gaps, "workbench_todo", counts["history_todo"], counts["workbench_todo"], "我的待办正式模型为空")
add_gap(gaps, "workbench_approval", counts["history_todo"], counts["workbench_approval"], "我的审批正式模型为空")
add_gap(gaps, "dashboard_fund", counts["fund_daily_summary"], counts["dashboard_fund"], "资金驾驶舱正式事实为空")
add_gap(gaps, "dashboard_cost", counts["cost_contracts"], counts["dashboard_cost"], "成本驾驶舱正式事实为空")
add_gap(gaps, "material_category", counts["legacy_material_category"], counts["product_category_legacy"], "材料分类正式投影为空")
add_gap(gaps, "material_catalog", counts["legacy_material_detail"], counts["material_catalog_legacy"], "材料档案正式模型为空")
add_gap(gaps, "receipt_income", counts["legacy_receipt_income"], counts["receipt_income"], "收款登记正式模型为空")
add_gap(gaps, "payment_execution", counts["legacy_payment_residual"], counts["payment_execution"], "付款登记正式模型为空")
add_gap(
    gaps,
    "expense_claim",
    counts["legacy_expense_deposit"] + counts["legacy_expense_reimbursement"],
    counts["expense_claim"],
    "费用报销正式模型为空",
)
add_gap(
    gaps,
    "invoice_registration",
    counts["legacy_invoice_registration"] + counts["legacy_invoice_tax"],
    counts["invoice_registration"],
    "发票登记正式模型为空",
)
add_gap(
    gaps,
    "tax_deduction_registration",
    counts["legacy_tax_deduction"],
    counts["tax_deduction_registration"],
    "抵扣登记正式模型为空",
)
add_gap(gaps, "financing_loan", counts["legacy_financing_loan"], counts["financing_loan"], "融资借款正式模型为空")
add_gap(
    gaps,
    "general_contract",
    counts["legacy_purchase_contract"] + counts["legacy_supplier_pricing"],
    counts["general_contract_legacy"],
    "历史合同正式合同模型为空",
)
add_gap(
    gaps,
    "construction_diary",
    counts["legacy_construction_diary"],
    counts["construction_diary"],
    "施工日志正式模型为空",
)
add_gap(
    gaps,
    "settlement_adjustment",
    counts["legacy_deduction_adjustment"],
    counts["settlement_adjustment"],
    "结算调整正式模型为空",
)
add_gap(
    gaps,
    "treasury_reconciliation",
    counts["legacy_fund_confirmation"] + counts["legacy_fund_daily_line"],
    counts["treasury_reconciliation"],
    "资金对账正式模型为空",
)
add_gap(gaps, "treasury_ledger", counts["account_transaction_line"], counts["treasury_ledger"], "资金台账正式模型为空")
if counts["partner_semantic_customer_rank_mismatch"] > 0:
    gaps.append(
        {
            "key": "partner_semantic_customer_rank",
            "source": counts["partner_semantic_customer_rank_mismatch"],
            "target": 0,
            "detail": "客户身份与收款/收入业务事实不一致",
        }
    )
if counts["partner_semantic_supplier_rank_mismatch"] > 0:
    gaps.append(
        {
            "key": "partner_semantic_supplier_rank",
            "source": counts["partner_semantic_supplier_rank_mismatch"],
            "target": 0,
            "detail": "供应商身份与合同/付款业务事实不一致",
        }
    )

warnings = []
if counts["legacy_material_detail"] > 0 and counts["material_catalog_with_category"] <= 0:
    warnings.append({"key": "material_catalog_category_link", "detail": "材料档案存在但未关联正式材料分类"})

payload = {
    "status": "PASS" if not gaps else "FAIL",
    "database": env.cr.dbname,  # noqa: F821
    "mode": "formal_projection_refresh_probe",
    "counts": counts,
    "gap_count": len(gaps),
    "gaps": gaps,
    "warning_count": len(warnings),
    "warnings": warnings,
    "decision": "formal_projection_refresh_ready" if not gaps else "formal_projection_refresh_gap",
}

output = artifact_root() / "formal_projection_refresh_probe_result_v1.json"
output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("FORMAL_PROJECTION_REFRESH_PROBE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))

if gaps:
    raise SystemExit(1)
