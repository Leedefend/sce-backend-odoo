#!/usr/bin/env python3
"""Align third accepted joint-project surfaces to formal business actions."""

from __future__ import annotations

import ast
import json
import os
from pathlib import Path
from typing import Any


SPECS = [
    ("扣款单", "smart_construction_core.action_sc_expense_claim_deduction_bill", "smart_construction_core.menu_scbs55_user_acceptance_300_扣款单"),
    ("扣款实缴登记", "smart_construction_core.action_sc_expense_claim_deduction_paid", "smart_construction_core.menu_scbs55_user_acceptance_330_扣款实缴登记"),
    ("扣款实缴退回", "smart_construction_core.action_sc_expense_claim_deduction_paid_refund", "smart_construction_core.menu_scbs55_user_acceptance_340_扣款实缴退回"),
    ("付款还保证金", "smart_construction_core.action_sc_payment_deposit_return", "smart_construction_core.menu_scbs55_user_acceptance_200_付款还保证金"),
    ("到款确认表", "smart_construction_core.action_sc_receipt_income_arrival_confirmation", "smart_construction_core.menu_scbs55_user_acceptance_350_到款确认表"),
    ("公司资料存档", "smart_construction_core.action_sc_company_document_archive", "smart_construction_core.menu_scbs55_user_acceptance_040_公司资料存档"),
    ("资金日报表", "smart_construction_core.action_sc_fund_daily_user_report", "smart_construction_core.menu_scbs55_user_acceptance_360_资金日报表"),
    ("请假/休假审批单", "smart_construction_core.action_sc_leave_request", "smart_construction_core.menu_scbs55_user_acceptance_050_请假_休假审批单"),
    ("社保人员登记", "smart_construction_core.action_sc_social_person_registration", "smart_construction_core.menu_scbs55_user_acceptance_090_社保人员登记"),
    ("社保登记", "smart_construction_core.action_sc_social_registration", "smart_construction_core.menu_scbs55_user_acceptance_100_社保登记"),
    ("补助", "smart_construction_core.action_sc_subsidy", "smart_construction_core.menu_scbs55_user_acceptance_120_补助"),
]


def ensure_allowed_db() -> None:
    allowlist = {
        item.strip()
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_demo").split(",")  # noqa: F821
        if item.strip()
    }
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def artifact_root() -> Path:
    candidates = []
    if os.getenv("MIGRATION_ARTIFACT_ROOT"):
        candidates.append(Path(os.environ["MIGRATION_ARTIFACT_ROOT"]))
    candidates.extend([Path("/mnt/artifacts/migration"), Path(f"/tmp/joint_acceptance_batch3/{env.cr.dbname}")])  # noqa: F821
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_test"
            probe.write_text("", encoding="utf-8")
            probe.unlink(missing_ok=True)
            return candidate
        except Exception:
            continue
    return Path(f"/tmp/joint_acceptance_batch3/{env.cr.dbname}")  # noqa: F821


def clean_domain(value: Any) -> list:
    if not value:
        return []
    if isinstance(value, (list, tuple)):
        return list(value)
    return ast.literal_eval(str(value))


def count_for(action) -> int:
    return env[action.res_model].sudo().with_context(active_test=False).search_count(clean_domain(action.domain))  # noqa: F821


def acceptance_action(menu_xmlid: str):
    menu = env.ref(menu_xmlid, raise_if_not_found=False)  # noqa: F821
    if not menu or not menu.action:
        raise RuntimeError({"acceptance_menu_without_action": menu_xmlid})
    return menu.action


ensure_allowed_db()

results = []
for label, formal_action_xmlid, acceptance_menu_xmlid in SPECS:
    formal_action = env.ref(formal_action_xmlid, raise_if_not_found=False)  # noqa: F821
    source_action = acceptance_action(acceptance_menu_xmlid)
    if not formal_action:
        raise RuntimeError({"missing_formal_action": formal_action_xmlid, "label": label})
    before = {
        "res_model": formal_action.res_model,
        "domain": formal_action.domain or "",
        "view_id": formal_action.view_id.id if formal_action.view_id else False,
        "views": formal_action.views,
        "count": count_for(formal_action),
    }
    acceptance = {
        "res_model": source_action.res_model,
        "domain": source_action.domain or "",
        "view_id": source_action.view_id.id if source_action.view_id else False,
        "views": source_action.views,
        "count": count_for(source_action),
    }
    formal_action.write(
        {
            "res_model": source_action.res_model,
            "domain": source_action.domain or False,
            "view_id": source_action.view_id.id if source_action.view_id else False,
            "views": source_action.views,
            "search_view_id": source_action.search_view_id.id if source_action.search_view_id else False,
            "context": source_action.context or "{}",
            "target": source_action.target or "current",
        }
    )
    after = {
        "res_model": formal_action.res_model,
        "domain": formal_action.domain or "",
        "view_id": formal_action.view_id.id if formal_action.view_id else False,
        "views": formal_action.views,
        "count": count_for(formal_action),
    }
    results.append(
        {
            "label": label,
            "formal_action_xmlid": formal_action_xmlid,
            "acceptance_menu_xmlid": acceptance_menu_xmlid,
            "before": before,
            "acceptance": acceptance,
            "after": after,
            "status": "PASS" if after == acceptance else "FAIL",
        }
    )

payload = {
    "mode": "joint_acceptance_batch3_formal_actions_apply",
    "database": env.cr.dbname,  # noqa: F821
    "status": "PASS" if all(row["status"] == "PASS" for row in results) else "FAIL",
    "results": results,
}
out = artifact_root() / "joint_acceptance_batch3_formal_actions_apply_result_v1.json"
out.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
env.cr.commit()  # noqa: F821
print("JOINT_ACCEPTANCE_BATCH3_FORMAL_ACTIONS_APPLY=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
