# FE Router Compat Shell Shrink Recheck Scan BB v1

## scope

- inspect only the recent residual surfaces adjacent to the completed router compat shell shrink
- do not rescan the whole repository
- list candidates only; do not classify or conclude implementation priority

## candidates

- `frontend/apps/web/src/router/index.ts`
  - `/compat/action/:actionId`
  - `/compat/form/:model/:id`
  - `/compat/record/:model/:id`
  - candidate status: retained compatibility entry registration, but now redirect-only rather than shell-page ownership
- `frontend/apps/web/src/app/resolvers/sceneRegistry.ts`
  - still retains `NATIVE_UI_CONTRACT_ROUTE_PREFIXES`
  - candidate status: adjacent legacy fallback path

## notes

- this scan stayed bounded to the recent residual surfaces adjacent to the completed router compat shell shrink
- router compat entries remain structurally present, but no longer mount dedicated compat shell pages
- no new backend semantic blocker is indicated by this bounded scan
- no implementation conclusion is made in this scan stage
