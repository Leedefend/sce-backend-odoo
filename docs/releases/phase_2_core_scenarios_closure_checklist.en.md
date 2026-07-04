# SCEMS v1.0 Phase 2: Core Scenarios Closure Checklist

## 1. Goal
Close the minimum usable loop for the 4 core v1 scenarios to make them demo-ready, verifiable, and deliverable.

## 2. Scenario Scope
- `my_work.workspace`
- `projects.ledger`
- `project.management`
- Business workbench (`contracts.workspace` / `cost.analysis` / `finance.workspace`)

## 3. Required Items

### A. Reachability
- [x] All 4 core scenarios are reachable from main navigation
- [x] `projects.ledger` can navigate into `project.management`
- [x] Default and fallback routes are available for each core scenario

### B. Contract Completeness
- [x] `my_work.workspace` includes todo/my projects/quick links/risk summary
- [x] `projects.ledger` includes list/filter/search/enter-console action
- [x] `project.management` includes 7 blocks: Header/Metrics/Progress/Contract/Cost/Finance/Risk
- [x] Business workbench exposes contract/cost/fund core entries

### C. Roles and Visibility
- [x] Project manager role can access all 4 core scenarios
- [x] Finance collaborator role can access fund-related scenarios
- [x] Management viewer role can see dashboard metrics blocks

### D. Runtime Stability
- [x] Two consecutive `system.init` calls produce stable scene structures
- [x] `ui.contract` is available in both user/hud modes
- [x] No blank page / unresolved action on key navigation entries

## 4. Suggested Verification Commands
- `make verify.phase_next.evidence.bundle`
- `make verify.scene.catalog.governance.guard`
- `make verify.project.form.contract.surface.guard`
- `make verify.release.phase2.core_scenarios_closure.guard`

## 5. Deliverables
- Scenario closure report (suggested: `artifacts/release/phase2_core_scenarios_closure.md`)
- Key verification artifacts (backend + scene governance)

## 6. Exit Criteria
- All checklist items complete
- Phase 2 status updated to `DONE` in execution board
- Phase 3 (role/permission system) officially started
