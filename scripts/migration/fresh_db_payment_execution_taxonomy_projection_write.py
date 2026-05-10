"""Normalize payment execution user-entry taxonomy for visible menu lanes."""

from __future__ import annotations

import json
import os
from pathlib import Path


def repo_root() -> Path:
    file_name = globals().get("__file__")
    if file_name:
        return Path(file_name).resolve().parents[2]
    return Path.cwd()


def artifact_root() -> Path:
    root = os.environ.get("MIGRATION_ARTIFACT_ROOT") or os.environ.get("HISTORY_CONTINUITY_ARTIFACT_ROOT")
    if root:
        return Path(root)
    return repo_root() / "artifacts" / "migration"


output_json = artifact_root() / "fresh_db_payment_execution_taxonomy_projection_write_result_v1.json"
output_json.parent.mkdir(parents=True, exist_ok=True)

Payment = env["sc.payment.execution"].sudo()  # noqa: F821

before_company = Payment.search_count(
    [("source_kind", "=", "actual_outflow"), ("payment_family", "=", "公司财务支出")]
)
before_legacy_actual = Payment.search_count(
    [("source_kind", "=", "actual_outflow"), ("payment_family", "=", "actual_outflow")]
)
before_partner = Payment.search_count(
    [("source_kind", "=", "actual_outflow"), ("payment_family", "in", ["往来单位付款", "SCBS供应商付款"])]
)

env.cr.execute(  # noqa: F821
    """
    UPDATE sc_payment_execution
       SET payment_family = '公司财务支出',
           write_date = NOW()
     WHERE source_kind = 'actual_outflow'
       AND payment_family = 'actual_outflow'
    """
)
normalized_company_finance_expense = env.cr.rowcount  # noqa: F821
env.cr.commit()  # noqa: F821

after_company = Payment.search_count(
    [("source_kind", "=", "actual_outflow"), ("payment_family", "=", "公司财务支出")]
)
after_legacy_actual = Payment.search_count(
    [("source_kind", "=", "actual_outflow"), ("payment_family", "=", "actual_outflow")]
)
after_partner = Payment.search_count(
    [("source_kind", "=", "actual_outflow"), ("payment_family", "in", ["往来单位付款", "SCBS供应商付款"])]
)

result = {
    "mode": "fresh_db_payment_execution_taxonomy_projection_write",
    "before_company_finance_expense": before_company,
    "before_legacy_actual_outflow_family": before_legacy_actual,
    "before_partner_payment": before_partner,
    "normalized_company_finance_expense": normalized_company_finance_expense,
    "after_company_finance_expense": after_company,
    "after_legacy_actual_outflow_family": after_legacy_actual,
    "after_partner_payment": after_partner,
    "status": "PASS" if after_legacy_actual == 0 and after_company >= before_company + before_legacy_actual else "REVIEW",
}

output_json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(result, ensure_ascii=False, indent=2))
