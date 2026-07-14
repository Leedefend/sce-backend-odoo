"""Resolve FE-B02R direct-route probes from stable XML IDs."""

targets = {
    "PLAN_ACTION": "smart_construction_core.action_sc_plan",
    "PLAN_MENU": "smart_construction_core.menu_sc_plan",
    "PLAN_REPORT_ACTION": "smart_construction_core.action_sc_plan_report",
    "PLAN_REPORT_MENU": "smart_construction_core.menu_sc_plan_report",
    "TENDER_ACTION": "smart_construction_core.action_sc_tender_registration",
    "TENDER_MENU": "smart_construction_core.menu_sc_tender_registration",
}

for key, xmlid in targets.items():
    record = env.ref(xmlid, raise_if_not_found=False)
    if not record:
        raise RuntimeError("missing FE-B02R runtime target: %s" % xmlid)
    print("FRONTEND_NAV_ACCESS_%s_ID=%s" % (key, record.id))
