# FE Action URL Producer Screen DP

```json
{
  "next_candidate_family": "scene_first_action_producer_migration",
  "family_scope": [
    "frontend/apps/web/src/views/HomeView.vue",
    "frontend/apps/web/src/views/MyWorkView.vue",
    "frontend/apps/web/src/views/WorkbenchView.vue",
    "frontend/apps/web/src/services/action_service.ts",
    "frontend/apps/web/src/app/suggested_action/runtime.ts"
  ],
  "reason": "The thin bridge is only covering still-active producers. The strongest remaining producers are frontend modules that already try `resolveSceneFirstActionLocation` or `resolveSceneFirstPath` and then fall back to `/compat/action/...` when scene resolution is unavailable. This fallback pattern is concentrated in HomeView, MyWorkView, WorkbenchView, action_service.ts, and suggested_action/runtime.ts. By contrast, useNavigationMenu is already normalizing `/native/action/...` into scene-first routes where possible and is not the dominant residual producer family for `/compat/action/...`. The next bounded migration batch should therefore target scene-first producer fallback removal in those action-entry emitters, ordered by highest user-visible entry surfaces first."
}
```
