# Frontend v0.3 Release Notes (Draft)

## Scope
- [x] Action view status machine (loading/empty/error)
- [x] Record view status machine (loading/empty/error)
- [x] List rendering extracted to ListPage
- [ ] MVP menu validated (menu_id/action_id recorded)
- [ ] Record view manual verification

## Verification
Commands run:
- [ ] `make fe.dev` (or `pnpm -C frontend dev`)
- [ ] Backend logs checked if needed
- [x] `BASE_URL=http://localhost:8070 DB_NAME=sc_demo scripts/diag/fe_smoke.sh` (401 without token, trace_id=6f3728e5866b)
- [x] `BASE_URL=http://localhost:8070 DB_NAME=sc_demo AUTH_TOKEN=... scripts/diag/fe_smoke.sh` (401 invalid token, trace_id=263a1fc09060)
- [x] `node scripts/verify/fe_view_state_smoke.js` (PASS)

Manual flow:
- [ ] Login → app.init
- [ ] Sidebar menu → `/m/:menuId` → `/a/:actionId`
- [ ] List loads real data
- [ ] Row click → `/r/:model/:id`
- [ ] Back returns to list
- [ ] Refresh preserves session

## MVP Trace
- menu_id:
- action_id:
- model:
- view_mode:
- record_id:
- nav_version:
- trace_id (if error):

## UI Evidence
- List page screenshot:
- Record page screenshot:

## Evidence
- [ ] Screenshot or log snippet
- [ ] MVP menu_id / action_id / view_mode
- [ ] Trace IDs (if error reproduced)
