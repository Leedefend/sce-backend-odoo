import json


def ref(xmlid):
    row = env.ref(xmlid, raise_if_not_found=False)
    if not row:
        raise RuntimeError("missing %s" % xmlid)
    return row


def target(menu_xmlid, record_xmlid):
    menu = ref(menu_xmlid)
    row = ref(record_xmlid)
    return {
        "model": row._name,
        "record_id": int(row.id),
        "action_id": int(menu.action.id),
        "menu_id": int(menu.id),
        "name": str(row.display_name),
    }


payment_menu = "smart_construction_core.menu_sc_user_payment_apply_acceptance"
payload = {
    "draft": target(payment_menu, "smart_construction_demo.fe_journey_payment_request_a"),
    "approval": target(payment_menu, "smart_construction_demo.fe_journey_payment_request_approval_a"),
    "reject": target(payment_menu, "smart_construction_demo.fe_journey_payment_request_reject_a"),
    "completed": target(payment_menu, "smart_construction_demo.fe_journey_payment_request_completed_a"),
    "settlement": target(
        "smart_construction_core.menu_sc_settlement_order",
        "smart_construction_demo.fe_journey_settlement_a",
    ),
    "work_settlement": target(
        "smart_construction_core.menu_sc_settlement_order",
        "smart_construction_demo.fe_b05_work_settlement_a",
    ),
}
print("FRONTEND_MY_WORK_APPROVAL_TARGETS_JSON=" + json.dumps(payload, ensure_ascii=True, separators=(",", ":")))
