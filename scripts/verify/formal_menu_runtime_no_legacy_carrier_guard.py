# -*- coding: utf-8 -*-
"""Runtime guard for formal product menus that must not use legacy carriers.

Run through Odoo shell:
    DB_NAME=sc_demo make verify.formal_menu.runtime_no_legacy_carrier_guard
"""

import json


FORMAL_MENUS = {
    "smart_construction_core.menu_sc_arrival_confirmation": {
        "expected_res_model": "sc.receipt.income",
        "expected_action_xmlid": "smart_construction_core.action_sc_receipt_income_arrival_confirmation",
    },
    "smart_construction_core.menu_sc_legacy_fuel_card_fact_acceptance": {
        "expected_res_model": "sc.fund.account.operation",
        "expected_action_xmlid": "smart_construction_core.action_sc_fuel_card_registration_formal",
    },
    "smart_construction_core.menu_sc_legacy_fuel_card_recharge_fact_acceptance": {
        "expected_res_model": "sc.fund.account.operation",
        "expected_action_xmlid": "smart_construction_core.action_sc_fuel_card_recharge_formal",
    },
    "smart_construction_core.menu_sc_company_user_roster_formal": {
        "expected_res_model": "res.users",
        "expected_action_xmlid": "smart_construction_core.action_sc_company_user_roster_formal",
    },
    "smart_construction_core.menu_sc_material_rental_in_acceptance": {
        "expected_res_model": "sc.material.rental.order",
        "expected_action_xmlid": "smart_construction_core.action_sc_material_rental_in_acceptance",
    },
    "smart_construction_core.menu_sc_material_rental_return_acceptance": {
        "expected_res_model": "sc.material.rental.order",
        "expected_action_xmlid": "smart_construction_core.action_sc_material_rental_return_acceptance",
    },
    "smart_construction_core.menu_sc_self_funding_advance_income": {
        "expected_res_model": "sc.self.funding.registration",
        "expected_action_xmlid": "smart_construction_core.action_sc_self_funding_registration_income",
    },
    "smart_construction_core.menu_sc_self_funding_advance_refund": {
        "expected_res_model": "sc.self.funding.registration",
        "expected_action_xmlid": "smart_construction_core.action_sc_self_funding_registration_refund",
    },
}


errors = []
rows = []

for menu_xmlid, expected in FORMAL_MENUS.items():
    menu = env.ref(menu_xmlid, raise_if_not_found=False)
    if not menu:
        errors.append({"menu_xmlid": menu_xmlid, "error": "menu_missing"})
        continue

    action = menu.action
    action_xmlid = ""
    res_model = ""
    if action:
        action_xmlid = action.get_external_id().get(action.id, "")
        res_model = getattr(action, "res_model", "") or ""

    row = {
        "menu_xmlid": menu_xmlid,
        "menu_name": menu.complete_name,
        "active": bool(menu.active),
        "action_xmlid": action_xmlid,
        "res_model": res_model,
        "expected_action_xmlid": expected["expected_action_xmlid"],
        "expected_res_model": expected["expected_res_model"],
    }
    rows.append(row)

    if not menu.active:
        errors.append({**row, "error": "formal_menu_inactive"})
    if not action:
        errors.append({**row, "error": "formal_menu_action_missing"})
        continue
    if action_xmlid != expected["expected_action_xmlid"]:
        errors.append({**row, "error": "formal_menu_action_xmlid_mismatch"})
    if res_model != expected["expected_res_model"]:
        errors.append({**row, "error": "formal_menu_res_model_mismatch"})
    if res_model.startswith("sc.legacy."):
        errors.append({**row, "error": "active_formal_menu_uses_legacy_model"})

report = {
    "guard": "formal_menu_runtime_no_legacy_carrier_guard",
    "checked_menu_count": len(FORMAL_MENUS),
    "rows": rows,
    "errors": errors,
    "status": "FAIL" if errors else "PASS",
}
print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
print(
    "FORMAL_MENU_RUNTIME_NO_LEGACY_CARRIER_GUARD="
    + json.dumps(report, ensure_ascii=False, sort_keys=True)
)
if errors:
    raise SystemExit(1)
