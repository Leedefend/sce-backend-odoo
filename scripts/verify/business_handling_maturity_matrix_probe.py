# -*- coding: utf-8 -*-
"""Classify target menus by real business handling maturity.

This is a read-only planning probe.  It separates:
- real business models that already carry domain fields and state/actions;
- formal business fact models that carry domain fields, fact semantics, and state actions;
- readonly analysis/reference surfaces;
- business data models that still need action/review proof.

Run with:
ENV=test ENV_FILE=.env.prod.sim DB_NAME=sc_prod_sim make odoo.shell.exec < scripts/verify/business_handling_maturity_matrix_probe.py
"""

from collections import Counter
import json

from odoo.tools.safe_eval import safe_eval


READONLY_ANALYSIS_MODELS = {
    "sc.fund.daily.summary",
    "sc.account.income.expense.summary",
    "sc.ar.ap.project.summary",
    "sc.ar.ap.company.summary",
    "sc.operating.metrics.project",
    "sc.treasury.ledger",
    "payment.ledger",
    "project.profit.compare",
}

SUPPORT_OR_MASTER_DATA_MODELS = {
    "hr.department",
    "project.cost.code",
    "res.partner",
    "sc.fund.account",
}

FORMAL_BUSINESS_FACT_MODELS = {
    "sc.dashboard.cockpit.fact",
    "sc.workbench.item",
    "sc.project.budget.fact",
    "sc.project.document.fact",
    "sc.material.document",
    "sc.labor.document",
    "sc.equipment.document",
    "sc.subcontract.document",
    "sc.construction.inspection",
    "sc.construction.report",
    "sc.finance.expense.document",
    "sc.fund.operation",
    "sc.analysis.report.fact",
}

HIGH_VALUE_BUSINESS_PATH_HINTS = (
    "合同中心",
    "财务中心",
    "物资与分包",
    "施工管理",
    "成本中心",
    "项目中心/项目预算",
)

PAUSED_BY_CURRENT_DECISION = ("物资与分包/物资管理/材料价格库", "基础设置/材料档案")

STATE_FIELD_NAMES = ("state", "lifecycle_state", "document_state", "validation_status")
BUSINESS_ACTION_HINTS = (
    "submit",
    "approve",
    "confirm",
    "done",
    "cancel",
    "reset",
    "reject",
    "revert",
    "mark",
    "to_",
    "set_state",
    "set_lifecycle",
    "set_active",
    "archive",
    "close",
    "lock",
    "unlock",
)
NON_TRANSITION_ACTION_PREFIXES = (
    "action_open",
    "action_view",
    "action_generate",
    "action_sc_stage_sync",
)


def _safe_count(model_name, domain=None):
    if not model_name or model_name not in env:
        return None
    try:
        return int(env[model_name].sudo().with_context(active_test=False).search_count(domain or []))
    except Exception as exc:
        return {"error": "%s: %s" % (type(exc).__name__, str(exc)[:180])}


def _safe_eval(raw, default):
    if raw in (None, False, ""):
        return default
    try:
        value = safe_eval(raw) if isinstance(raw, str) else raw
    except Exception:
        return default
    if isinstance(value, tuple):
        value = list(value)
    return value if isinstance(value, type(default)) else default


def _action_domain(action):
    return _safe_eval(getattr(action, "domain", None), [])


def _action_context(action):
    return _safe_eval(getattr(action, "context", None), {})


def _target_tree():
    return env["sc.business.menu.taxonomy.seed"].sudo().target_tree()


def _child_by_name(parent, name):
    return env["ir.ui.menu"].sudo().with_context(
        active_test=False,
        lang="zh_CN",
        **{"ir.ui.menu.full_list": True},
    ).search(
        [("parent_id", "=", parent.id), ("name", "=", name), ("active", "=", True)],
        limit=1,
    )


def _target_leaves():
    root = env.ref("smart_construction_core.menu_sc_root", raise_if_not_found=False)
    if not root:
        return []
    leaves = []
    for top_name, top_children in _target_tree().items():
        top = _child_by_name(root, top_name)
        for child_name, child_value in top_children.items():
            child = _child_by_name(top, child_name) if top else env["ir.ui.menu"].sudo()
            if isinstance(child_value, dict) and "model" not in child_value:
                for leaf_name in child_value:
                    leaf = _child_by_name(child, leaf_name) if child else env["ir.ui.menu"].sudo()
                    leaves.append(("%s/%s/%s" % (top_name, child_name, leaf_name), leaf))
            else:
                leaves.append(("%s/%s" % (top_name, child_name), child))
    return leaves


def _business_specific_fields(model_name):
    if model_name not in env:
        return []
    model = env[model_name]
    if not hasattr(model, "_business_specific_fields"):
        return []
    try:
        return [name for name in model._business_specific_fields() if name in model._fields]
    except Exception:
        return []


