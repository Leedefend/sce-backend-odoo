# SCEMS v1.0 Phase 5: Verification and Deployment Checklist

## 1. Goal
Complete release-level verification and deployment readiness to ensure the system is verifiable, deployable, and rollback-ready.

## 2. Coverage
- Backend verification chain
- Frontend build and quality gates
- Deployment scripts and environment readiness
- Release evidence and archival

## 3. Required Items

### A. Verification Closure
- [x] Release-critical verify chain passes (scene/catalog/runtime/contract)
- [x] Core business path smoke tests pass
- [x] Key role paths (PM/Finance/Management) pass
- [x] Release-grade demo seed is loaded and accepted (`demo.load.release` + `verify.demo.release.seed`)

### B. Contract and Consistency
- [x] `system.init` and `ui.contract` are stable in both user/hud modes
- [x] Delivery policy and runtime navigation output are aligned
- [x] No release-blocking drift between exports and runtime

### C. Deployment Readiness
- [x] `dev/test/prod` environment parameter matrix is complete
- [x] Docker deployment flow is repeatable
- [x] Module install/upgrade/rollback scripts are executable

### D. Documentation Completeness
- [x] Deployment guide: `docs/deploy/deployment_guide_v1.en.md`
- [x] Demo script: `docs/demo/system_demo_v1.en.md`
- [x] Acceptance checklist: `docs/releases/user_acceptance_checklist.en.md`

### E. Evidence and Archival
- [x] Release verification evidence archived in unified location
- [x] Key artifacts are traceable (command/time/result)
- [x] Release conclusion (pass/block) is explicitly recorded

## 4. Suggested Verification Commands
- `make demo.load.release DB_NAME=sc_demo`
- `make verify.demo.release.seed DB_NAME=sc_demo`
- `make verify.phase_next.evidence.bundle`
- `make verify.runtime.surface.dashboard.strict.guard`
- `make verify.project.form.contract.surface.guard`
- `make verify.scene.catalog.governance.guard`

## 5. Deliverables
- Phase 5 report (suggested: `artifacts/release/phase5_verification_deployment.md`)
- Verification evidence package (backend artifacts + scene governance + frontend quality)

## 6. Exit Criteria
- All checklist items complete
- Deployment/rollback rehearsal passes
- Execution board Phase 5 updated to `DONE`
