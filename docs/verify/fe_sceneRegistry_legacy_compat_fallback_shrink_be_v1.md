# FE SceneRegistry Legacy Compat Fallback Shrink BE v1

## scope

- shrink legacy `/compat/*` handling only inside `sceneRegistry.ts`
- retire the global compat prefix normalization baseline
- keep scene-ready route materialization stable and scene-first

## verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-20-FE-SCENEREGISTRY-LEGACY-COMPAT-FALLBACK-SHRINK-BE.yaml` → `PASS`
- `pnpm -C frontend/apps/web typecheck:strict` → `PASS`
- `pnpm -C frontend/apps/web build` → `PASS` with existing chunk-size warning only
- `git diff --check -- agent_ops/tasks/ITER-2026-04-20-FE-SCENEREGISTRY-LEGACY-COMPAT-FALLBACK-SHRINK-BE.yaml docs/verify/fe_sceneRegistry_legacy_compat_fallback_shrink_be_v1.md docs/ops/iterations/delivery_context_switch_log_v1.md frontend/apps/web/src/app/resolvers/sceneRegistry.ts` → `PASS`

## implementation

- removed the global `NATIVE_UI_CONTRACT_ROUTE_PREFIXES` constant from `sceneRegistry`
- removed the global delivery-route normalization helper that interpreted `/compat/*` as a runtime-wide baseline
- retained legacy compat handling only inside `toSceneFromSceneReadyEntry(...)`
  - public `entry_target.route` still wins first
  - when no public route exists and the legacy scene-ready route is `/compat/action/*`, `/compat/form/*`, or `/compat/record/*`, the route falls back to `/s/<sceneKey>`

## decision

```json
{
  "status": "PASS",
  "global_compat_prefix_baseline_retired": true,
  "remaining_compat_behavior": "bounded scene-ready legacy fallback only",
  "backend_semantic_blocker": "none newly indicated by this batch"
}
```
