# Frontend v0.8.1 Scene Registry + Capability + Trace (Draft)

## Scope
- Workbench fallback for menu without action / action without model (no navigation deadlock)
- Scene registry schema validation (dev-visible diagnostics, prod-safe ignore)
- Capability guard (menu disabled + Workbench fallback + StatusPanel variant)
- Trace propagation + HUD/StatusPanel consistency + copy trace
- StatusPanel error shape unified via composable
- Semantic routes (/projects, /projects/:id) with fallback to action/record

## Verification (System-bound)
### Container
- [x] `make verify.portal.recordview_hud_smoke.container` (PASS, 2026-02-04)
  - Artifacts: `/mnt/artifacts/codex/portal-shell-v0_7-ui/20260204T052536`
- [x] `make verify.portal.ui.v0_7.container` (PASS, 2026-02-04)
  - Artifacts: `/mnt/artifacts/codex/portal-shell-v0_6/20260204T052552`
  - Artifacts: `/mnt/artifacts/codex/portal-shell-v0_7-ui/20260204T052555`

## Notes
- No module upgrade required (frontend-only + scripts).
- Fallback strategy: Workbench for missing action/model or missing capability.
- Scene registry validation is dev-visible; prod ignores invalid scenes.
