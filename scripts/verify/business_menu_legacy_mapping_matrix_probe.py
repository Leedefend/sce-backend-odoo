# -*- coding: utf-8 -*-
"""Map target business menus to current model counts and legacy data domains.

Run with:
ENV=test ENV_FILE=.env.prod.sim DB_NAME=sc_prod_sim make odoo.shell.exec < scripts/verify/business_menu_legacy_mapping_matrix_probe.py
"""

from collections import Counter, defaultdict
import json

from odoo.tools.safe_eval import safe_eval


PATH_DOMAIN_RULES = (
    ("material", ("物资", "材料", "采购", "入库", "出库", "库存")),
    ("contract", ("合同", "签证", "结算")),
    ("receipt_income", ("收款", "收入合同")),
    ("payment_execution", ("付款", "支出合同", "应付")),
    ("invoice_registration", ("发票", "开票", "进项", "销项")),
    ("treasury_fund", ("资金", "账户", "保证金", "余额", "划拨", "调拨")),
    ("expense", ("费用", "报销", "备用金", "借款", "还款")),
    ("project", ("项目", "立项", "投标")),
    ("construction_diary", ("施工", "质量", "安全", "日志", "日报", "周报", "月报", "劳务", "机械", "分包")),
    ("workflow", ("待办", "审批")),
    ("attachment_file", ("资料", "归档", "备案", "附件")),
)

MODEL_DOMAIN_RULES = (
    ("attachment_file", ("file", "attachment", "evidence")),
    ("material", ("material", "product", "inventory", "stock")),
    ("construction_diary", ("construction", "diary", "task", "attendance", "labor", "machine", "subcontract")),
    ("receipt_income", ("receipt", "income", "collection", "receivable")),
    ("payment_execution", ("payment", "outflow", "payable")),
    ("invoice_registration", ("invoice", "tax")),
    ("treasury_fund", ("fund", "treasury", "account", "cash")),
    ("contract", ("contract", "agreement")),
    ("partner", ("partner", "supplier", "customer", "vendor")),
    ("expense", ("expense", "reimbursement", "deposit")),
    ("settlement", ("settlement", "adjustment")),
    ("workflow", ("workflow", "audit", "approval", "todo")),
    ("project", ("project",)),
)


def _domain_from_path(path):
    for domain, hints in PATH_DOMAIN_RULES:
        if any(hint in path for hint in hints):
            return domain
    return "unclassified"


def _domain_from_model(model_name):
    haystack = (model_name or "").lower()
    for domain, hints in MODEL_DOMAIN_RULES:
        if any(hint in haystack for hint in hints):
            return domain
    return "unclassified"


def _safe_count(model_name, domain=None):
    if not model_name or model_name not in env:
        return None
    try:
        return int(env[model_name].sudo().search_count(domain or []))
    except Exception as exc:
        return {"error": "%s: %s" % (type(exc).__name__, str(exc)[:180])}


def _safe_action_domain(menu):
    if not menu or not menu.action or menu.action._name != "ir.actions.act_window":
        return []
    raw = getattr(menu.action, "domain", None)
    if raw in (None, False, ""):
        return []
    try:
        parsed = safe_eval(raw) if isinstance(raw, str) else raw
    except Exception:
        return []
    if isinstance(parsed, tuple):
        parsed = list(parsed)
    return parsed if isinstance(parsed, list) else []


def _has_legacy_signal(model_name):
    if not model_name or model_name not in env:
        return False
    fields = env[model_name]._fields
    return any(
        name in fields
        for name in ("source_origin", "legacy_source_model", "legacy_source_table", "legacy_record_id")
    ) or any(name.startswith("legacy_") or "_legacy_" in name for name in fields)


def _legacy_domain_counts():
    result = defaultdict(int)
    legacy_source_models = defaultdict(list)
    for ir_model in env["ir.model"].sudo().search([], order="model"):
        model_name = ir_model.model
        if not model_name or model_name not in env:
            continue
        fields = env[model_name]._fields
        is_legacy_source = model_name.startswith("sc.legacy.")
        is_legacy_backed = _has_legacy_signal(model_name)
        if not (is_legacy_source or is_legacy_backed):
            continue
        domain = _domain_from_model(model_name)
        count = _safe_count(model_name)
        if isinstance(count, int):
            result[domain] += count
        if count:
            legacy_source_models[domain].append(
                {
                    "model": model_name,
                    "records": count,
                    "class": "legacy_raw_fact" if is_legacy_source else "formal_legacy_backed",
                }
            )
    for domain, rows in legacy_source_models.items():
        rows.sort(key=lambda row: row["records"] if isinstance(row["records"], int) else 0, reverse=True)
    return result, legacy_source_models


