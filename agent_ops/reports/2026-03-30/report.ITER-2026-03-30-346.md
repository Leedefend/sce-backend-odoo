# ITER-2026-03-30-346 Report

## Summary

- Preserved native preview `route` metadata in `smart_core` release-navigation projection, with fallback to policy scene routes for scene-only preview menus.
- Extended frontend menu resolution so scene-only preview menus can use backend-provided route fallback when no `action_id` is available.
- Re-ran the preview usability smoke after backend/frontend restart and reached 21/21 PASS for demo PM preview menus.

## Changed Files

- `agent_ops/tasks/ITER-2026-03-30-346.yaml`
- `addons/smart_core/delivery/menu_service.py`
- `addons/smart_core/tests/test_delivery_menu_service_native_preview.py`
- `frontend/apps/web/src/views/MenuView.vue`
- `frontend/apps/web/src/app/resolvers/menuResolver.ts`
- `frontend/apps/web/src/app/resolvers/menuResolverCore.js`
- `scripts/verify/release_navigation_preview_menu_usability_smoke.mjs`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-30-346.yaml` -> PASS
- `python3 -m unittest discover -s addons/smart_core/tests -p 'test_delivery_menu_service_native_preview.py'` -> PASS
- `pnpm -C frontend/apps/web typecheck:strict` -> PASS
- `node scripts/verify/release_navigation_preview_menu_usability_smoke.mjs` -> PASS

## Risk Analysis

- Risk level remained low.
- The backend change is additive metadata passthrough only; it does not alter business semantics, ACL, or financial logic.
- A residual UX alignment issue remains: some portal-labeled preview entries still resolve to `/s/project.management`, which is usable but may not yet match the label semantics perfectly.

## Rollback

- `git restore agent_ops/tasks/ITER-2026-03-30-346.yaml`
- `git restore addons/smart_core/delivery/menu_service.py`
- `git restore addons/smart_core/tests/test_delivery_menu_service_native_preview.py`
- `git restore frontend/apps/web/src/views/MenuView.vue`
- `git restore frontend/apps/web/src/app/resolvers/menuResolver.ts`
- `git restore frontend/apps/web/src/app/resolvers/menuResolverCore.js`
- `git restore scripts/verify/release_navigation_preview_menu_usability_smoke.mjs`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`
- `git restore agent_ops/reports/2026-03-30/report.ITER-2026-03-30-346.md`
- `git restore agent_ops/state/task_results/ITER-2026-03-30-346.json`

## Next Suggestion

- Start a semantic alignment batch for preview menu target meanings, especially `工作台 / 生命周期驾驶舱 / 能力矩阵`, so their final landing pages match the published menu labels instead of only satisfying minimum openability.
