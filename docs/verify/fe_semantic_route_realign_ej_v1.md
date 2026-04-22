# FE Semantic Route Realign EJ

- Scope:
  - `scripts/verify/fe_semantic_route_smoke.js`
- Change:
  - removed stale assertions against deleted native-prefix implementation details
  - verifier now checks current runtime guarantees in `sceneRegistry.ts`:
    - `resolveSceneRoute(...)` remains the semantic route normalizer
    - legacy compat route detection exists
    - legacy compat route inputs degrade to semantic `defaultRoute`
    - `publicEntryRoute` is preferred ahead of legacy route
    - entry-target parsing still participates in route resolution
    - unified home scene key and route guarantees remain frozen
- Verification:
  - `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-21-VERIFY-SEMANTIC-ROUTE-REALIGN-EJ.yaml`
  - `node scripts/verify/fe_semantic_route_smoke.js`
  - `git diff --check -- agent_ops/tasks/ITER-2026-04-21-VERIFY-SEMANTIC-ROUTE-REALIGN-EJ.yaml scripts/verify/fe_semantic_route_smoke.js docs/verify/fe_semantic_route_realign_ej_v1.md docs/ops/iterations/delivery_context_switch_log_v1.md`
