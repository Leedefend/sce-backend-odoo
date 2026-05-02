# -*- coding: utf-8 -*-
"""Runtime probe for the Smart Construction business menu taxonomy.

Run with:
ENV=test ... DB_NAME=sc_prod_sim make odoo.shell.exec < scripts/verify/business_menu_taxonomy_runtime_probe.py
"""

from collections import defaultdict
import json


EXPECTED_TOP = [
    "智慧大屏",
    "工作台",
    "项目中心",
    "合同中心",
    "物资与分包",
    "施工管理",
    "成本中心",
    "财务中心",
    "统计分析",
    "基础设置",
]

LEGACY_TOP_NAMES = {"业务中心", "配置中心", "数据中心", "项目管理", "合同管理", "财务管理"}
GROUP_REQUIRED_ROOTS = {"项目中心", "合同中心", "财务中心", "统计分析"}
PROBE_USERS = ["demo_business_full", "linshizhanghao", "admin"]


def _external_id(record):
    return record.get_external_id().get(record.id, "")


def _children_by_parent(menus):
    children = defaultdict(list)
    seen = set()
    for menu in menus:
        if menu.id in seen:
            continue
        seen.add(menu.id)
        children[menu.parent_id.id].append(menu)
    return children


def _visible_tree_for_user(root, user):
    menu_model = env["ir.ui.menu"].with_user(user).with_context(lang="zh_CN")
    menus = menu_model.search(
        [("id", "child_of", root.id), ("active", "=", True)],
        order="parent_id,sequence,id",
    )
    return _children_by_parent(menus)


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


def _action_view_modes(action):
    view_mode = getattr(action, "view_mode", "") or ""
    modes = {mode.strip() for mode in view_mode.split(",") if mode.strip()}
    return modes


def _unique_names(records):
    names = []
    seen = set()
    for record in records:
        if record.name in seen:
            continue
        seen.add(record.name)
        names.append(record.name)
    return names


def _menu_path(menu):
    names = []
    current = menu
    while current:
        names.append(current.name)
        current = current.parent_id
    return "/".join(reversed(names))


def _target_menu_paths(root):
    paths = {root.name}
    for top_name, top_children in _target_tree().items():
        top_path = "%s/%s" % (root.name, top_name)
        paths.add(top_path)
        for child_name, child_value in top_children.items():
            child_path = "%s/%s" % (top_path, child_name)
            paths.add(child_path)
            if isinstance(child_value, dict) and "model" not in child_value:
                for leaf_name in child_value:
                    paths.add("%s/%s" % (child_path, leaf_name))
    return paths


def _active_menu_subtree(root):
    collected = env["ir.ui.menu"].sudo()

    def walk(menu):
        nonlocal collected
        children = env["ir.ui.menu"].sudo().with_context(
            active_test=False,
            lang="zh_CN",
            **{"ir.ui.menu.full_list": True},
        ).search(
            [("parent_id", "=", menu.id), ("active", "=", True)],
            order="sequence,id",
        )
        for child in children:
            collected |= child
            walk(child)

    root = root.sudo().with_context(active_test=False, lang="zh_CN")
    if root.active:
        collected |= root
    walk(root)
    return collected


