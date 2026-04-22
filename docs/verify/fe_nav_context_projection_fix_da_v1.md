# FE Nav Context Projection Fix DA

## Goal

Preserve `action_id` while projecting scene-known menu entries from `/m/:menuId`
 to `/s/:sceneKey`.

## Verification

1. `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-20-FE-NAV-CONTEXT-PROJECTION-FIX-DA.yaml`
   - PASS
2. `pnpm -C frontend/apps/web typecheck:strict`
   - PASS
3. `pnpm -C frontend/apps/web build`
   - PASS
   - Existing chunk-size warning only.
4. `BASE_URL=http://127.0.0.1:5174 API_BASE_URL=http://127.0.0.1:8069 DB_NAME=sc_demo E2E_LOGIN=wutao E2E_PASSWORD=demo make verify.portal.unified_system_menu_click_usability_smoke.host`
   - FAIL
   - Artifact: `artifacts/codex/unified-system-menu-click-usability-smoke/20260420T082009Z/summary.json`
   - Frozen result:
     - `leaf_count=31`
     - `fail_count=26`
     - `nav_source=release_tree`
     - `error=menu click usability failures=26`
5. `git diff --check -- agent_ops/tasks/ITER-2026-04-20-FE-NAV-CONTEXT-PROJECTION-FIX-DA.yaml docs/verify/fe_nav_context_projection_fix_da_v1.md docs/ops/iterations/delivery_context_switch_log_v1.md frontend/apps/web/src/app/resolvers/menuResolver.ts frontend/apps/web/src/router/index.ts`
   - PASS

## Result

The targeted projection change passed local frontend gates but did not improve
the real menu click usability smoke.

The latest artifact keeps the overall failure count at 26 and also freezes new
failing ids compared with the previous artifact, so this line stops on
`verify_failed` rather than continuing directly.