def _target_tree():
    return env["sc.business.menu.taxonomy.seed"].target_tree()


def _child_by_name(parent, name):
    return env["ir.ui.menu"].sudo().with_context(
        active_test=False,
        lang="zh_CN",
        **{"ir.ui.menu.full_list": True},
    ).search(
        [("parent_id", "=", parent.id), ("name", "=", name), ("active", "=", True)],
        limit=1,
    )


def _target_leaf_specs(root):
    specs = []
    for top_name, top_children in _target_tree().items():
        top = _child_by_name(root, top_name)
        for child_name, child_value in top_children.items():
            child = _child_by_name(top, child_name) if top else env["ir.ui.menu"].sudo()
            if isinstance(child_value, dict) and "model" not in child_value:
                for leaf_name in child_value:
                    leaf = _child_by_name(child, leaf_name) if child else env["ir.ui.menu"].sudo()
                    specs.append({"path": "%s/%s/%s" % (top_name, child_name, leaf_name), "menu": leaf})
            else:
                specs.append({"path": "%s/%s" % (top_name, child_name), "menu": child})
    return specs


def _action_model(menu):
    if not menu or not menu.action or menu.action._name != "ir.actions.act_window":
        return None
    return getattr(menu.action, "res_model", None)


def main():
    root = env.ref("smart_construction_core.menu_sc_root", raise_if_not_found=False)
    if not root:
        print(json.dumps({"ok": False, "failures": [{"check": "root_missing"}]}, ensure_ascii=False, indent=2))
        return 1
    root = root.sudo().with_context(active_test=False, lang="zh_CN")
    legacy_counts, legacy_sources = _legacy_domain_counts()

    rows = []
    blockers = []
    for spec in _target_leaf_specs(root):
        menu = spec["menu"]
        path = spec["path"]
        model_name = _action_model(menu)
        action_filter_domain = _safe_action_domain(menu)
        action_domain = _domain_from_model(model_name)
        path_domain = _domain_from_path(path)
        business_domain = action_domain if action_domain != "unclassified" else path_domain
        current_count = _safe_count(model_name, action_filter_domain)
        legacy_domain_count = legacy_counts.get(business_domain, 0)
        row = {
            "path": path,
            "menu_id": menu.id if menu else None,
            "action_id": menu.action.id if menu and menu.action else None,
            "model": model_name,
            "action_filter_domain": action_filter_domain,
            "business_domain": business_domain,
            "path_domain": path_domain,
            "action_domain": action_domain,
            "current_model_records": current_count,
            "legacy_domain_records": legacy_domain_count,
            "legacy_source_top": legacy_sources.get(business_domain, [])[:5],
            "legacy_signal_on_model": _has_legacy_signal(model_name),
            "mapping_priority": "none",
        }
        if not menu:
            row["mapping_priority"] = "blocker_menu_missing"
            blockers.append(row)
        elif not model_name:
            row["mapping_priority"] = "blocker_action_model_missing"
            blockers.append(row)
        elif legacy_domain_count and current_count == 0:
            row["mapping_priority"] = "high_empty_formal_model_with_legacy_data"
        elif legacy_domain_count and not row["legacy_signal_on_model"]:
            row["mapping_priority"] = "medium_model_without_legacy_traceability"
        elif legacy_domain_count:
            row["mapping_priority"] = "mapped_or_projection_exists"
        rows.append(row)

    priorities = Counter(row["mapping_priority"] for row in rows)
    domains = Counter(row["business_domain"] for row in rows)
    result = {
        "ok": not blockers,
        "database": env.cr.dbname,
        "leaf_count": len(rows),
        "priority_counts": dict(sorted(priorities.items())),
        "domain_counts": dict(sorted(domains.items())),
        "high_priority_rows": [row for row in rows if row["mapping_priority"].startswith("high_")],
        "blockers": blockers,
        "rows": rows,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


main()
