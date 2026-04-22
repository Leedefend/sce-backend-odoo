# FE Scene-First Producer Closure EB

- Scope:
  - `frontend/apps/web/src/views/HomeView.vue`
  - `frontend/apps/web/src/views/MyWorkView.vue`
  - `frontend/apps/web/src/views/WorkbenchView.vue`
- Change:
  - scene-known producer fallbacks no longer jump to `/compat/action/...` or `/r/...` first
  - when `sceneLocation` cannot be derived but the caller already carries `sceneKey`, navigation now stays on `/s/:sceneKey` and carries `action_id` / `record_id` / `model` in query
  - Workbench keeps the old compat/native fallback only when current route query does not provide a provable scene key
- Verification:
  - `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-21-FE-SCENE-FIRST-PRODUCER-CLOSURE-EB.yaml`
  - `pnpm -C frontend/apps/web typecheck:strict`
  - `pnpm -C frontend/apps/web build`
  - `git diff --check -- agent_ops/tasks/ITER-2026-04-21-FE-SCENE-FIRST-PRODUCER-CLOSURE-EB.yaml frontend/apps/web/src/views/HomeView.vue frontend/apps/web/src/views/MyWorkView.vue frontend/apps/web/src/views/WorkbenchView.vue docs/verify/fe_scene_first_producer_closure_eb_v1.md docs/ops/iterations/delivery_context_switch_log_v1.md`
