# FE SceneRegistry Compat Prefix Shrink Recheck Scan AT v1

## scope

- inspect only the recent residual surfaces adjacent to the completed `sceneRegistry` shrink
- do not rescan the whole repository
- list candidates only; do not classify or conclude implementation priority

## candidates

- `frontend/apps/web/src/app/resolvers/sceneRegistry.ts`
  - still contains `NATIVE_UI_CONTRACT_ROUTE_PREFIXES`
  - after batch `AS`, this no longer drives the primary `scene.route` source and is now a bounded legacy fallback candidate
- `frontend/apps/web/src/router/index.ts`
  - still registers guarded private compat shell routes:
    - `/compat/action/:actionId`
    - `/compat/form/:model/:id`
    - `/compat/record/:model/:id`
  - candidate status: residual router shell, not yet classified as dominant
- `frontend/apps/web/src/composables/useNavigationMenu.ts`
  - unresolved `/native/action/:id` still rewrites to `/compat/action/:id`
  - candidate status: unresolved native-action fallback surface

## notes

- this scan stayed bounded to the recent residual surfaces adjacent to the completed `sceneRegistry` shrink
- no new backend semantic blocker is indicated by this bounded scan
- no implementation conclusion is made in this scan stage
