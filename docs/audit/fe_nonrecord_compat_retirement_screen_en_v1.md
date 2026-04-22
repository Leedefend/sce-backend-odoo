# FE Non-Record Compat Retirement Screen EN

```json
{
  "eligible_for_full_scene_purification": false,
  "next_candidate_family": "backend_scene_orchestration_route_supply_and_legacy_ingress_migration",
  "reason": "Current evidence does not support direct retirement of the non-record compat family. The frontend router still registers `/a/:actionId`, `/compat/action/:actionId`, and `/f/:model/:id`; `sceneRegistry.ts` still treats `/compat/action/*` and `/compat/form/*` as legal legacy delivery inputs; bounded producer fallbacks in HomeView, MyWorkView, WorkbenchView, and suggested_action/runtime.ts still emit `/compat/action/...` when no legal scene target can be proven; CapabilityMatrixView still recognizes `/compat/action/*` and `/compat/form/*` as internal routes. More importantly, backend-delivered contract snapshots still publish `/f/project.project/new?...` and `/a/246-248` route targets. That means the system has completed the scene-first mainline, but it has not yet satisfied the stronger condition required for all-route scenification. Further purification now depends on backend scene-orchestration route supply and explicit retirement/migration of legacy action/form ingress, not on frontend-only bridge deletion.",
  "bounded_evidence": [
    "frontend/apps/web/src/router/index.ts:79-82",
    "frontend/apps/web/src/app/resolvers/sceneRegistry.ts:282-283",
    "frontend/apps/web/src/views/HomeView.vue:2155",
    "frontend/apps/web/src/views/MyWorkView.vue:1264",
    "frontend/apps/web/src/views/WorkbenchView.vue:503",
    "frontend/apps/web/src/app/suggested_action/runtime.ts:342",
    "frontend/apps/web/src/views/CapabilityMatrixView.vue:121-124",
    "docs/contract/snapshots/system_init_intent_admin.json:383-396",
    "docs/contract/snapshots/system_init_intent_admin.json:777-822"
  ],
  "decision": {
    "route_mainline_scene_first": true,
    "all_routes_scene_pure_now": false,
    "frontend_only_retirement_safe": false
  }
}
```
