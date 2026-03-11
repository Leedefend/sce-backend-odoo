# SCEMS v1.0 Phase 6: Pilot Scope and Execution Baseline (W6-01)

## 1. Participant Roles and Responsibilities

| Role | Headcount | Primary Responsibility | Acceptance Output |
|---|---:|---|---|
| Project Manager | 2 | Run the end-to-end project path and approvals | Full-path operation log + issue list |
| Project Member | 3 | Execute tasks and submit progress/business data | Scenario usability feedback |
| Finance Collaborator | 2 | Validate payment requests, payments, and ledger consistency | Finance/payment path verification record |
| Management Viewer | 1 | Validate dashboard readability and decision visibility | Management-view experience conclusion |
| System Administrator | 1 | Ensure environment, permissions, and rollback window | Launch window and rollback record |

## 2. Pilot Sample Data

| Domain | Sample Count | Minimum Coverage |
|---|---:|---|
| Projects | 3 | one in-progress, one near-closeout, one risk-alert |
| Contracts | 6 | main contracts, subcontracts, change contracts |
| Cost | 9 | budget, actual, deviation samples |
| Finance | 6 | payment requests, payment results, cash in/out |
| Risk | 8 | progress/cost/contract/finance risk samples |

## 3. Issue Reporting Path and Severity

- Reporting entry: step number from `docs/demo/system_demo_v1.en.md` + real screenshot.
- Ledger file: `docs/releases/phase_6_issue_ledger.en.md`.
- Severity levels:
  - `P0`: launch-blocking or core-chain unavailable.
  - `P1`: core function available but incorrect result/high risk.
  - `P2`: usability/experience issue, non-blocking for launch.

## 4. Launch Windows and Owners (Baseline)

| Item | Baseline Window | Owner |
|---|---|---|
| Pilot window | T+1 ~ T+3 | Product owner + project manager |
| Issue convergence window | T+4 ~ T+5 | Engineering lead |
| Launch window | T+6 | Release manager |
| Rollback window | within 2h after launch | System administrator |

## 5. W6-01 Done Definition

- Participant list is confirmed and executable.
- Sample set covers project/contract/cost/finance/risk.
- Issue path, severity standard, and ledger location are traceable.
