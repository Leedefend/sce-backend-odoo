# FE Project Overview Blank Screen DN

```json
{
  "next_candidate_family": "action_route_registration_missing",
  "family_scope": [
    "frontend/apps/web/src/router/index.ts",
    "frontend/apps/web/src/views/ActionViewShell.vue",
    "frontend/apps/web/src/views/ActionView.vue"
  ],
  "reason": "The reported blank page URL `/a/584?menu_id=385` does not match any registered frontend route. `router/index.ts` currently registers `/s/:sceneKey`, `/m/:menuId`, and `/workbench`, but no `/a/:actionId`, `/compat/action/:actionId`, or equivalent action route. At the same time, `ActionView` already derives `actionId` from `route.params.actionId`, and multiple frontend call sites still navigate to `/compat/action/...` or `/a/...` style action URLs. `App.vue` also has no 404/status fallback for unmatched routes, so an unmatched action URL collapses into a blank shell. The stronger next family is missing action-route registration on the frontend consumer boundary, not backend semantic supply."
}
```
