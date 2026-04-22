# FE Menu Entry Target Consumer Implement BO v1

## scope

- prefer backend `entry_target` in menu consumer
- keep `route` as compatibility fallback
- keep scope bounded to menu consumer and its typed node shape

## verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-20-FE-MENU-ENTRY-TARGET-CONSUMER-IMPLEMENT-BO.yaml` → `PASS`
- `pnpm -C frontend/apps/web typecheck:strict` → `PASS`
- `pnpm -C frontend/apps/web build` → `PASS` with existing chunk-size warning only
- `git diff --check -- agent_ops/tasks/ITER-2026-04-20-FE-MENU-ENTRY-TARGET-CONSUMER-IMPLEMENT-BO.yaml docs/verify/fe_menu_entry_target_consumer_implement_bo_v1.md docs/ops/iterations/delivery_context_switch_log_v1.md frontend/apps/web/src/composables/useNavigationMenu.ts frontend/apps/web/src/types/navigation.ts` → `PASS`

## implementation

- menu node type now includes formal `entry_target`
- `useNavigationMenu` now resolves navigation in this order:
  - `entry_target` first
  - legacy `route` second
- scene-shaped `entry_target` directly yields scene-first menu routes
- compatibility-shaped `entry_target` still falls back through existing route normalization behavior
- existing `route` fallback remains in place for staged compatibility

## decision

```json
{
  "status": "PASS",
  "menu_consumer_now_entry_target_first": true,
  "frontend_native_action_reinterpretation_demoted": "compatibility fallback only",
  "remaining_gap": "needs one more bounded recheck to verify whether menu boundary is now fully aligned",
  "backend_semantic_blocker": "none"
}
```
