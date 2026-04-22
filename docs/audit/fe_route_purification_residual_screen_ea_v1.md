# FE Route Purification Residual Screen EA

```json
{
  "next_candidate_family": "scene_first_route_authority_closure",
  "family_scope": [
    "frontend/apps/web/src/views/HomeView.vue",
    "frontend/apps/web/src/views/MyWorkView.vue",
    "frontend/apps/web/src/views/WorkbenchView.vue",
    "frontend/apps/web/src/services/action_service.ts",
    "frontend/apps/web/src/app/suggested_action/runtime.ts",
    "frontend/apps/web/src/views/MenuView.vue",
    "frontend/apps/web/src/views/RecordView.vue"
  ],
  "reason": "Existing bounded scan and screen artifacts already separate residual route surfaces into two classes. Router registration and sceneRegistry compat-prefix recognition are still present, but the prior native-route authority and bridge-inventory outputs freeze them as compatibility baseline rather than the first dominant purification target. By contrast, the current strongest product-authority residual family is the set of frontend emitters and consumers that already attempt scene-first resolution but still fall back to native or compat action/record routes during ordinary user navigation. HomeView, MyWorkView, WorkbenchView, action_service.ts, and suggested_action/runtime.ts remain the dominant producer side, while MenuView and RecordView remain the clearest consumer-side authority gaps. The first full-purification batch should therefore close these scene-first fallback branches before any bridge retirement line. If a specific emitter still cannot produce a scene target after this closure attempt, that individual path should then open a backend scene-orchestration semantic-supply line rather than preserving frontend authority drift."
}
```
