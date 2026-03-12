# Demo Data Backfill Plan (Round 2)

## Goal
- Provide stable factual demo records for workbench action pipelines.
- Cover three primary action sources: tasks, payment requests, and risk signals.
- Ensure factual records are visible in `today_actions` and `risk.actions` across roles.

## Coverage
- Workbench home (`portal.dashboard` / workspace home)
- Task Center (`task.center`)
- Payment Requests (`finance.payment_requests`)
- Risk Center (`risk.center`)

## Models and Data Sources
- `project.task`
  - Target states: `sc_state in (ready, in_progress)`; fallback `kanban_state in (normal, blocked)`.
  - Target volume: at least 3 actionable tasks per demo project.
- `payment.request`
  - Target states: `draft/submit/approve/approved`.
  - Target volume: at least 2 payment requests per demo project.
- `project.risk` (or `project.project.health_state` fallback)
  - Target states: `warn/risk`.
  - Target volume: at least 1 risk signal per demo project.

## Delivered in this backend iteration
- Real business action feeds are injected in `system_init` extension:
  - `task_items`
  - `payment_requests`
  - `risk_actions`
- Workbench diagnostics now expose dual metrics:
  - `business_rate` (semantic business)
  - `factual_rate` (factual records)

## Next Data Backfill Actions
1. Add Round 2 demo data file in `smart_construction_demo` (recommended: `data/scenario/s10_contract_payment/25_workbench_actions.xml`).
2. Backfill minimal closed-loop task/payment/risk records for `sc_demo_project_001/002`.
3. Re-verify with `make demo.reset` + `make verify.workbench.extraction_hit_rate.report`.

## Acceptance
- In `artifacts/backend/workbench_extraction_hit_rate_report.md`, all roles show:
  - `today_factual_rate > 0`
  - `risk_factual_rate > 0`
- Workbench first screen displays factual action/risk rows, not only templates.

