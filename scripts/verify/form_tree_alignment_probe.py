# -*- coding: utf-8 -*-
"""Audit target menu list fields that must be reachable from the form view.

The probe uses Odoo's resolved runtime views so inherited native forms are
audited against the same structure that ui.contract and users receive.
"""

import json

from lxml import etree


def _fields_from_arch(arch):
    root = etree.fromstring((arch or "").encode("utf-8"))
    return [node.get("name") for node in root.xpath(".//field[@name]") if node.get("name")]


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
    tree = env["sc.business.menu.taxonomy.seed"].target_tree()  # noqa: F821
    leaves = []
    for top_name, top_children in tree.items():
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


def _resolved_view(model, view_type):
    if model not in env:  # noqa: F821
        return None
    return env[model].sudo().with_context(lang="zh_CN").get_view(view_type=view_type)  # noqa: F821


def main():
    rows = []
    failures = []
    for path, menu in _target_leaves():
        action = menu.action if menu else None
        if not action or action._name != "ir.actions.act_window":
            continue
        model = action.res_model
        tree_view = _resolved_view(model, "tree")
        form_view = _resolved_view(model, "form")
        tree_fields = _fields_from_arch(tree_view.get("arch")) if tree_view else []
        form_fields = _fields_from_arch(form_view.get("arch")) if form_view else []
        missing = [field for field in tree_fields if field not in form_fields]
        row = {
            "path": path,
            "menu_id": menu.id,
            "action_id": action.id,
            "model": model,
            "tree_view_id": tree_view.get("id") if tree_view else None,
            "form_view_id": form_view.get("id") if form_view else None,
            "tree_fields": tree_fields,
            "form_fields": form_fields,
            "tree_missing_from_form": missing,
            "ok": not missing,
        }
        rows.append(row)
        if missing:
            failures.append(row)
    result = {
        "ok": not failures,
        "database": env.cr.dbname,  # noqa: F821
        "checked": len(rows),
        "failure_count": len(failures),
        "failures": failures,
        "rows": rows,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


main()