def _selection_fact_types(model_name):
    if model_name not in env:
        return []
    model = env[model_name]
    if not hasattr(model, "_selection_fact_type"):
        return []
    try:
        return [{"value": value, "label": label} for value, label in model._selection_fact_type()]
    except Exception:
        return []


def _header_action_names(model_name):
    if model_name not in env:
        return []
    actions = []
    model = env[model_name]
    for name in dir(model):
        if not name.startswith("action_"):
            continue
        if name.startswith(NON_TRANSITION_ACTION_PREFIXES):
            continue
        if any(hint in name for hint in BUSINESS_ACTION_HINTS):
            actions.append(name)
    return actions


def _model_signal(model_name):
    if model_name not in env:
        return {}
    fields = env[model_name]._fields
    return {
        "has_state": any(name in fields for name in STATE_FIELD_NAMES),
        "state_fields": [name for name in STATE_FIELD_NAMES if name in fields],
        "has_project": "project_id" in fields,
        "has_partner": "partner_id" in fields,
        "has_amount": any(name in fields for name in ("amount", "amount_total", "paid_amount", "planned_amount")),
        "has_legacy_trace": any(
            name in fields
            for name in ("source_origin", "legacy_source_model", "legacy_source_table", "legacy_record_id")
        )
        or any(name.startswith("legacy_") for name in fields),
    }


def _maturity(path, model_name, record_count, domain, context):
    if not model_name:
        return "missing_action_model"
    if model_name in READONLY_ANALYSIS_MODELS:
        return "readonly_analysis_or_reference"
    if path in PAUSED_BY_CURRENT_DECISION:
        return "paused_material_data_scope"
    if model_name in SUPPORT_OR_MASTER_DATA_MODELS:
        return "support_or_master_data_model"
    if model_name in FORMAL_BUSINESS_FACT_MODELS:
        has_fact_type_default = bool(context.get("default_fact_type"))
        if _business_specific_fields(model_name) and _header_action_names(model_name) and has_fact_type_default:
            return "formal_business_fact_model_ready_for_flow_proof"
        return "formal_business_fact_model_contract_gap"
    signal = _model_signal(model_name)
    if signal.get("has_state") and _header_action_names(model_name):
        return "real_business_handling_model"
    if signal.get("has_project") or signal.get("has_partner") or signal.get("has_amount"):
        return "business_data_entry_model_ready_for_write_proof"
    return "support_or_master_data_model"


def _priority(path, maturity):
    if maturity in ("missing_action_model",):
        return "P0"
    if maturity == "formal_business_fact_model_contract_gap" and any(hint in path for hint in HIGH_VALUE_BUSINESS_PATH_HINTS):
        return "P1"
    if maturity == "formal_business_fact_model_ready_for_flow_proof" and any(
        hint in path for hint in HIGH_VALUE_BUSINESS_PATH_HINTS
    ):
        return "P1_FLOW_PROOF"
    if maturity == "business_data_entry_model_ready_for_write_proof":
        return "P1_WRITE_PROOF"
    if maturity == "paused_material_data_scope":
        return "PAUSED"
    return "P2"


def main():
    rows = []
    for path, menu in _target_leaves():
        action = menu.action if menu and menu.action and menu.action._name == "ir.actions.act_window" else None
        model_name = getattr(action, "res_model", None) if action else None
        domain = _action_domain(action) if action else []
        context = _action_context(action) if action else {}
        record_count = _safe_count(model_name, domain)
        maturity = _maturity(path, model_name, record_count, domain, context)
        row = {
            "path": path,
            "menu_id": menu.id if menu else None,
            "action_id": action.id if action else None,
            "model": model_name,
            "record_count": record_count,
            "action_domain": domain,
            "action_context_defaults": sorted(key for key in context if str(key).startswith("default_")),
            "maturity": maturity,
            "priority": _priority(path, maturity),
            "model_signal": _model_signal(model_name) if model_name else {},
            "business_specific_fields": _business_specific_fields(model_name) if model_name else [],
            "fact_types": _selection_fact_types(model_name) if model_name in FORMAL_BUSINESS_FACT_MODELS else [],
            "header_action_names": _header_action_names(model_name) if model_name else [],
        }
        rows.append(row)

    maturity_counts = Counter(row["maturity"] for row in rows)
    priority_counts = Counter(row["priority"] for row in rows)
    focus_rows = [
        row
        for row in rows
        if row["priority"] in ("P0", "P1", "P1_FLOW_PROOF", "P1_WRITE_PROOF")
    ]
    result = {
        "ok": True,
        "database": env.cr.dbname,
        "checked": len(rows),
        "maturity_counts": dict(sorted(maturity_counts.items())),
        "priority_counts": dict(sorted(priority_counts.items())),
        "focus_count": len(focus_rows),
        "focus_rows": focus_rows,
        "rows": rows,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


main()
