# FE Router Compat Shell Shrink BA v1

## scope

- shrink router compat shell routes only
- keep route names for compatibility entry calls
- redirect to scene-first or diagnostic-only workbench instead of mounting compat shell components

## verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-20-FE-ROUTER-COMPAT-SHELL-SHRINK-BA.yaml` → `PASS`
- `pnpm -C frontend/apps/web typecheck:strict` → `PASS`
- `pnpm -C frontend/apps/web build` → `PASS` with existing chunk-size warning only
- `git diff --check -- agent_ops/tasks/ITER-2026-04-20-FE-ROUTER-COMPAT-SHELL-SHRINK-BA.yaml docs/verify/fe_router_compat_shell_shrink_ba_v1.md docs/ops/iterations/delivery_context_switch_log_v1.md frontend/apps/web/src/router/index.ts` → `PASS`

## implementation

- router keeps the named compatibility entry points:
  - `name: 'action'`
  - `name: 'record'`
  - `name: 'model-form'`
- those three compat routes no longer mount `ActionViewShell` or `ContractFormPage` from router registration
- compat route records now redirect immediately:
  - resolved scene identity → target scene route
  - unresolved identity → diagnostic-only `/workbench`
- previous `beforeEach` shell-resolution branches for `action/record/model-form` were removed from router guard ownership

## decision

```json
{
  "status": "PASS",
  "dominant_compat_boundary_shrunk": "router compat shell registration no longer owns shell-page rendering",
  "compat_route_names_preserved": true,
  "remaining_secondary_boundary": "legacy-only sceneRegistry compat prefix fallback",
  "backend_semantic_blocker": "none newly indicated by this batch"
}
```
