"""Resolve stable FE-B04 browser targets without hard-coding database IDs."""

import json


def target(menu_xmlid, record_xmlid):
    menu = env.ref(menu_xmlid)
    action = menu.action
    record = env.ref(record_xmlid)
    return {
        "menu_id": int(menu.id),
        "menu_xmlid": menu_xmlid,
        "action_id": int(action.id),
        "action_xmlid": action.get_external_id().get(action.id, ""),
        "model": action.res_model,
        "record_id": int(record.id),
        "record_xmlid": record_xmlid,
        "display_name": record.display_name,
    }


payload = {
    "project": target("smart_construction_core.menu_sc_project_project", "smart_construction_demo.fe_project_a"),
    "contract": target("smart_construction_core.menu_sc_construction_contract", "smart_construction_demo.fe_contract_a"),
    "settlement": target("smart_construction_core.menu_sc_settlement_order", "smart_construction_demo.fe_settlement_a"),
    "payment_request": target("smart_construction_core.menu_sc_user_payment_apply_acceptance", "smart_construction_demo.fe_request_a_001"),
    "payment_request_company_b": target("smart_construction_core.menu_sc_user_payment_apply_acceptance", "smart_construction_demo.fe_request_c_001"),
    "payment_execution": target("smart_construction_core.menu_sc_payment_execution", "smart_construction_demo.fe_execution_a"),
    "journey_settlement": target("smart_construction_core.menu_sc_settlement_order", "smart_construction_demo.fe_journey_settlement_a"),
    "journey_request": target("smart_construction_core.menu_sc_user_payment_apply_acceptance", "smart_construction_demo.fe_journey_payment_request_a"),
}
print("FRONTEND_FINANCIAL_WORKSPACE_TARGETS_JSON=%s" % json.dumps(payload, ensure_ascii=True, separators=(",", ":")))
