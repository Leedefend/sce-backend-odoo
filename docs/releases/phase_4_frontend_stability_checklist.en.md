# SCEMS v1.0 Phase 4: Frontend Stability Checklist

## 1. Goal
Unify page framework, block components, and interaction conventions to make V1 frontend stable, predictable, and trainable.

## 2. Coverage
- Scene pages: `SceneView` / `WorkbenchView` / key business views
- Contract-driven pages: `ui.contract` driven views
- Block components: Header / Metric / Progress / Table / Alert

## 3. Required Items

### A. Page Framework Consistency
- [ ] Core scenario pages follow a unified layout container and spacing rules
- [ ] Title/breadcrumb/back behavior is consistent
- [ ] Empty/loading/error states are consistent

### B. Block Component Consistency
- [x] 7 blocks share consistent visual hierarchy and data presentation
- [x] Metric/table/alert components follow unified props and data contract patterns
- [ ] Missing-data fallback style and copy are consistent

### C. Interaction Consistency
- [ ] Primary action button placement and naming are consistent
- [ ] Key navigation path (`ledger -> management`) is consistent
- [ ] Search/filter/sort feedback is consistent (no silent failures)

### D. Cross-Mode Consistency (user/hud)
- [ ] Key pages render in both user and hud modes
- [ ] contract_mode differences are explainable and non-breaking
- [ ] No critical component loss after mode switch

### E. Stability and Observability
- [ ] No severe frontend console errors during key operations
- [x] Key frontend smoke scripts pass
- [ ] Critical failures are diagnosable (sufficient logs/errors)

## 4. Suggested Verification Commands
- `make verify.frontend.build`
- `make verify.frontend.typecheck.strict`
- `make verify.frontend.lint.src`
- `make verify.frontend.page_contract.runtime_universal.guard`
- `make verify.frontend.page_block_registry_guard`
- `make verify.frontend.page_renderer_default_guard`
- `make verify.frontend.page_block_renderer_smoke`
- `make verify.phase_next.evidence.bundle`

## 5. Deliverables
- Frontend stability report (suggested: `artifacts/release/phase4_frontend_stability.md`)
- Key page screenshots/recordings (suggested under `artifacts/release/`)

## 6. Exit Criteria
- All checklist items complete
- Core scenarios are demo-stable in user/hud modes
- Execution board Phase 4 updated to `DONE`
