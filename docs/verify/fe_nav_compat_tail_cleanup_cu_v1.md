# FE Nav Compat Tail Cleanup CU

## Goal

Reduce frontend-only compatibility-tail usability degradation on the scenarized
navigation menu without reopening backend menu boundary work.

## Verification

1. `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-20-FE-NAV-COMPAT-TAIL-CLEANUP-CU.yaml`
   - PASS
2. `pnpm -C frontend/apps/web typecheck:strict`
   - PASS
3. `pnpm -C frontend/apps/web build`
   - PASS
   - Existing build warnings only.
4. `git diff --check -- agent_ops/tasks/ITER-2026-04-20-FE-NAV-COMPAT-TAIL-CLEANUP-CU.yaml docs/verify/fe_nav_compat_tail_cleanup_cu_v1.md docs/ops/iterations/delivery_context_switch_log_v1.md frontend/apps/web/src/composables/useNavigationMenu.ts frontend/apps/web/src/components/MenuTree.vue`
   - PASS

## Outcome

- menu directories keep directory semantics instead of inheriting the first
  descendant route as a pseudo direct-entry path
- unresolved native-action routes no longer bounce the user to `/workbench`
  from menu normalization
- renderer-side label handling is reduced to generic cleanup instead of local
  business-role rewriting
- disabled menu copy now stays user-facing and stable rather than exposing raw
  reason tokens
