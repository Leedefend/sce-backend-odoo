"""Resolve database-local action ids for the browser fixture runner."""

payment_action = env.ref("smart_construction_core.action_payment_request_user_payment_apply")
payment_menu = env.ref("smart_construction_core.menu_sc_user_payment_apply_acceptance")
print("FRONTEND_FIXTURE_PAYMENT_ACTION_ID=%s" % payment_action.id)
print("FRONTEND_FIXTURE_PAYMENT_MENU_ID=%s" % payment_menu.id)
