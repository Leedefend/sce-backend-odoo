# Frontend v0.7 UI Hardening Notes (Draft)

## Scope
- UX hardening for verification-grade UI (no contract changes)
- RecordView status clarity + HUD + footer meta
- Guard utilities to prevent groups-related crashes

## Verification (System-bound)
### Gate Sequence (Container Plane)
1. `make verify.portal.view_state`
2. `make verify.portal.guard_groups`
3. `make verify.portal.fe_smoke.container`
4. `make verify.portal.v0_6.container`
5. `make verify.portal.recordview_hud_smoke.container`
6. `make verify.portal.ui.v0_7.container`

### Gate Command (template)
```
make verify.portal.ui.v0_7.container \
  DB_NAME=sc_demo \
  MVP_MODEL=project.project \
  ROOT_XMLID=smart_construction_core.menu_sc_root \
  E2E_LOGIN=svc_project_ro \
  E2E_PASSWORD='***' \
  ARTIFACTS_DIR=artifacts/codex/portal-shell-v0_7-ui/<TIMESTAMP>
```

### Verification Output (2026-02-03)
- [x] `make verify.portal.view_state` (PASS)
- [x] `make verify.portal.guard_groups` (PASS)
- [x] `make verify.portal.fe_smoke.container DB_NAME=sc_demo E2E_LOGIN=svc_project_ro E2E_PASSWORD=***` (PASS)
- [x] `make verify.portal.v0_6.container DB_NAME=sc_demo MVP_MODEL=project.project ROOT_XMLID=smart_construction_core.menu_sc_root E2E_LOGIN=svc_project_ro E2E_PASSWORD=*** ARTIFACTS_DIR=artifacts/codex/portal-shell-v0_6/20260203T074434` (PASS)
- [x] `make verify.portal.recordview_hud_smoke.container DB_NAME=sc_demo MVP_MODEL=project.project ROOT_XMLID=smart_construction_core.menu_sc_root E2E_LOGIN=svc_project_ro E2E_PASSWORD=*** ARTIFACTS_DIR=artifacts/codex/portal-shell-v0_7-ui/20260203T074455` (PASS)

## Evidence (Artifacts)
- v0.6 write regression: artifacts/codex/portal-shell-v0_6/20260203T074434/
- HUD smoke: artifacts/codex/portal-shell-v0_7-ui/20260203T074455/

## Manual UX Verification (Phase 7)
- [ ] Loading state visible
- [ ] Empty state distinct
- [ ] Error shows code + trace_id
- [ ] Edit/Save/Cancel behavior clear
- [ ] HUD shows model/record_id/trace_id

## Screenshots (attach)
- List page (empty or data)
- Record page (HUD + status bar)
