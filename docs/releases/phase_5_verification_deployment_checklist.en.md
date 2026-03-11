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
- [ ] Release-critical verify chain passes (scene/catalog/runtime/contract)
- [ ] Core business path smoke tests pass
- [ ] Key role paths (PM/Finance/Management) pass

### B. Contract and Consistency
- [ ] `system.init` and `ui.contract` are stable in both user/hud modes
- [ ] Delivery policy and runtime navigation output are aligned
- [ ] No release-blocking drift between exports and runtime

### C. Deployment Readiness
- [ ] `dev/test/prod` environment parameter matrix is complete
- [ ] Docker deployment flow is repeatable
- [ ] Module install/upgrade/rollback scripts are executable

### D. Documentation Completeness
- [ ] Deployment guide: `docs/deploy/deployment_guide_v1.md`
- [ ] Demo script: `docs/demo/system_demo_v1.md`
- [ ] Acceptance checklist: `docs/releases/user_acceptance_checklist.md`

### E. Evidence and Archival
- [ ] Release verification evidence archived in unified location
- [ ] Key artifacts are traceable (command/time/result)
- [ ] Release conclusion (pass/block) is explicitly recorded

## 4. Suggested Verification Commands
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

