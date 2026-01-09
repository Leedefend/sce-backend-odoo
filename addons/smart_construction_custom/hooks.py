# -*- coding: utf-8 -*-
def _safe_ref(env, xmlid):
    try:
        return env.ref(xmlid, raise_if_not_found=False)
    except Exception:
        return None


def post_init_hook(env):
    group = _safe_ref(env, "smart_construction_core.group_sc_business_full")
    if not group:
        return

    implied_xmlids = [
        "smart_construction_core.group_sc_internal_user",
        "smart_construction_core.group_sc_cap_contact_manager",
        "smart_construction_core.group_sc_cap_project_manager",
        "smart_construction_core.group_sc_cap_contract_manager",
        "smart_construction_core.group_sc_cap_cost_manager",
        "smart_construction_core.group_sc_cap_material_manager",
        "smart_construction_core.group_sc_cap_purchase_manager",
        "smart_construction_core.group_sc_cap_finance_manager",
        "smart_construction_core.group_sc_cap_settlement_manager",
        "smart_construction_core.group_sc_cap_data_read",
    ]

    to_add = []
    for xmlid in implied_xmlids:
        ref = _safe_ref(env, xmlid)
        if ref and ref not in group.implied_ids:
            to_add.append(ref.id)

    if to_add:
        group.write({"implied_ids": [(4, gid) for gid in to_add]})
