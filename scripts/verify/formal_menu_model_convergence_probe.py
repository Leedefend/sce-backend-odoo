# -*- coding: utf-8 -*-
"""Probe target menu leaves that should not expose legacy carrier models."""

import json

from odoo.tools.safe_eval import safe_eval


LEGACY_FORBIDDEN_PUBLIC_PATHS = {
    "智慧大屏/资金驾驶舱": "sc.dashboard.cockpit.fact",
    "智慧大屏/成本驾驶舱": "sc.dashboard.cockpit.fact",
    "工作台/我的待办": "sc.workbench.item",
    "工作台/我的审批": "sc.workbench.item",
    "财务中心/资金账户/账户管理": "sc.fund.account",
    "财务中心/资金账户/资金日报表": "sc.fund.operation",
    "物资与分包/物资管理/材料价格库": "sc.material.catalog",
    "基础设置/材料档案": "sc.material.catalog",
}


def _target_tree():
    return env["sc.business.menu.taxonomy.seed"].target_tree()  # noqa: F821


def _child_by_name(parent, name):
    return env["ir.ui.menu"].sudo().with_context(  # noqa: F821
        active_test=False,
        lang="zh_CN",
        **{"ir.ui.menu.full_list": True},
    ).search(
        [("parent_id", "=", parent.id), ("name", "=", name), ("active", "=", True)],
        limit=1,
    )


def _model_count(model_name):
    if not model_name or model_name not in env:  # noqa: F821
        return None
    return env[model_name].sudo().search_count([])  # noqa: F821


def _action_domain_count(action, model_name):
    if not action or not model_name or model_name not in env:  # noqa: F821
        return None
    domain = []
    raw_domain = getattr(action, "domain", None)
    if raw_domain:
        try:
            domain = safe_eval(raw_domain) if isinstance(raw_domain, str) else raw_domain
        except Exception:
            domain = []
    if not isinstance(domain, (list, tuple)):
        domain = []
    try:
        return env[model_name].sudo().search_count(list(domain))  # noqa: F821
    except Exception:
        return None


def main():
    root = env.ref("smart_construction_core.menu_sc_root", raise_if_not_found=False)  # noqa: F821
    failures = []
    rows = []
    if not root:
        print(json.dumps({"ok": False, "failures": [{"check": "root_missing"}]}, ensure_ascii=False, indent=2))
        return 1
    root = root.sudo().with_context(active_test=False, lang="zh_CN")
    for top_name, top_children in _target_tree().items():
        top = _child_by_name(root, top_name)
        for child_name, child_value in top_children.items():
            child = _child_by_name(top, child_name) if top else env["ir.ui.menu"].sudo()  # noqa: F821
            leaf_names = child_value.keys() if isinstance(child_value, dict) and "model" not in child_value else [None]
            for leaf_name in leaf_names:
                if leaf_name:
                    path = "%s/%s/%s" % (top_name, child_name, leaf_name)
                    menu = _child_by_name(child, leaf_name) if child else env["ir.ui.menu"].sudo()  # noqa: F821
                else:
                    path = "%s/%s" % (top_name, child_name)
                    menu = child
                if path not in LEGACY_FORBIDDEN_PUBLIC_PATHS:
                    continue
                action = menu.action if menu else None
                model = getattr(action, "res_model", None) if action and action._name == "ir.actions.act_window" else None
                expected = LEGACY_FORBIDDEN_PUBLIC_PATHS[path]
                row = {
                    "path": path,
                    "menu_id": menu.id if menu else None,
                    "action_id": action.id if action else None,
                    "model": model,
                    "expected_model": expected,
                    "record_count": _action_domain_count(action, model),
                    "model_record_count": _model_count(model),
                    "ok": model == expected,
                }
                rows.append(row)
                if not row["ok"]:
                    failures.append(row)
    result = {
        "ok": not failures,
        "checked": len(rows),
        "rows": rows,
        "failures": failures,
        "counts": {
            "workbench_item": _model_count("sc.workbench.item"),
            "history_todo": _model_count("sc.history.todo"),
            "fund_account": _model_count("sc.fund.account"),
            "legacy_account_master": _model_count("sc.legacy.account.master"),
            "fund_daily_summary": _model_count("sc.fund.daily.summary"),
            "legacy_fund_daily_snapshot": _model_count("sc.legacy.fund.daily.snapshot.fact"),
            "product_template": _model_count("product.template"),
            "dashboard_cockpit_fact": _model_count("sc.dashboard.cockpit.fact"),
        },
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


main()
