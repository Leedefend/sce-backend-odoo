#!/usr/bin/env python3
"""Audit whether historical facts are carried by user-facing business entries."""

from __future__ import annotations

import json
import os
from pathlib import Path


def repo_root() -> Path:
    env_root = os.getenv("MIGRATION_REPO_ROOT")
    candidates = []
    if env_root:
        candidates.append(Path(env_root))
    candidates.extend([Path("/mnt"), Path.cwd()])
    for candidate in candidates:
        if (candidate / "addons/smart_construction_core/__manifest__.py").exists():
            return candidate
    return Path.cwd()


def artifact_root() -> Path:
    raw = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(raw)] if raw else []
    candidates.append(repo_root() / "artifacts/migration")
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
    raise RuntimeError({"artifact_root_not_writable": [str(path) for path in candidates]})


def count(model_name: str, domain: list, *, active_test: bool = False) -> int:
    if model_name not in env:  # noqa: F821
        return 0
    return env[model_name].sudo().with_context(active_test=active_test).search_count(domain)  # noqa: F821


TARGETS = [
    {
        "key": "repayment_registration",
        "source_model": "sc.legacy.account.transaction.line",
        "source_domain": [("source_table", "=", "ZJGL_ZCDFSZ_FXJK_HK"), ("direction", "=", "income"), ("amount", ">", 0)],
        "target_model": "sc.expense.claim",
        "target_domain": [("claim_type", "=", "project_company_repay"), ("expense_type", "=", "还款登记")],
    },
    {
        "key": "contractor_project_repay",
        "source_model": "sc.legacy.account.transaction.line",
        "source_domain": [
            ("source_table", "=", "C_FKGL_ZHJZJWL"),
            ("direction", "=", "income"),
            ("amount", ">", 0),
            ("source_summary", "not ilike", "归还公司款"),
            ("source_summary", "not ilike", "还公司款"),
            ("source_summary", "not ilike", "项目还款"),
        ],
        "target_model": "sc.expense.claim",
        "target_domain": [("expense_type", "=", "承包人还项目款")],
    },
    {
        "key": "project_repay_company",
        "source_model": "sc.legacy.account.transaction.line",
        "source_domain": [
            ("source_table", "=", "C_FKGL_ZHJZJWL"),
            ("direction", "=", "income"),
            ("amount", ">", 0),
            ("project_id", "!=", False),
            "|",
            "|",
            ("source_summary", "ilike", "归还公司款"),
            ("source_summary", "ilike", "还公司款"),
            ("source_summary", "ilike", "项目还款"),
        ],
        "target_model": "sc.expense.claim",
        "target_domain": [("claim_type", "=", "project_company_repay"), ("expense_type", "=", "项目还公司款登记")],
    },
    {
        "key": "deduction_bill",
        "source_model": "sc.legacy.deduction.adjustment.line",
        "source_domain": [("project_id", "!=", False)],
        "target_model": "sc.expense.claim",
        "target_domain": [("claim_type", "=", "expense"), ("expense_type", "=", "扣款单")],
    },
    {
        "key": "deduction_paid",
        "source_model": "sc.legacy.account.transaction.line",
        "source_domain": [
            ("source_table", "=", "T_KK_SJDJB_CB"),
            ("direction", "=", "expense"),
            ("amount", ">", 0),
            ("active", "=", True),
            ("project_id", "!=", False),
        ],
        "target_model": "sc.expense.claim",
        "target_domain": [("claim_type", "=", "expense"), ("expense_type", "=", "扣款实缴登记")],
    },
    {
        "key": "deduction_paid_refund",
        "source_model": "sc.legacy.account.transaction.line",
        "source_domain": [
            ("source_table", "=", "T_KK_SJTHB_CB"),
            ("direction", "=", "income"),
            ("amount", ">", 0),
            ("active", "=", True),
            ("project_id", "!=", False),
        ],
        "target_model": "sc.expense.claim",
        "target_domain": [("claim_type", "=", "deduction_refund"), ("expense_type", "=", "扣款实缴退回")],
    },
    {
        "key": "deposit_claim",
        "source_model": "sc.legacy.self.funding.fact",
        "source_domain": [("project_id", "!=", False)],
        "target_model": "sc.expense.claim",
        "target_domain": [("legacy_source_model", "=", "sc.legacy.self.funding.fact")],
    },
    {
        "key": "fund_account_between",
        "source_model": "sc.legacy.account.transaction.line",
        "source_domain": [
            ("source_table", "=", "C_FKGL_ZHJZJWL"),
            ("direction", "=", "expense"),
            ("amount", ">", 0),
            ("active", "=", True),
        ],
        "target_model": "sc.fund.account.operation",
        "target_domain": [("operation_type", "=", "transfer_between")],
    },
    {
        "key": "fund_daily_report",
        "source_model": "sc.legacy.fund.daily.line",
        "source_domain": [("project_id", "!=", False)],
        "target_model": "sc.fund.account.operation",
        "target_domain": [("operation_type", "=", "fund_daily_report")],
    },
    {
        "key": "arrival_confirmation",
        "source_model": "sc.legacy.fund.confirmation.line",
        "source_domain": [("project_id", "!=", False)],
        "target_model": "sc.receipt.income",
        "target_domain": [("source_kind", "=", "receipt_income"), ("receipt_type", "=", "到款确认表")],
    },
    {
        "key": "payment_execution_cost_ledger",
        "source_model": "sc.payment.execution",
        "source_domain": [
            ("project_id", "!=", False),
            ("paid_amount", ">", 0),
            ("state", "not in", ["draft", "cancel"]),
        ],
        "target_model": "project.cost.ledger",
        "target_domain": [("source_model", "=", "sc.payment.execution")],
    },
    {
        "key": "expense_claim_cost_ledger",
        "source_model": "sc.expense.claim",
        "source_domain": [
            ("project_id", "!=", False),
            ("direction", "=", "outflow"),
            ("amount", ">", 0),
            ("state", "not in", ["draft", "cancel"]),
        ],
        "target_model": "project.cost.ledger",
        "target_domain": [("source_model", "=", "sc.expense.claim")],
    },
    {
        "key": "subcontract_settlement_cost_ledger",
        "source_model": "sc.subcontract.settlement",
        "source_domain": [
            ("project_id", "!=", False),
            ("amount_total", ">", 0),
            ("state", "not in", ["draft", "cancel"]),
        ],
        "target_model": "project.cost.ledger",
        "target_domain": [("source_model", "=", "sc.subcontract.settlement")],
    },
    {
        "key": "settlement_order_cost_ledger",
        "source_model": "sc.settlement.order",
        "source_domain": [
            ("project_id", "!=", False),
            ("settlement_type", "=", "out"),
            ("amount_total", ">", 0),
            ("state", "not in", ["draft", "cancel"]),
        ],
        "target_model": "project.cost.ledger",
        "target_domain": [("source_model", "=", "sc.settlement.order")],
    },
]

items = []
for target in TARGETS:
    source_count = count(target["source_model"], target["source_domain"])
    carried_count = count(target["target_model"], target["target_domain"])
    gap = source_count > 0 and carried_count == 0
    items.append(
        {
            "key": target["key"],
            "source_model": target["source_model"],
            "source_count": source_count,
            "target_model": target["target_model"],
            "carried_count": carried_count,
            "gap": gap,
        }
    )

gaps = [item for item in items if item["gap"]]
payload = {
    "mode": "formal_business_backfill_audit_probe",
    "database": env.cr.dbname,  # noqa: F821
    "status": "PASS" if not gaps else "FAIL",
    "decision": "formal_business_backfill_ready" if not gaps else "formal_business_backfill_gap",
    "gap_count": len(gaps),
    "items": items,
}
output_json = artifact_root() / "formal_business_backfill_audit_probe_result_v1.json"
output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("FORMAL_BUSINESS_BACKFILL_AUDIT_PROBE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
if gaps:
    raise RuntimeError(payload)
