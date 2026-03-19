# 9-Module Pre-Go-Live Acceptance Matrix v1

## Notes
- This matrix is for delivery seal-off acceptance, not feature planning.
- Status values: `PASS` / `FAIL` / `PENDING`.

| Module | Key Scene Entry | Key Roles | Data Prerequisite | Mandatory Verification | Status |
|---|---|---|---|---|---|
| Project Management | `projects.list` / `projects.ledger` / `projects.intake` | PM/Executive | Project master data | scene contract + list/form smoke | PENDING |
| Project Cockpit | `project.management` / `portal.dashboard` | Executive/PM | Project+risk aggregates | dashboard contract + role journey | PENDING |
| Contract Management | `contract.center` / `contracts.workspace` | Contract Manager/Executive | Contract master data | contract guard + anomaly flow | PENDING |
| Cost Management | `cost.*` | Cost Manager/PM | Budget/ledger/progress | list/action/batch smoke | PENDING |
| Finance | `finance.*` / `payments.*` | Finance Manager | payment/settlement data | finance journey + settlement guard | PENDING |
| Risk Management | `risk.center` / `risk.monitor` | PM/Executive | risk action data | risk flow smoke + escalation check | PENDING |
| Task Management | `task.center` / `my_work.workspace` | All roles | workitem data | workitem query + action closure | PENDING |
| Data & Dictionary | `data.dictionary` | Config/Implementation | business dictionary data | dictionary CRUD smoke | PENDING |
| Configuration Center | `config.project_cost_code` | Config Admin | cost-code master data | config read/write smoke | PENDING |

## Exit Criteria
- All 9 modules move from `PENDING/FAIL` to `PASS`.
- Each module includes at least one system-bound evidence item (command, DB, commit, result).

