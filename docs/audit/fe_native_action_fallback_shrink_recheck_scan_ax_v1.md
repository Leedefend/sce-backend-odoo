# FE Native Action Fallback Shrink Recheck Scan AX v1

## scope

- inspect only the recent residual surfaces adjacent to the completed native-action fallback shrink
- do not rescan the whole repository
- list candidates only; do not classify or conclude implementation priority

## candidates

- `frontend/apps/web/src/router/index.ts`
  - still registers guarded private compat shell routes:
    - `/compat/action/:actionId`
    - `/compat/form/:model/:id`
    - `/compat/record/:model/:id`
  - candidate status: strong residual router shell
- `frontend/apps/web/src/app/resolvers/sceneRegistry.ts`
  - still retains `NATIVE_UI_CONTRACT_ROUTE_PREFIXES`
  - candidate status: secondary legacy fallback path
- `frontend/apps/web/src/composables/useNavigationMenu.ts`
  - still recognizes `/native/action/:id`, but unresolved branch no longer emits `/compat/action/:id`
  - candidate status: no longer an active private compat emitter in this bounded scan

## notes

- this scan stayed bounded to the recent residual surfaces adjacent to the completed native-action fallback shrink
- no new backend semantic blocker is indicated by this bounded scan
- no implementation conclusion is made in this scan stage
