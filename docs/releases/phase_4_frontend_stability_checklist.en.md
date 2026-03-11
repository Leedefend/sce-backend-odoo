# SCEMS v1.0 Phase 4: Frontend Stability Checklist

## 1. Goal
Unify page framework, block components, and interaction conventions to make V1 frontend stable, predictable, and trainable.

## 2. Coverage
- Scene pages: `SceneView` / `WorkbenchView` / key business views
- Contract-driven pages: `ui.contract` driven views
- Block components: Header / Metric / Progress / Table / Alert

## 3. Required Items

### A. Page Framework Consistency
- [x] Core scenario pages follow a unified layout container and spacing rules
- [x] Title/breadcrumb/back behavior is consistent
- [x] Empty/loading/error states are consistent

### B. Block Component Consistency
- [x] 7 blocks share consistent visual hierarchy and data presentation
- [x] Metric/table/alert components follow unified props and data contract patterns
- [x] Missing-data fallback style and copy are consistent

### C. Interaction Consistency
- [x] Primary action button placement and naming are consistent
- [x] Key navigation path (`ledger -> management`) is consistent
- [x] Search/filter/sort feedback is consistent (no silent failures)

### D. Cross-Mode Consistency (user/hud)
- [x] Key pages render in both user and hud modes
- [x] contract_mode differences are explainable and non-breaking
- [x] No critical component loss after mode switch

### E. Stability and Observability
- [x] No severe frontend console errors during key operations
- [x] Key frontend smoke scripts pass
- [x] Critical failures are diagnosable (sufficient logs/errors)

## 4. Suggested Verification Commands
- `make verify.frontend.build`
- `make verify.frontend.typecheck.strict`
- `make verify.frontend.lint.src`
- `make verify.frontend.page_contract.runtime_universal.guard`
- `make verify.frontend.page_block_registry_guard`
- `make verify.frontend.page_renderer_default_guard`
- `make verify.frontend.page_block_renderer_smoke`
- `make verify.frontend.runtime_navigation_hud.guard`
- `make verify.page_contract.role_orchestration_variance.guard`
- `make verify.scene.hud.trace.smoke`
- `make verify.scene.meta.trace.smoke`
- `make verify.frontend.contract_runtime.guard`
- `make verify.frontend.contract_route.guard`
- `make verify.frontend.home_layout_section_coverage.guard`
- `make verify.frontend.home_orchestration_consumption.guard`
- `make verify.frontend.page_contract_boundary.guard`
- `make verify.list.surface.clean`
- `make verify.frontend.search_groupby_savedfilters.guard`
- `make verify.ui.product.stability`
- `make verify.phase_next.evidence.bundle`

## 5. Deliverables
- Frontend stability report (suggested: `artifacts/release/phase4_frontend_stability.md`)
- Key page screenshots/recordings (suggested under `artifacts/release/`)

## 6. Exit Criteria
- All checklist items complete
- Core scenarios are demo-stable in user/hud modes
- Execution board Phase 4 updated to `DONE`
