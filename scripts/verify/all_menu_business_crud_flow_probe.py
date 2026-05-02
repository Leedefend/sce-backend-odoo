# -*- coding: utf-8 -*-
"""Actual CRUD probe for target business menus.

This probe creates, writes, and reads one record per writable target menu using
the menu action context/domain as the semantic source.  It rolls back at the end.

Run with:
ENV=test ENV_FILE=.env.prod.sim DB_NAME=sc_prod_sim make odoo.shell.exec < scripts/verify/all_menu_business_crud_flow_probe.py
"""

import json
from datetime import date, datetime

from odoo.tools.safe_eval import safe_eval


READ_ONLY_MODELS = {
    "sc.fund.daily.summary",
    "sc.account.income.expense.summary",
    "sc.ar.ap.project.summary",
    "sc.ar.ap.company.summary",
    "sc.operating.metrics.project",
    "sc.treasury.ledger",
    "payment.ledger",
    "project.profit.compare",
}

SKIP_CREATE_MODELS = READ_ONLY_MODELS | {
    "ir.ui.menu",
}

MODEL_REQUIRED_VALS = {
    "project.project": {"name": "全菜单CRUD验收项目"},
    "tender.bid": {"tender_name": "全菜单CRUD验收投标", "bid_amount": 100},
    "project.boq.line": {"code": "CRUD-BOQ", "name": "全菜单CRUD验收清单", "quantity": 1, "price": 1},
    "project.budget": {"name": "全菜单CRUD验收目标成本", "amount_cost_target": 1, "amount_revenue_target": 2},
    "project.budget.cost.alloc": {"ratio": 1, "amount_budget": 1, "note": "全菜单CRUD验收"},
    "project.cost.ledger": {"date": "2026-05-02", "amount": 1, "note": "全菜单CRUD验收"},
    "project.material.plan": {},
    "purchase.order": {},
    "project.progress.entry": {"date": "2026-05-02", "progress_percent": 1},
    "construction.contract": {"name": "全菜单CRUD验收合同", "amount_total": 1},
    "sc.settlement.adjustment": {"name": "全菜单CRUD验收签证", "amount": 1},
    "sc.settlement.order": {"name": "全菜单CRUD验收结算", "invoice_amount": 1},
    "sc.receipt.income": {"name": "全菜单CRUD验收收款", "amount": 1},
    "payment.request": {"name": "全菜单CRUD验收付款申请", "amount": 1},
    "sc.payment.execution": {"name": "全菜单CRUD验收付款登记", "invoice_amount": 1},
    "sc.invoice.registration": {"name": "全菜单CRUD验收发票", "amount_total": 1},
    "project.funding.baseline": {"total_amount": 1},
    "sc.expense.claim": {"name": "全菜单CRUD验收费用", "amount": 1},
    "sc.fund.account": {"name": "全菜单CRUD验收账户", "account_no": "CRUD-ACCOUNT"},
    "sc.treasury.reconciliation": {"name": "全菜单CRUD验收资金对账"},
    "sc.financing.loan": {"name": "全菜单CRUD验收融资借款", "amount": 1},
    "sc.general.contract": {"name": "全菜单CRUD验收一般合同", "amount_total": 1},
    "res.partner": {"name": "全菜单CRUD验收往来单位"},
    "hr.department": {"name": "全菜单CRUD验收内部单位"},
    "product.template": {"name": "全菜单CRUD验收材料档案"},
    "sc.material.catalog": {"name": "全菜单CRUD验收材料档案", "code": "CRUD-MAT-CATALOG"},
    "project.cost.code": {"name": "全菜单CRUD验收预算类型", "code": "CRUD-COST", "type": "other"},
    "sc.dictionary": {"name": "全菜单CRUD验收字典", "code": "crud_probe"},
    "sc.approval.policy": {"name": "全菜单CRUD验收审批配置"},
}


def _target_tree():
    return env["sc.business.menu.taxonomy.seed"].sudo().target_tree()  # noqa: F821


