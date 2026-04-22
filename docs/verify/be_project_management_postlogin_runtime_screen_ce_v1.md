# BE Project Management Post-Login Runtime Screen CE

## Goal

Classify the bounded post-login `/s/project.management` failure after the
verifier converged past login submit, and decide whether the remaining blocker
belongs to backend scene-orchestration semantic supply or frontend generic
consumer misuse.

## Screening Scope

1. Reuse the latest bounded verifier artifact instead of re-opening the full
   browser-debug chain.
2. Inspect the `system.init` / navigation-tree / scene-ready supply boundary for
   the same login context.
3. Freeze the next implementation battlefield to one layer only.

## Evidence

1. Latest bounded browser artifact:
   - `artifacts/codex/project-dashboard-primary-entry-browser-smoke/20260420T061244Z/`
   - `login_submit_result.json` shows login succeeds and navigates to
     `/s/project.management`.
   - The first post-login surface already reports `暂无导航数据` and
     `菜单树为空，请尝试刷新初始化。`

2. Live `system.init` / `system.init.inspect` check under `wutao / demo`:
   - login token acquisition succeeds
   - both intents return `ok=true`
   - `active_scene_key=portal.dashboard`
   - `nav_menu_count=0`
   - `nav_release_count=0`
   - `scene_ready_contract_v1.scenes` includes a nested `scene.key=project.management`
     row, but that row has no top-level `scene_key`, no `entry`, and no `target`

3. Frontend generic consumer behavior is consistent with the empty-nav contract:
   - [AppShell.vue](/mnt/e/sc-backend-odoo/frontend/apps/web/src/layouts/AppShell.vue:152)
     renders `暂无导航数据` when `initStatus === 'ready' && !menuCount`
   - [session.ts](/mnt/e/sc-backend-odoo/frontend/apps/web/src/stores/session.ts:1108)
     only errors when nav is missing entirely; a present-but-empty nav contract
     still lands in ready state with empty `menuTree` / `releaseNavigationTree`

## Screen Result

Classification: backend `scene_orchestration` semantic-supply gap.

Why this is not a frontend-primary issue:
- the frontend reaches the declared scene route only after successful login
- the empty navigation symptom is already present in the bounded post-login
  snapshot before any deeper scene interaction
- the startup contract itself declares `portal.dashboard` as active and returns
  zero navigation rows, so the frontend is consuming an already-degraded
  startup/orchestration surface

What remains missing on the backend side:
- a startup/runtime navigation contract that is non-empty for this role/session
- a scene-ready row for `project.management` that projects usable entry/target
  semantics instead of only a nested `scene.key`

## Decision

The next batch should stay on the backend battlefield and target the
`scene_orchestration` layer only. It should repair post-login startup/runtime
semantic supply for `project.management` and the associated navigation surface,
without introducing frontend model-specific branching.
