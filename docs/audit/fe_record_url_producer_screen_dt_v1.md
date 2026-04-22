# FE Record URL Producer Screen DT

```json
{
  "next_candidate_family": "record_url_producer_fallback_shrink",
  "family_scope": [
    "frontend/apps/web/src/views/HomeView.vue",
    "frontend/apps/web/src/views/MyWorkView.vue",
    "frontend/apps/web/src/views/WorkbenchView.vue",
    "frontend/apps/web/src/services/action_service.ts",
    "frontend/apps/web/src/app/suggested_action/runtime.ts"
  ],
  "reason": "The bounded known record URL producers have already partially converged. HomeView, MyWorkView, WorkbenchView, and action_service all call resolveSceneFirstFormOrRecordLocation first and only fall back to `/compat/record/...` when scene resolution fails. The strongest residual producer is suggested_action/runtime.ts, which also attempts scene-first but only from parsed query context and therefore may still lack enough scene identity on some invocations. This means the next legal frontend batch is not another bridge expansion; it is a bounded producer-fallback shrink focused first on the weakest residual producer and then any remaining record fallback emitters with sufficient scene context."
}
```
