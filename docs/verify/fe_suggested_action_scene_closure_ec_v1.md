# FE Suggested Action Scene Closure EC

- Scope:
  - `frontend/apps/web/src/app/suggested_action/runtime.ts`
- Change:
  - `open_project`, `open_action`, and `open_record` now treat carried `scene_key` or `scene` query identity as the second fallback layer after `findSceneByEntryAuthority`
  - when that scene identity exists, suggested-action runtime returns to `/s/:sceneKey` instead of `/compat/action/...` or `/r/...`
  - compat/native fallbacks remain only for scene-unknown paths
- Verification:
  - `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-21-FE-SUGGESTED-ACTION-SCENE-CLOSURE-EC.yaml`
  - `pnpm -C frontend/apps/web typecheck:strict`
  - `pnpm -C frontend/apps/web build`
  - `git diff --check -- agent_ops/tasks/ITER-2026-04-21-FE-SUGGESTED-ACTION-SCENE-CLOSURE-EC.yaml frontend/apps/web/src/app/suggested_action/runtime.ts docs/verify/fe_suggested_action_scene_closure_ec_v1.md docs/ops/iterations/delivery_context_switch_log_v1.md`
