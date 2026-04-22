# FE SceneRegistry Legacy Compat Fallback Shrink Recheck Scan BF v1

## scope

- inspect only the recent residual surfaces adjacent to the completed sceneRegistry fallback shrink
- do not rescan the whole repository
- list candidates only; do not classify or conclude implementation priority

## candidates

- `frontend/apps/web/src/app/resolvers/sceneRegistry.ts`
  - still retains bounded `isLegacyCompatRoute(...)`
  - candidate status: residual legacy compat interpretation, but now only inside scene-ready conversion
- `frontend/apps/web/src/router/index.ts`
  - `/compat/action/:actionId`
  - `/compat/form/:model/:id`
  - `/compat/record/:model/:id`
  - candidate status: redirect-only compatibility entry registration

## notes

- this scan stayed bounded to the recent residual surfaces adjacent to the completed sceneRegistry fallback shrink
- no new backend semantic blocker is indicated by this bounded scan
- no implementation conclusion is made in this scan stage