def _child_by_name(parent, name):
    return env["ir.ui.menu"].sudo().with_context(  # noqa: F821
        active_test=False,
        lang="zh_CN",
        **{"ir.ui.menu.full_list": True},
    ).search(
        [("parent_id", "=", parent.id), ("name", "=", name), ("active", "=", True)],
        limit=1,
    )


def _target_leaves():
    root = env.ref("smart_construction_core.menu_sc_root", raise_if_not_found=False)  # noqa: F821
    if not root:
        return []
    leaves = []
    for top_name, top_children in _target_tree().items():
        top = _child_by_name(root, top_name)
        for child_name, child_value in top_children.items():
            child = _child_by_name(top, child_name) if top else env["ir.ui.menu"].sudo()  # noqa: F821
            if isinstance(child_value, dict) and "model" not in child_value:
                for leaf_name in child_value:
                    leaf = _child_by_name(child, leaf_name) if child else env["ir.ui.menu"].sudo()  # noqa: F821
                    leaves.append(("%s/%s/%s" % (top_name, child_name, leaf_name), leaf))
            else:
                leaves.append(("%s/%s" % (top_name, child_name), child))
    return leaves


def _safe_eval_or(raw, default):
    if raw in (None, False, ""):
        return default
    try:
        value = safe_eval(raw) if isinstance(raw, str) else raw
    except Exception:
        return default
    return value if isinstance(value, type(default)) else default


def _action_domain(action):
    domain = _safe_eval_or(getattr(action, "domain", None), [])
    return list(domain) if isinstance(domain, (list, tuple)) else []


def _action_context(action):
    context = _safe_eval_or(getattr(action, "context", None), {})
    return dict(context) if isinstance(context, dict) else {}


def _first_id(model_name, domain=None):
    if model_name not in env:  # noqa: F821
        return False
    rec = env[model_name].sudo().search(domain or [], limit=1)  # noqa: F821
    return rec.id if rec else False


def _ensure_budget_boq_line_id():
    existing = _first_id("project.budget.boq.line")
    if existing:
        return existing
    budget = env["project.budget"].sudo().create(  # noqa: F821
        {
            "name": "全菜单CRUD验收预算",
            "project_id": _first_id("project.project"),
            "amount_cost_target": 1,
            "amount_revenue_target": 2,
        }
    )
    line = env["project.budget.boq.line"].sudo().create(  # noqa: F821
        {
            "budget_id": budget.id,
            "name": "全菜单CRUD验收预算清单行",
            "uom_id": _first_id("uom.uom"),
            "qty_bidded": 1,
            "price_bidded": 1,
        }
    )
    return line.id


def _ensure_tender_bid_id():
    existing = _first_id("tender.bid")
    if existing:
        return existing
    rec = env["tender.bid"].sudo().create(  # noqa: F821
        {
            "project_id": _first_id("project.project"),
            "owner_id": _first_id("res.partner"),
            "tender_name": "全菜单CRUD验收投标",
            "bid_amount": 1,
        }
    )
    return rec.id


def _funding_ready_project_id():
    project = env["project.project"].sudo().search(  # noqa: F821
        [("funding_enabled", "=", True), ("code", "!=", False)],
        limit=1,
    )
    return project.id if project else _first_id("project.project")


def _ensure_wbs_id(project_id):
    existing = env["construction.work.breakdown"].sudo().search(  # noqa: F821
        [("project_id", "=", project_id)],
        limit=1,
    )
    if existing:
        return existing.id
    rec = env["construction.work.breakdown"].sudo().create(  # noqa: F821
        {
            "name": "全菜单CRUD验收工程结构",
            "code": "CRUD-WBS",
            "project_id": project_id,
        }
    )
    return rec.id


