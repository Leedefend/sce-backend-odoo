# -*- coding: utf-8 -*-
"""Role-based operability matrix for business menu leaves.

Run with:
ENV=test ENV_FILE=.env.prod.sim DB_NAME=sc_prod_sim make odoo.shell.exec < scripts/verify/business_menu_role_operability_matrix_probe.py
"""

from collections import defaultdict
import json


PROBE_USERS = ["wutao", "demo_business_full", "linshizhanghao", "admin"]
ACTION_MODEL = "ir.actions.act_window"


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
                    specs.append(
                        {
                            "path": "%s/%s/%s" % (top_name, child_name, leaf_name),
                            "menu": leaf,
                        }
                    )
            else:
                specs.append(
                    {
                        "path": "%s/%s" % (top_name, child_name),
                        "menu": child,
                    }
                )
    return specs


def _visible_menu_ids(root, user):
    menus = env["ir.ui.menu"].with_user(user).with_context(lang="zh_CN").search(
        [("id", "child_of", root.id), ("active", "=", True)],
        order="parent_id,sequence,id",
    )
    return set(menus.ids)


def _action_view_modes(action):
    return {mode.strip() for mode in (getattr(action, "view_mode", "") or "").split(",") if mode.strip()}


def _model_exists(model_name):
    return bool(model_name and model_name in env)


def _is_business_fact_model(model):
    field_names = set(model._fields)
    return {"document_no", "fact_type", "business_date", "state"}.issubset(field_names) and hasattr(model, "action_submit")


def _view_loads(model, view_type):
    try:
        view = model.get_view(view_id=False, view_type=view_type)
    except Exception as exc:
        return False, "%s: %s" % (type(exc).__name__, str(exc)[:240])
    return bool(view.get("arch")), ""


def _check_visible_leaf(user, path, menu):
    row = {
        "login": user.login,
        "path": path,
        "menu_id": menu.id,
        "visible": True,
        "ok": True,
        "blockers": [],
        "warnings": [],
    }
    if not menu:
        row["ok"] = False
        row["blockers"].append("target_menu_missing")
        return row
    if not menu.action:
        row["ok"] = False
        row["blockers"].append("action_missing")
        return row
    action = menu.action
    row["action"] = "%s,%s" % (action._name, action.id)
    if action._name != ACTION_MODEL:
        row["ok"] = False
        row["blockers"].append("unsupported_action_type:%s" % action._name)
        return row
    model_name = getattr(action, "res_model", "")
    row["model"] = model_name
    if not _model_exists(model_name):
        row["ok"] = False
        row["blockers"].append("model_missing:%s" % model_name)
        return row
    model = env[model_name].with_user(user)
    rights = {
        "read": model.check_access_rights("read", raise_exception=False),
        "create": model.check_access_rights("create", raise_exception=False),
        "write": model.check_access_rights("write", raise_exception=False),
        "unlink": model.check_access_rights("unlink", raise_exception=False),
    }
    row["rights"] = rights
    if not rights["read"]:
        row["ok"] = False
        row["blockers"].append("read_access_denied")

    modes = _action_view_modes(action)
    row["view_mode"] = getattr(action, "view_mode", "")
    if not ({"tree", "list"} & modes):
        row["ok"] = False
        row["blockers"].append("list_view_mode_missing")
    if "form" not in modes:
        row["ok"] = False
        row["blockers"].append("form_view_mode_missing")

    if rights["read"]:
        list_ok, list_error = _view_loads(model, "tree")
        form_ok, form_error = _view_loads(model, "form")
        row["views"] = {"list": list_ok, "form": form_ok}
        if not list_ok:
            row["ok"] = False
            row["blockers"].append("list_view_load_failed:%s" % list_error)
        if not form_ok:
            row["ok"] = False
            row["blockers"].append("form_view_load_failed:%s" % form_error)

    row["business_fact_model"] = _is_business_fact_model(model)
    if row["business_fact_model"] and not rights["create"]:
        row["warnings"].append("business_fact_create_not_allowed_for_role")
    if row["business_fact_model"] and not rights["write"]:
        row["warnings"].append("business_fact_write_not_allowed_for_role")
    return row


def main():
    failures = []
    root = env.ref("smart_construction_core.menu_sc_root", raise_if_not_found=False)
    if not root:
        print(json.dumps({"ok": False, "failures": [{"check": "root_missing"}]}, ensure_ascii=False, indent=2))
        return 1
    root = root.sudo().with_context(active_test=False, lang="zh_CN")
    leaf_specs = _target_leaf_specs(root)

    users = []
    missing_users = []
    for login in PROBE_USERS:
        user = env["res.users"].sudo().search([("login", "=", login), ("active", "=", True)], limit=1)
        if user:
            users.append(user)
        else:
            missing_users.append(login)

    rows = []
    per_role = {}
    warning_rows = []
    by_model = defaultdict(lambda: {"visible_leaves": 0, "roles": set()})
    for user in users:
        visible_ids = _visible_menu_ids(root, user)
        role_rows = []
        for spec in leaf_specs:
            menu = spec["menu"]
            if not menu or menu.id not in visible_ids:
                continue
            row = _check_visible_leaf(user, spec["path"], menu)
            rows.append(row)
            role_rows.append(row)
            if row.get("model"):
                by_model[row["model"]]["visible_leaves"] += 1
                by_model[row["model"]]["roles"].add(user.login)
            if not row["ok"]:
                failures.append(row)
            if row["warnings"]:
                warning_rows.append(row)
        per_role[user.login] = {
            "user": user.name,
            "visible_target_leaves": len(role_rows),
            "pass": sum(1 for row in role_rows if row["ok"]),
            "fail": sum(1 for row in role_rows if not row["ok"]),
            "business_fact_visible": sum(1 for row in role_rows if row.get("business_fact_model")),
            "business_fact_create_warnings": sum(
                1 for row in role_rows if "business_fact_create_not_allowed_for_role" in row["warnings"]
            ),
            "business_fact_write_warnings": sum(
                1 for row in role_rows if "business_fact_write_not_allowed_for_role" in row["warnings"]
            ),
        }

    model_summary = {
        model: {"visible_leaves": value["visible_leaves"], "roles": sorted(value["roles"])}
        for model, value in sorted(by_model.items())
    }
    result = {
        "ok": not failures,
        "root": root.name,
        "target_leaf_count": len(leaf_specs),
        "probe_users": [user.login for user in users],
        "missing_users": missing_users,
        "per_role": per_role,
        "checked_visible_role_leaf_pairs": len(rows),
        "blocking_failure_count": len(failures),
        "warning_count": len(warning_rows),
        "model_summary": model_summary,
        "failures": failures,
        "warnings": warning_rows[:200],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


raise SystemExit(main())
