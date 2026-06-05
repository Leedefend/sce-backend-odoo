#!/usr/bin/env python3
"""Point selected formal business menus at accepted joint-project list surfaces."""

from __future__ import annotations

import ast
import json
import os
from pathlib import Path
from typing import Any


SPECS = [
    {
        "label": "投标报名管理",
        "formal_action_xmlid": "smart_construction_core.action_sc_tender_registration",
        "formal_menu_xmlid": "smart_construction_core.menu_sc_tender_registration",
        "acceptance_menu_xmlid": "smart_construction_core.menu_scbs55_user_acceptance_160_投标报名管理",
    },
    {
        "label": "投标报名费申请",
        "formal_action_xmlid": "smart_construction_core.action_sc_tender_registration_fee",
        "formal_menu_xmlid": "smart_construction_core.menu_sc_tender_registration_fee",
        "acceptance_menu_xmlid": "smart_construction_core.menu_scbs55_user_acceptance_170_投标报名费申请",
    },
    {
        "label": "收入",
        "formal_action_xmlid": "smart_construction_core.action_sc_receipt_income_user_income",
        "formal_menu_xmlid": "smart_construction_core.menu_sc_user_income",
        "acceptance_menu_xmlid": "smart_construction_core.menu_scbs55_user_acceptance_250_收入",
    },
    {
        "label": "公司财务支出",
        "formal_action_xmlid": "smart_construction_core.action_sc_payment_execution_company_finance_expense",
        "formal_menu_xmlid": "smart_construction_core.menu_sc_company_finance_expense",
        "acceptance_menu_xmlid": "smart_construction_core.menu_scbs55_user_acceptance_260_公司财务支出",
    },
    {
        "label": "预缴税款",
        "formal_action_xmlid": "smart_construction_core.action_sc_invoice_prepaid_tax_user",
        "formal_menu_xmlid": "smart_construction_core.menu_sc_invoice_prepaid_tax_user",
        "acceptance_menu_xmlid": "smart_construction_core.menu_scbs55_user_acceptance_410_预缴税款",
    },
    {
        "label": "抵扣登记",
        "formal_action_xmlid": "smart_construction_core.action_sc_tax_deduction_registration_user",
        "formal_menu_xmlid": "smart_construction_core.menu_sc_tax_deduction_registration_user",
        "acceptance_menu_xmlid": "smart_construction_core.menu_scbs55_user_acceptance_430_抵扣登记",
    },
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
    candidates.extend([Path("/mnt/artifacts/migration"), Path(f"/tmp/joint_acceptance_redbox/{env.cr.dbname}")])  # noqa: F821
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_test"
            probe.write_text("", encoding="utf-8")
            probe.unlink(missing_ok=True)
            return candidate
        except Exception:
            continue
    return Path(f"/tmp/joint_acceptance_redbox/{env.cr.dbname}")  # noqa: F821


def clean_domain(domain_text: Any) -> list:
    if not domain_text:
        return []
    if isinstance(domain_text, (list, tuple)):
        return list(domain_text)
    return ast.literal_eval(str(domain_text))


def count_for(action) -> int:
    return env[action.res_model].sudo().with_context(active_test=False).search_count(clean_domain(action.domain))  # noqa: F821


def action_from_menu_xmlid(xmlid: str):
    menu = env.ref(xmlid, raise_if_not_found=False)  # noqa: F821
    if not menu or not menu.action:
        raise RuntimeError({"acceptance_menu_without_action": xmlid})
    return menu.action


ensure_allowed_db()

results = []
for spec in SPECS:
    formal_action = env.ref(spec["formal_action_xmlid"], raise_if_not_found=False)  # noqa: F821
    formal_menu = env.ref(spec["formal_menu_xmlid"], raise_if_not_found=False)  # noqa: F821
    acceptance_action = action_from_menu_xmlid(spec["acceptance_menu_xmlid"])

    if not formal_action:
        raise RuntimeError({"missing_formal_action": spec})
    if formal_action._name != "ir.actions.act_window" or acceptance_action._name != "ir.actions.act_window":
        raise RuntimeError({"unexpected_action_type": spec, "formal_type": formal_action._name, "acceptance_type": acceptance_action._name})

    before = {
        "res_model": formal_action.res_model,
        "domain": formal_action.domain or "",
        "view_id": formal_action.view_id.id if formal_action.view_id else False,
        "views": formal_action.views,
        "count": count_for(formal_action),
    }
    acceptance = {
        "res_model": acceptance_action.res_model,
        "domain": acceptance_action.domain or "",
        "view_id": acceptance_action.view_id.id if acceptance_action.view_id else False,
        "views": acceptance_action.views,
        "count": count_for(acceptance_action),
    }

    formal_action.write(
        {
            "res_model": acceptance_action.res_model,
            "domain": acceptance_action.domain or False,
            "view_id": acceptance_action.view_id.id if acceptance_action.view_id else False,
            "views": acceptance_action.views,
            "search_view_id": acceptance_action.search_view_id.id if acceptance_action.search_view_id else False,
            "context": acceptance_action.context or "{}",
            "target": acceptance_action.target or "current",
        }
    )
    if formal_menu:
        formal_menu.write({"action": f"ir.actions.act_window,{formal_action.id}", "active": True})

    after = {
        "res_model": formal_action.res_model,
        "domain": formal_action.domain or "",
        "view_id": formal_action.view_id.id if formal_action.view_id else False,
        "views": formal_action.views,
        "count": count_for(formal_action),
    }
    results.append(
        {
            "label": spec["label"],
            "formal_action_xmlid": spec["formal_action_xmlid"],
            "formal_menu_xmlid": spec["formal_menu_xmlid"],
            "acceptance_menu_xmlid": spec["acceptance_menu_xmlid"],
            "before": before,
            "acceptance": acceptance,
            "after": after,
            "status": "PASS" if after == acceptance else "FAIL",
        }
    )

payload = {
    "mode": "joint_acceptance_redbox_formal_actions_apply",
    "database": env.cr.dbname,  # noqa: F821
    "status": "PASS" if all(row["status"] == "PASS" for row in results) else "FAIL",
    "results": results,
}
out = artifact_root() / "joint_acceptance_redbox_formal_actions_apply_result_v1.json"
out.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
env.cr.commit()  # noqa: F821
print("JOINT_ACCEPTANCE_REDBOX_FORMAL_ACTIONS_APPLY=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