def _value_for_field(field, model_name, field_name):
    field_type = getattr(field, "type", "")
    if field_type in ("char", "text", "html"):
        return "全菜单CRUD验收"
    if field_type == "date":
        return date(2026, 5, 2).isoformat()
    if field_type == "datetime":
        return datetime(2026, 5, 2, 10, 0, 0).strftime("%Y-%m-%d %H:%M:%S")
    if field_type == "boolean":
        return True
    if field_type == "selection":
        selection = field.selection
        if callable(selection):
            selection = selection(env[model_name])  # noqa: F821
        return selection[0][0] if selection else False
    if field_type in ("float", "monetary"):
        return 1.0
    if field_type == "integer":
        return 1
    if field_type == "many2one":
        return _first_id(field.comodel_name)
    return None


def _defaults_from_action_context(context):
    vals = {}
    for key, value in (context or {}).items():
        if key.startswith("default_") and value not in (None, False, ""):
            vals[key.replace("default_", "", 1)] = value
    return vals


def _domain_defaults(domain):
    vals = {}
    for item in domain or []:
        if isinstance(item, (tuple, list)) and len(item) == 3 and item[1] == "=":
            vals[item[0]] = item[2]
    return vals


def _build_vals(model_name, action):
    model = env[model_name].sudo()  # noqa: F821
    context = _action_context(action)
    vals = {}
    vals.update(_domain_defaults(_action_domain(action)))
    vals.update(_defaults_from_action_context(context))
    vals.update(MODEL_REQUIRED_VALS.get(model_name, {}))
    vals = {key: value for key, value in vals.items() if key in model._fields}

    if "project_id" in model._fields and not vals.get("project_id"):
        vals["project_id"] = _funding_ready_project_id() if model_name == "project.funding.baseline" else _first_id("project.project")
    if "partner_id" in model._fields and not vals.get("partner_id"):
        vals["partner_id"] = _first_id("res.partner")
    if "owner_id" in model._fields and not vals.get("owner_id"):
        vals["owner_id"] = _first_id("res.partner")
    if "customer_id" in model._fields and not vals.get("customer_id"):
        vals["customer_id"] = _first_id("res.partner")
    if "supplier_id" in model._fields and not vals.get("supplier_id"):
        vals["supplier_id"] = _first_id("res.partner")
    if "department_id" in model._fields and not vals.get("department_id"):
        vals["department_id"] = _first_id("hr.department")
    if "handler_id" in model._fields and not vals.get("handler_id"):
        vals["handler_id"] = env.uid  # noqa: F821
    if "requester_id" in model._fields and not vals.get("requester_id"):
        vals["requester_id"] = env.uid  # noqa: F821
    if "uom_id" in model._fields and not vals.get("uom_id"):
        vals["uom_id"] = _first_id("uom.uom")
    if "currency_id" in model._fields and not vals.get("currency_id"):
        vals["currency_id"] = env.company.currency_id.id  # noqa: F821
    if "cost_code_id" in model._fields and not vals.get("cost_code_id"):
        vals["cost_code_id"] = _first_id("project.cost.code")
    if "bid_id" in model._fields and not vals.get("bid_id"):
        vals["bid_id"] = _ensure_tender_bid_id()
    if "budget_id" in model._fields and not vals.get("budget_id"):
        vals["budget_id"] = _first_id("project.budget")
    if "budget_boq_line_id" in model._fields and not vals.get("budget_boq_line_id"):
        vals["budget_boq_line_id"] = _ensure_budget_boq_line_id()
    if "payee_id" in model._fields and not vals.get("payee_id"):
        vals["payee_id"] = _first_id("res.partner")
    if "subcontractor_id" in model._fields and not vals.get("subcontractor_id"):
        vals["subcontractor_id"] = _first_id("res.partner")
    if "responsible_party_id" in model._fields and not vals.get("responsible_party_id"):
        vals["responsible_party_id"] = _first_id("res.partner")
    if "product_id" in model._fields and not vals.get("product_id"):
        vals["product_id"] = _first_id("product.product")
    if "warehouse_id" in model._fields and not vals.get("warehouse_id"):
        vals["warehouse_id"] = _first_id("stock.warehouse")
    if "source_location_id" in model._fields and not vals.get("source_location_id"):
        vals["source_location_id"] = _first_id("stock.location")
    if "dest_location_id" in model._fields and not vals.get("dest_location_id"):
        vals["dest_location_id"] = _first_id("stock.location")
    if "wbs_id" in model._fields and not vals.get("wbs_id"):
        vals["wbs_id"] = _ensure_wbs_id(vals.get("project_id") or _first_id("project.project"))

    required_names = [
        name
        for name, field in model._fields.items()
        if getattr(field, "required", False)
        and not getattr(field, "readonly", False)
        and not getattr(field, "compute", None)
        and name != "state"
        and name not in vals
    ]
    default_vals = model.with_context(**context).default_get(required_names)
    vals.update({name: value for name, value in default_vals.items() if value not in (None, False, "")})
    for name in required_names:
        if vals.get(name) not in (None, False, ""):
            continue
        value = _value_for_field(model._fields[name], model_name, name)
        if value not in (None, False, ""):
            vals[name] = value
    return vals


