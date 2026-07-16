"""Verify FE-B04 is carried by the real ui.contract.v2 response."""

import json

from odoo.addons.smart_core.handlers.ui_contract_v2 import UiContractV2Handler


user = env["res.users"].sudo().search([("login", "=", "demo_role_finance")], limit=1)
request = env.ref("smart_construction_demo.fe_journey_payment_request_a")
menu = env.ref("smart_construction_core.menu_sc_user_payment_apply_acceptance")
finance_env = env(user=user.id, context={**env.context, "allowed_company_ids": user.company_ids.ids})
params = {
    "op": "action_open",
    "action_id": int(menu.action.id),
    "menu_id": int(menu.id),
    "record_id": int(request.id),
    "render_profile": "edit",
    "client_type": "web_pc",
    "delivery_profile": "full",
}
result = UiContractV2Handler(finance_env, payload=params).run(payload=params)
data = result.data if hasattr(result, "data") and isinstance(result.data, dict) else (
    result.get("data") if isinstance(result, dict) else {}
)
runtime = data.get("runtimeContract") if isinstance(data, dict) and isinstance(data.get("runtimeContract"), dict) else {}
workspace = runtime.get("businessWorkspace") if isinstance(runtime.get("businessWorkspace"), dict) else {}
actions = runtime.get("businessActions") if isinstance(runtime.get("businessActions"), list) else []
submit = next((row for row in actions if isinstance(row, dict) and row.get("action_key") == "submit" and row.get("method") == "action_submit"), None)
assert (result.ok if hasattr(result, "ok") else result.get("ok")) is True
assert workspace.get("kind") == "payment_request" and workspace.get("record_id") == request.id
assert workspace.get("version") == "2.0"
assert (workspace.get("identity") or {}).get("object_label") == "付款申请"
assert (workspace.get("state") or {}).get("semantic")
assert submit and submit.get("allowed") is True
assert (submit.get("presentation") or {}).get("tier") == "primary"
assert (submit.get("mutation") or {}).get("operation") == "submit"
assert (submit.get("action_safety") or {}).get("requires_confirm") is True
print("[verify.frontend.financial_workspace.v2_contract] PASS")
print(json.dumps({"runtime_keys": sorted(runtime), "submit": submit}, ensure_ascii=False, indent=2, default=str))
