# SCEMS v1.0 Execution Board

Status legend: `TODO` / `DOING` / `BLOCKED` / `DONE`

## 1. Milestones

| Phase | Goal | Status | Key Output |
|---|---|---|---|
| Phase 0 | Scope freeze | DONE | `release_scope_v1.en.md` `system_asset_inventory.en.md` `release_gap_analysis.en.md` |
| Phase 1 | Navigation convergence | DONE | delivery-policy main-nav lock report |
| Phase 2 | Core scenario closure | DOING | acceptance records for 4 key scenarios (workspace baseline closed) |
| Phase 3 | Role/permission system | DOING | role matrix + ACL/visibility verification |
| Phase 4 | Frontend stability | TODO | unified page framework and block conventions |
| Phase 5 | Verification/deployment | TODO | release verification bundle + deployment docs |
| Phase 6 | Pilot and launch | TODO | pilot report + v1.0 release record |

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
| W3-03 | Close 3 runtime-focused cases | P3 | DOING | 7-block/scene reason-code/deep-link policy checks pass |

## 5. Phase Entry Criteria

### Phase 1 -> Phase 2
- `construction_pm_v1` main navigation lock completed
- navigation/scene/delivery policy alignment verified

### Phase 2 -> Phase 3
- 4 core scenarios demo-ready
- `project.management` 7-block contract passes verification