def _writable_probe_field(model_name, rec):
    preferred = [
        "description",
        "note",
        "remark",
        "summary",
        "name",
        "result_note",
    ]
    forbidden = {"state", "lifecycle_state", "document_state", "validation_status"}
    model = env[model_name]  # noqa: F821
    for name in preferred:
        if name in forbidden:
            continue
        field = model._fields.get(name)
        if not field or getattr(field, "readonly", False) or getattr(field, "compute", None):
            continue
        return name
    for name, field in model._fields.items():
        if name in forbidden:
            continue
        if getattr(field, "type", "") in ("char", "text") and not getattr(field, "readonly", False) and not getattr(field, "compute", None):
            return name
    return None


def _probe_menu(path, menu):
    row = {
        "path": path,
        "menu_id": menu.id if menu else None,
        "action_id": None,
        "model": "",
        "status": "fail",
        "checks": {},
        "error": "",
    }
    action = menu.action if menu else None
    if not action or action._name != "ir.actions.act_window":
        row["error"] = "missing_act_window"
        return row
    model_name = action.res_model
    row.update({"action_id": action.id, "model": model_name})
    if model_name in SKIP_CREATE_MODELS:
        row["status"] = "not_applicable_readonly"
        return row
    if model_name not in env:  # noqa: F821
        row["error"] = "model_missing"
        return row
    model = env[model_name].sudo().with_context(**_action_context(action))  # noqa: F821
    if not model.check_access_rights("create", raise_exception=False):
        row["status"] = "not_applicable_no_create_right"
        return row
    try:
        with env.cr.savepoint():  # noqa: F821
            vals = _build_vals(model_name, action)
            rec = model.create(vals)
            row["checks"]["created_id"] = rec.id
            row["checks"]["create"] = True
            write_field = _writable_probe_field(model_name, rec)
            if write_field:
                rec.write({write_field: "%s / 已编辑" % (rec[write_field] or "全菜单CRUD验收")})
                row["checks"]["write_field"] = write_field
                row["checks"]["write"] = True
            else:
                row["checks"]["write"] = "no_simple_writable_text_field"
            read_fields = ["id"]
            if write_field:
                read_fields.append(write_field)
            rec.read(read_fields)
            row["checks"]["read"] = True
            row["status"] = "pass"
    except Exception as exc:
        row["error"] = "%s: %s" % (type(exc).__name__, str(exc)[:300])
    return row


def main():
    rows = []
    failures = []
    try:
        for path, menu in _target_leaves():
            row = _probe_menu(path, menu)
            rows.append(row)
            if row["status"] == "fail":
                failures.append(row)
    finally:
        env.cr.rollback()  # noqa: F821

    result = {
        "ok": not failures,
        "database": env.cr.dbname,  # noqa: F821
        "rollback": True,
        "checked": len(rows),
        "pass_count": sum(1 for row in rows if row["status"] == "pass"),
        "not_applicable_count": sum(1 for row in rows if row["status"].startswith("not_applicable")),
        "failure_count": len(failures),
        "failures": failures,
        "rows": rows,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True, default=str))
    return 0 if not failures else 1


raise SystemExit(main())
