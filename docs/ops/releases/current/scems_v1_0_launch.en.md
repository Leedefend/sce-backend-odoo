# SCEMS v1.0 Launch Record

## 1. Release Batch Information
- Version: `SCEMS v1.0`
- Release branch: `release/construction-system-v1.0`
- Release date: `2026-03-11`
- Release owner: `Codex (proxy execution, pending business sign-off)`

## 2. Release Windows and Ownership

| Item | Window | Owner | Status |
|---|---|---|---|
| Release window | 2026-03-11 17:17 ~ 17:30 | release manager (proxy: Codex) | executed |
| Rollback window | 2026-03-11 17:30 ~ 19:30 | system administrator | reserved |
| Observation window (24h) | 2026-03-11 17:30 ~ 2026-03-12 17:30 | on-duty owner | in progress |

## 3. Release Execution Log

| Step | Command/Action | Result | Evidence Path |
|---|---|---|---|
| Deployment readiness | `make ps` | PASS | terminal output (2026-03-11 17:17) |
| Module install/upgrade | `make mod.install` / `make mod.upgrade` | PASS (reused from Phase 5 rehearsal) | `docs/releases/phase_5_verification_deployment_execution_report.en.md` |
| Go-live switch | `make verify.portal.my_work_smoke.container DB_NAME=sc_demo` + `make verify.portal.scene_package_ui_smoke.container DB_NAME=sc_demo` | PASS | `/mnt/artifacts/codex/my-work-smoke-v10_2/20260311T091718` + `/mnt/artifacts/codex/portal-scene-package-ui-v10_6/20260311T091722` |
| Stable rollback rehearsal | `make scene.rollback.stable` | PASS | terminal output (2026-03-11 17:17) |

## 4. Post-release Spot Checks

| Check Item | Result | Notes |
|---|---|---|
| Login and My Work | PASS | `verify.portal.my_work_smoke.container` |
| Projects Ledger and Console | PASS | `verify.portal.scene_package_ui_smoke.container` |
| Contract/Cost/Finance/Risk | PASS | `verify.runtime.surface.dashboard.strict.guard` (W6-02 evidence) |
| Management readonly view | PASS | `verify.role.management_viewer.readonly.guard` |

## 5. Release Conclusion
- Conclusion: `conditional pass (to become PASS after 24h observation)`
- Blocking items: `none (current P0=0)`
- Approver: `pending business owner sign-off`
