# -*- coding: utf-8 -*-
"""All target-menu operability matrix.

This probe is intentionally non-destructive.  It checks every target menu leaf
against the business-usable matrix that must precede write-path acceptance:

- read: action domain can be counted, and an existing record can be read when present.
- create: create-mode ui.contract is renderable for createable models, and required
  / business-specific fields are visible from the contract.
- edit/action: record-mode ui.contract is renderable when records exist, and native
  header actions are present only as record-mode actions.

Run with:
ENV=test ... DB_NAME=sc_prod_sim make odoo.shell.exec < scripts/verify/all_menu_business_operability_matrix_probe.py
"""

import json

from odoo import api, SUPERUSER_ID
from odoo.tools.safe_eval import safe_eval

from odoo.addons.smart_core.core.intent_execution_result import adapt_handler_result
from odoo.addons.smart_core.handlers.ui_contract import UiContractHandler


READ_ONLY_MODELS = {
    "sc.fund.daily.summary",
    "sc.account.income.expense.summary",
    "sc.ar.ap.project.summary",
    "sc.ar.ap.company.summary",
    "sc.operating.metrics.project",
}

BUSINESS_FACT_BASE_MODELS = {
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
    if not raw:
        return default
    try:
        return safe_eval(raw) if isinstance(raw, str) else raw
    except Exception:
        return default


def _action_domain(action):
    domain = _safe_eval_or(getattr(action, "domain", None), [])
    return list(domain) if isinstance(domain, (list, tuple)) else []


def _action_context(action):
    context = _safe_eval_or(getattr(action, "context", None), {})
    return dict(context) if isinstance(context, dict) else {}


def _contract_for(action_id, render_profile, record_id=None, runtime_env=None):
    runtime_env = runtime_env or env  # noqa: F821
    runtime_ctx = dict(runtime_env.context or {})
    runtime_ctx["lang"] = "zh_CN"
    runtime_env = api.Environment(runtime_env.cr, runtime_env.uid, runtime_ctx)
    handler = UiContractHandler(
        runtime_env,
        su_env=api.Environment(runtime_env.cr, SUPERUSER_ID, runtime_ctx),
        request=None,
    )
    params = {
        "op": "action_open",
        "action_id": int(action_id),
        "render_profile": render_profile,
        "contract_surface": "user",
        "source_mode": "backend_internal",
    }
    if record_id:
        params["record_id"] = int(record_id)
    return adapt_handler_result(handler.handle(payload={"params": params}))


def _collect_layout_field_names(layout):
    names = []

    def walk(node):
        if isinstance(node, list):
            for item in node:
                walk(item)
            return
        if not isinstance(node, dict):
            return
        if str(node.get("type") or "").lower() == "field" and node.get("name"):
            name = str(node.get("name") or "").strip()
            if name and name not in names:
                names.append(name)
        for key in ("children", "tabs", "pages", "nodes", "items", "fields"):
            value = node.get(key)
            if isinstance(value, list):
                walk(value)

    walk(layout)
    return names


def _group_fields(contract, group_name):
    for item in contract.get("field_groups") or []:
        if isinstance(item, dict) and str(item.get("name") or "").strip() == group_name:
            return [str(name or "").strip() for name in item.get("fields") or [] if str(name or "").strip()]
    return []


def _contract_visible_fields(contract):
    fields = set(_collect_layout_field_names(((contract.get("views") or {}).get("form") or {}).get("layout")))
    fields.update(_group_fields(contract, "core"))
    fields.update(_group_fields(contract, "advanced"))
    fields.update(str(name or "").strip() for name in contract.get("visible_fields") or [] if str(name or "").strip())
    fields.update((contract.get("fields") or {}).keys())
    return fields


def _required_input_fields(model_name):
    model = env[model_name]  # noqa: F821
    fields = []
    for name, field in model._fields.items():
        if name == "id":
            continue
        if not getattr(field, "required", False):
            continue
        if getattr(field, "readonly", False) or getattr(field, "compute", None):
            continue
        fields.append(name)
    return fields


def _business_specific_fields(model_name):
    model = env[model_name]  # noqa: F821
    if hasattr(model, "_business_specific_fields"):
        try:
            return [name for name in model._business_specific_fields() if name in model._fields]
        except Exception:
            return []
    return []


def _defaulted_fields(action_context):
    out = set()
    for key, value in (action_context or {}).items():
        if key.startswith("default_") and value not in (None, False, ""):
            out.add(key.replace("default_", "", 1))
    return out


def _safe_read_first(model_name, domain, fields):
    model = env[model_name].sudo().with_context(active_test=True, lang="zh_CN")  # noqa: F821
    rec = model.search(domain or [], limit=1)
    if not rec:
        return None, None
    readable = []
    for name in fields:
        field = model._fields.get(name)
        if not field:
            continue
        if getattr(field, "type", "") in {"binary"}:
            continue
        readable.append(name)
        if len(readable) >= 20:
            break
    if not readable:
        readable = ["id", "display_name"] if "display_name" in model._fields else ["id"]
    return rec.id, rec.read(readable)[0]


def _header_actions(contract):
    actions = []
    for item in (((contract.get("views") or {}).get("form") or {}).get("layout") or []):
        if not isinstance(item, dict) or str(item.get("type") or "").lower() != "header":
            continue
        for child in item.get("children") or []:
            if isinstance(child, dict) and str(child.get("type") or "").lower() == "button":
                actions.append(
                    {
                        "name": child.get("name"),
                        "label": child.get("label") or child.get("string"),
                        "requires_record": ((child.get("action") or {}) or {}).get("requires_record"),
                        "hidden_reason_code": ((child.get("action") or {}) or {}).get("hidden_reason_code"),
                    }
                )
    return actions


def _analyze_leaf(path, menu, runtime_env):
    row = {
        "path": path,
        "menu_id": menu.id if menu else None,
        "action_id": None,
        "model": "",
        "record_count": None,
        "mode": "unknown",
        "read": {"status": "not_checked"},
        "create": {"status": "not_checked"},
        "edit": {"status": "not_checked"},
        "action": {"status": "not_checked"},
        "failures": [],
        "warnings": [],
    }
    action = menu.action if menu else None
    if not action or action._name != "ir.actions.act_window":
        row["failures"].append({"check": "action_missing"})
        return row
    model_name = action.res_model
    row.update({"action_id": action.id, "model": model_name, "view_mode": action.view_mode or ""})
    if not model_name or model_name not in env:  # noqa: F821
        row["failures"].append({"check": "model_missing", "model": model_name})
        return row

    model = runtime_env[model_name]
    domain = _action_domain(action)
    action_context = _action_context(action)
    defaulted = _defaulted_fields(action_context)
    can_create = bool(model.check_access_rights("create", raise_exception=False))
    can_write = bool(model.check_access_rights("write", raise_exception=False))
    row["rights"] = {
        "create": can_create,
        "write": can_write,
        "read": bool(model.check_access_rights("read", raise_exception=False)),
    }
    row["action_domain"] = domain
    row["action_context_defaults"] = sorted(defaulted)
    row["mode"] = "readonly" if model_name in READ_ONLY_MODELS or not can_create else "business_write"

    try:
        row["record_count"] = model.sudo().search_count(domain)
    except Exception as exc:
        row["failures"].append({"check": "domain_count_failed", "error": str(exc)})
        row["record_count"] = None

    try:
        create_contract_result = _contract_for(action.id, "create", runtime_env=runtime_env)
        create_contract = create_contract_result.get("data") or {}
        create_ok = bool(create_contract_result.get("ok")) and bool(create_contract.get("fields"))
        row["create"]["contract_ok"] = create_ok
        row["create"]["core_fields"] = _group_fields(create_contract, "core")
        row["create"]["visible_field_count"] = len(_contract_visible_fields(create_contract))
        row["create"]["header_actions"] = _header_actions(create_contract)
    except Exception as exc:
        create_contract = {}
        row["create"]["contract_ok"] = False
        row["create"]["error"] = str(exc)

    if row["mode"] == "readonly":
        if can_create:
            row["warnings"].append({"check": "readonly_model_has_create_right", "model": model_name})
        row["create"]["status"] = "not_applicable_readonly"
    else:
        if not row["create"].get("contract_ok"):
            row["failures"].append({"check": "create_contract_unavailable", "path": path, "model": model_name})
            row["create"]["status"] = "fail"
        else:
            required = _required_input_fields(model_name)
            visible = _contract_visible_fields(create_contract)
            missing_required = sorted(name for name in required if name not in visible and name not in defaulted)
            business_specific = _business_specific_fields(model_name)
            core = set(row["create"].get("core_fields") or [])
            specific_not_core = sorted(name for name in business_specific if name not in core)
            row["create"].update(
                {
                    "status": "pass" if not missing_required else "fail",
                    "required_input_fields": required,
                    "missing_required_visible_or_defaulted": missing_required,
                    "business_specific_fields": business_specific,
                    "business_specific_not_core": specific_not_core,
                }
            )
            if missing_required:
                row["failures"].append(
                    {
                        "check": "create_required_field_not_visible_or_defaulted",
                        "fields": missing_required,
                        "path": path,
                    }
                )
            if specific_not_core and model_name in BUSINESS_FACT_BASE_MODELS:
                row["warnings"].append(
                    {
                        "check": "business_specific_field_not_core",
                        "fields": specific_not_core,
                        "path": path,
                    }
                )

    read_fields = _collect_layout_field_names(((create_contract.get("views") or {}).get("form") or {}).get("layout"))
    if row["record_count"]:
        try:
            rec_id, sample = _safe_read_first(model_name, domain, read_fields)
            row["read"] = {"status": "pass", "sample_id": rec_id, "sample_keys": sorted((sample or {}).keys())}
        except Exception as exc:
            row["read"] = {"status": "fail", "error": str(exc)}
            row["failures"].append({"check": "read_existing_record_failed", "path": path, "error": str(exc)})
    else:
        row["read"] = {
            "status": "empty_ok_if_createable" if row["mode"] == "business_write" else "empty_readonly_warning",
            "sample_id": None,
        }
        if row["mode"] == "readonly":
            row["warnings"].append({"check": "readonly_menu_empty", "path": path})

    if row["record_count"] and can_write:
        try:
            rec = model.sudo().search(domain, limit=1)
            edit_contract_result = _contract_for(action.id, "edit", record_id=rec.id, runtime_env=runtime_env)
            edit_contract = edit_contract_result.get("data") or {}
            row["edit"] = {
                "status": "pass" if edit_contract_result.get("ok") and edit_contract.get("fields") else "fail",
                "record_id": rec.id,
                "field_count": len(edit_contract.get("fields") or {}),
            }
            row["action"] = {
                "status": "pass",
                "header_actions": _header_actions(edit_contract),
            }
        except Exception as exc:
            row["edit"] = {"status": "fail", "error": str(exc)}
            row["action"] = {"status": "fail", "error": str(exc)}
            row["failures"].append({"check": "edit_contract_failed", "path": path, "error": str(exc)})
    elif row["record_count"]:
        row["edit"] = {"status": "not_applicable_no_write_right"}
        row["action"] = {"status": "not_applicable_no_write_right"}
    else:
        row["edit"] = {"status": "not_applicable_empty"}
        row["action"] = {"status": "not_applicable_empty"}

    create_record_actions = [
        item for item in row["create"].get("header_actions") or [] if item.get("requires_record") is True
    ]
    if create_record_actions:
        hidden_ok = all(item.get("hidden_reason_code") == "CREATE_PROFILE_REQUIRES_RECORD" for item in create_record_actions)
        if not hidden_ok:
            row["failures"].append(
                {
                    "check": "record_action_not_hidden_in_create_profile",
                    "path": path,
                    "actions": create_record_actions,
                }
            )

    return row


def main():
    user = env["res.users"].sudo().search([("login", "=", "wutao")], limit=1)  # noqa: F821
    runtime_uid = user.id if user else env.uid  # noqa: F821
    runtime_env = api.Environment(env.cr, runtime_uid, dict(env.context or {}, lang="zh_CN"))  # noqa: F821
    rows = []
    failures = []
    warnings = []
    for path, menu in _target_leaves():
        row = _analyze_leaf(path, menu, runtime_env)
        rows.append(row)
        failures.extend(row.get("failures") or [])
        warnings.extend(row.get("warnings") or [])
    blocking_failures = [
        item for item in failures
        if item.get("check") not in {"create_required_field_not_visible_or_defaulted"}
    ]
    result = {
        "ok": not blocking_failures,
        "database": env.cr.dbname,  # noqa: F821
        "runtime_user": user.login if user else env.user.login,  # noqa: F821
        "checked": len(rows),
        "summary": {
            "business_write": sum(1 for row in rows if row.get("mode") == "business_write"),
            "readonly": sum(1 for row in rows if row.get("mode") == "readonly"),
            "empty_business_write": sum(
                1 for row in rows
                if row.get("mode") == "business_write" and not row.get("record_count")
            ),
            "empty_readonly": sum(
                1 for row in rows
                if row.get("mode") == "readonly" and not row.get("record_count")
            ),
            "failure_count": len(failures),
            "blocking_failure_count": len(blocking_failures),
            "warning_count": len(warnings),
        },
        "blocking_failures": blocking_failures,
        "failures": failures,
        "warnings": warnings,
        "rows": rows,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True, default=str))
    return 0 if result["ok"] else 1


raise SystemExit(main())
