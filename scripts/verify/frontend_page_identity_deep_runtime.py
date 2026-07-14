"""Resolve FE-B03 deep-browser targets from stable fixture and menu XML IDs."""

import json


def target(menu_xmlid, record_xmlid=None):
    menu = env.ref(menu_xmlid)
    action = menu.action
    if not action:
        raise RuntimeError("menu has no action: %s" % menu_xmlid)
    action_xmlid = action.get_external_id().get(action.id, "")
    if not action_xmlid:
        raise RuntimeError("action has no XML ID: %s" % menu_xmlid)
    row = {
        "menu_id": menu.id,
        "menu_xmlid": menu_xmlid,
        "action_id": action.id,
        "action_xmlid": action_xmlid,
        "model": action.res_model,
        "action_name": action.name,
    }
    if record_xmlid:
        record = env.ref(record_xmlid)
        row.update({
            "record_id": record.id,
            "record_xmlid": record_xmlid,
            "display_name": record.display_name,
        })
    return row


payload = {
    "project": target(
        "smart_construction_core.menu_sc_project_project",
        "smart_construction_demo.fe_project_a",
    ),
    "contract": target(
        "smart_construction_core.menu_sc_construction_contract",
        "smart_construction_demo.fe_contract_a",
    ),
    "settlement": target(
        "smart_construction_core.menu_sc_settlement_order",
        "smart_construction_demo.fe_settlement_a",
    ),
    "payment_request": target(
        "smart_construction_core.menu_sc_user_payment_apply_acceptance",
        "smart_construction_demo.fe_request_a_001",
    ),
    "payment_execution": target(
        "smart_construction_core.menu_sc_payment_execution",
        "smart_construction_demo.fe_execution_a",
    ),
}
print("FRONTEND_PAGE_IDENTITY_DEEP_TARGETS_JSON=%s" % json.dumps(payload, ensure_ascii=True, separators=(",", ":")))
