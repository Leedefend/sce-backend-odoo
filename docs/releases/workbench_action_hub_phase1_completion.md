# Workbench Action Hub Phase 1 Completion

## Scope

Phase 1 focuses on structural convergence of `portal.dashboard` into an action-first workspace while keeping platform core mechanisms unchanged.

## Completed

- Enforced the primary page protocol on workbench rendering (`page_orchestration_v1`) with explicit action-first section order.
- Converged workbench main layout into:
  - `today_focus` (primary)
  - `analysis` + `quick_entries` (secondary)
  - `hero` (trailing context)
- Unified provider and builder defaults so section semantics do not drift between different data paths.
- Removed primary-zone dependence on `advice_fold` and reduced data density in first-screen cards.
- Hardened business-first semantics for `today_actions` and `risk.actions` with fallback kept as secondary.
- Added source badges (`业务` / `兜底`) on action and risk cards for factual transparency.
- Limited quick-entry block item count to keep workbench focused as an action hub.

## Verification

- `make verify.frontend.typecheck.strict`
- `make verify.frontend.build`
- `make verify.project.dashboard.contract`
- `make deploy.prod.sim.oneclick ENV=test ENV_FILE=.env.prod.sim COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim`

## Known follow-up (Phase 2)

- Expand PM-visible business records by fixing role assignment + demo owner coverage.
- Increase factual business action coverage to reduce fallback proportion.
- Add role template tuning for PM / Finance / Owner ranking differences.
