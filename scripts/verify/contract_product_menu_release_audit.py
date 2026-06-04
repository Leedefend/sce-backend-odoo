# -*- coding: utf-8 -*-
from __future__ import annotations

import json


CONTRACT_CENTER_XMLID = "smart_construction_core.menu_sc_contract_center"
SETTLEMENT_CENTER_XMLID = "smart_construction_core.menu_sc_settlement_center"
REQUIRED_CONTRACT_GROUP_XMLID = "smart_construction_core.group_sc_cap_contract_read"
REQUIRED_SETTLEMENT_GROUP_XMLID = "smart_construction_core.group_sc_cap_settlement_read"

REQUIRED_RELEASED_CONTRACT_MENU_XMLIDS = (
    "smart_construction_core.menu_sc_contract_income",
    "smart_construction_core.menu_sc_project_income_contract",
    "smart_construction_core.menu_sc_income_contract_execution",
    "smart_construction_core.menu_sc_contract_event",
    "smart_construction_core.menu_sc_general_contract",
    "smart_construction_core.menu_sc_contract_expense",
    "smart_construction_core.menu_sc_expense_contract_execution",
)

REQUIRED_RELEASED_SETTLEMENT_MENU_XMLIDS = (
    "smart_construction_core.menu_sc_settlement_order",
    "smart_construction_core.menu_sc_settlement_adjustment",
    "smart_construction_core.menu_sc_income_contract_settlement",
    "smart_construction_core.menu_sc_expense_contract_settlement",
    "smart_construction_core.menu_sc_material_settlement",
    "smart_construction_core.menu_sc_labor_settlement",
    "smart_construction_core.menu_sc_equipment_settlement",
    "smart_construction_core.menu_sc_material_rental_settlement",
    "smart_construction_core.menu_sc_subcontract_settlement",
)

REQUIRED_RELEASED_MENU_XMLIDS = REQUIRED_RELEASED_CONTRACT_MENU_XMLIDS + REQUIRED_RELEASED_SETTLEMENT_MENU_XMLIDS

REQUIRED_USER_VISIBLE_MENU_XMLIDS = (
    CONTRACT_CENTER_XMLID,
    *REQUIRED_RELEASED_CONTRACT_MENU_XMLIDS,
    SETTLEMENT_CENTER_XMLID,
    "smart_construction_core.menu_sc_settlement_order",
    "smart_construction_core.menu_sc_settlement_adjustment",
)

USER_ACCEPTANCE_PRODUCT_MENU_XMLIDS = {
    "smart_construction_core.menu_sc_customer_partner",
    "smart_construction_core.menu_sc_supplier_partner",
}

USER_ACCEPTANCE_MENU_KEY_TOKENS = (
    "_acceptance",
    "user_acceptance",
)

VISIBLE_CHECK_USERS = (
    "demo_role_project_read",
    "sc_fx_pm",
)


def _ref(xmlid):
    record = env.ref(xmlid, raise_if_not_found=False)  # noqa: F821
    if not record:
        raise AssertionError("missing xmlid: %s" % xmlid)
    return record


def _external_id(record):
    return record.get_external_id().get(record.id, "") if record else ""


def _is_user_acceptance_key(value):
    key = str(value or "").strip()
    return key in USER_ACCEPTANCE_PRODUCT_MENU_XMLIDS or any(token in key for token in USER_ACCEPTANCE_MENU_KEY_TOKENS)


def _assert_menu_has_group(menu_xmlid, group_xmlid):
    menu = _ref(menu_xmlid)
    group = _ref(group_xmlid)
    if group not in menu.groups_id:
        raise AssertionError(
            "%s missing %s; groups=%s"
            % (menu_xmlid, group_xmlid, sorted(_external_id(row) for row in menu.groups_id))
        )


def _released_policy_menu_keys(product_key):
    policy = env["sc.product.policy"].sudo().search([("product_key", "=", product_key)], limit=1)  # noqa: F821
    if not policy:
        raise AssertionError("missing product policy: %s" % product_key)
    if not policy.active or policy.access_level != "public":
        raise AssertionError("%s must be active public" % product_key)

    keys = set()
    for group in policy.menu_groups or []:
        if not isinstance(group, dict):
            continue
        for menu in group.get("menus") or []:
            if not isinstance(menu, dict):
                continue
            if menu.get("enabled") and menu.get("release_state") == "released":
                keys.add(str(menu.get("page_key") or menu.get("menu_key") or ""))
    return keys


def _assert_user_visible(login, menu_xmlids):
    user = env["res.users"].sudo().search([("login", "=", login)], limit=1)  # noqa: F821
    if not user:
        raise AssertionError("missing verification user: %s" % login)
    visible_ids = set(env["ir.ui.menu"].with_user(user)._visible_menu_ids())  # noqa: F821
    missing = []
    for xmlid in menu_xmlids:
        menu = _ref(xmlid)
        if menu.id not in visible_ids:
            missing.append(xmlid)
    if missing:
        raise AssertionError("%s cannot see required released menus: %s" % (login, missing))


def main():
    for menu_xmlid in (CONTRACT_CENTER_XMLID, *REQUIRED_RELEASED_CONTRACT_MENU_XMLIDS):
        _assert_menu_has_group(menu_xmlid, REQUIRED_CONTRACT_GROUP_XMLID)
    for menu_xmlid in (SETTLEMENT_CENTER_XMLID, *REQUIRED_RELEASED_SETTLEMENT_MENU_XMLIDS[:2]):
        _assert_menu_has_group(menu_xmlid, REQUIRED_SETTLEMENT_GROUP_XMLID)

    product_results = {}
    for product_key in ("construction.standard", "construction.preview"):
        keys = _released_policy_menu_keys(product_key)
        missing = [xmlid for xmlid in REQUIRED_RELEASED_MENU_XMLIDS if xmlid not in keys]
        if missing:
            raise AssertionError("%s missing released formal pages: %s" % (product_key, missing))
        product_results[product_key] = len(keys)

    for login in VISIBLE_CHECK_USERS:
        _assert_user_visible(login, REQUIRED_USER_VISIBLE_MENU_XMLIDS)

    print(
        json.dumps(
            {
                "status": "PASS",
                "db": env.cr.dbname,  # noqa: F821
                "contract_center": CONTRACT_CENTER_XMLID,
                "settlement_center": SETTLEMENT_CENTER_XMLID,
                "released_contract_pages": list(REQUIRED_RELEASED_CONTRACT_MENU_XMLIDS),
                "released_settlement_pages": list(REQUIRED_RELEASED_SETTLEMENT_MENU_XMLIDS),
                "product_released_menu_counts": product_results,
                "visible_users": list(VISIBLE_CHECK_USERS),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


main()
