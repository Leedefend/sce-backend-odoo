# SCEMS v1.0 Phase 6: Pilot Rehearsal Record (W6-02)

## 1. Rehearsal Batch

| Batch | Time | Participants | Conclusion | Recorder |
|---|---|---|---|---|
| Batch-1 | 2026-03-11 | PM/Project Member/Finance/Management | PASS | Codex |

## 2. Core Path Checks

| Path | Result | Notes |
|---|---|---|
| Login -> My Work | PASS | `make verify.portal.my_work_smoke.container DB_NAME=sc_demo` |
| My Work -> Projects Ledger | PASS | `make verify.portal.scene_package_ui_smoke.container DB_NAME=sc_demo` |
| Projects Ledger -> Project Management Console | PASS | `make verify.portal.scene_package_ui_smoke.container DB_NAME=sc_demo` |
| Console -> Contract Execution | PASS | `make verify.runtime.surface.dashboard.strict.guard` |
| Console -> Cost Control | PASS | `make verify.runtime.surface.dashboard.strict.guard` |
| Console -> Finance Management | PASS | `make verify.runtime.surface.dashboard.strict.guard` |
| Console -> Risk Alerts | PASS | `make verify.runtime.surface.dashboard.strict.guard` |

## 3. Role-based Validation

| Role | Key Checks | Result | Notes |
|---|---|---|---|
| Project Manager | overview, progress, risk handling entry | PASS | scene package + dashboard strict guard |
| Project Member | task collaboration and visibility | PASS | my_work smoke + scene package ui smoke |
| Finance Collaborator | payment request, finance view, consistency | PASS | dashboard strict guard |
| Management Viewer | readonly access, metrics visibility, risk summary | PASS | `make verify.role.management_viewer.readonly.guard` |

## 4. Issue Severity Closure Summary

| Severity | New | Closed | Open | Launch Blocking |
|---|---:|---:|---:|---|
| P0 | 0 | 0 | 0 | No |
| P1 | 0 | 0 | 0 | No |
| P2 | 0 | 0 | 0 | No |

## 5. W6-02 Decision

- Decision: `DONE`
- Conditions for `DONE`:
  - all core path checks completed;
  - all key role validations completed;
  - open `P0` count remains `0`.
