# FE SceneRegistry Compat Prefix Shrink AS v1

## scope

- prefer `entry_target.route` as the primary public scene route source inside `sceneRegistry`
- retain `/compat/*` route normalization only as a bounded legacy fallback
- keep frontend consumption scene-first without widening path scope beyond `sceneRegistry.ts`

## implementation

- `sceneRegistry` now prefers backend-provided `meta.target.entry_target.route` as the public source of `scene.route`
- `/compat/action/*`, `/compat/form/*`, `/compat/record/*` normalization remains only when the incoming payload still lacks a public `entry_target.route`
- existing scene-first consumers continue to read `scene.route`, but that route is now sourced from the public scene entry contract first

## verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-20-FE-SCENEREGISTRY-COMPAT-PREFIX-SHRINK-AS.yaml` → `PASS`
- `pnpm -C frontend/apps/web typecheck:strict` → `PASS`
- `pnpm -C frontend/apps/web build` → `PASS` with existing chunk-size warning only
- `git diff --check -- agent_ops/tasks/ITER-2026-04-20-FE-SCENEREGISTRY-COMPAT-PREFIX-SHRINK-AS.yaml docs/verify/fe_sceneRegistry_compat_prefix_shrink_as_v1.md docs/ops/iterations/delivery_context_switch_log_v1.md frontend/apps/web/src/app/resolvers/sceneRegistry.ts` → `PASS`

## decision

```json
{
  "status": "PASS",
  "scene_route_primary_source": "entry_target.route",
  "compat_prefix_recognition": "legacy fallback only",
  "residual_boundary": "guarded router compat registration shell and unresolved native-action fallback",
  "backend_semantic_blocker": "none newly indicated by this implementation batch"
}
```
