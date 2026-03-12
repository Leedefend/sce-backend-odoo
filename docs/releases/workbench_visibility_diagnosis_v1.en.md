# Workbench Visibility Diagnosis Report (v1)

## Background
- Symptom: `sc_fx_pm` had significantly lower `today_factual_rate` than `finance/owner`.
- Goal: confirm whether the root cause is permission policy, demo ownership, or frontend rendering.

## Evidence
- Environment: `sc_prod_sim` (prod-sim).
- Data points: `workspace_home.diagnostics.extraction_stats` and `ext_facts.smart_construction_core.workspace_business_source` from `app.init`.
- Compared accounts: `sc_fx_pm` / `sc_fx_finance` / `sc_fx_executive`.

Key observations (before fix):
- `sc_fx_pm`: `task_items=0, payment_requests=0, risk_actions=2`
- `sc_fx_finance`: `task_items=0, payment_requests>0, risk_actions=2`
- `sc_fx_executive`: `task_items=0, payment_requests>0, risk_actions=2`

Conclusion: PM lacked factual action sources; this was not a frontend issue.

## Root Cause

### 1) Permission side (by design)
- PM fixture account does not include finance capability groups.
- `payment.request` invisibility for PM is expected under current ACL/capability baseline.

### 2) Ownership side (demo data)
- Demo project/task ownership was biased toward system/admin users.
- PM did not have a stable factual task pool for `today_actions`.

### 3) Not root cause
- Frontend layout/style did not cause this discrepancy.
- Hit-rate logic was correct; source visibility was the bottleneck.

## Fix Strategy (executed)

### A. Keep ACL baseline unchanged
- No permission broadening for PM.

### B. Add PM-visible factual source
- Added `project_actions` in `system_init` extension (factual actions from visible projects).
- Included `project_actions` in business-first `today_actions` source order.

### C. Backfill demo data
- Added Round 2 demo records for tasks and payment requests (projects 001/002).
- Loaded by upgrading `smart_construction_demo` in `sc_prod_sim`.

## Post-fix Result
- Latest report: `artifacts/backend/workbench_extraction_hit_rate_report.md`.

Result summary:
- `pm`: `today_factual_rate = 83.33%`
- `finance`: `today_factual_rate = 100%`
- `owner`: `today_factual_rate = 100%`
- `risk_factual_rate = 100%` for all roles

## Guardrails
- For new demo roles, ensure at least two factual source categories are visible (task/risk/payment).
- Keep dual metrics in workbench diagnostics:
  - `business_rate` (semantic business)
  - `factual_rate` (factual records)

## One-line Conclusion
- The issue was caused by role-visible factual source scarcity (permission + ownership), and is fixed via PM-visible project actions plus Round 2 demo backfill, without changing the permission baseline.

