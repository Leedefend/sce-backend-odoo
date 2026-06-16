# -*- coding: utf-8 -*-
"""Audit custom user menu preferences for split handling entries.

Run inside Odoo shell:
    bash scripts/ops/odoo_shell_exec.sh < scripts/verify/user_menu_preference_runtime_audit.py
"""

from odoo.addons.smart_construction_custom.models import user_preferences
from odoo.addons.smart_core.handlers import system_init


def _menu_key(row):
    return str(row.get("menu_xmlid") or row.get("page_key") or row.get("menu_key") or "").strip()


def _iter_menus(policy):
    for group in policy.menu_groups or []:
        if not isinstance(group, dict):
            continue
        for menu in group.get("menus") if isinstance(group.get("menus"), list) else []:
            if isinstance(menu, dict):
                yield menu


Policy = env["sc.product.policy"].sudo().with_context(active_test=False)
policies = Policy.search([("product_key", "in", ["construction.standard", "construction.preview"])], order="product_key")
failures = []
checked = 0

for policy in policies:
    menus_by_key = {_menu_key(menu): menu for menu in _iter_menus(policy)}
    for menu in _iter_menus(policy):
        checked += 1
        if str(menu.get("disposition_policy") or "").strip() == "merge_by_category":
            failures.append((
                policy.product_key,
                _menu_key(menu),
                "merged_business_entry_policy_forbidden",
                menu.get("label") or menu.get("page_label"),
                menu.get("integration_target"),
                menu.get("allowed_business_category_codes"),
            ))

    for menu_xmlid, rule in user_preferences.USER_SPLIT_HANDLING_MENU_RULES.items():
        menu = menus_by_key.get(menu_xmlid)
        if not menu:
            continue
        checked += 1
        category_code = str(rule["category_code"] or "").strip()
        label = str(rule["label"] or "").strip()
        allowed = menu.get("allowed_business_category_codes")
        if allowed != [category_code]:
            failures.append((policy.product_key, menu_xmlid, "bad_allowed_business_category_codes", allowed))
        if str(menu.get("default_business_category_code") or "").strip() != category_code:
            failures.append((policy.product_key, menu_xmlid, "bad_default_business_category_code", menu.get("default_business_category_code")))
        if str(menu.get("disposition_policy") or "").strip() != "keep_list_form":
            failures.append((policy.product_key, menu_xmlid, "bad_disposition_policy", menu.get("disposition_policy")))
        if str(menu.get("entry_target_policy") or "").strip() != "keep_list_form":
            failures.append((policy.product_key, menu_xmlid, "bad_entry_target_policy", menu.get("entry_target_policy")))
        if str(menu.get("integration_target") or "").strip() != "sc.expense.claim %s" % label:
            failures.append((policy.product_key, menu_xmlid, "bad_integration_target", menu.get("integration_target")))
        if menu.get("integration_entry_target"):
            failures.append((policy.product_key, menu_xmlid, "stale_integration_entry_target", menu.get("integration_entry_target")))
        if str(menu.get("policy_note") or "").strip() != "custom_user_split_merged_handling_menu":
            failures.append((policy.product_key, menu_xmlid, "bad_policy_note", menu.get("policy_note")))

    merged = []
    for menu in _iter_menus(policy):
        allowed = menu.get("allowed_business_category_codes") if isinstance(menu.get("allowed_business_category_codes"), list) else []
        default = str(menu.get("default_business_category_code") or "").strip()
        split_codes = [str(code or "").strip() for code in [default, *allowed]]
        if not any(code in user_preferences.USER_SPLIT_HANDLING_CATEGORY_CODES for code in split_codes):
            continue
        checked += 1
        menu_xmlid = _menu_key(menu)
        if str(menu.get("disposition_policy") or "").strip() != "keep_list_form":
            failures.append((policy.product_key, menu_xmlid, "cash_handling_not_split", menu.get("disposition_policy")))
        if str(menu.get("entry_target_policy") or "").strip() != "keep_list_form":
            failures.append((policy.product_key, menu_xmlid, "cash_handling_bad_entry_target_policy", menu.get("entry_target_policy")))
        if str(menu.get("integration_target") or "").strip() == "sc.expense.claim 费用/保证金申请":
            merged.append(menu)
        if menu.get("integration_entry_target"):
            failures.append((policy.product_key, menu_xmlid, "cash_handling_stale_integration_entry_target", menu.get("integration_entry_target")))

    if merged:
        failures.append((policy.product_key, "merged_expense_deposit_entry_still_present", len(merged)))

    for rule in user_preferences.USER_SPLIT_CONTRACT_HANDLING_MENU_RULES:
        menu_xmlid = str(rule["menu_xmlid"])
        menu = menus_by_key.get(menu_xmlid)
        checked += 1
        if not menu:
            failures.append((policy.product_key, menu_xmlid, "missing_contract_split_menu"))
            continue
        category_code = str(rule["category_code"])
        if str(menu.get("disposition_policy") or "").strip() != "keep_list_form":
            failures.append((policy.product_key, menu_xmlid, "contract_not_split", menu.get("disposition_policy")))
        if str(menu.get("entry_target_policy") or "").strip() != "keep_list_form":
            failures.append((policy.product_key, menu_xmlid, "contract_bad_entry_target_policy", menu.get("entry_target_policy")))
        if menu.get("allowed_business_category_codes") != [category_code]:
            failures.append((policy.product_key, menu_xmlid, "contract_bad_allowed_business_category_codes", menu.get("allowed_business_category_codes")))
        if str(menu.get("integration_target") or "").strip() == "construction.contract 合同办理":
            failures.append((policy.product_key, menu_xmlid, "contract_still_merged_target"))
        if menu.get("integration_entry_target"):
            failures.append((policy.product_key, menu_xmlid, "contract_stale_integration_entry_target", menu.get("integration_entry_target")))

    merged_contract = [
        menu
        for menu in _iter_menus(policy)
        if str(menu.get("integration_target") or "").strip() == "construction.contract 合同办理"
        or (
            str(menu.get("menu_xmlid") or "").strip() == "smart_construction_core.menu_sc_construction_contract"
            and str(menu.get("label") or "").strip() == "合同办理"
        )
    ]
    if merged_contract:
        failures.append((policy.product_key, "merged_contract_handling_entry_still_present", len(merged_contract)))

    merged_contract_settlement = []
    for menu in _iter_menus(policy):
        category_code = str(menu.get("default_business_category_code") or "").strip()
        if category_code not in user_preferences.USER_SPLIT_CONTRACT_SETTLEMENT_CATEGORY_CODES:
            continue
        checked += 1
        menu_xmlid = _menu_key(menu)
        if str(menu.get("disposition_policy") or "").strip() != "keep_list_form":
            failures.append((policy.product_key, menu_xmlid, "contract_settlement_not_split", menu.get("disposition_policy")))
        if str(menu.get("entry_target_policy") or "").strip() != "keep_list_form":
            failures.append((policy.product_key, menu_xmlid, "contract_settlement_bad_entry_target_policy", menu.get("entry_target_policy")))
        if menu.get("allowed_business_category_codes") != [category_code]:
            failures.append((policy.product_key, menu_xmlid, "contract_settlement_bad_allowed_business_category_codes", menu.get("allowed_business_category_codes")))
        if str(menu.get("integration_target") or "").strip() == "sc.settlement.order 结算办理":
            merged_contract_settlement.append(menu)
        if menu.get("integration_entry_target"):
            failures.append((policy.product_key, menu_xmlid, "contract_settlement_stale_integration_entry_target", menu.get("integration_entry_target")))
    if merged_contract_settlement:
        failures.append((policy.product_key, "merged_contract_settlement_entry_still_present", len(merged_contract_settlement)))

if failures:
    print("[user_menu_preference_runtime_audit] FAIL checked=%s failures=%s" % (checked, len(failures)))
    for failure in failures:
        print(failure)
    raise SystemExit(1)

print("[user_menu_preference_runtime_audit] PASS checked=%s policies=%s" % (checked, len(policies)))

sample_node = {
    "label": "收入合同执行",
    "menu_id": 485,
    "children": [],
    "meta": {
        "menu_id": 485,
        "menu_xmlid": "smart_construction_core.menu_sc_income_contract_execution",
        "productization_source": "smart_construction_custom.user_menu_preference",
    },
}
filtered, meta = system_init._filter_nav_by_release_gate(
    [sample_node],
    {
        "applied": True,
        "product_key": "construction.standard",
        "allowed": {
            "page_keys": [],
            "menu_keys": [],
            "menu_xmlids": [],
            "routes": [],
            "menu_ids": [],
            "action_ids": [],
        },
    },
)
if not filtered:
    raise SystemExit("user preference menu must survive stale release gate filtering: %s" % meta)
print("[user_menu_preference_runtime_audit] release_gate_user_preference_passthrough=PASS")
