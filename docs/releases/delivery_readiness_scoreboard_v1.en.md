# Delivery Readiness Scoreboard v1

## 1. Purpose

This scoreboard provides a single delivery-facing view for delivery managers, implementation teams, and engineering, including:

- readiness status for the 9 delivery modules
- frontend quality gate status
- system-bound verification evidence
- known limits and next actions

---

## 2. Current Snapshot

- Branch: `codex/delivery-sprint-seal-gaps`
- Scope: ActionView frontend main path + release sealing docs
- Conclusion: `P0 frontend static blockers are cleared; module-level system-bound smoke can proceed`

### 2.1 Gate Results (Current Iteration)

- `pnpm -C frontend lint`: pass (`0 errors`, warnings only)
- `pnpm -C frontend typecheck:strict`: pass
- `pnpm -C frontend build`: pass

### 2.2 Payment Approval Smoke N+2 Migration Status

- `live_no_allowed_actions`: sunset completed (N+2)
- `live_no_executable_actions`: single source of truth
- Approval aggregate chain (strict audit mode):
  - `PAYMENT_APPROVAL_NEED_UPGRADE=0 PAYMENT_APPROVAL_FIELD_AUDIT_STRICT=1 make verify.portal.payment_request_approval_all_smoke.container` passed
- Field consumer audit:
  - `make verify.portal.payment_request_approval_field_consumer_audit` passed (`unexpected_deprecated_refs=0`)

---

## 3. Nine-Module Readiness Matrix (Delivery View)

| Module | Representative Scenes | Status | Evidence | Next Step |
|---|---|---|---|---|
| Project Management | `projects.list` / `projects.intake` | `IN_PROGRESS` | Navigation and capability mapping are in place; frontend gate passes | Add PM journey smoke |
| Project Execution | `projects.execution` / `projects.detail` | `IN_PROGRESS` | Scenes are registered and reachable | Add execution-center data validation |
| Task Management | `task.center` | `IN_PROGRESS` | Scene entry exists | Add task-center list/filter smoke |
| Risk Management | `risk.center` / `risk.monitor` | `IN_PROGRESS` | Scene entries exist | Add risk-alert closed-loop checks |
| Cost Management | `cost.project_boq` / `cost.project_budget` | `IN_PROGRESS` | ActionView path stability improved | Add budget/ledger real-data checks |
| Contract Management | `contract.center` | `IN_PROGRESS` | Scene entry exists | Add contract-center action-chain smoke |
| Finance Management | `finance.payment_requests` / `finance.center` | `IN_PROGRESS` | Finance entries are present in nav | Add approval/ledger flow checks |
| Data & Dictionary | `data.dictionary` | `READY_FOR_PILOT` | Clear entry and narrow dependency scope | Add sample-data regression |
| Config Center | `config.project_cost_code` | `READY_FOR_PILOT` | Admin-facing entry is clear | Add admin-role acceptance |

Status definition:

- `READY_FOR_PILOT`: ready to enter pilot acceptance
- `IN_PROGRESS`: features/entries exist, but key journey evidence is still missing
- `BLOCKED`: hard blockers prevent delivery

---

## 4. Gaps Closed in This Iteration

1. Cleared ActionView frontend lint/type blockers (`any`, unused, regex, etc.)
2. Passed the three frontend gate checks (lint/typecheck/build)
3. Landed a full set of sprint docs (Blockers / 9-module matrix / Week-1 seal plan)

---

## 5. Known Limits

1. System-bound journey evidence per role is still needed for all 9 modules
2. Scene Contract field-level strict validation is not fully sealed yet
3. Module status here is a delivery-governance signal, not a formal business sign-off

---

## 6. Recommended Next Iteration (Priority)

### P0 (Immediate)

1. Produce smoke evidence for PM / Finance / Procurement / Executive role journeys
2. Add “data prerequisites + acceptance steps + result” for each of the 9 modules
3. Track scene contract/provider shape gaps as release blockers

### P1 (Next)

1. Record latest passing environment tuple (DB/seed/bundle/commit)
2. Wire this scoreboard into the release checklist