def _check_leaf_action(failures, path, menu, action_stats):
    if not menu.action:
        failures.append({"check": "target_leaf_action_missing", "path": path, "menu_id": menu.id})
        return
    action = menu.action
    res_model = getattr(action, "res_model", "")
    if res_model == "sc.business.menu.carrier":
        failures.append({"check": "legacy_carrier_action", "path": path, "action": "%s,%s" % (action._name, action.id)})
    if res_model.startswith("sc.") and res_model not in {
        "sc.business.menu.carrier",
        "sc.operating.metrics.project",
        "sc.settlement.order",
        "sc.settlement.adjustment",
        "sc.invoice.registration",
        "sc.expense.claim",
        "sc.fund.daily.summary",
        "sc.fund.daily.line",
        "sc.treasury.ledger",
        "sc.account.income.expense.summary",
        "sc.ar.ap.project.summary",
        "sc.ar.ap.company.summary",
    }:
        action_stats["formal_model_leaves"] += 1
        action_stats["formal_model_paths"].append({"path": path, "model": res_model})
    else:
        action_stats["direct_action_leaves"] += 1
    modes = _action_view_modes(action)
    has_list = bool({"tree", "list"} & modes)
    has_form = "form" in modes
    if not has_list or not has_form:
        failures.append(
            {
                "check": "target_leaf_view_mode",
                "path": path,
                "action": "%s,%s" % (action._name, action.id),
                "view_mode": getattr(action, "view_mode", ""),
                "expected": "tree/list + form",
            }
        )


def _check_target_tree(failures, root):
    checked_leaves = 0
    action_stats = {"direct_action_leaves": 0, "formal_model_leaves": 0, "formal_model_paths": []}
    for top_name, top_children in _target_tree().items():
        top = _child_by_name(root, top_name)
        if not top:
            failures.append({"check": "target_top_missing", "path": top_name})
            continue
        for child_name, child_value in top_children.items():
            child = _child_by_name(top, child_name)
            if not child:
                failures.append({"check": "target_menu_missing", "path": "%s/%s" % (top_name, child_name)})
                continue
            if isinstance(child_value, dict) and "model" not in child_value:
                if child.action:
                    failures.append({"check": "target_container_has_action", "path": "%s/%s" % (top_name, child_name)})
                for leaf_name in child_value:
                    leaf = _child_by_name(child, leaf_name)
                    leaf_path = "%s/%s/%s" % (top_name, child_name, leaf_name)
                    if not leaf:
                        failures.append({"check": "target_leaf_missing", "path": leaf_path})
                        continue
                    _check_leaf_action(failures, leaf_path, leaf, action_stats)
                    checked_leaves += 1
            else:
                _check_leaf_action(failures, "%s/%s" % (top_name, child_name), child, action_stats)
                checked_leaves += 1
    return checked_leaves, action_stats


def _check_active_duplicate_siblings(failures, root):
    menus = _active_menu_subtree(root)
    seen = {}
    duplicates = []
    for menu in menus:
        if not menu.parent_id:
            continue
        key = (menu.parent_id.id, menu.name)
        if key in seen:
            duplicates.append({"parent": menu.parent_id.name, "name": menu.name, "ids": [seen[key], menu.id]})
        else:
            seen[key] = menu.id
    if duplicates:
        failures.append({"check": "active_duplicate_sibling_menu", "actual": duplicates})


def _check_active_duplicate_paths(failures, root):
    menus = _active_menu_subtree(root)
    by_path = defaultdict(list)
    external_ids = menus.get_external_id()
    for menu in menus:
        by_path[_menu_path(menu)].append(menu)
    duplicates = []
    for path, path_menus in by_path.items():
        if len(path_menus) <= 1:
            continue
        duplicates.append(
            {
                "path": path,
                "items": [
                    {
                        "id": menu.id,
                        "name": menu.name,
                        "xmlid": external_ids.get(menu.id, ""),
                        "parent_id": menu.parent_id.id,
                    }
                    for menu in path_menus
                ],
            }
        )
    if duplicates:
        failures.append({"check": "active_duplicate_menu_path", "actual": duplicates})


def _check_no_non_target_active_menus(failures, root):
    target_paths = _target_menu_paths(root)
    menus = _active_menu_subtree(root)
    extras = []
    for menu in menus:
        path = _menu_path(menu)
        if path not in target_paths:
            extras.append(
                {
                    "id": menu.id,
                    "name": menu.name,
                    "path": path,
                    "action": "%s,%s" % (menu.action._name, menu.action.id) if menu.action else "",
                }
            )
    if extras:
        failures.append({"check": "non_target_active_menu", "actual": extras})


