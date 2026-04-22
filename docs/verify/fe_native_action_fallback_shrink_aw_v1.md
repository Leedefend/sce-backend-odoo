# FE Native Action Fallback Shrink AW v1

## scope

- shrink unresolved `/native/action/:id` fallback in navigation normalization
- keep scene-first resolution
- avoid widening scope into router compat shell retirement

## verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-20-FE-NATIVE-ACTION-FALLBACK-SHRINK-AW.yaml` → `PASS`
- `pnpm -C frontend/apps/web typecheck:strict` → `PASS`
- `pnpm -C frontend/apps/web build` → `PASS` with existing chunk-size warning only
- `git diff --check -- agent_ops/tasks/ITER-2026-04-20-FE-NATIVE-ACTION-FALLBACK-SHRINK-AW.yaml docs/verify/fe_native_action_fallback_shrink_aw_v1.md docs/ops/iterations/delivery_context_switch_log_v1.md frontend/apps/web/src/composables/useNavigationMenu.ts` → `PASS`

## implementation

- resolved `/native/action/:id` still opens scene-first when `findSceneByEntryAuthority({ actionId })` succeeds
- unresolved `/native/action/:id` no longer rewrites to `/compat/action/:id`
- unresolved branch now routes to diagnostic-only `/workbench` with:
  - `reason=CONTRACT_CONTEXT_MISSING`
  - `diag=navigation_native_action_missing_scene_identity`
  - `action_id=<id>`

## decision

```json
{
  "status": "PASS",
  "active_compat_emitter_removed": "useNavigationMenu unresolved native-action -> /compat/action",
  "remaining_dominant_boundary": "guarded router private compat registration shell",
  "backend_semantic_blocker": "none newly indicated by this batch"
}
```
