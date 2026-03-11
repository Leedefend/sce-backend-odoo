# SCEMS v1.0 Phase 1: Navigation Convergence Checklist

## 1. Goal
Ensure `construction_pm_v1` primary navigation, scene configuration, and runtime output are aligned.

## 2. Required Items

### A. Policy Definition
- [ ] `construction_pm_v1` is the sole primary delivery surface
- [ ] Main navigation allowlist is fixed to 7 entries
- [ ] `config.*`, `data.*`, `internal.*` are hidden from primary navigation

### B. Runtime Alignment
- [ ] `system.init` navigation output matches allowlist
- [ ] `system.init` scene list is traceable from navigation
- [ ] `project.management` is directly reachable from navigation

### C. Documentation Alignment
- [ ] Release plan navigation definition matches runtime policy
- [ ] `docs/releases/release_scope_v1.en.md` reflects latest navigation baseline
- [ ] Execution board reflects current Phase 1 status

## 3. Suggested Verification Commands
- `make verify.scene.catalog.governance.guard`
- `make verify.project.form.contract.surface.guard`
- `make verify.runtime.surface.dashboard.strict.guard`

## 4. Deliverables
- Navigation convergence report (suggested: `artifacts/release/phase1_navigation_convergence.md`)
- Runtime evidence artifacts (verify JSON/MD)

## 5. Exit Criteria
- All checklist items complete
- Phase 1 status moved to `DONE`
- Phase 2 tasks created and started

