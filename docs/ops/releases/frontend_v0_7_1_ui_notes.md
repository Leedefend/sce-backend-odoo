# Frontend v0.7.1 UI Notes (Draft)

## Scope
- v0.7.1 polish pass for de-odooify list/action/record UX
- HUD trace context improvements
- StatusPanel error cards include error_code + trace_id

## Verification (System-bound)
### Gate Sequence (Container Plane)
1. `make verify.portal.ui.v0_7.container`
2. `make verify.portal.guard_groups`
3. `make verify.portal.recordview_hud_smoke.container`

### Gate Command (template)
```
make verify.portal.ui.v0_7.container \
  DB_NAME=sc_demo \
  MVP_MODEL=project.project \
  ROOT_XMLID=smart_construction_core.menu_sc_root \
  E2E_LOGIN=svc_project_ro \
  E2E_PASSWORD='***' \
  ARTIFACTS_DIR=artifacts/codex/portal-shell-v0_7_1/<TIMESTAMP>
```

### Verification Output (2026-02-04)
- [x] `make verify.portal.ui.v0_7.container` (PASS)
- [x] `make verify.portal.guard_groups` (PASS)
- [x] `make verify.portal.recordview_hud_smoke.container` (PASS)

## Evidence (Artifacts)
- v0.7 UI gate: `artifacts/codex/portal-shell-v0_6/20260204T011905/`
- HUD smoke: `artifacts/codex/portal-shell-v0_7-ui/20260204T011907/`

## Note
- Semantic routing MVP evidence removed; frontend now renders strictly from backend-provided data.

## Manual UX Verification
- [ ] Loading state visible
- [ ] Empty state distinct
- [ ] Error shows code + trace_id
- [ ] Edit/Save/Cancel behavior clear
- [ ] HUD shows last_intent/latency/write_mode
