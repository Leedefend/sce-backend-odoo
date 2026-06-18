# -*- coding: utf-8 -*-
from __future__ import annotations

import json


PRODUCT_KEYS = ("construction.standard", "construction.preview")
VISIBLE_CHECK_USERS = ("wutao", "demo_role_project_read", "sc_fx_pm")
ALLOWED_HIDDEN_RELEASE_DOMAINS = {"internal_config"}
TRUTHY_VALUES = {"1", "true", "yes", "on"}


def _text(value):
    return str(value or "").strip()


def _external_id(record):
    return record.get_external_id().get(record.id, "") if record else ""


def _assert_product_navigation_mode():
    Param = env["ir.config_parameter"].sudo()  # noqa: F821
    acceptance_only = Param.get_param("smart_core.nav.user_data_acceptance_only", "")
    user_menu_config = Param.get_param("smart_core.nav.user_menu_config.enabled", "")
    if _text(acceptance_only).lower() in TRUTHY_VALUES:
        raise AssertionError(
            "smart_core.nav.user_data_acceptance_only must be disabled for full product menu release"
        )
    if _text(user_menu_config).lower() not in TRUTHY_VALUES:
        raise AssertionError(
            "smart_core.nav.user_menu_config.enabled must be enabled so low-code menu configuration can apply"
        )
    return {
        "smart_core.nav.user_data_acceptance_only": _text(acceptance_only) or "0",
        "smart_core.nav.user_menu_config.enabled": _text(user_menu_config) or "0",
    }


def _released_policy_menus(product_key):
    policy = env["sc.product.policy"].sudo().search([("product_key", "=", product_key)], limit=1)  # noqa: F821
    if not policy:
        raise AssertionError("missing product policy: %s" % product_key)
    if not policy.active or policy.access_level != "public":
        raise AssertionError("%s must be active public" % product_key)

    rows = []
    hidden = []
    allowed_hidden = []
    for group in policy.menu_groups or []:
        if not isinstance(group, dict):
            continue
        for menu in group.get("menus") or []:
            if not isinstance(menu, dict):
                continue
            if menu.get("enabled") and menu.get("release_state") == "released":
                rows.append(menu)
            else:
                item = {
                    "group": _text(group.get("group_label") or group.get("group_key")),
                    "menu": _text(menu.get("menu_xmlid") or menu.get("page_key") or menu.get("menu_key")),
                    "enabled": bool(menu.get("enabled")),
                    "release_state": _text(menu.get("release_state")),
                    "release_domain": _text(menu.get("release_domain")),
                    "access_level": _text(menu.get("access_level")),
                }
                if item["release_domain"] in ALLOWED_HIDDEN_RELEASE_DOMAINS:
                    allowed_hidden.append(item)
                else:
                    hidden.append(item)
    if hidden:
        raise AssertionError("%s still has hidden product menus: %s" % (product_key, hidden[:20]))
    if not rows:
        raise AssertionError("%s has no released menus" % product_key)
    return rows, allowed_hidden


def _visible_menu_ids_by_login():
    out = {}
    for login in VISIBLE_CHECK_USERS:
        user = env["res.users"].sudo().search([("login", "=", login)], limit=1)  # noqa: F821
        if not user:
            continue
        out[login] = set(env["ir.ui.menu"].with_user(user)._visible_menu_ids())  # noqa: F821
    if not out:
        raise AssertionError("no verification users exist: %s" % (VISIBLE_CHECK_USERS,))
    return out


def _assert_menu_runtime(menu_row, visible_by_login):
    menu_xmlid = _text(menu_row.get("menu_xmlid") or menu_row.get("page_key") or menu_row.get("menu_key"))
    if not menu_xmlid:
        raise AssertionError("released menu is missing menu_xmlid/page_key: %s" % menu_row)
    menu = env.ref(menu_xmlid, raise_if_not_found=False)  # noqa: F821
    if not menu:
        raise AssertionError("released menu xmlid does not resolve: %s" % menu_xmlid)
    if hasattr(menu, "active") and not bool(menu.active):
        raise AssertionError("released menu is inactive: %s" % menu_xmlid)
    if not menu.action:
        raise AssertionError("released menu has no action: %s" % menu_xmlid)
    action_id = int(menu_row.get("action_id") or 0)
    if action_id and int(menu.action.id or 0) != action_id:
        raise AssertionError(
            "released menu action drift: %s policy=%s actual=%s"
            % (menu_xmlid, action_id, int(menu.action.id or 0))
        )
    res_model = _text(getattr(menu.action, "res_model", "")) or _text(menu_row.get("res_model"))
    if not res_model:
        raise AssertionError("released menu action has no res_model: %s" % menu_xmlid)
    if res_model not in env:  # noqa: F821
        raise AssertionError("released menu action model missing: %s -> %s" % (menu_xmlid, res_model))
    visible_logins = [login for login, visible_ids in visible_by_login.items() if int(menu.id) in visible_ids]
    if not visible_logins:
        raise AssertionError(
            "released menu is not visible to verification users: %s groups=%s"
            % (menu_xmlid, sorted(_external_id(group) for group in menu.groups_id))
        )
    return {
        "menu_xmlid": menu_xmlid,
        "label": _text(menu.name),
        "path": _text(menu_row.get("visible_menu_path")),
        "action_id": int(menu.action.id or 0),
        "res_model": res_model,
        "visible_logins": visible_logins,
    }


def main():
    runtime_mode = _assert_product_navigation_mode()
    visible_by_login = _visible_menu_ids_by_login()
    product_counts = {}
    hidden_counts = {}
    audited = {}
    seen = set()
    for product_key in PRODUCT_KEYS:
        rows, allowed_hidden = _released_policy_menus(product_key)
        product_counts[product_key] = len(rows)
        hidden_counts[product_key] = len(allowed_hidden)
        for row in rows:
            menu_xmlid = _text(row.get("menu_xmlid") or row.get("page_key") or row.get("menu_key"))
            if menu_xmlid in seen:
                continue
            audited[menu_xmlid] = _assert_menu_runtime(row, visible_by_login)
            seen.add(menu_xmlid)

    print(
        json.dumps(
            {
                "status": "PASS",
                "db": env.cr.dbname,  # noqa: F821
                "products": product_counts,
                "runtime_mode": runtime_mode,
                "allowed_hidden_internal_menu_counts": hidden_counts,
                "unique_released_menu_count": len(audited),
                "visible_users": sorted(visible_by_login),
                "sample_menus": list(audited.values())[:20],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


main()
