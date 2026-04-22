# BE Enterprise Bootstrap Scene Identity Screen ET

```json
{
  "implementation_safe_now": false,
  "result": "PASS_WITH_RISK",
  "reason": "The repository does not yet prove a stable scene target for enterprise bootstrap steps. `smart_enterprise_base/core_extension.py` still publishes only `action_id`, `menu_id`, xmlids, and `/a/...` routes for company/department/user setup steps. Bounded search found no existing enterprise scene keys or `/s/...` route publication tied to those steps. On the consumer side, `frontend/apps/web/src/stores/session.ts` normalizes enterprise targets into only `{ action_id, menu_id, action_xmlid, menu_xmlid, route }`, and `HomeView.vue` consumes that shape by trying `resolveSceneFirstActionLocation(actionId, menuId)` first and then falling back to `target.route` or `/compat/action/...`. Without proven scene-registry mapping for the enterprise bootstrap actions, and without frontend support for a richer `entry_target` payload on this contract surface, replacing `/a/...` publication here would be assumption-driven.",
  "bounded_evidence": [
    "addons/smart_enterprise_base/core_extension.py:12-21",
    "frontend/apps/web/src/stores/session.ts:63-69",
    "frontend/apps/web/src/stores/session.ts:358-367",
    "frontend/apps/web/src/views/HomeView.vue:2126-2155",
    "docs/contract/snapshots/ui_contract_intent_admin.json:565-603",
    "docs/contract/snapshots/system_init_intent_admin.json:774-822"
  ],
  "next_candidate_family": "backend_scene_identity_supply_or_frontend_consumer_contract_extension",
  "decision": {
    "enterprise_bootstrap_route_supply_now": false,
    "generic_menu_interpreter_now": false,
    "must_stop_on_uncertainty": true
  }
}
```
