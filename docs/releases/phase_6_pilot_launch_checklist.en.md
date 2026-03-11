# SCEMS v1.0 Phase 6: Pilot and Launch Checklist

## 1. Goal
Complete pilot run, feedback closure, and official launch to ensure v1.0 is production-stable.

## 2. Coverage
- Pilot organization and scenarios
- Final pre-launch gates
- Official launch execution
- Post-launch monitoring and follow-up

## 3. Required Items

### A. Pilot Preparation
- [x] Pilot scope, org units, and role participants are defined
- [x] Pilot data set is ready (project/contract/cost/fund/risk samples)
- [x] Pilot script and issue-reporting channel are defined

### B. Pilot Execution
- [ ] Core business path is fully rehearsed end-to-end
- [ ] Key roles (PM/Finance/Management) complete validation
- [ ] Pilot issues are classified by severity and closed

### C. Launch Gates
- [ ] Exit criteria for Phase 0~5 are all satisfied
- [ ] No P0 launch-blocking defects remain
- [ ] Final release review concludes "go-live approved"

### D. Launch Execution
- [ ] Release window, rollback window, and owners are confirmed
- [ ] Release steps executed by script and recorded
- [ ] Post-release key feature spot-check passes

### E. Post-launch Operation
- [ ] Key indicators are healthy in first 24 hours
- [ ] User feedback intake and triage flow is active
- [ ] v1.0 post-launch summary is completed

## 4. Suggested Verification Commands
- `make verify.phase_next.evidence.bundle`
- `make verify.scene.catalog.governance.guard`
- `make verify.runtime.surface.dashboard.strict.guard`

## 5. Deliverables
- Pilot report (suggested: `artifacts/release/phase6_pilot_report.md`)
- Launch record (suggested: `docs/ops/releases/current/scems_v1_0_launch.md`)
- Post-launch review (suggested: `docs/releases/scems_v1_0_post_launch_review.md`)

## 6. Exit Criteria
- All checklist items complete
- v1.0 launch completed and auditable
- Execution board Phase 6 updated to `DONE`
