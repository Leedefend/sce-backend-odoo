# ITER-2026-03-30-345 Report

## Summary

- Fixed `/m/:menu_id` resolution so preview release-navigation menus resolve against the active published navigation tree instead of only the legacy menu tree.
- Added cold-start retry triggers in `MenuView` so direct menu routes re-resolve after `system.init` loads the navigation trees.
- Tightened the preview usability smoke so `Menu resolve failed`, `menu not found`, and contract-context fallback pages are recorded as real failures.

## Changed Files

- `agent_ops/tasks/ITER-2026-03-30-345.yaml`
- `frontend/apps/web/src/views/MenuView.vue`
- `frontend/apps/web/src/app/resolvers/menuResolver.ts`
- `frontend/apps/web/src/app/resolvers/menuResolverCore.js`
- `scripts/verify/release_navigation_preview_menu_usability_smoke.mjs`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-30-345.yaml` -> PASS
- `pnpm -C frontend/apps/web typecheck:strict` -> PASS
- `node scripts/verify/release_navigation_preview_menu_usability_smoke.mjs` -> FAIL (收敛到仅剩 `menu_id=312` 一项 scene-only 预发布菜单回退到 workbench)

## Risk Analysis

- Risk level remained low.
- The batch only changed frontend route resolution and smoke assertions; no backend contract semantics were changed here.
- The new smoke behavior is intentionally stricter, so it may surface additional real failures in future batches rather than hiding them as false positives.

## Rollback

- `git restore agent_ops/tasks/ITER-2026-03-30-345.yaml`
- `git restore frontend/apps/web/src/views/MenuView.vue`
- `git restore frontend/apps/web/src/app/resolvers/menuResolver.ts`
- `git restore frontend/apps/web/src/app/resolvers/menuResolverCore.js`
- `git restore scripts/verify/release_navigation_preview_menu_usability_smoke.mjs`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`
- `git restore agent_ops/reports/2026-03-30/report.ITER-2026-03-30-345.md`
- `git restore agent_ops/state/task_results/ITER-2026-03-30-345.json`

## Next Suggestion

- Preserve backend native preview routes for scene-only menus, then let `MenuView` use route fallback when `scene_key` exists but no `action_id` is available.