def main():
    failures = []
    root = env.ref("smart_construction_core.menu_sc_root", raise_if_not_found=False)
    if not root:
        failures.append({"check": "root", "missing": "smart_construction_core.menu_sc_root"})
        print(json.dumps({"ok": False, "failures": failures}, ensure_ascii=False, indent=2))
        return 1

    root = root.sudo().with_context(active_test=False, lang="zh_CN")
    direct_top = []
    for xmlid in [
        "menu_sc_projection_root",
        "menu_sc_workspace_center",
        "menu_sc_project_center",
        "menu_sc_contract_center",
        "menu_sc_material_center",
        "menu_sc_construction_management_center",
        "menu_sc_cost_center",
        "menu_sc_finance_center",
        "menu_sc_data_center",
        "menu_sc_business_config_center",
    ]:
        menu = env.ref("smart_construction_core.%s" % xmlid, raise_if_not_found=False)
        if menu:
            direct_top.append(menu.sudo().with_context(active_test=False, lang="zh_CN"))
    direct_top_names = [menu.name for menu in direct_top if menu.active and menu.parent_id.id == root.id]
    missing_top = [name for name in EXPECTED_TOP if name not in direct_top_names]
    if missing_top:
        failures.append({"check": "sudo_top_missing", "missing": missing_top, "actual": direct_top_names})
    legacy_top = [name for name in direct_top_names if name in LEGACY_TOP_NAMES]
    if legacy_top:
        failures.append({"check": "legacy_top_visible", "actual": legacy_top})
    structural_menus = [root] + direct_top
    structural_with_action = [menu.name for menu in structural_menus if menu.action]
    if structural_with_action:
        failures.append({"check": "structural_action", "actual": structural_with_action})
    structural_with_groups = [menu.name for menu in structural_menus if menu.groups_id]
    if structural_with_groups:
        failures.append({"check": "structural_groups", "actual": structural_with_groups})

    checked_target_leaves, action_stats = _check_target_tree(failures, root)
    _check_active_duplicate_siblings(failures, root)
    _check_active_duplicate_paths(failures, root)
    _check_no_non_target_active_menus(failures, root)

    user_results = {}
    visible_union = set()
    for login in PROBE_USERS:
        user = env["res.users"].sudo().search([("login", "=", login), ("active", "=", True)], limit=1)
        if not user:
            user_results[login] = {"skipped": "missing_or_inactive"}
            continue
        children = _visible_tree_for_user(root, user)
        visible_top = children[root.id]
        visible_names = [menu.name for menu in visible_top]
        visible_union.update(visible_names)
        legacy_visible = [name for name in visible_names if name in LEGACY_TOP_NAMES]
        if legacy_visible:
            failures.append({"check": "user_legacy_top", "login": login, "actual": legacy_visible})
        for top in visible_top:
            if top.name not in GROUP_REQUIRED_ROOTS:
                continue
            ungrouped = [
                {"name": child.name, "xmlid": _external_id(child)}
                for child in children[top.id]
                if child.action
            ]
            if ungrouped:
                failures.append({"check": "user_ungrouped_action", "login": login, "root": top.name, "actual": ungrouped})
        user_results[login] = {
            "name": user.name,
            "top": visible_names,
            "children": {top.name: _unique_names(children[top.id]) for top in visible_top},
        }

    union_missing = [name for name in EXPECTED_TOP if name not in visible_union]
    if union_missing:
        failures.append({"check": "probe_user_union_missing", "missing": union_missing, "visible_union": sorted(visible_union)})

    result = {
        "ok": not failures,
        "root": root.name,
        "sudo_top": direct_top_names,
        "checked_target_leaves": checked_target_leaves,
        "action_stats": action_stats,
        "probe_users": user_results,
        "failures": failures,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


raise SystemExit(main())
