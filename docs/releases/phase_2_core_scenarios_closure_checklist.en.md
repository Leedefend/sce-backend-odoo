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
- [ ] All 4 core scenarios are reachable from main navigation
- [ ] `projects.ledger` can navigate into `project.management`
- [ ] Default and fallback routes are available for each core scenario

### B. Contract Completeness
- [ ] `my_work.workspace` includes todo/my projects/quick links/risk summary
- [ ] `projects.ledger` includes list/filter/search/enter-console action
- [ ] `project.management` includes 7 blocks: Header/Metrics/Progress/Contract/Cost/Finance/Risk
- [ ] Business workbench exposes contract/cost/fund core entries

### C. Roles and Visibility
- [ ] Project manager role can access all 4 core scenarios
- [ ] Finance collaborator role can access fund-related scenarios
- [ ] Management viewer role can see dashboard metrics blocks

### D. Runtime Stability
- [ ] Two consecutive `system.init` calls produce stable scene structures
- [ ] `ui.contract` is available in both user/hud modes
- [ ] No blank page / unresolved action on key navigation entries

## 4. Suggested Verification Commands
- `make verify.phase_next.evidence.bundle`
- `make verify.scene.catalog.governance.guard`
- `make verify.project.form.contract.surface.guard`

## 5. Deliverables
- Scenario closure report (suggested: `artifacts/release/phase2_core_scenarios_closure.md`)
- Key verification artifacts (backend + scene governance)

## 6. Exit Criteria
- All checklist items complete
- Phase 2 status updated to `DONE` in execution board
- Phase 3 (role/permission system) officially started

