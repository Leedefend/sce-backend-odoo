# SCEMS v1.0 Execution Board

Status legend: `TODO` / `DOING` / `BLOCKED` / `DONE`

## 1. Milestones

| Phase | Goal | Status | Key Output |
|---|---|---|---|
| Phase 0 | Scope freeze | DONE | `release_scope_v1.en.md` `system_asset_inventory.en.md` `release_gap_analysis.en.md` |
| Phase 1 | Navigation convergence | DONE | delivery-policy main-nav lock report |
| Phase 2 | Core scenario closure | DOING | acceptance records for 4 key scenarios (workspace baseline closed) |
| Phase 3 | Role/permission system | DONE | role matrix + ACL/visibility verification + exit-readiness report |
| Phase 4 | Frontend stability | DONE | unified page framework and block conventions (with user/hud and container smoke evidence) |
| Phase 5 | Verification/deployment | DONE | release verification bundle + deployment docs + deployment/rollback rehearsal evidence |
| Phase 6 | Pilot and launch | DOING | pilot kickoff report + v1.0 release record |

## 2. Current Window (W1)

- Release-branch kickoff record: `docs/releases/phase_0_scope_freeze_execution.en.md`

### W1 Goals
- Finish Phase 1 (navigation convergence)
- Start Phase 2 (core scenario closure)

### W1 Tasks

| ID | Task | Phase | Status | Acceptance |
|---|---|---|---|---|
| W1-01 | Lock `construction_pm_v1` main-nav allowlist | P1 | DONE | policy and runtime output are aligned |
| W1-02 | Publish nav-to-scene mapping | P1 | DONE | all 7 nav items are traceable |
| W1-03 | Add `project.management` 7-block contract verify | P2 | DONE | verify can assert all 7 blocks |
| W1-04 | Close minimum loop for `my_work.workspace` | P2 | DONE | todo/my projects/quick links visible |
| W1-05 | Close ledger-to-management route chain | P2 | DONE | `projects.ledger -> project.management` reachable |

## 3. Risk List

| Risk | Level | Symptom | Mitigation |
|---|---|---|---|
| Semantic-contract drift | High | block exists but metric semantics drift | define required block fields + whitelist |
| Role visibility inconsistency | Medium | unstable cross-role visibility | add role-matrix verification scripts |
| Doc/implementation divergence | Medium | docs lag behind delivery | mandatory board update per phase close |

## 4. Current Window (W2)

| ID | Task | Phase | Status | Acceptance |
|---|---|---|---|---|
| W2-01 | Add management-viewer readonly guard | P3 | DONE | `verify.role.management_viewer.readonly.guard` PASS |
| W2-02 | Unify `project_member` role mapping | P3 | DONE | `verify.role.project_member.unification.guard` PASS |
| W2-03 | Add system-admin minimum-permission audit report | P3 | DONE | `verify.role.system_admin.minimum_permission_audit.guard` PASS |

### W3 Tasks (Phase 3 Exit Closeout)

| ID | Task | Phase | Status | Acceptance |
|---|---|---|---|---|
| W3-01 | ACL minimum-set guard | P3 | DONE | `verify.role.acl.minimum_set.guard` PASS |
| W3-02 | Relation access-policy consistency audit | P3 | DONE | `verify.relation.access_policy.consistency.audit` PASS |
| W3-03 | Close 3 runtime-focused cases | P3 | DONE | `verify.project.dashboard.role_runtime.guard` + `verify.scene.permission_reasoncode_deeplink.guard` PASS |

### W4 Tasks (Phase 4 Frontend Stability)

| ID | Task | Phase | Status | Acceptance |
|---|---|---|---|---|
| W4-01 | Frontend page/block static guard baseline | P4 | DONE | 9 frontend guards PASS |
| W4-02 | Build and typecheck baseline | P4 | DONE | `verify.frontend.build` + `verify.frontend.typecheck.strict` PASS |
| W4-03 | Lint baseline debt closeout | P4 | DONE | `verify.frontend.lint.src` 0 errors (6 warnings remain) |
| W4-04 | user/hud cross-mode stability checks | P4 | DONE | hud navigation/orchestration variance/trace smoke all PASS |
| W4-05 | Page framework and interaction closeout | P4 | DONE | A/C verification command chain all PASS |
| W4-06 | Severe-console-error evidence | P4 | DONE | fe/hud/render-mode container smoke all PASS |

### W5 Tasks (Phase 5 Verification & Deployment)

| ID | Task | Phase | Status | Acceptance |
|---|---|---|---|---|
| W5-01 | Release-critical verify baseline | P5 | DONE | phase_next/runtime strict/scene governance PASS |
| W5-02 | Core smoke and key role paths | P5 | DONE | my_work smoke + role floor + management readonly PASS |
| W5-03 | Deployment/demo/UAT docs completion | P5 | DONE | deploy/demo/UAT docs available |
| W5-04 | Deployment and rollback rehearsal evidence | P5 | DONE | `make up`/`make mod.install`/`make mod.upgrade`/`make scene.rollback.stable` PASS |
| W5-05 | Release conclusion archival | P5 | DONE | Phase 5 report and checklist explicitly record a pass |

### W6 Tasks (Phase 6 Pilot and Launch)

| ID | Task | Phase | Status | Acceptance |
|---|---|---|---|---|
| W6-01 | Freeze pilot org and sample data scope | P6 | DONE | `phase_6_pilot_scope_definition.en.md` covers roles/samples/issue path |
| W6-02 | Run core-path pilot and severity closure | P6 | DOING | full-chain rehearsal done and P0 blockers reduced to zero |
| W6-03 | Execute launch and 24h observation review | P6 | TODO | launch record, spot-check, and 24h monitoring conclusion available |

## 5. Phase Entry Criteria

### Phase 1 -> Phase 2
- `construction_pm_v1` main navigation lock completed
- navigation/scene/delivery policy alignment verified

### Phase 2 -> Phase 3
- 4 core scenarios demo-ready
- `project.management` 7-block contract passes verification
