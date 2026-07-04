# 9-Module Pre-Go-Live Acceptance Matrix v1

## Notes
- This matrix is for delivery seal-off acceptance, not feature planning.
- Status values: `PASS` / `CLOSED`.
- Final closeout date: `2026-07-05`

| Module | Key Scene Entry | Key Roles | Data Prerequisite | Mandatory Verification | Status |
|---|---|---|---|---|---|
| Project Management | `projects.list` / `projects.ledger` / `projects.intake` | PM/Executive | Project master data | `verify.scene.delivery.readiness.role_matrix` | PASS |
| Project Cockpit | `project.management` / `portal.dashboard` | Executive/PM | Project+risk aggregates | `verify.project.dashboard.contract` + role matrix | PASS |
| Contract Management | `contract.center` / `contracts.workspace` | Contract Manager/Executive | Contract master data | `verify.scene.delivery.readiness.role_matrix` | PASS |
| Cost Management | `cost.*` | Cost Manager/PM | Budget/ledger/progress | `verify.scene.delivery.readiness.role_matrix` | PASS |
| Finance | `finance.*` / `payments.*` | Finance Manager | payment/settlement data | `verify.portal.payment_request_approval_all_smoke.container` | PASS |
| Risk Management | `risk.center` / `risk.monitor` | PM/Executive | risk action data | `verify.scene.delivery.readiness.role_matrix` | PASS |
| Task Management | `task.center` / `my_work.workspace` | All roles | workitem data | `verify.scene.delivery.readiness.role_matrix` | PASS |
| Data & Dictionary | `data.dictionary` | Config/Implementation | business dictionary data | `verify.scene.delivery.readiness.role_matrix` | PASS |
| Configuration Center | `config.project_cost_code` | Config Admin | cost-code master data | `verify.scene.delivery.readiness.role_matrix` | PASS |

## Exit Criteria
- All 9 modules are at `PASS`.
- Each module includes at least one system-bound evidence item (command, DB, commit, result).
- Fixed gate: `make verify.release.delivery_9_module.final_closeout.guard`
- Cross evidence: `verify.portal.payment_request_approval_field_consumer_audit`, `verify.release.master_stage.final_closeout.guard`
