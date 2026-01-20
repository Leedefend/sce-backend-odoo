# P3 Audit Query Contract v0.1

## 0. Purpose

P3 reconciliation must be traceable. Every cumulative change must have audit evidence.
This document defines query contracts only; no API implementation here.

## 1. AuditRecord v1 Reference

Source model: `sc.audit.log`

Fields:
- event_code
- action
- model
- res_id
- actor_uid
- actor_login
- ts
- before_json
- after_json
- reason
- trace_id
- company_id
- project_id

## 2. Query Dimensions

Q1: By Project
- Filter: project_id

Q2: By Target
- Filter: model + res_id

Q3: By Event Code
- Filter: event_code in (...)

Q4: By Actor
- Filter: actor_uid or actor_login

Q5: By Period Window
- Filter: ts between [start, end]

Q6: By Trace Correlation
- Filter: trace_id

## 3. Minimal Response Shape

Required fields for reconciliation and UI rendering:
- ts
- event_code
- model
- res_id
- actor_login
- trace_id
- reason (nullable)
- before
- after

Notes:
- before/after are derived from before_json/after_json (string or parsed JSON).

## 4. Ordering / Pagination

- Order: ts desc, id desc
- Pagination: limit + offset

## 5. Event Code Dictionary

| event_code | model |
| --- | --- |
| task_ready | project.task |
| task_started | project.task |
| task_done | project.task |
| task_cancelled | project.task |
| progress_submitted | project.progress.entry |
| progress_reverted | project.progress.entry |
| period_locked | project.cost.period |
| period_unlocked | project.cost.period |
| contract_bound | sc.settlement.order.line |
| contract_unbound | sc.settlement.order.line |
| payment_submitted | payment.request |
| payment_approved | payment.request |
| payment_rejected | payment.request |
| payment_paid | payment.request |

## 6. Reconciliation Linkage

- contract_amount_total
  - Evidence: contract create/update events (gap: no explicit event code; P3 runtime to add)

- settlement_amount_approved_cum
  - Evidence: settlement approve/done events (gap: missing event codes; P3 runtime to add)

- payment_requested_cum
  - Evidence: payment_submitted / payment_approved

- payment_paid_cum
  - Evidence: payment_paid

- period_locked_cost_total
  - Evidence: period_locked

- partner reconciliation aggregates
  - Evidence: payment_submitted / payment_approved / payment_paid + settlement events (gap: settlement event codes)

Gap list (P3 runtime, not in this sprint):
- settlement submit/approve/done event codes
- contract change event codes (amount/terms)
